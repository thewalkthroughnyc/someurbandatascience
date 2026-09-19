"""04 — The model, once per rent series.

Run:  python src/04_model.py              (or: make model)

    ln(rent_i) = b0 + b1 * walk_M_i + controls + e_i

b1 is the Ridgewood gradient: percent change in rent per additional minute
of walking from the nearest M-only station. Controls hold building
characteristics and distance to other nearby stations fixed, so b1 means
"near the M-only cluster" rather than "near some train."

Fits the same model against all four cleaned tables from 03 (combined,
1BR, 2BR, 3BR) as a robustness check — the pattern holds regardless of
bedroom size — and consolidates the results into one model_summary.txt
and one coefficients.json (the p5 sketch's data source).

Robustness menu (rerun with edits, don't build a framework):
  - drop flag_topcoded tracts          (top-code attenuation check)
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
    suffix = C.SPINE_TAG + suffix
    df = pd.read_csv(C.PROCESSED / f"analysis_table{suffix}.csv", dtype={"GEOID": str})
    res, info = lib.fit_model(df, rent_col=rent_col)
    p0 = lib.predicted_p0(res, df)

    # Realistic-range check: same model, restricted to tracts within a 30-min
    # walk of the nearest M-only station -- the population anyone would
    # actually walk to, rather than the whole band out to 100+ minutes.
    # Smaller N => less power; report it, don't headline it.
    df_near = df[df["walk_M_min"] <= 30]
    _, info_near = lib.fit_model(df_near, rent_col=rent_col)

    print(f"\n--- {label} ---")
    print(f"  {info['formula']}")
    print(f"  N = {info['n']} tracts   R^2 = {info['r2']:.3f}   (HC1 robust SEs)")
    print(f"  b1 (walk_M_min):        {info['beta1_per_min']:+.4f}  "
          f"(se {info['beta1_se']:.4f}, t={info['beta1_t']:+.2f})")
    print(f"  = {info['pct_per_min']:+.2f}% rent per additional walk minute from the M")
    print(f"  P0 (rent at the M-only station door): ${p0:,.0f}/mo")
    print(f"  -- restricted to walk_M_min <= 30 min (N={info_near['n']}) --")
    print(f"  b1 (near-only):         {info_near['beta1_per_min']:+.4f}  "
          f"(se {info_near['beta1_se']:.4f}, t={info_near['beta1_t']:+.2f})")

    summary_text = (
        f"{'=' * 62}\n WALK NO. 08 — {label.upper()}\n{'=' * 62}\n"
        f"{res.summary()}\n\n"
        f"Restricted to walk_M_min <= 30 min (N={info_near['n']}): "
        f"b1 = {info_near['beta1_per_min']:+.4f} "
        f"(se {info_near['beta1_se']:.4f}, t={info_near['beta1_t']:+.2f})\n"
    )
    coeff_payload = lib.coefficients_payload(info["beta1_per_min"], p0, info["n"], source="model")
    coeff_payload["beta1_t"] = round(info["beta1_t"], 2)
    return summary_text, coeff_payload


def main() -> None:
    print("=" * 62)
    print(" WALK NO. 08 — THE RIDGEWOOD GRADIENT, PER BEDROOM SIZE")
    print("=" * 62)

    summaries = []
    coefficients = {}
    for label, suffix, rent_col in SERIES:
        summary_text, coeff_payload = run_series(label, suffix, rent_col)
        summaries.append(summary_text)
        coefficients[suffix.lstrip("_") or "combined"] = coeff_payload

    (C.ROOT / "outputs" / f"model_summary{C.SPINE_TAG}.txt").write_text("\n\n".join(summaries))
    lib.write_json(C.TOOL / f"coefficients{C.SPINE_TAG}.json", coefficients)
    print(f"\n-> outputs/model_summary{C.SPINE_TAG}.txt, "
          f"outputs/tool/coefficients{C.SPINE_TAG}.json (all four series, one file each)")

    print("\n" + "=" * 62)
    print("Caveats that go in the writeup, not under the rug:")
    print("  - cross-sectional and descriptive, not causal")
    print("  - M-only stations are clustered in one corner: 'near the M' and")
    print("    'in Ridgewood' are hard to separate; the walk's E/W bearings test it")
    print("  - ACS medians are 2020-24 averages incl. stabilized units ->")
    print("    the asking-rent gradient a mover faces is likely steeper")
    print("  - neighboring tracts are not independent; HC1 doesn't fix that")
    print("=" * 62)


if __name__ == "__main__":
    main()
