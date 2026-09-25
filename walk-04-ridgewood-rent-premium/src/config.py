from dotenv import load_dotenv
load_dotenv()

"""Walk No. 04 — all knobs in one place.

Every parameter you might turn at a gate lives here, so a Gate 1 fix
("widen the band") is a one-line edit, not a code hunt.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"
TOOL = ROOT / "outputs" / "tool"

# ---------------------------------------------------------------- ACS
ACS_YEAR = 2024          # 2020-2024 5-year (released Jan 2026). Script falls
                         # back to 2023 automatically if this vintage 404s.
STATE_FIPS = "36"        # New York
COUNTY_FIPS = ["047", "081"]  # Kings AND Queens — the band crosses into
                              # Ridgewood/Maspeth along the Wyckoff Av stretch
                              # and across Newtown Creek. Kings-only silently
                              # clips the north side of the sample.

# Census API now requires a key (free, instant): 
#   https://api.census.gov/data/key_signup.html
# Set it as an environment variable:  export CENSUS_API_KEY=...
# The script will try keyless first and tell you loudly if it's rejected.

ACS_VARS = {
    "B25064_001E": "med_rent",        # median gross rent ($/mo) — the outcome
    "B25064_001M": "med_rent_moe",    # its margin of error (90% CI)
    "B01003_001E": "pop",
    "B25003_001E": "occ_units",
    "B25003_003E": "renter_hh",       # renter-occupied units
    "B25035_001E": "med_year_built",
    "B25018_001E": "med_rooms",
    "B25024_001E": "units_total",
    "B25024_002E": "units_1det",
    "B25024_003E": "units_1att",
    "B25024_008E": "units_20_49",
    "B25024_009E": "units_50plus",

    # B25031 — median gross rent, broken out by bedroom count (same concept
    # as B25064, split into bins). Variable codes are standard across ACS
    # vintages; if 01 rejects one, check the 2024 table shell.
    "B25031_003E": "med_rent_1br",
    "B25031_003M": "med_rent_1br_moe",
    "B25031_004E": "med_rent_2br",
    "B25031_004M": "med_rent_2br_moe",
    "B25031_005E": "med_rent_3br",
    "B25031_005M": "med_rent_3br_moe",
}

# ---------------------------------------------------------------- geography
# TIGER (not cartographic-boundary) because it carries INTPTLAT/INTPTLON —
# internal points guaranteed to fall inside the polygon, better than raw
# centroids for weird tract shapes.
TIGER_URL = "https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_36_tract.zip"

STATIONS_URL = "https://data.ny.gov/api/views/39hk-dx4f/rows.csv?accessType=DOWNLOAD"

EPSG_LOCAL = 2263        # NY Long Island State Plane, units = US survey FEET.
                         # You'll meet this CRS in every NYC dataset; get used
                         # to it now. NOTE the feet — meters live elsewhere.
FT_PER_MILE = 5280.0
M_PER_FT = 0.3048

# ---------------------------------------------------------------- the band
BAND_RADIUS_MILES = 1.25   # buffer around the corridor line, both sides. The
                           # line is drawn along the long east-west spine 01
                           # builds from station points; 1.25 mi is wide enough
                           # to reach north into Ridgewood/Middle Village, where
                           # the M-only cluster — the subject — sits.
                           # GATE 1 LEVER: if the tract count is thin, raise
                           # this (1.5) and rerun 01. Nothing else changes.
NONL_STATION_MARGIN_MILES = 0.5   # stations just outside the band still matter
                                  # as sources; include them.

BAND_SPINE = os.environ.get("BAND_SPINE", "L").upper()
                           # Which line's stations the corridor spine is drawn
                           # through before buffering:
                           #   "L" — the Brooklyn L run. The original sample;
                           #         the finding was made here. Default.
                           #   "M" — the Myrtle Av M run through Ridgewood /
                           #         Middle Village. A robustness check that
                           #         redraws the sample around the subject.
                           # Run the alternate with:  BAND_SPINE=M make all
SPINE_TAG = "" if BAND_SPINE == "L" else f"_{BAND_SPINE.lower()}spine"
                           # suffix on every processed/output file so both runs
                           # coexist; the L run keeps the plain filenames.

LIMITED_SERVICE_ROUTES = ["M"]    # stations where this is the ONLY route get
                                  # split into a separate, weaker tier: the M
                                  # runs solo (no other line) on much of its
                                  # Ridgewood/Middle Village stretch, and
                                  # late nights (~10-11pm to 5am) it doesn't
                                  # run into Manhattan at all — it's cut back
                                  # to a shuttle between Middle Village-
                                  # Metropolitan Av and Myrtle Av-Broadway.
                                  # A station pairing M with J/Z (e.g.
                                  # Myrtle Av) still counts as regular
                                  # non-L service — a real alternative
                                  # exists at that stop.

# ---------------------------------------------------------------- walk times
GRAPH_MARGIN_MILES = 0.35  # build the walk network slightly beyond the band
                           # so border tracts aren't routed on a clipped graph
WALK_SPEED_M_PER_MIN = 80.0   # 4.8 km/h ≈ 3 mph
SNAP_FLAG_M = 400          # flag tracts whose internal point snapped to the
                           # network more than this far away (parks, cemeteries)

# ---------------------------------------------------------------- cleaning
MIN_RENTER_HH = 100        # drop tracts with fewer renter households than this
                           # — kills cemetery/industrial tracts (Evergreens,
                           # East Williamsburg) where a "median rent" is noise
CV_FLAG = 0.30             # flag low-reliability medians: coefficient of
                           # variation = (MOE / 1.645) / estimate > 0.30
RENT_TOPCODE = 3500        # ACS top-codes median gross rent ("$3,500+").
                           # Verify against the 2024 vintage docs; tracts at
                           # the cap get flagged either way — matters at the
                           # Bedford end, where true medians exceed it.

GATE1_COMFORTABLE_N = 120  # suggestion only — the gate decision is yours

# ---------------------------------------------------------------- charts
CHART_RENT_YLIM = (1200, 3600)  # rent window the scatters display ($/mo).
                                # The band is market-rate Ridgewood; a handful
                                # of deeply subsidized tracts sit far below it
                                # and, left in, squash everything else into the
                                # top half of the frame. Tracts outside the
                                # window are COUNTED IN A CORNER NOTE on the
                                # chart, never silently dropped — and they stay
                                # in the model regardless; this is a display
                                # choice only. Set to None for matplotlib's
                                # automatic range.

BINNED_EDGES = [0, 15, 30, 45, 60]  # walk-minute bins for the binned-gradient
                                    # chart. The scatter's 0-30 window is the
                                    # flat part of the curve; the gradient only
                                    # becomes visible once the farther tracts
                                    # are in the frame, so this chart runs to 60.
                                    # Past that it stops reading as "a walk" at
                                    # all — Jordan's call, 2026-09-24.
BINNED_MIN_N = 5                    # skip a bin thinner than this: a median of
                                    # three tracts is not worth a dot.
