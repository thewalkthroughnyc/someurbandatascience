"""Pipeline orchestrator: pulls crash + Citi Bike data, attempts segmentation
/ denominator / stats, and writes one static JSON the front end reads.

Designed to run end-to-end TODAY even though segmentation, the denominator,
and the statistics are stubs: block identity/order/treated-flag/LTS come
straight from config and always populate. Anything that needs a stub
(raw counts need block geometry from segmentation; rates need the
denominator; the hover-panel effect estimate needs DiD/interval) is
attempted, and on NotImplementedError the corresponding field is written as
null with `"computed": false` rather than crashing the whole build. As you
fill in each stub, its section of the JSON starts populating — no pipeline
rewiring needed.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from config import corridor as cfg  # noqa: E402

from bedford_corridor.denominator import attribute_trips_to_blocks, trips_per_block  # noqa: E402
from bedford_corridor.ingest.centerline import fetch_named_streets  # noqa: E402
from bedford_corridor.ingest.crashes import (  # noqa: E402
    clean_crashes,
    clean_person,
    fetch_crashes,
    fetch_person,
    filter_cyclist_rows,
    join_crashes_person,
)
from bedford_corridor.routing.cache import RouteCache  # noqa: E402
from bedford_corridor.segmentation import segment_corridor  # noqa: E402
from bedford_corridor.stats.did import estimate_did  # noqa: E402
from bedford_corridor.stats.interval import small_count_interval  # noqa: E402

DATA_CACHE = REPO_ROOT / "data_cache"
WEB_DATA_OUT = REPO_ROOT / "web" / "data" / "corridor.json"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def block_id_for(from_street: str, to_street: str) -> str:
    return f"{slugify(from_street)}__{slugify(to_street)}"


def base_blocks() -> list[dict]:
    """Block identity/order/treated-flag/LTS — always available, no stub
    dependency. This alone is enough to render view 3 (LTS) and the strip
    map's static structure.
    """
    lts_config = yaml.safe_load((REPO_ROOT / "config" / "lts.yaml").read_text())
    lts_by_pair = {
        (b["from_street"], b["to_street"]): b for b in lts_config["blocks"]
    }

    blocks = []
    treated_set = {tuple(pair) for pair in cfg.TREATED_BLOCKS}
    for i in range(len(cfg.CROSS_STREETS) - 1):
        from_street, to_street = cfg.CROSS_STREETS[i], cfg.CROSS_STREETS[i + 1]
        lts_entry = lts_by_pair.get((from_street, to_street), {})
        blocks.append(
            {
                "block_id": block_id_for(from_street, to_street),
                "sequence_number": i,
                "from_street": from_street,
                "to_street": to_street,
                "from_coords": cfg.CROSS_STREET_COORDS.get(from_street),
                "to_coords": cfg.CROSS_STREET_COORDS.get(to_street),
                "is_treated": (from_street, to_street) in treated_set,
                "lts": lts_entry.get("lts"),
                "lts_notes": lts_entry.get("notes", ""),
            }
        )
    return blocks


def try_segment_geometry() -> gpd.GeoDataFrame | None:
    try:
        centerline = fetch_named_streets(cfg.CORRIDOR_BBOX)
    except Exception as e:  # pragma: no cover - network dependent
        print(f"  [warn] could not fetch centerline geometry: {e}", file=sys.stderr)
        return None
    try:
        return segment_corridor(cfg.CROSS_STREETS, cfg.TREATED_BLOCKS, centerline)
    except NotImplementedError:
        print("  [stub] segmentation.segment_corridor not implemented — raw counts and "
              "rates will be null until it is.", file=sys.stderr)
        return None


def try_raw_counts(blocks_geo: gpd.GeoDataFrame | None) -> dict[str, dict[str, dict]] | None:
    """block_id -> {'before': {...}, 'after': {...}}. None if geometry unavailable."""
    if blocks_geo is None:
        return None

    crashes = clean_crashes(
        fetch_crashes(
            date_from=cfg.PROTECTED_LANE_INSTALL_DATE,
            date_to=datetime.date.today(),
            bbox=cfg.CORRIDOR_BBOX,
            domain=cfg.SOCRATA_DOMAIN,
            dataset_id=cfg.SOCRATA_CRASHES_DATASET_ID,
        )
    )
    if crashes.empty:
        return None

    persons = filter_cyclist_rows(
        clean_person(
            fetch_person(
                date_from=cfg.PROTECTED_LANE_INSTALL_DATE,
                date_to=datetime.date.today(),
                domain=cfg.SOCRATA_DOMAIN,
                dataset_id=cfg.SOCRATA_PERSON_DATASET_ID,
            )
        )
    )
    joined = join_crashes_person(crashes, persons)

    points = gpd.GeoDataFrame(
        joined,
        geometry=gpd.points_from_xy(joined["longitude"], joined["latitude"]),
        crs="EPSG:4326",
    ).dropna(subset=["geometry"])

    # Buffer block lines by 25m in a projected (metric) CRS — never buffer
    # in EPSG:4326, degrees aren't meters. Reproject both sides consistently.
    blocks_proj = blocks_geo.to_crs("EPSG:32618")
    blocks_proj["geometry"] = blocks_proj.geometry.buffer(25)
    points_proj = points.to_crs("EPSG:32618")

    joined_blocks = gpd.sjoin(points_proj, blocks_proj[["block_id", "geometry"]], how="inner", predicate="within")

    counts: dict[str, dict[str, dict]] = {}
    for block_id, group in joined_blocks.groupby("block_id"):
        before = group[group["crash_date"].dt.date < cfg.TREATMENT_DATE]
        after = group[group["crash_date"].dt.date >= cfg.TREATMENT_DATE]
        counts[block_id] = {
            "before": {"cyclist_injuries": int(len(before)), "computed": True},
            "after": {"cyclist_injuries": int(len(after)), "computed": True},
        }
    return counts


def try_rates(blocks_geo: gpd.GeoDataFrame | None, raw_counts: dict | None) -> dict | None:
    if blocks_geo is None or raw_counts is None:
        return None
    try:
        cache = RouteCache(DATA_CACHE / "routes.sqlite")
        # NOTE: trip ingestion/attribution needs monthly Citi Bike CSVs
        # already downloaded into data_cache/citibike/ (see README "Data
        # setup") — build_json does not fetch them automatically since the
        # file list depends on which months you want in the study window.
        trips = pd.DataFrame(columns=["ride_id", "start_station_id", "end_station_id"])
        attributed = attribute_trips_to_blocks(trips, blocks_geo, cache)
        denom = trips_per_block(
            attributed, blocks_geo,
            pd.Timestamp(cfg.PROTECTED_LANE_INSTALL_DATE), pd.Timestamp(cfg.TREATMENT_DATE),
        )
    except NotImplementedError:
        print("  [stub] denominator not implemented — view 2 (rate) will be null until it is.",
              file=sys.stderr)
        return None

    rates = {}
    denom_by_block = denom.set_index("block_id")["modeled_trips"].to_dict()
    interval_stub_warned = False
    for block_id, counts in raw_counts.items():
        trips_n = denom_by_block.get(block_id)
        if not trips_n:
            rates[block_id] = {"computed": False}
            continue

        after_injuries = counts["after"]["cyclist_injuries"]
        try:
            interval = small_count_interval(count=after_injuries, exposure=trips_n)
            interval_json = {
                "rate": interval.rate, "low": interval.low, "high": interval.high,
                "is_null": interval.is_null,
            }
        except NotImplementedError:
            if not interval_stub_warned:
                print("  [stub] stats.interval not implemented — per-block intervals will be null.",
                      file=sys.stderr)
                interval_stub_warned = True
            interval_json = None

        rates[block_id] = {
            "computed": True,
            "before": counts["before"]["cyclist_injuries"] / trips_n * 10_000,
            "after": after_injuries / trips_n * 10_000,
            "after_interval": interval_json,
        }
    return rates


def build(output_path: Path = WEB_DATA_OUT) -> dict:
    print("Building corridor.json ...", file=sys.stderr)
    blocks = base_blocks()

    blocks_geo = try_segment_geometry()
    raw_counts = try_raw_counts(blocks_geo)
    rates = try_rates(blocks_geo, raw_counts)

    for block in blocks:
        bid = block["block_id"]
        block["raw_counts"] = (raw_counts or {}).get(bid, {"computed": False})
        block["rate_per_10k_trips"] = (rates or {}).get(bid, {"computed": False})

    treated_ids = [b["block_id"] for b in blocks if b["is_treated"]]
    control_ids = [b["block_id"] for b in blocks if not b["is_treated"]]

    did_result = None
    try:
        # Requires outcomes built from raw_counts across sub-periods, which
        # in turn requires segmentation + enough post-treatment history —
        # left null until both the geometry stub and enough time have passed.
        estimate_did(pd.DataFrame(), treated_ids, control_ids, cfg.TREATMENT_DATE)
    except NotImplementedError:
        print("  [stub] stats.did not implemented — corridor-level effect estimate will be null.",
              file=sys.stderr)

    output = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "treatment_date": cfg.TREATMENT_DATE.isoformat(),
        "protected_lane_install_date": cfg.PROTECTED_LANE_INSTALL_DATE.isoformat(),
        "corridor": {
            "street": cfg.CORRIDOR_STREET,
            "start": cfg.CORRIDOR_START,
            "end": cfg.CORRIDOR_END,
        },
        "blocks": blocks,
        "did_result": did_result,
        "data_status": {
            "segmentation_available": blocks_geo is not None,
            "raw_counts_available": raw_counts is not None,
            "rates_available": rates is not None,
            "did_available": did_result is not None,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2))
    print(f"Wrote {output_path}", file=sys.stderr)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=WEB_DATA_OUT)
    args = parser.parse_args()
    build(args.out)
