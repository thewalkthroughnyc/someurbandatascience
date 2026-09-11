"""04 — The model. (Week 3 work: Mon Sep 14. Runnable the moment 03 has run.)

Run:  python src/04_model.py              (or: make model)

    ln(rent_i) = b0 + b1 * walkL_i + b2 * walkNonL_i + controls + e_i

Reads data/processed/analysis_table.csv, prints the three numbers that
carry the piece, and overwrites outputs/tool/coefficients.json — which is
the p5 sketch's data source. "Swap real numbers into the tool" is therefore
just: run this script, redeploy.

Week-3 robustness menu (rerun with edits, don't build a framework):
  - drop flag_topcoded tracts          (Bedford-end attenuation check)
  - drop flag_low_reliability tracts   (MOE check)
  - WLS weighted by renter_hh          (thin-tract check)
  - straight-line distance instead of network (does b1 move?)
Sanity-check the magnitude against the transit-capitalization literature
(Debrezion et al.) before believing it.
"""

from __future__ import annotations

import pandas as pd

import config as C
import lib


def main() -> None:
    df = pd.read_csv(C.PROCESSED / "analysis_table.csv", dtype={"GEOID": str})
    res, info = lib.fit_model(df)

    (C.ROOT / "outputs" / "model_summary.txt").write_text(str(res.summary()))
    p0 = lib.predicted_p0(res, df)
    lib.write_json(
        C.TOOL / "coefficients.json",
        lib.coefficients_payload(info["beta1_per_min"], p0, info["n"], source="model"),
    )

    print("=" * 62)
    print(" WALK NO. 08 — THE NUMBERS")
    print("=" * 62)
    print(f"  {info['formula']}")
    print(f"  N = {info['n']} tracts   R^2 = {info['r2']:.3f}   (HC1 robust SEs)")
    print()
    print(f"  b1 (walk_L_min):        {info['beta1_per_min']:+.4f}  "
          f"(se {info['beta1_se']:.4f})")
    print(f"  = {info['pct_per_min']:+.2f}% rent per additional walk minute")
    print()
    print(f"  THE HALF-LIFE:          {info['half_life_min']:.1f} minutes")
    print(f"  P0 (rent at the door):  ${p0:,.0f}/mo")
    print()
    print("  coefficients.json updated -> the p5 tool now shows real numbers")
    print("  full table -> outputs/model_summary.txt")
    print("=" * 62)
    print("\nCaveats that go in the writeup, not under the rug:")
    print("  - cross-sectional and descriptive, not causal (Walk 09's DiD is")
    print("    where identification lives)")
    print("  - ACS medians are 2020-24 averages incl. stabilized units ->")
    print("    the asking-rent gradient a mover faces is likely steeper")
    print("  - neighboring tracts are not independent; HC1 doesn't fix that")


if __name__ == "__main__":
    main()
