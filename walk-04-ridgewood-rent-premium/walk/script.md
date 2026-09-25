# Script — Walk No. 04

**Start: the corner of Seneca Ave and Palmetto St.** Four groups, four
directions, three predictions each, reconvene at the start, then walk to
Abracadabra Magic Cafe.

## Opening (say this)

> Hey, and welcome to the fourth math walk. Thanks for coming.
>
> On this walk you're going to make a prediction about how rent changes with
> distance from a train station. We'll split into four groups and head four
> different directions.
>
> Here's the rule that keeps us together: everybody walks fifteen minutes out,
> then turns around and comes back.** Not to a destination — to a time. That way
> we all cover about the same ground and we all get back here at the same time.
>
> **North group** — up Palmetto, right on Woodward Ave, left on Putnam Ave,
> heading for the Fresh Pond Road M. You probably won't quite reach it in
> fifteen. That's fine — turn around wherever you are.
>
> **South group** — west on Seneca, a block over make a left on Gates Ave, and
> head down toward Knickerbocker Ave.
>
> **West group** — with me. Down Seneca to Grover Cleveland Park, right on Hart,
> and out to the intersections.
>
> **East group** — east along Seneca toward Evergreen Park.
>
> On your walk you're making **three predictions** about rent: one in the first
> minute, one around minutes 7 to 10, and one around minutes 12 to 15, right
> before you turn around. This is based on what you already know about rent —
> that's your only intuition. The only thing I'll tell you is that Ridgewood is
> an up-and-coming neighborhood.
>
> We'll meet back here in about **35 minutes**, then walk over to Abracadabra
> and talk about it. Any questions?

## Timing — time-boxed, not destination-boxed

**Everyone walks 15 minutes out and turns around.** ~30 min of walking, ~35 with
stops. Nobody has to reach their landmark; the landmark is just a bearing.

This is the right call for the analysis, not only for the logistics: holding
walk-time constant across all four groups means **direction is the only thing
that varies.** It also means the east and west endpoints don't need measuring —
whatever they reach in 15 minutes is the data point.

Roughly where 15 minutes lands each group, measured on the walk graph at
80 m/min:

| Group | Bearing | ~15 min reaches |
|---|---|---|
| North | Palmetto → Woodward → Putnam | just short of Fresh Pond Rd (15.8 min) |
| South | Seneca → Gates Ave | Knickerbocker Av (15.4 min) |
| West | Seneca → Grover Cleveland Park → Hart | ~the intersections (Jordan's map read: 13 min) |
| East | Seneca east | ~Evergreen Park (Jordan's map read: 15 min) |

**One wrinkle to be ready for:** the south group passes Myrtle-Wyckoff at about
minute 7. That is *not* an M-only station — it's the L transfer complex, the one
the analysis had to special-case. So in the model's terms the south group's
middle prediction lands near a local *maximum* distance from any M-only station,
where the model predicts a dip but observed rent shows a rise. That gap isn't an
error to hide — it's the confound this walk exists to probe: better transit
(L + M) vs. distance from the M-only cluster.

## The reveal, at regroup

- Everyone's guesses on one chart against the model.
- **The north and south groups have a real number at each of their three
  predictions.** Observed median rent within 0.4 mi, matched to where each
  prediction falls:

  | | minute 1 | ~minute 7 | ~minute 15 |
  |---|---|---|---|
  | **North** | Seneca Av **$2,083** | Forest Av **$1,926** | Fresh Pond Rd **$1,913** |
  | **South** | Seneca Av **$2,083** | Myrtle-Wyckoff **$2,134** | Knickerbocker Av **$2,116** |

- Same fifteen minutes, opposite directions, opposite answers: north falls ~$170,
  south rises ~$33. That's the whole walk in one line.
- Two things worth saying out loud:
  - **The drop isn't linear.** North loses $157 in the first seven minutes and
    only $13 in the next eight. The gradient is steepest close to the station,
    which is what a decay model predicts and what people rarely guess.
  - **The south side is noisier than it looks.** Myrtle-Wyckoff and
    Knickerbocker swap order depending on how wide a radius you draw, so don't
    over-claim that small dip at minute 15. The honest read is "rising, then
    flat."
- East and west (perpendicular to the M) are the genuinely open question. No
  prediction from the data — this is live, and it's the part that tests whether
  the premium is about the train or about Ridgewood.

## Close (at the cafe)

- The gradient: rent falls about **half a percent per minute** you walk away
  from an M-only station.
- The value-capture number, then the closing question — say it as written, so
  it lands as the question they've been walking on all afternoon:
  **If proximity to a subway station generates a premium, who captures it?**
