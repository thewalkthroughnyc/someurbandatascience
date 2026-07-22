# Project: Urban Data Science Self-Study

## About me

Jordan Jones — 7th-grade math teacher at a Bushwick, Brooklyn school (BCPS).
Currently self-studying precalculus. Transitioning toward urban data science
and PropTech: analyzing real-estate economics, transit access, and neighborhood
change in Central Brooklyn.

No assumed CS background. I know math (ratios, percentages, basic algebra)
but not programming idioms. Explain new concepts by analogy to things a math teacher would already know.

## Datasets I'll work with

| Dataset | What it contains | Why I care |
|---------|-----------------|------------|
| NYC PLUTO | Every tax lot in NYC: zoning, FAR, lot area, building class, assessed value | Core of any property analysis |
| ACRIS | NYC deed/mortgage records | Ownership chains, sale prices, cap-rate inputs |
| MTA GTFS (B38) | Stop locations, headways, trip counts on the B38 bus | My daily commute; transit access proxy |
| NYC 311 | Service requests by address | Neighborhood service-quality signal |
| Census ACS | Block-group demographics, income, housing cost burden | Context for displacement risk |

## How I want to be taught

1. **No assumed CS background.** Define every term the first time it appears.
2. **Inefficient → idiomatic.** Show the "obvious" Python first (loop, if/else),
   then refactor to the pandas or list-comprehension version. Name what changed and why.
3. **Anchor examples to my world.** Use real Bushwick addresses (e.g. 441 Wilson Ave),
   B38 stop names, cap-rate calculations, and 311 complaint types I'd actually see.
4. **Connect math I know.** Cap rate = NOI / price (like a ratio). FAR = built SF / lot SF.
   ACS margin-of-error uses the same z-score logic I teach. Tie new ideas to these.
5. **Explain before you code.** One-sentence plain-English summary of what a cell does
   before the code, not after.
6. **Flag gotchas.** Warn me when pandas has a footgun (chained indexing, inplace=,
   dtype inference on PLUTO columns) before I hit it.

## Project layout

```
walkthrough-data/
├── CLAUDE.md          ← you are here
├── .gitignore
├── notebooks/         ← one .ipynb per study day
├── data/              ← raw downloads, gitignored
└── src/               ← reusable helper modules
```

## Vocabulary cheat-sheet (for Claude)

- **Cap rate** — Net Operating Income ÷ Purchase Price. Higher = better yield.
- **PLUTO** — Primary Land Use Tax Lot Output. One row per tax lot.
- **BBL** — Borough-Block-Lot, the unique NYC parcel ID (e.g. 3-034900-0001).
- **FAR** — Floor Area Ratio: how much building is allowed per square foot of lot.
- **GTFS** — General Transit Feed Specification: standard format for transit schedules.
- **ACS** — American Community Survey, 5-year estimates at block-group level.
- **B38** — The DeKalb Ave bus. Runs through Bushwick; my daily commute route.

## Session norms

- Working language: Python 3, pandas, geopandas, JupyterLab (already installed in .venv).
- Keep data/ gitignored — files there can be large and are re-downloadable.
- Each notebook should be self-contained: imports at the top, no hidden state.
- When I ask "why does this work?", explain the mechanism, not just the result.
