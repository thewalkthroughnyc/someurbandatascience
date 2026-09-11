"""Verified corridor facts. Single source of truth — nothing here is computed,
everything here was looked up and cited in METHODS.md.

If you re-verify any of these against a primary source (DOT press release,
LION centerline file, Socrata dataset page), update the value AND the
`# source:` comment above it.
"""

import datetime

# ---------------------------------------------------------------------------
# Treatment
# ---------------------------------------------------------------------------

# source: user-confirmed 2025-08-06 (protection removal work on the
# Willoughby–Flushing segment reported complete by this date; DOT gave no
# single official "completed on" press date — see METHODS.md Data Sources).
TREATMENT_DATE = datetime.date(2025, 8, 6)

# source: NYC DOT protected lane install, completed late 2024 (Streetsblog,
# multiple articles reference "installed last year" as of mid-2025 coverage).
# Confirm exact date against a DOT press release before treating this as final.
PROTECTED_LANE_INSTALL_DATE = datetime.date(2024, 12, 1)  # TODO: verify exact day

# ---------------------------------------------------------------------------
# Corridor extent
# ---------------------------------------------------------------------------

CORRIDOR_STREET = "Bedford Avenue"
CORRIDOR_START = "Dean Street"
CORRIDOR_END = "Flushing Avenue"

# Cross streets along Bedford Ave from Dean St to Flushing Ave, in order,
# south to north. Derived from OSM intersection nodes (Overpass API),
# spot-checked individually via Nominatim. NOT yet cross-checked against
# NYC's LION street centerline file — do that before treating block 6
# (Monroe St -> Gates Ave) as correct; that gap was suspiciously short
# (~13m between intersection nodes) and may indicate one of the two
# doesn't actually cross Bedford Ave, or LION disagrees with OSM here.
CROSS_STREETS = [
    "Dean Street",
    "Atlantic Avenue",
    "Fulton Street",
    "Hancock Street",
    "Putnam Avenue",
    "Monroe Street",
    "Gates Avenue",
    "Greene Avenue",
    "Lafayette Avenue",
    "DeKalb Avenue",
    "Willoughby Avenue",
    "Myrtle Avenue",
    "Park Avenue",
    "Flushing Avenue",
]

# The three blocks where DOT removed protection in Jul/Aug 2025, reverting to
# a painted lane between parked cars and moving traffic. Everything else in
# CROSS_STREETS stayed protected. Expressed as (from_street, to_street) pairs
# matching consecutive entries in CROSS_STREETS.
TREATED_BLOCKS = [
    ("Willoughby Avenue", "Myrtle Avenue"),
    ("Myrtle Avenue", "Park Avenue"),
    ("Park Avenue", "Flushing Avenue"),
]

# Approximate lat/lon for each cross-street intersection, WGS84. Source: OSM
# Overpass API, named intersection nodes on Bedford Ave (Aug 2026 pull) —
# same query used to verify CROSS_STREETS above. Good enough for plotting
# the strip map's real geography; NOT a substitute for the actual block
# LineString geometry segmentation.segment_corridor() is meant to produce
# (this is points only, no notion of the block face between them).
CROSS_STREET_COORDS = {
    "Dean Street": (40.677416, -73.952748),
    "Atlantic Avenue": (40.679080, -73.952957),
    "Fulton Street": (40.680878, -73.953418),
    "Hancock Street": (40.682389, -73.953717),
    "Putnam Avenue": (40.683469, -73.953931),
    "Monroe Street": (40.685275, -73.954292),
    "Gates Avenue": (40.685402, -73.954317),
    "Greene Avenue": (40.688292, -73.954892),
    "Lafayette Avenue": (40.689309, -73.955098),
    "DeKalb Avenue": (40.691259, -73.955480),
    "Willoughby Avenue": (40.693377, -73.955903),
    "Myrtle Avenue": (40.694473, -73.956121),
    "Park Avenue": (40.696685, -73.956561),
    "Flushing Avenue": (40.698862, -73.956998),
}

# Rough bounding box around the corridor (Dean St to Flushing Ave, Bedford Ave
# +/- ~150m) used to pre-filter Socrata/Citi Bike pulls before precise block
# attribution. lat/lon, WGS84. Pad generously — this only needs to be cheap
# and inclusive, not exact; exact attribution happens after segmentation.
CORRIDOR_BBOX = {
    "min_lat": 40.6740,
    "max_lat": 40.7010,
    "min_lon": -73.9620,
    "max_lon": -73.9520,
}

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

# source: https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95
SOCRATA_DOMAIN = "data.cityofnewyork.us"
SOCRATA_CRASHES_DATASET_ID = "h9gi-nx95"
# source: https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Person/f55k-p6yu
SOCRATA_PERSON_DATASET_ID = "f55k-p6yu"

# source: https://citibikenyc.com/system-data
CITIBIKE_SYSTEM_DATA_URL = "https://citibikenyc.com/system-data"
# Current (Feb 2021-present) schema. Covers our whole study window
# (pre-period predates Dec 2024 install; that's still within this schema).
CITIBIKE_SCHEMA_CURRENT = [
    "ride_id", "rideable_type", "started_at", "ended_at",
    "start_station_name", "start_station_id", "end_station_name", "end_station_id",
    "start_lat", "start_lng", "end_lat", "end_lng", "member_casual",
]
# Legacy (pre-2021) schema. Included for completeness / robustness per
# project instructions; not expected to be hit for this study's date range.
CITIBIKE_SCHEMA_LEGACY = [
    "tripduration", "starttime", "stoptime",
    "start station id", "start station name", "start station latitude", "start station longitude",
    "end station id", "end station name", "end station latitude", "end station longitude",
    "bikeid", "usertype", "birth year", "gender",
]

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

# Public OSRM demo servers only route "driving" — the cycling profile requires
# a self-hosted OSRM instance built with the bicycle.lua profile. See
# README.md "Routing setup" for the docker-compose one-liner. Override via
# the OSRM_BASE_URL env var if you're pointing at a different host.
OSRM_DEFAULT_BASE_URL = "http://localhost:5000"
OSRM_PROFILE = "bike"
