"""Walk No. 08 — shared logic, kept out of the run scripts so it can be tested.

Rule of thumb: anything that touches the network (Census API, Overpass,
data.ny.gov) lives in the numbered scripts; anything that transforms data
lives here and has a test in tests/test_lib.py.
"""

from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
from shapely import contains_xy
from shapely.geometry import LineString

import config as C

# --------------------------------------------------------------- column utils


def pick_col(df: pd.DataFrame, *needles: str) -> str:
    """Return the first column whose lowercased name contains ALL needles.

    Defensive against schema drift in the data.ny.gov stations CSV
    (column names have shuffled between dataset versions).
    """
    for col in df.columns:
        low = col.lower()
        if all(n.lower() in low for n in needles):
            return col
    raise KeyError(f"No column matching {needles!r} in {list(df.columns)}")


def has_route(routes: str, route: str) -> bool:
    """Token-exact match on the space-separated Daytime Routes field.

    'L' matches 'L' but not... well, nothing else contains L, but token
    matching is the correct habit ('J' must not match 'J Z' wrongly split).
    """
    if not isinstance(routes, str):
        return False
    return route in routes.split()


# --------------------------------------------------------------- geometry


def corridor_line(points_xy: list[tuple[float, float]]) -> LineString:
    """LineString through station points in route order (projected coords)."""
    if len(points_xy) < 2:
        raise ValueError("Need at least two stations to draw a corridor")
    return LineString(points_xy)


def band_polygon(line: LineString, radius_ft: float):
    """The sample-frame band: buffer around the corridor, both sides."""
    return line.buffer(radius_ft)


def points_in_polygon(xs, ys, poly) -> np.ndarray:
    """Vectorised point-in-polygon (shapely 2.x)."""
    return contains_xy(poly, np.asarray(xs, dtype=float), np.asarray(ys, dtype=float))


# --------------------------------------------------------------- ACS handling


def to_numeric_acs(s: pd.Series) -> pd.Series:
    """Coerce an ACS column to float and null out jam values.

    The API encodes 'no estimate' as large negative sentinels
    (-666666666, -888888888, ...). Anything <= 0 is not a real rent,
    year, or count for our variables, so it becomes NaN.
    """
    out = pd.to_numeric(s, errors="coerce")
    return out.where(out > 0)


def rent_cv(est: pd.Series, moe: pd.Series) -> pd.Series:
    """Coefficient of variation from a 90%-CI margin of error."""
    return (moe / 1.645) / est


def clean_tracts(
    df: pd.DataFrame, rent_col: str = "med_rent", moe_col: str = "med_rent_moe"
) -> tuple[pd.DataFrame, list[tuple[str, int]]]:
    """Apply the cleaning rules; return (clean_df, log).

    rent_col/moe_col pick which rent series to clean — the blended
    med_rent by default, or one of the bedroom-specific columns
    (med_rent_1br, med_rent_2br, med_rent_3br) for the per-bedroom cuts.

    The log is a list of (decision, rows affected) — this is the
    'log every decision and the rows it cost' rule made mechanical.
    03_clean_join.py writes it to outputs/cleaning_log.md.
    """
    log: list[tuple[str, int]] = []
    df = df.copy()

    n0 = len(df)
    df = df[df[rent_col].notna()]
    log.append(("Dropped tracts with no ACS median-rent estimate (jam values / suppressed)", n0 - len(df)))

    # Flags first (kept, not dropped — robustness checks re-run without them)
    df["flag_topcoded"] = df[rent_col] >= C.RENT_TOPCODE
    log.append((f"Flagged tracts at/above the ${C.RENT_TOPCODE:,} ACS top-code (kept)", int(df["flag_topcoded"].sum())))

    df["rent_cv"] = rent_cv(df[rent_col], df[moe_col])
    df["flag_low_reliability"] = df["rent_cv"] > C.CV_FLAG
    log.append((f"Flagged low-reliability medians, CV > {C.CV_FLAG:.0%} (kept)", int(df["flag_low_reliability"].sum())))

    n1 = len(df)
    df = df[df["renter_hh"].fillna(0) >= C.MIN_RENTER_HH]
    log.append((f"Dropped tracts with < {C.MIN_RENTER_HH} renter households (cemeteries, industrial)", n1 - len(df)))

    if "walk_L_min" in df.columns:
        n2 = len(df)
        df = df[df["walk_L_min"].notna()]
        log.append(("Dropped tracts unreachable on the walk network", n2 - len(df)))

        if "snap_m" in df.columns:
            df["flag_far_snap"] = df["snap_m"] > C.SNAP_FLAG_M
            log.append((f"Flagged internal points snapping > {C.SNAP_FLAG_M} m to the network (kept)", int(df["flag_far_snap"].sum())))

    # Derived shares used as controls
    df["renter_share"] = df["renter_hh"] / df["occ_units"]
    df["share_1unit"] = (df["units_1det"].fillna(0) + df["units_1att"].fillna(0)) / df["units_total"]
    df["share_20plus"] = (df["units_20_49"].fillna(0) + df["units_50plus"].fillna(0)) / df["units_total"]

    return df, log


# --------------------------------------------------------------- model


def half_life(beta1: float) -> float:
    """Walk time (minutes) at which the premium halves: ln 2 / |beta1|."""
    return float(np.log(2) / abs(beta1))


MODEL_CONTROLS = [
    "walk_nonL_min",     # the key control: 'far from the L' often means 'near the J'
    "med_year_built",
    "med_rooms",
    "renter_share",
    "share_1unit",
    "share_20plus",
]


def fit_model(df: pd.DataFrame):
    """ln(rent) on walk time to the L, with whatever controls are present.

    Returns (results, info dict). HC1 robust SEs. Spatial autocorrelation
    across neighboring tracts is a real caveat — note it in the writeup;
    Conley/cluster SEs are a week-3 robustness item, not a blocker.
    """
    import statsmodels.formula.api as smf

    d = df.copy()
    d["log_rent"] = np.log(d["med_rent"])
    controls = [c for c in MODEL_CONTROLS if c in d.columns and d[c].notna().any()]
    formula = "log_rent ~ walk_L_min" + "".join(f" + {c}" for c in controls)
    d = d.dropna(subset=["log_rent", "walk_L_min"] + controls)

    res = smf.ols(formula, data=d).fit(cov_type="HC1")
    b1 = float(res.params["walk_L_min"])
    info = {
        "formula": formula,
        "n": int(res.nobs),
        "beta1_per_min": b1,
        "beta1_se": float(res.bse["walk_L_min"]),
        "pct_per_min": (np.exp(b1) - 1) * 100,
        "half_life_min": half_life(b1),
        "r2": float(res.rsquared),
    }
    return res, info


def predicted_p0(res, df: pd.DataFrame) -> float:
    """Model-implied rent at the station door (walk_L = 0), controls at
    sample means. Feeds the p5 tool's P(w) = P0 * exp(beta1 * w).

    Note: plain exp() of the log-scale prediction, no smearing correction —
    fine for a visualization anchor, say so if anyone asks.
    """
    row = {c: [df[c].mean()] for c in MODEL_CONTROLS if c in df.columns}
    row["walk_L_min"] = [0.0]
    return float(np.exp(res.predict(pd.DataFrame(row))[0]))


def coefficients_payload(beta1: float, p0: float, n: int | None, source: str) -> dict:
    """The contract between the model and the p5 tool. 04 overwrites the
    dummy version of this file; the sketch never needs to change."""
    return {
        "beta1_per_min": round(beta1, 5),
        "p0_monthly_rent": round(p0, 0),
        "half_life_min": round(half_life(beta1), 1),
        "n_tracts": n,
        "source": source,
        "generated": time.strftime("%Y-%m-%d %H:%M"),
    }


def write_json(path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
