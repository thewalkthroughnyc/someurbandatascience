"""Ingest Citi Bike monthly trip CSVs and normalize them to one schema.

Citi Bike changed their column schema in Feb 2021 (see
config/corridor.py:CITIBIKE_SCHEMA_CURRENT / _LEGACY). This study's date
range (pre-Dec-2024 baseline through present) only ever needs the current
schema, but both are handled here per project instructions, and because a
"handle both, detect which one you got" reader is exactly the kind of
boilerplate this project's rules say to just build.

Trip-to-block attribution (which blocks a trip's route crosses) is NOT here
— that's the stubbed denominator logic. This module only gets clean,
normalized trip rows with a station pair and a timestamp.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

# Normalized output schema, regardless of which raw schema came in.
NORMALIZED_COLUMNS = [
    "ride_id",
    "started_at",
    "ended_at",
    "start_station_id",
    "start_station_name",
    "start_lat",
    "start_lng",
    "end_station_id",
    "end_station_name",
    "end_lat",
    "end_lng",
    "member_casual",
]

_CURRENT_RENAME = {
    "ride_id": "ride_id",
    "started_at": "started_at",
    "ended_at": "ended_at",
    "start_station_id": "start_station_id",
    "start_station_name": "start_station_name",
    "start_lat": "start_lat",
    "start_lng": "start_lng",
    "end_station_id": "end_station_id",
    "end_station_name": "end_station_name",
    "end_lat": "end_lat",
    "end_lng": "end_lng",
    "member_casual": "member_casual",
}

_LEGACY_RENAME = {
    "starttime": "started_at",
    "stoptime": "ended_at",
    "start station id": "start_station_id",
    "start station name": "start_station_name",
    "start station latitude": "start_lat",
    "start station longitude": "start_lng",
    "end station id": "end_station_id",
    "end station name": "end_station_name",
    "end station latitude": "end_lat",
    "end station longitude": "end_lng",
    "usertype": "member_casual",
}


def detect_schema(columns: list[str]) -> str:
    """Return 'current' or 'legacy' based on which columns are present.
    Raises if neither schema's distinguishing columns match — better to fail
    loudly than silently emit an all-null normalized frame.
    """
    cols = set(columns)
    if "ride_id" in cols and "started_at" in cols:
        return "current"
    if "starttime" in cols and "tripduration" in cols:
        return "legacy"
    raise ValueError(f"Unrecognized Citi Bike CSV schema, columns: {sorted(cols)}")


def read_monthly_csv(path: Path) -> pd.DataFrame:
    """Read one monthly Citi Bike file — handles both the raw .csv and the
    .zip-of-csv(s) Citi Bike ships (large months split into multiple CSVs
    inside one zip).
    """
    if path.suffix == ".zip":
        frames = []
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.endswith(".csv") and not name.startswith("__MACOSX"):
                    with zf.open(name) as f:
                        frames.append(pd.read_csv(io.BytesIO(f.read()), low_memory=False))
        if not frames:
            raise ValueError(f"No CSV found inside {path}")
        return pd.concat(frames, ignore_index=True)
    return pd.read_csv(path, low_memory=False)


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Rename+coerce a raw monthly frame (either schema) to NORMALIZED_COLUMNS."""
    if df.empty:
        return pd.DataFrame(columns=NORMALIZED_COLUMNS)

    schema = detect_schema(list(df.columns))
    rename = _CURRENT_RENAME if schema == "current" else _LEGACY_RENAME
    out = df.rename(columns=rename)

    if schema == "legacy" and "ride_id" not in out.columns:
        # Legacy schema has no ride_id — synthesize a stable one from
        # start/end timestamps + station ids + bike id rather than using the
        # row's positional index (which isn't stable across re-reads/filters).
        out["ride_id"] = (
            out["bikeid"].astype(str)
            + "_"
            + out["started_at"].astype(str)
            + "_"
            + out["start_station_id"].astype(str)
        )

    missing = [c for c in NORMALIZED_COLUMNS if c not in out.columns]
    for c in missing:
        out[c] = pd.NA

    out = out[NORMALIZED_COLUMNS].copy()
    out["started_at"] = pd.to_datetime(out["started_at"], errors="coerce")
    out["ended_at"] = pd.to_datetime(out["ended_at"], errors="coerce")
    for c in ("start_lat", "start_lng", "end_lat", "end_lng"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["start_station_id"] = out["start_station_id"].astype("string")
    out["end_station_id"] = out["end_station_id"].astype("string")
    return out


def filter_near_corridor(df: pd.DataFrame, bbox: dict[str, float]) -> pd.DataFrame:
    """Keep only trips with a start OR end station inside the corridor bbox.
    A generous first pass — a trip that starts and ends outside the bbox but
    routes through it (e.g. a through-trip on Bedford Ave) is NOT caught
    here and needs the OSRM routing step, not a station-location filter.
    """
    in_bbox_start = (
        df["start_lat"].between(bbox["min_lat"], bbox["max_lat"])
        & df["start_lng"].between(bbox["min_lon"], bbox["max_lon"])
    )
    in_bbox_end = (
        df["end_lat"].between(bbox["min_lat"], bbox["max_lat"])
        & df["end_lng"].between(bbox["min_lon"], bbox["max_lon"])
    )
    return df[in_bbox_start | in_bbox_end].copy()


def download_monthly_csv(url: str, dest_dir: Path) -> Path:
    """Download one monthly file from citibikenyc.com/system-data into
    dest_dir, skipping if already cached there. Boilerplate I/O — the URL
    list itself (which months you need) is a build_json.py / config concern.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / url.split("/")[-1]
    if dest.exists():
        return dest
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest
