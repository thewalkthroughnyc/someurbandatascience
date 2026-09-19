# Walk No. 08 — The Ridgewood Rent Premium

## What this is
Analysis behind a public math walk, not a portfolio project. The
Walkthrough NYC, run by Jordan, a 7th-grade math teacher in Bushwick. The
output is a number people test on a sidewalk.

## The published question vs. the actual finding
Published question (Aug 31): does median gross rent decline with network
walk time to the nearest L station? **That's not what the data showed.**

Once you control for distance to every other nearby train and for basic
housing differences (building age, unit size, renter share), walking
distance to the L is **not a reliable predictor of rent** — statistically
indistinguishable from zero, consistent across the blended market and all
three bedroom-specific cuts (1BR/2BR/3BR).

The real, robust signal: **distance to the nearest M-only station**, all
of which sit in one cluster in Ridgewood/Middle Village (Central Av,
Knickerbocker Av, Forest Av, Fresh Pond Rd, Middle Village-Metropolitan
Av, Seneca Av). Rent **rises**, not falls, as you approach that cluster —
strongly significant in every bedroom size (β ≈ −0.43% to −0.62% per walk
minute, t = −3.9 to −5.3). This is now the headline finding. The walk and
the Substack post are both being restructured around it, in progress as
of today (2026-09-19).

**Important, hard-won correction:** Myrtle-Wyckoff Avs is *not* part of
the M-only tier, even though it looks M-only in a naive per-row read of
the MTA stations data. The raw feed splits that station into two rows —
one for the M, one for the L — because it's a real L+M transfer complex.
`01_pull_acs.py`'s station tagging groups by `Complex ID` specifically to
catch this; don't undo that grouping when touching that code.

## Why the walk starts at Seneca Ave, not DeKalb
Seneca Ave sits roughly in the middle of the M-only cluster. Four teams,
each testing something specific:
- **North, toward Middle Village** — stays inside the M-only cluster (Forest
  Av, Fresh Pond Rd also M-only along the way). Tests variation *within*
  the cluster.
- **South, toward Myrtle-Wyckoff Avs** — *leaves* the M-only cluster,
  approaching a full L+M complex. Should show rent falling as the walk
  leaves Ridgewood's isolation behind.
- **East and west, perpendicular to the M line** — distance to that
  specific train vs. just being in Ridgewood generally. This is the one
  bearing that can live-test the analysis's own unresolved confound: is
  this a transit-quality effect or a neighborhood-identity one?

## Method
```
ln(rent_i) = β₀ + β₁·walk_L_i + β₂·walk_nonL_i + β₃·walk_limited_i + γ·X_i + ε_i
```
- `walk_L`: network walk time to nearest L station.
- `walk_nonL`: nearest *full-service* non-L station (A/C/J/Z, and — since
  the fix — the Myrtle-Wyckoff Avs L+M complex).
- `walk_limited`: nearest true M-only station (`config.py`'s
  `LIMITED_SERVICE_ROUTES`). **This is the coefficient that matters.**
- Controls X: median year built, median rooms, renter share, unit-mix
  shares. HC1 robust SEs. Run once per rent series (combined/1BR/2BR/3BR).
- Two charts per series: rent vs. `walk_L_min` (the original, now a null
  result) and rent vs. `walk_limited_min` (the real one) —
  `scatter_rent_vs_walk*.png` and `scatter_rent_vs_ridgewood*.png`.

## Pipeline
| Script | Make target | Does |
|---|---|---|
| `src/01_pull_acs.py` | `make pull` | Stations → corridor → band → TIGER tracts → ACS pull (blended + per-bedroom). Tags L / full-service non-L / M-only-limited, complex-aware. Prints Gate 1. |
| `src/02_walk_times.py` | `make walktimes` | OSMnx walk graph, multi-source Dijkstra x3 (L, full non-L, limited). |
| `src/03_clean_join.py` | `make clean_join` | Cleans + plots **both** charts for all four rent series. Prints Gate 2 for each. |
| `src/04_model.py` | `make model` | Fits all four series, prints β for `walk_L_min` *and* `walk_limited_min`, writes `model_summary*.txt` and `coefficients*.json`. |

`src/config.py` holds every tunable knob. `src/lib.py` holds the tested
logic (`clean_tracts`, `fit_model`, `is_limited_only`, etc.), parameterized
by `rent_col`/`moe_col` so the same functions run all four series.

## Status (as of 2026-09-19)
- **Gate 1 & 2 — cleared, all four series, both charts.**
- **Model complete, all four series.** L-specific effect: null, everywhere.
  M-only/Ridgewood effect: strong and significant, everywhere.
- **Substack post — draft in progress**, `substack_post.md` at repo root.
  Real numbers in; closing thesis (who captures the Ridgewood premium)
  still being decided.
- **Walk materials — being rewritten** around Seneca Ave (`walk/route.md`
  updated; `packet.md`/`script.md` still reference the old DeKalb-centered
  design pending the closing-thesis decision).
- Open, not a blocker: the Ridgewood-cluster confound (transit quality vs.
  neighborhood identity) — the east/west bearings are designed to probe
  this live.

## Deadlines
- **Sat Sep 19 (today)** — Substack findings post. Immovable.
- **Sat Sep 26** — the walk, now starting at Seneca Ave (M), not DeKalb Av (L).

## How to work with me
I direct this analysis; I don't write the code. That's a deliberate
choice — my time goes to the walk series, not to becoming an engineer. So:

- **Explain in plain English, not just code.** When you change something,
  say what it does and why before applying it.
- **Keep it simple.** Prefer the readable version over the clever one.
  Parameters belong in `config.py` so Walk No. 09 is a config change, not
  a rewrite.
- **The analysis decisions are mine.** Specification, controls, sample
  frame, interpretation — propose options, don't decide.
- **Maintain a plain-prose section in README.md** describing what each
  script does. Not code comments. Prose I can read in six months.
- Don't add dependencies or abstractions without asking.
