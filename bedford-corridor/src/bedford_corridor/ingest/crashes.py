"""Ingest + clean NYPD Motor Vehicle Collisions data (crashes + person tables)
for the Bedford Ave corridor. Pure ingestion/cleaning — no block attribution,
no rate calculation, no statistics. Those are downstream and, per project
rules, are either stubbed (denominator/stats) or done in build_json.py once
segmentation exists (spatial join of crash points to block geometries).
"""

from __future__ import annotations

import datetime

import pandas as pd

from bedford_corridor.ingest.socrata import fetch_dataset

CRASH_NUMERIC_COLUMNS = [
    "number_of_persons_injured",
    "number_of_persons_killed",
    "number_of_pedestrians_injured",
    "number_of_pedestrians_killed",
    "number_of_cyclist_injured",
    "number_of_cyclist_killed",
    "number_of_motorist_injured",
    "number_of_motorist_killed",
]


def fetch_crashes(
    date_from: datetime.date,
    date_to: datetime.date,
    bbox: dict[str, float],
    domain: str,
    dataset_id: str,
) -> pd.DataFrame:
    """Pull crashes within `bbox` and [date_from, date_to] from Socrata.

    Filtering by bbox server-side (rather than street name) is deliberate:
    on_street_name/cross_street_name are free-text NYPD fields with
    inconsistent abbreviations and casing ("BEDFORD AVE" vs "BEDFORD AVENUE"
    vs "BEDFORD AV"). A lat/lon box is a cheap, reliable first pass; exact
    corridor/block membership is decided later via spatial join against the
    segmented block geometries.
    """
    where = (
        f"crash_date between '{date_from.isoformat()}T00:00:00' "
        f"and '{date_to.isoformat()}T23:59:59' "
        f"and latitude between {bbox['min_lat']} and {bbox['max_lat']} "
        f"and longitude between {bbox['min_lon']} and {bbox['max_lon']}"
    )
    return fetch_dataset(domain=domain, dataset_id=dataset_id, where=where)


def fetch_person(
    date_from: datetime.date,
    date_to: datetime.date,
    domain: str,
    dataset_id: str,
) -> pd.DataFrame:
    """Pull person-level rows for the same date window. Filtered only by
    date (person rows carry no lat/lon) — narrowed to the corridor later by
    inner-joining on collision_id against `fetch_crashes` output.
    """
    where = (
        f"crash_date between '{date_from.isoformat()}T00:00:00' "
        f"and '{date_to.isoformat()}T23:59:59'"
    )
    return fetch_dataset(domain=domain, dataset_id=dataset_id, where=where)


def clean_crashes(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce dtypes Socrata hands back as strings. Two gotchas handled here:

    - collision_id kept as a string (nullable Int64 would silently round-trip
      fine today, but there's no guarantee Socrata never issues a
      non-numeric id — treat it like an opaque key, not a number).
    - injury/kill counts: NaN on a genuinely missing report should NOT
      become 0 via a careless fillna; we coerce to nullable Int64 and leave
      missing as <NA> so a sum() downstream doesn't silently treat "unknown"
      as "zero crashes happened."
    """
    if df.empty:
        return df

    out = df.copy()
    out["collision_id"] = out["collision_id"].astype("string")
    out["crash_date"] = pd.to_datetime(out["crash_date"], errors="coerce")
    for col in ("latitude", "longitude"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in CRASH_NUMERIC_COLUMNS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
    return out


def clean_person(df: pd.DataFrame) -> pd.DataFrame:
    """Same dtype-safety treatment as clean_crashes, for the person table."""
    if df.empty:
        return df

    out = df.copy()
    out["collision_id"] = out["collision_id"].astype("string")
    out["crash_date"] = pd.to_datetime(out["crash_date"], errors="coerce")
    if "person_age" in out.columns:
        out["person_age"] = pd.to_numeric(out["person_age"], errors="coerce").astype("Int64")
    return out


def filter_cyclist_rows(person_df: pd.DataFrame) -> pd.DataFrame:
    """Person-table rows for bicyclists only."""
    if person_df.empty:
        return person_df
    return person_df[person_df["person_type"] == "Bicyclist"].copy()


def join_crashes_person(crashes_df: pd.DataFrame, person_df: pd.DataFrame) -> pd.DataFrame:
    """Left-join person rows onto their parent crash (crashes_df as base).
    Returns a person-grained table: multiple rows per crash when a crash has
    multiple people, one all-NaN-person row for crashes with no person match.

    person_df is typically fetched citywide-by-date (see fetch_person), wider
    than crashes_df's bbox-filtered scope — so person rows outside the
    corridor are expected to drop out here. That's the intended narrowing,
    not a bug. What IS a bug, and what we guard against, is collision_id not
    being unique in crashes_df: a duplicated crash id would silently fan the
    merge out (multiply rows) rather than narrow it.
    """
    dupe_ids = crashes_df["collision_id"][crashes_df["collision_id"].duplicated()]
    if not dupe_ids.empty:
        raise ValueError(
            f"crashes_df has {dupe_ids.nunique()} duplicate collision_id values — "
            "merge would fan out crash rows, not just attach person rows. "
            "Deduplicate crashes_df before joining."
        )
    return crashes_df.merge(person_df, on="collision_id", how="left", suffixes=("", "_person"))
