"""03 — Clean, join, and look.

Run:  python src/03_clean_join.py          (or: make clean_join)

Runs the same clean + scatter step once per rent series: the combined
blended median and the three bedroom-specific cuts. Produces, per series:
  - data/processed/analysis_table[_Nbr].csv   one row per tract, model-ready
  - outputs/cleaning_log[_Nbr].md             every decision and the rows it cost
  - outputs/figures/scatter_rent_vs_ridgewood[_Nbr].png  THE plot — rent vs.
    walk to the nearest M-only (Ridgewood) station, 0-30 min, with a lowess
    overlay. Look at it. The plot is the gate, not the printed slope.
  - outputs/figures/gradient_binned[_Nbr].png  the same gradient as group
    medians out to 60 min — the version that reads from ten feet away.
"""

from __future__ import annotations

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

import config as C
import lib

# One entry per rent series: (label, rent column, MOE column, output filename suffix)
SERIES = [
    ("combined (all bedrooms)", "med_rent", "med_rent_moe", ""),
    ("1BR", "med_rent_1br", "med_rent_1br_moe", "_1br"),
    ("2BR", "med_rent_2br", "med_rent_2br_moe", "_2br"),
    ("3BR", "med_rent_3br", "med_rent_3br_moe", "_3br"),
]

# One entry per chart: (x column, x-axis label, output filename stem)
CHARTS = [
    ("walk_M_min", "Network walk time to nearest M-only (Ridgewood) station (min)",
     "scatter_rent_vs_ridgewood"),
]

# Chart ink. BLUE carries the data; MUTED is reference/annotation, never a
# second data series.
BLUE, INK, MUTED = "#1f77b4", "#2b2b2b", "#8a8f98"


def make_scatter(d: pd.DataFrame, rent_col: str, x_col: str, x_label: str,
                  label: str, out_png) -> float:
    """One scatter + lowess + bivariate slope, restricted to the realistic
    0-30 min walking range — both the fit and the display, not just the
    display, so far-away tracts don't smooth out the local pattern.

    The y-axis is held to config.CHART_RENT_YLIM so a few deeply subsidized
    tracts don't squash the market-rate spread into the top of the frame.
    That is a DISPLAY choice only: the lowess, the slope, and the model all
    still use every tract, and any point outside the window is counted in a
    note on the chart rather than quietly disappearing.

    Returns the bivariate slope from the restricted range."""
    full_n = len(d)
    d = d[d[x_col] <= 30]

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
    ax.scatter(d[x_col], d[rent_col], s=22, alpha=0.55, edgecolor="none")

    # Fit on every tract in range, including any the y-window will hide.
    lo = sm.nonparametric.lowess(np.log(d[rent_col]), d[x_col], frac=0.3)
    ax.plot(lo[:, 0], np.exp(lo[:, 1]), lw=2.2)

    ax.set_yscale("log")
    ax.set_xlim(0, 30)

    if C.CHART_RENT_YLIM:
        y_lo, y_hi = C.CHART_RENT_YLIM
        ax.set_ylim(y_lo, y_hi)
        # Dollar ticks beat matplotlib's 2 x 10^3 for a walk audience.
        ticks = [t for t in (1200, 1500, 2000, 2500, 3000, 3500) if y_lo <= t <= y_hi]
        ax.set_yticks(ticks)
        ax.set_yticklabels([f"${t:,}" for t in ticks])
        ax.minorticks_off()

        n_out = int(((d[rent_col] < y_lo) | (d[rent_col] > y_hi)).sum())
        if n_out:
            ax.text(0.01, 0.02,
                    f"{n_out} of {len(d)} tracts fall outside this rent range "
                    f"(still in the fit and the model)",
                    transform=ax.transAxes, ha="left", va="bottom",
                    fontsize=7.5, alpha=0.65)

    ax.set_xlabel(x_label)
    ax.set_ylabel(f"ACS median gross rent, {label} ($/mo, log scale)")
    vintage = int(d["acs_vintage"].iloc[0]) if "acs_vintage" in d else C.ACS_YEAR
    ax.set_title(
        f"Rent vs. walk time to the nearest M-only (Ridgewood) station — {label}\n"
        f"{len(d)} of {full_n} tracts within 30 min · ACS {vintage - 4}-{vintage} 5-year",
        fontsize=10.5)
    ax.text(0.99, 0.02, "The Walkthrough NYC · Walk No. 04", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8, alpha=0.6)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)

    biv = sm.OLS(np.log(d[rent_col]), sm.add_constant(d[x_col])).fit()
    return float(biv.params[x_col])


def make_binned_chart(d: pd.DataFrame, rent_col: str, label: str, out_png) -> None:
    """Median rent per walk-time bin, out to config.BINNED_EDGES[-1].

    The scatter crops at 30 minutes, which is the flat part of the curve —
    this chart is the one where the gradient is actually visible, because it
    keeps the farther tracts that give "near" something to be measured
    against. Bootstrapped 95% intervals on each median (seeded, so reruns
    don't churn the PNG), and the fitted model as a dashed reference line.

    The model is refit here rather than read from coefficients.json so this
    script stays runnable before 04 has ever been run.
    """
    rng = np.random.default_rng(0)
    edges = C.BINNED_EDGES
    full = d                                   # the model is the FULL-sample
    d = d[d["walk_M_min"] <= edges[-1]]        # one; only the bins are capped

    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        s = d[(d["walk_M_min"] > lo) & (d["walk_M_min"] <= hi)]
        if len(s) < C.BINNED_MIN_N:
            continue
        vals = s[rent_col].values
        boot = [np.median(rng.choice(vals, len(vals), replace=True)) for _ in range(2000)]
        rows.append(dict(x=s["walk_M_min"].median(), med=np.median(vals), n=len(s),
                         lab=f"{lo}\u2013{hi}", lo=np.percentile(boot, 2.5),
                         hi=np.percentile(boot, 97.5)))
    if len(rows) < 2:
        print(f"  (binned chart skipped — only {len(rows)} usable bin(s))")
        return
    B = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=150)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#e6e6e3", lw=0.8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#cfcfca")

    try:
        res, info = lib.fit_model(full, rent_col=rent_col)
        b1, p0 = info["beta1_per_min"], lib.predicted_p0(res, full)
        w = np.linspace(0, edges[-1], 300)
        ax.plot(w, p0 * np.exp(b1 * w), ls="--", lw=1.6, color=MUTED, zorder=1)
        ax.annotate("model, controls held fixed — full sample\n"
                    f"({b1 * 100:+.2f}% per minute, n={info['n']})",
                    xy=(edges[-1] * 0.95, p0 * np.exp(b1 * edges[-1] * 0.95)),
                    xytext=(0.08, 0.10), textcoords="axes fraction",
                    fontsize=8.5, color=MUTED, ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    except Exception as exc:                      # a thin series may not fit
        print(f"  (model reference line skipped: {exc})")

    ax.errorbar(B.x, B.med, yerr=[B.med - B.lo, B.hi - B.med], fmt="none",
                ecolor=BLUE, elinewidth=1.4, capsize=4, alpha=0.55, zorder=2)
    ax.plot(B.x, B.med, "-", lw=2.0, color=BLUE, zorder=3)
    ax.scatter(B.x, B.med, s=70, color=BLUE, zorder=4, edgecolor="white", linewidth=1.5)
    for r in B.itertuples():
        ax.annotate(f"${r.med:,.0f}", (r.x, r.med), textcoords="offset points",
                    xytext=(0, 15), ha="center", fontsize=10, color=INK, fontweight="bold")
        ax.annotate(f"n={r.n}", (r.x, r.med), textcoords="offset points",
                    xytext=(0, -17), ha="center", fontsize=8, color=MUTED)

    # Leave room for every interval: a clipped error bar reads as "goes on
    # forever", which is a worse lie than a roomy axis.
    pad = 0.06 * (B.hi.max() - B.lo.min())
    ax.set_xlim(-2, edges[-1] + 2)
    ax.set_ylim(B.lo.min() - pad, B.hi.max() + pad)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}")
    ax.set_xticks(edges)
    ax.set_xlabel("Network walk time to the nearest M-only (Ridgewood) station (min)")
    ax.set_ylabel(f"Median gross rent, {label} ($/mo)")
    ax.set_title("Rent falls the farther you get from an M-only station\n"
                 f"{label} · median across the {len(d)} tracts within "
                 f"{edges[-1]} minutes' walk",
                 fontsize=11.5, color=INK, loc="left", x=0)
    ax.text(0.99, 0.02, "The Walkthrough NYC \u00b7 Walk No. 04", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8, color=MUTED)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def process_series(df: pd.DataFrame, label: str, rent_col: str, moe_col: str, suffix: str) -> None:
    suffix = C.SPINE_TAG + suffix   # e.g. "_mspine_1br"; plain "_1br" for the L-spine run
    clean, log = lib.clean_tracts(df, rent_col=rent_col, moe_col=moe_col)
    clean.to_csv(C.PROCESSED / f"analysis_table{suffix}.csv", index=False)

    lines = [
        f"# Cleaning log — Walk No. 04 ({label})",
        "",
        "Every dropped row is a modeling decision. This file is generated by",
        "`src/03_clean_join.py`; the rules live in `src/lib.py::clean_tracts`",
        "and `src/config.py`.",
        "",
        "| Decision | Tracts affected |",
        "|---|---|",
        *[f"| {desc} | {n} |" for desc, n in log],
        "",
        f"**Final analysis sample: {len(clean)} tracts.**",
    ]
    (C.ROOT / "outputs" / f"cleaning_log{suffix}.md").write_text("\n".join(lines))

    print(f"\n--- {label} ---")
    print(f"Cleaning log -> outputs/cleaning_log{suffix}.md")
    for desc, n in log:
        print(f"  - {desc}: {n}")
    print(f"Analysis table -> data/processed/analysis_table{suffix}.csv  ({len(clean)} tracts)")

    for x_col, x_label, stem in CHARTS:
        d = clean.dropna(subset=[rent_col, x_col])
        out_png = C.FIGURES / f"{stem}{suffix}.png"
        b = make_scatter(d, rent_col, x_col, x_label, label, out_png)
        print(f"Scatter -> {out_png.relative_to(C.ROOT)}")
        print(f"  Bivariate slope (no controls): {b * 100:+.2f}% per walk minute")
        if b < 0:
            print(f"  Naive half-life at that slope: {lib.half_life(b):.0f} min")

    binned_png = C.FIGURES / f"gradient_binned{suffix}.png"
    make_binned_chart(clean.dropna(subset=[rent_col, "walk_M_min"]), rent_col,
                      label, binned_png)
    print(f"Binned gradient -> {binned_png.relative_to(C.ROOT)}")


def main() -> None:
    tracts = gpd.read_file(C.PROCESSED / f"band_tracts{C.SPINE_TAG}.geojson")
    walks = pd.read_csv(C.PROCESSED / f"walk_times{C.SPINE_TAG}.csv", dtype={"GEOID": str})
    df = pd.DataFrame(tracts.drop(columns="geometry")).merge(
        walks, on="GEOID", how="left", validate="1:1"
    )

    for label, rent_col, moe_col, suffix in SERIES:
        process_series(df, label, rent_col, moe_col, suffix)

    print("\n" + "=" * 62)
    print(" GATE 2 — SIGNAL (all four series, both charts)")
    print("=" * 62)
    print("  Now OPEN THE SCATTERS and look. The plots are the gate, not the")
    print("  printed slope. No visible slope is still a piece — a better one.")
    print("=" * 62)


if __name__ == "__main__":
    main()
