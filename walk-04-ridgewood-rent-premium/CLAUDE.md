# Walk No. 04 — The Ridgewood Rent Premium

## What this is
Analysis behind a public math walk, not a portfolio project. The
Walkthrough NYC, run by Jordan, a 7th-grade math teacher in Bushwick. The
output is a number people test on a sidewalk.

## The finding
Rent rises the closer you get to the M-only stations clustered in
Ridgewood and Middle Village — Central Av, Knickerbocker Av, Forest Av,
Fresh Pond Rd, Middle Village-Metropolitan Av, Seneca Av. β ≈ −0.43% to
−0.62% per walk minute, t = −3.9 to −5.3, significant in every bedroom
size (combined/1BR/2BR/3BR). P0 — model-implied rent at an M-only station
door — is about $2,200/mo for the blended market.

The M is the subject. Distances to other nearby stations are controls,
held fixed so the coefficient means "near the M-only cluster" rather than
"near some train"; none of them carries a reliable signal of its own.

Within the cluster, rent isn't uniform: it runs highest at the
Bushwick/Ridgewood end (around Central Av, ~$2,300 median) and falls going
deeper into Queens (Forest Av, Fresh Pond Rd, ~$1,900). A single
"distance to nearest M-only station" term treats every M-only station
alike and misses that west→east slope — it over-predicts the Queens end by
~$150–200. See limitations in README, and the walk bearings below.

**Hard-won data correction:** Myrtle-Wyckoff Avs is *not* M-only, even
though it looks that way in a naive per-row read of the MTA stations feed
— the feed splits that transfer complex into two rows, one per line.
`01_pull_acs.py` groups by `Complex ID` to catch this. Don't undo that.

## The walk starts at Seneca Ave
Seneca Ave is the middle of the M-only cluster. Four teams, expectations
set from the station-by-station data, not from theory:
- **North, toward Middle Village** (Forest Av, Fresh Pond Rd) — the
  deeper-into-Queens end. Rent **falls** this way: ~$2,080 around Seneca
  → ~$1,910 around Fresh Pond Rd.
- **South, toward Myrtle-Wyckoff Avs** — the Bushwick/Ridgewood end.
  Rent **rises, slightly**: ~$2,080 → ~$2,130, and keeps rising past
  Myrtle-Wyckoff toward Central Av (~$2,300).
- **East and west, perpendicular to the M line** — distance to that
  specific train vs. just being in Ridgewood. No data prediction; this is
  the live experiment, and it probes the analysis's own unresolved
  confound (transit quality vs. neighborhood identity).

## Method
```
ln(rent_i) = β₀ + β₁·walk_M_i + controls + ε_i
```
- `walk_M_min`: network walk time to the nearest M-only station.
  **β₁ is the number.** Reported in plain terms, not as a half-life — the
  M-only stations are clustered in one corner, not spread through the
  sample.
- Controls: distance to other nearby stations (`walk_L_min`,
  `walk_nonL_min` — held fixed, neither significant on its own), median
  year built, median rooms, renter share, unit-mix shares. HC1 robust SEs.
- Run once per rent series (combined/1BR/2BR/3BR) as a robustness check;
  results consolidated into one `model_summary.txt` and one
  `coefficients.json`.
- Two charts per series. `scatter_rent_vs_ridgewood*.png` is the
  tract-level scatter, restricted to the realistic 0–30 min walking range
  (both the display and the lowess fit, so far-away tracts don't smooth
  out the local pattern), with the y-axis held to `CHART_RENT_YLIM` so a
  few deeply subsidized tracts don't squash the market-rate spread — they
  stay in the model and are counted in a note on the chart.
  `gradient_binned*.png` is the one that reads from across a sidewalk:
  median rent per walk-time bin out to 60 min (`BINNED_EDGES`), with
  bootstrapped 95% intervals and the full-sample model as a dashed
  reference. It runs to 60 rather than 30 because the 0–30 window is the
  flat part of the curve, and past 60 it stops reading as "a walk" —
  Jordan's call, 2026-09-24. Its title is deliberately descriptive: the
  combined, 1BR and 2BR series fall across the bins, but **3BR rises**
  ($2,364 → $2,634), so the chart must not assert a direction.
- Realistic-range check (tracts with `walk_M_min` ≤ 30): the raw
  correlation looks stronger, but the controlled model loses power — 3 of
  4 series stop being significant. The full-sample result is the reliable
  one; the restricted version is a caveat, not a replacement.
- Sample-frame check (`BAND_SPINE=M make all`): redraw the band around the
  M's own Ridgewood run instead of the L corridor. Sample halves (113
  usable tracts vs. 227) and the contrast collapses — median walk to the
  nearest M-only station drops from 44 min to 18, so nearly every tract is
  "near." Point estimates go the same way and get larger (−0.82%/min
  combined) but none of the four series is significant (t = −1.6 to −1.9;
  3BR flips sign). **Read as consistent but underpowered, not as a failed
  replication** — Jordan's call, 2026-09-19. The original band's power
  comes from containing the far-from-M tracts that give the gradient
  something to be measured against. The headline stands on the original
  sample; say so plainly in the writeup.

## Pipeline
| Script | Make target | Does |
|---|---|---|
| `src/01_pull_acs.py` | `make pull` | Stations → tag the M-only tier (complex-aware) → corridor spine → band → TIGER tracts → ACS pull (blended + per-bedroom). Prints Gate 1. |
| `src/02_walk_times.py` | `make walktimes` | OSMnx walk graph, multi-source Dijkstra x3 (M-only; full non-L and L as controls). Labels each tract's nearest M-only station. |
| `src/03_clean_join.py` | `make clean_join` | Cleans, then plots two charts per rent series: the tract-level scatter (0–30 min) and the binned-median gradient (out to 60 min). Prints Gate 2. |
| `src/04_model.py` | `make model` | Fits all four series; the M coefficient is the headline. Writes `model_summary.txt` and `coefficients.json`. |

`src/config.py` holds every tunable knob. `src/lib.py` holds the tested
logic (`clean_tracts`, `fit_model`, `is_limited_only`, etc.), parameterized
by `rent_col`/`moe_col` so the same functions run all four series.
`make test` runs offline in seconds and plants a coefficient on
`walk_M_min` to confirm the model recovers it.

The band (`BAND_RADIUS_MILES`) is buffered around a corridor spine drawn
through one line's stations in order — `config.BAND_SPINE`, read from the
environment. Default `"L"`: the Brooklyn L run, a long east-west spine
whose band reaches north into Queens and captures the M-only cluster; the
original sample, plain filenames, where the finding was made. `"M"`: the
Myrtle Av M run (GTFS M01–M10, Middle Village → Central Av); every
processed/output file gets a `_mspine` tag so both runs coexist. Run it
with `BAND_SPINE=M make all`. See the sample-frame check under Method for
how the two compare.

## Status (as of 2026-09-24)
- Gates 1 & 2 cleared, all four series. Model complete; M-first everywhere
  in code, outputs, and docs.
- Sample-frame robustness run (`_mspine` outputs) done and committed;
  consistent direction, not significant. Headline stays on the original
  band.
- Substack post — published.
- Walk materials — Seneca Ave start; four bearings, expectations set from
  the station-by-station data. East and west scouted on foot.
- **Total premium — settled 2026-09-24: the 20-minute reference.** Within a
  20-minute walk of an M-only station, 69,047 renter households pay about
  $96/mo more than they would 20 minutes out — roughly **$79M/yr**. Built
  off the combined M gradient (β = −0.00492, P0 = $2,200) and weighted by
  `renter_hh`. The number swings hard on the reference distance ($178M at
  30 min, $361M at 44), so it is always stated as "compared to living 20
  minutes away." Lives on the packet back page and in the README finding
  table. Unrelated to the ≤30-min realistic-range check under Method,
  which is unchanged.
- Open, all Jordan's: the closing thesis (who captures the Ridgewood
  premium).

## Deadlines
- **Sat Sep 19** — Substack findings post. Done.
- **Sat Sep 26** — the walk, meets at Seneca Ave (M). Packets print Fri
  Sep 25.

## How to work with me
I direct this analysis; I don't write the code. That's a deliberate
choice — my time goes to the walk series, not to becoming an engineer. So:

- **Explain in plain English, not just code.** When you change something,
  say what it does and why before applying it.
- **Keep it simple.** Prefer the readable version over the clever one.
  Parameters belong in `config.py` so Walk No. 05 is a config change, not
  a rewrite.
- **The analysis decisions are mine.** Specification, controls, sample
  frame, interpretation — propose options, don't decide.
- **Maintain a plain-prose section in README.md** describing what each
  script does. Not code comments. Prose I can read in six months.
- Don't add dependencies or abstractions without asking.
