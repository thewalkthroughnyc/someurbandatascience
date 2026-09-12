# Walk No. 08 — L-train rent premium

Part of *The Walkthrough NYC*. Read `HANDOFF.md` for the full narrative;
this file is the fast-orientation version for a new session.

## The question

**"How much of your rent is the walk to the L?"**

Does ACS median gross rent decline with network walk time to the nearest
Brooklyn L station, across census tracts in a 1.25-mile band north and south
of the corridor (Bedford Av → Canarsie)? The L runs east–west, so the rent
variation of interest runs *perpendicular* to the line — hence a band, not a
line of tracts along the spine.

Key control: network walk time to the nearest **non-L** station. Without it,
"far from the L" quietly means "near the J/M/Z," and the coefficient on the L
is contaminated by proximity to everything else.

```
ln(rent_i) = β₀ + β₁·walk_L_i + β₂·walk_nonL_i + γ·X_i + ε_i
```

HC1 robust SEs. Descriptive accessibility gradient, not causal — station
placement and neighborhood change are entangled in a cross-section.

## The headline number

**Half-life:** `w½ = ln(2) / |β₁|` — the walk time, in minutes, at which the
L premium has decayed by half. `lib.half_life()`.

Second number: total accessibility premium across the band vs. what the
public actually captured (the tool/sketch side of the piece).

## Pipeline

Scripts are numbered and run in order; `Makefile` wraps them.

| Script | Make target | Does | Status |
|---|---|---|---|
| `src/01_pull_acs.py` | `make pull` | Stations → corridor line → band polygon → TIGER tracts (Kings+Queens) → ACS pull. Prints **Gate 1**. | ✅ done |
| `src/02_walk_times.py` | `make walktimes` | OSMnx walk graph, multi-source Dijkstra to L and non-L station sets. Slow first run (10–30 min), cached after. | ⏳ not run |
| `src/03_clean_join.py` | `make clean_join` | Merge, clean, write `outputs/cleaning_log.md`, scatter w/ lowess. Prints **Gate 2**. | ⏳ not run |
| `src/04_model.py` | `make model` | Fit, print β₁ / half-life / P0, write `outputs/model_summary.txt` and `outputs/tool/coefficients.json`. | ⏳ being rewritten by hand — **do not write this file for the user, review only** |

`src/config.py` holds every tunable knob (band radius, top-code, gate
thresholds). `src/lib.py` holds the pure, tested logic — the only thing under
test (`tests/test_lib.py`, offline, seconds).

## The two gates

- **Gate 1 — SAMPLE** (`01`, prints at end of `make pull`): is there enough
  band to estimate on? Suggested floor `GATE1_COMFORTABLE_N = 120` usable
  tracts. **Cleared 2026-09-10: 240 tracts in band, 20 Brooklyn L stations,
  49 non-L stations for the control.** Lever if thin: raise
  `BAND_RADIUS_MILES` in `config.py` and rerun `01` — nothing else changes.
- **Gate 2 — SIGNAL** (`03`, prints at end of `make clean_join`): is there a
  visible decaying relationship in `outputs/figures/scatter_rent_vs_walk.png`?
  The bivariate slope it prints is an aid, not the gate — *the plot* is the
  gate. Not yet run; needs `02`'s `walk_times.csv` first.

## Hard deadlines

- **Sat Sep 19** — Substack findings post.
- **Sat Sep 26** — public math walk, meets at DeKalb Av (L).

Both are immovable. Cut order if behind schedule: reel → p5 tool → Walk 09
prep → robustness checks. Never the post, never the walk.

## Working with the user on this repo

The user is a math teacher rewriting `src/04_model.py` from scratch by hand —
it's the actual analysis and what they'll be asked to defend in interviews.

- **Never write `src/04_model.py` for them.** Review what they write and push
  back with questions; don't hand over code. (The current file predates this
  rule and is a full draft from an earlier session — left in place for
  reference, not to be edited or treated as final.)
- **Everything else in `src/` — walk through it function by function**, in
  plain language, checking understanding with questions rather than just
  explaining. This applies to `lib.py`, the numbered scripts, and `config.py`.
- **Show diffs before applying changes**, with a plain-language note on what
  the diff does, even for small fixes — the user asks for the code to be
  legible to them line by line, not just correct.
- Dependency/boilerplate fixes (imports, `requirements.txt`, path handling)
  are fine to just make — they're not what the user is here to learn.
