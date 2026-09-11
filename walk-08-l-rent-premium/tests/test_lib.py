"""Offline tests — no network needed. Run:  python tests/test_lib.py

Three tests on the transforms ("three is infinitely more than zero"):
  1. geometry: corridor line -> band -> point selection
  2. cleaning: jam values, top-code flag, CV flag, renter floor
  3. model recovery: simulate tracts with a planted beta1, confirm
     fit_model + half_life recover it. This is the proof that week 3
     is a number swap, not a build.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

import config as C
import lib


def test_geometry():
    line = lib.corridor_line([(0, 0), (5000, 0), (10000, 0)])
    band = lib.band_polygon(line, 2000)
    xs = [0, 5000, 10000, 0]
    ys = [1000, -1500, 1999, 3000]           # in, in, in, out
    inside = lib.points_in_polygon(xs, ys, band)
    assert inside.tolist() == [True, True, True, False], inside
    print("  ok  geometry: band buffer + point-in-polygon selection")


def test_cleaning():
    df = pd.DataFrame({
        "med_rent": lib.to_numeric_acs(pd.Series(["2400", "-666666666", "3600", "1800", "2100"])),
        "med_rent_moe": [200, 100, 300, 1500, 250],
        "renter_hh": [500, 400, 800, 600, 40],
        "occ_units": [700, 500, 900, 800, 300],
        "units_1det": [10, 5, 0, 20, 100],
        "units_1att": [40, 30, 10, 60, 80],
        "units_20_49": [100, 50, 300, 20, 0],
        "units_50plus": [0, 0, 200, 0, 0],
        "units_total": [700, 500, 900, 800, 300],
    })
    clean, log = lib.clean_tracts(df)
    logd = dict(log)

    assert lib.to_numeric_acs(pd.Series(["-666666666"])).isna().all()
    assert len(clean) == 3                                   # jam + low-renter dropped
    assert logd[[k for k in logd if "jam" in k][0]] == 1
    assert clean["flag_topcoded"].sum() == 1                 # the 3600 tract
    assert clean["flag_low_reliability"].sum() == 1          # moe 1500 on est 1800
    assert (clean["renter_share"] <= 1).all()
    print("  ok  cleaning: jam values, top-code + CV flags, renter floor, log counts")


def test_model_recovery():
    rng = np.random.default_rng(8)           # walk 08, of course
    n = 300
    beta1_true = -0.03
    walk = rng.uniform(1, 35, n)
    walk_nonL = rng.uniform(2, 30, n)
    yr = rng.integers(1900, 2015, n).astype(float)
    rooms = rng.uniform(2.5, 5.5, n)
    log_rent = (8.1 + beta1_true * walk + 0.004 * walk_nonL
                + 0.0002 * yr + 0.02 * rooms + rng.normal(0, 0.10, n))
    df = pd.DataFrame({
        "med_rent": np.exp(log_rent),
        "walk_L_min": walk,
        "walk_nonL_min": walk_nonL,
        "med_year_built": yr,
        "med_rooms": rooms,
        "renter_share": rng.uniform(0.2, 0.9, n),
        "share_1unit": rng.uniform(0, 0.6, n),
        "share_20plus": rng.uniform(0, 0.5, n),
    })
    res, info = lib.fit_model(df)
    assert abs(info["beta1_per_min"] - beta1_true) < 0.005, info["beta1_per_min"]
    assert abs(info["half_life_min"] - lib.half_life(beta1_true)) < 4
    p0 = lib.predicted_p0(res, df)
    assert 1000 < p0 < 8000, p0
    payload = lib.coefficients_payload(info["beta1_per_min"], p0, info["n"], "test")
    assert set(payload) >= {"beta1_per_min", "p0_monthly_rent", "half_life_min"}
    print(f"  ok  model: planted b1={beta1_true} recovered as "
          f"{info['beta1_per_min']:+.4f}; half-life "
          f"{info['half_life_min']:.1f} min (true {lib.half_life(beta1_true):.1f})")


if __name__ == "__main__":
    print("tests/test_lib.py")
    test_geometry()
    test_cleaning()
    test_model_recovery()
    print("all tests passed")
