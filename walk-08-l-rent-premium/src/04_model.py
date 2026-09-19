"""04 — The model, once per rent series.

Run:  python src/04_model.py              (or: make model)

    ln(rent_i) = b0 + b1 * walk_L_i + b2 * walk_nonL_i + b3 * walk_limited_i + controls + e_i

Fits the same model against all four cleaned tables from 03 (combined,
1BR, 2BR, 3BR) — kept as a robustness check (the pattern holds regardless
of bedroom size), but the walk itself no longer asks people to guess for a
specific bedroom count, so all four series' results are consolidated into
one model_summary.txt and one coefficients.json rather than four of each.

Week-3 robustness menu (rerun with edits, don't build a framework):
  - drop flag_topcoded tracts          (Bedford-end attenuation check)
  - drop flag_low_reliability tracts   (MOE check)
  - WLS weighted by renter_hh          (thin-tract check)
  - straight-line distance instead of network (does b1 move?)
Sanity-check the magnitude against the transit-capitalization literature
(Debrezion et al.) before believing it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config as C
import lib

# One entry per rent series: (label, analysis-table suffix, rent column)
SERIES = [
    ("combined (all bedrooms)", "", "med_rent"),
    ("1BR", "_1br", "med_rent_1br"),
    ("2BR", "_2br", "med_rent_2br"),
    ("3BR", "_3br", "med_rent_3br"),
]


def run_series(label: str, suffix: str, rent_col: str) -> tuple[str, dict]:
    """Fit one series; return (summary text, coefficients payload) rather
    than writing per-suffix files, so main() can consolidate all four."""
    df = pd.read_csv(C.PROCESSED / f"analysis_table{suffix}.csv", dtype={"GEOID": str})
    res, info = lib.fit_model(df, rent_col=rent_col)
    p0 = lib.predicted_p0(res, df)

    b_lim, se_lim = res.params["walk_limited_min"], res.bse["walk_limited_min"]

    # Realistic-range check: same model, restricted to tracts within a 30-min
    # walk of the nearest M-only station -- the population anyone would
    # actually walk to, rather than the whole band out to 100+ minutes.
    df_near = df[df["walk_limited_min"] <= 30]
    res_near, info_near = lib.fit_model(df_near, rent_col=rent_col)
    b_near = res_near.params["walk_limited_min"]
    se_near = res_near.bse["walk_limited_min"]

    print(f"\n--- {label} ---")
    print(f"  {info['formula']}")
    print(f"  N = {info['n']} tracts   R^2 = {info['r2']:.3f}   (HC1 robust SEs)")
    print(f"  b1 (walk_L_min):        {info['beta1_per_min']:+.4f}  "
          f"(se {info['beta1_se']:.4f})")
    print(f"  = {info['pct_per_min']:+.2f}% rent per additional walk minute")
    print(f"  THE HALF-LIFE:          {info['half_life_min']:.1f} minutes")
    print(f"  P0 (rent at the door):  ${p0:,.0f}/mo")
    print(f"  b (walk_limited_min):   {b_lim:+.4f}  (se {se_lim:.4f}, "
          f"t={b_lim/se_lim:+.2f}) -- the Ridgewood/M-only gradient")
    print(f"  -- restricted to walk_limited_min <= 30 min (N={info_near['n']}) --")
    print(f"  b (walk_limited_min, near-only): {b_near:+.4f}  (se {se_near:.4f}, "
          f"t={b_near/se_near:+.2f})")

    summary_text = (
        f"{'=' * 62}\n WALK NO. 08 — {label.upper()}\n{'=' * 62}\n"
        f"{res.summary()}\n\n"
        f"walk_limited_min (Ridgewood/M-only gradient): {b_lim:+.4f} "
        f"(se {se_lim:.4f}, t={b_lim/se_lim:+.2f})\n"
        f"Restricted to walk_limited_min <= 30 min (N={info_near['n']}): "
        f"{b_near:+.4f} (se {se_near:.4f}, t={b_near/se_near:+.2f})\n"
    )
    coeff_payload = lib.coefficients_payload(info["beta1_per_min"], p0, info["n"], source="model")
    coeff_payload["walk_limited_beta_per_min"] = round(b_lim, 5)
    coeff_payload["walk_limited_t"] = round(b_lim / se_lim, 2)
    return summary_text, coeff_payload


def main() -> None:
    print("=" * 62)
    print(" WALK NO. 08 — THE NUMBERS, PER BEDROOM SIZE (robustness check)")
    print("=" * 62)

    summaries = []
    coefficients = {}
    for label, suffix, rent_col in SERIES:
        summary_text, coeff_payload = run_series(label, suffix, rent_col)
        summaries.append(summary_text)
        coefficients[suffix.lstrip("_") or "combined"] = coeff_payload

    (C.ROOT / "outputs" / "model_summary.txt").write_text("\n\n".join(summaries))
    lib.write_json(C.TOOL / "coefficients.json", coefficients)
    print("\n-> outputs/model_summary.txt, outputs/tool/coefficients.json "
          "(all four series, one file each)")

    print("\n" + "=" * 62)
    print("Caveats that go in the writeup, not under the rug:")
    print("  - cross-sectional and descriptive, not causal (Walk 09's DiD is")
    print("    where identification lives)")
    print("  - ACS medians are 2020-24 averages incl. stabilized units ->")
    print("    the asking-rent gradient a mover faces is likely steeper")
    print("  - neighboring tracts are not independent; HC1 doesn't fix that")
    print("=" * 62)


if __name__ == "__main__":
    main()
