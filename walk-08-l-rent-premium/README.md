# Walk No. 08 — The Ridgewood Rent Premium

**Status: in progress** — model complete: rent rises the closer you get to Ridgewood's M-only stations, a real and robust finding · walk **Sat Sep 26**, meets at the Seneca Ave (M) station. <!-- Jordan: add the Luma RSVP link here and at the bottom -->

Part of [The Walkthrough NYC](https://example.substack.com) <!-- Jordan: real link -->, a public math walk series: publish a question, build the analysis in the open, then test the finding with strangers on a sidewalk. This one started as a question about the L. It isn't anymore.

## The finding

| | |
|---|---|
| Rent vs. distance into Ridgewood (nearest M-only station) | **−0.43% to −0.62% per minute — strongly significant in every bedroom size (t = −3.9 to −5.3)** |
| Rent vs. walk time to the L, alone | No reliable effect once controls are added — β ≈ −0.2%/min, not statistically significant, consistent across all four bedroom sizes |
| Total accessibility premium in the catchment vs. what the public recovered | *(open — see note)* |

<!-- Jordan: the "total premium" row above was going to be built from the L-specific
β, which isn't reliable enough to extrapolate from — decide whether to build it off the
Ridgewood gradient instead, or drop the row. Full numbers per series in
outputs/model_summary.txt and outputs/tool/coefficients.json. -->

![Rent vs walk time to the nearest Ridgewood M-only station](outputs/figures/scatter_rent_vs_ridgewood.png)
![Rent vs walk time to the L](outputs/figures/scatter_rent_vs_walk.png)

## The question

Rent rises the closer you get to the M-only stations clustered in
Ridgewood and Middle Village — Central Av, Knickerbocker Av, Forest Av,
Fresh Pond Rd, Middle Village-Metropolitan Av, Seneca Av. That's the real
finding here: the neighborhood around the *weaker* train commands a
premium, strongly and consistently, across every bedroom size.

That's not the question this piece started with. The original premise
was about the L specifically — rent near the subway is higher, the
closer to the L, the more you pay. That's not what happened. Once you
control for distance to every other nearby train and for basic
differences in the housing stock, distance to the L doesn't predict rent
at all, anywhere, in any bedroom size. The L turned out to be the wrong
train to be asking about. Ridgewood is the actual story.

## Data & sample frame

Every choice below is a modeling decision, stated before pulling, per house rules.

- **Unit of analysis: census tract.** Outcome is **ACS 2020–2024 5-year median gross rent** (table B25064, plus B25031 split by bedroom count) — public, reproducible, and covering what people actually pay rather than only what's listed. Margins of error are pulled alongside and used to flag low-reliability tracts (CV > 30%).
- **Geography: a 1.25-mile band spanning both Brooklyn and Queens, not just the tracts on the L's spine.** The sample was built around the L corridor (Bedford Av to Canarsie–Rockaway Pkwy) so there'd be enough perpendicular variation to estimate any gradient — but the band's reach into Queens is what actually captured Ridgewood, the part that mattered. <!-- Jordan: this rationale is yours from the Sep 7 notes — rephrase in your voice -->
- **The band crosses the county line by design.** North of the Wyckoff Av stretch is Ridgewood, and across Newtown Creek is Maspeth — both Queens. A Kings-only pull would have silently clipped out the actual finding.
- **Distance is network walk time, not straight-line** — OSMnx pedestrian network, tract internal point to the nearest station, at 80 m/min. The Bushwick street grid and the Cemetery of the Evergreens make crow-flies and on-foot diverge sharply; that divergence is much of the point.
- **Non-L stations are split into two tiers**, not treated as one group: full-service stations (A/C/J/Z, and the Myrtle-Wyckoff Avs L+M complex), and stations where the M is the *only* route — which also loses through-service to Manhattan overnight, cut back to a Middle Village–Myrtle Av shuttle. Only that second tier — the true M-only stations — turned out to matter.
- **Exclusions:** tracts with no rent estimate (ACS jam values), and tracts with fewer than 100 renter households — cemeteries and industrial land where a "median rent" is noise. Every rule and its cost in rows is machine-logged to [`outputs/cleaning_log.md`](outputs/cleaning_log.md).

## Method

```
ln(rent_i) = β₀ + β₁·walkL_i + β₂·walkNonL_i + β₃·walkLimited_i + γ·X_i + ε_i
```

**β₃ — walk time to the nearest M-only Ridgewood station — is the number that matters.** Strong and significant across every bedroom size, described in plain terms rather than a half-life, since those stations are clustered in one corner of the map rather than spread through the band. β₁ (the L) isn't reliable, anywhere.

Logs, because the premium is proportional — a station matters in percent of rent, not fixed dollars, and a β×100 reads directly as percent per walk minute. Controls X: median year built, median rooms, renter share, unit-mix shares. HC1 robust standard errors.

**This is a descriptive accessibility gradient, not a causal estimate.** Station locations and neighborhood change are entangled; the cross-section can't separate them. (Walk No. 09's candidate design — the L shutdown as difference-in-differences — is where identification lives.)

## Reproduce

```bash
pip install -r requirements.txt
export CENSUS_API_KEY=...   # free + instant: https://api.census.gov/data/key_signup.html
make pull        # 01: band, tracts, ACS rent (blended + per-bedroom) → prints Gate 1
make walktimes   # 02: OSMnx walk times, 3-way split (L / full non-L / M-only)
make clean_join  # 03: cleaning log + two scatters per series → prints Gate 2
make model       # 04: β for the Ridgewood gradient and for walk-to-L, per series
make test        # offline tests on the transforms
```

Raw downloads cache to `data/raw/` (gitignored); everything derived is regenerated by the scripts.

## Repo map

```
src/           config.py (every knob) · lib.py (tested logic) · 01–04 (the pipeline)
tests/         offline tests, incl. simulated-data recovery of a planted β₁
data/          raw/ (cached downloads, gitignored) · processed/ (committed, small)
outputs/       figures/ · cleaning_log.md · tool/coefficients.json → feeds the p5 sketch
walk/          route.md · packet.md · script.md — the sidewalk layer, starts at Seneca Ave
```

## Honest limitations

- ACS medians average 2020–2024 and include rent-stabilized units, so the gradient here is likely **flatter** than the asking-rent gradient a mover faces today. If anything, this underestimates the premium.
- Median gross rent is top-coded (~$3,500+); tracts at the cap are flagged, and 3BR tracts hit the cap far more often than 1BR (~13% vs ~3%), as you'd expect from bigger units costing more.
- Tract internal points are geometric, not population-weighted; block-weighted centroids are the known upgrade.
- Stations are points, not entrances; at tract resolution the difference is noise, but it's a real simplification.
- Neighboring tracts aren't independent. HC1 doesn't fix spatial autocorrelation; treat the SEs as friendly.
- The combined series blends every bedroom count into one tract-level median; the 1BR/2BR/3BR cuts address that directly, but each has a thinner, noisier sample than the combined series (a subgroup within a tract has fewer surveyed households, so more tracts get dropped or flagged low-reliability).
- The Ridgewood/M-only gradient is the strongest signal in the model, but M-only stations are geographically clustered in one corner of the band. That makes it hard to separate "closer to a weaker-service line" from "closer to Ridgewood specifically" — the gradient may reflect the neighborhood's own price dynamics as much as anything about that particular train. The walk's east/west bearings are designed to probe exactly this, live.
- Restricting to tracts within a realistic 30-minute walk of an M-only station makes the raw correlation look *stronger*, but the full controlled model loses statistical power there — three of the four bedroom sizes stop being significant once the sample shrinks that much. The full-band result is the one that's actually reliable and consistent across every series; the realistic-range version is a caveat worth mentioning, not a replacement number.

## The walk

Sat Sep 26, ~90 minutes, starting at the **Seneca Ave (M)** station entrance — the middle of the M-only cluster, where the actual finding lives. Four teams, four directions:

- **North, toward Middle Village** — stays inside the M-only cluster. Tests whether the premium holds steady or varies within Ridgewood itself.
- **South, toward Myrtle-Wyckoff Avs** — leaves the M-only cluster for a full L+M station. Should show rent falling as the walk leaves Ridgewood's isolation behind.
- **East and west, perpendicular to the M line** — tests whether this is really about that specific train, or just about being in Ridgewood generally.

Each team predicts a rent *before* looking anything up — anchored on their own housing (their own bedroom count, their own rent, their own walk to a subway), not a hypothetical bedroom size, since the finding holds the same way regardless of unit size. We regroup to plot everyone's guesses against the model on one chart, live. <!-- Jordan: RSVP link, and the closing question — "the L created this premium, who's collecting it" doesn't fit anymore since the finding isn't about the L. Your call on the replacement; substack_post.md has a couple of draft directions. -->
