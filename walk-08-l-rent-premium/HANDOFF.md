# HANDOFF — Walk No. 08 (L-train rent premium)

> **SUPERSEDED — 2026-09-19.** This describes the original scaffold-building
> plan from Sep 7, centered on the L corridor. The actual finding turned out
> to be about Ridgewood/M-only stations, not the L — the model, the walk
> route, and the writeup have all moved. See `CLAUDE.md` for the current,
> accurate picture (question, method, pipeline, status, deadlines) and
> `README.md` for the public writeup. Everything below is kept for history
> only — don't treat it as current.

Context for a fresh session. Written 2026-09-07, end of the scaffold build.
Read this first, then `README.md`, then `src/config.py`.

---

## The question

**"How much of your rent is the walk to the L?"**

Method: ACS 5-year median gross rent (B25064) by census tract, across a wide band
north and south of the Brooklyn L corridor (Bedford Av → Canarsie). The L runs
east–west, so the rent variation of interest is *perpendicular* to the line —
hence a band, not a radius.

- Treatment variable: OSMnx network walk time from tract internal point to nearest L station.
- Key control: walk time to nearest **non-L** station. Without it, "far from the L"
  quietly means "near the J" and the coefficient is garbage.
- Model: `ln(rent) ~ walk_min_L + walk_min_nonL + controls`, HC1 standard errors.
- Headline number: half-life, `w½ = ln2 / |β₁|` — minutes of walking that cost you half the premium.
- Second number: total premium across the band vs. what the public recovers.

The walk itself starts at **DeKalb Av (L)**, four bearings — two on-corridor
(expect flat rent), two off-corridor (expect decay). See `walk/route.md`.
Start moved from Wilson Av because a cemetery blocks one bearing.

---

## Repo layout

Scripts are numbered and run in order. `Makefile` wraps them.

| Script | Make target | What it does |
|---|---|---|
| `src/01_pull_acs.py` | `make pull` | Stations → L corridor line → band polygon → TIGER tracts → ACS pull. **Prints Gate 1.** |
| `src/02_walk_times.py` | `make walktimes` | OSMnx walk graph, one multi-source Dijkstra per station set. Slow: 10–30 min first run, cached after. |
| `src/03_clean_join.py` | `make clean_join` | Merge, clean, write `outputs/cleaning_log.md`, scatter w/ lowess. **Prints Gate 2.** |
| `src/04_model.py` | `make model` | Fit, print β₁ / half-life / P0, write `model_summary.txt` and `outputs/tool/coefficients.json`. |

`src/lib.py` holds the pure logic and is the only thing under test.
`tests/test_lib.py` runs offline in seconds (`make test`).

`outputs/tool/coefficients.json` is the **data contract** for the p5 tool.
It currently holds dummy values (β₁ = −0.02, P0 = 2800) so the sketch can be
built before the real numbers exist. `make model` overwrites it.

---

## Where things stand

Day 8 of 28. The Sep 19 findings post and the walk itself are immovable.

Planned sequence for the remaining free weekday evenings (after-school program
starts Sep 14, so evenings get scarce):

- **Mon** — repo scaffold + Census pull ← *the scaffold is done; the pull is the live step*
- **Tue** — OSMnx walk times
- **Wed** — Gate 1 checkpoint
- **Thu** — clean/join, scatter, Gate 2
- **Fri–Sat** — p5 tool scaffold against dummy coefficients
- **Sun** — DeKalb recon + b-roll

Note: `01` prints Gate 1 as soon as it runs, so Wednesday's checkpoint may clear
on Monday night. If so, everything pulls forward and the freed time goes to the
p5 tool — the artifact most at risk of getting cut.

**Cut order if behind:** reel → p5 tool → Walk 09 prep → robustness checks.
Never the post, never the walk.

---

## Three live catches

1. **Census API key is now required.** Keyless requests to the Census Data API no
   longer work. Free key at `api.census.gov/data/key_signup.html`. The script
   reads `CENSUS_API_KEY` from the environment and fails loudly with that link if
   it's missing. `export` only persists for the current terminal session — it must
   be set again in any new shell before `make pull`.

2. **The band crosses into Queens.** Ridgewood sits north of the Wyckoff stretch;
   Maspeth is across Newtown Creek. `COUNTY_FIPS` is `["047", "081"]` (Kings +
   Queens) for exactly this reason — a Kings-only pull silently clips the northern
   half of the sample. The Ridgewood M stations also belong in the non-L control set.

3. **ACS top-codes median gross rent** around $3,500. This will bite the Bedford
   end of the corridor. Affected tracts are flagged in the cleaning log; the
   robustness menu includes a re-run with them dropped. Left unhandled, β₁
   attenuates and nothing in the output says why.

---

## Defaults awaiting ratification

All in `src/config.py`, all deliberately one-line changes:

- `BAND_RADIUS_MILES = 1.25` — **the Gate 1 lever.** Thin tract count? Widen to 1.5 and rerun.
- `MIN_RENTER_HH = 100` — tracts below this are dropped (thin renter base → noisy median).
- `CV_FLAG = 0.30` — MOE reliability flag, not a drop.
- `RENT_TOPCODE = 3500` — see catch 3.
- `GATE1_COMFORTABLE_N = 120` — the number Gate 1 is judged against.
- `ACS_YEAR = 2024` with automatic 2023 fallback. The 2020–2024 5-year release
  landed 2026-01-29, later than the usual December cadence.
- `EPSG_LOCAL = 2263` (NY Long Island, feet), `WALK_SPEED = 80` m/min.
- Scripts, not notebooks — deliberate, matches the production-Python direction.

---

## Verified vs. not

**Verified offline:** geometry helpers, ACS jam-value handling (−666666666),
cleaning rules, and a full simulated end-to-end run on synthetic data that
recovers a planted β₁ (−0.03 planted, −0.0295 recovered). `03` and `04` have both
executed successfully against fake inputs. Week 3 really is a number swap.

**Not verified:** every live network call. The stations CSV, the TIGER shapefile,
the Census API, and the Overpass/OSMnx fetch were all unreachable from the build
sandbox. Expect small schema-drift fixes on first run — the stations loader
already matches columns defensively for this reason. If `01` fails, the traceback
is the interesting thing, not the script.

---

## Working agreements

- **Commit in slices as each stage verifies**, not the whole repo at once. A repo
  whose history is one commit reads as a prop rather than as work.
- README prose about the sample frame is drafted with `<!-- -->` comments marking
  where the author's own voice goes. Those stay unwritten until he writes them.
- Honest-limitations section in the README is load-bearing, not boilerplate.

---

## Immediate next steps

1. Confirm the terminal is actually in the repo (`pwd`, `ls` — expect `Makefile`, `src`, `tests`, `walk`).
2. `git init`, commit the scaffold as slice one.
3. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
4. `make test` — three tests, seconds.
5. `export CENSUS_API_KEY=...`
6. `make pull` — first contact with live APIs. Read the Gate 1 count it prints.
7. Gate 1 comfortable → commit slice two, and consider kicking off `make walktimes`
   before bed since it needs no supervision. Thin → widen `BAND_RADIUS_MILES`, rerun.
