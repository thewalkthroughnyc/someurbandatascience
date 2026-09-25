# Packet layout (print Fri Sep 25 — fixed layout, only the numbers change)

> **The packets are built.** `make packet` writes `walk/packet_north.pdf`,
> `packet_south.pdf`, `packet_west.pdf` and `packet_east.pdf` — US Letter,
> four pages each, one per group. The copy and the numbers live at the top
> of `src/make_packet.py`; this file stays as the reasoning behind the
> layout. Print each group's file for the people in that group.

- **Route map**, start marked at Seneca Ave & Palmetto St, the four group routes,
  the six M-only stations.
- **Your route**, printed per group (north / south / west / east) so nobody is
  navigating off a shared map.
- **Prediction table — three rows, by the clock, not by building.** This matches
  the script: people predict at a time, wherever they happen to be standing.

  | # | When | Where you are | Your rent guess | Actual | Error |
  |---|---|---|---|---|---|
  | 1 | first minute | | | | |
  | 2 | minutes 7–10 | | | | |
  | 3 | minutes 12–15 | | | | |

  **Print the rule at the top of this page: walk 15 minutes out, then turn
  around.** Time-boxed, not destination-boxed — everyone covers the same
  ground and gets back together.

  No bedroom size to pick and no "anchor on your own rent" prompt — the script
  gives people one piece of intuition only ("Ridgewood is up-and-coming"), and
  the packet shouldn't hand them more.

- **The Ridgewood-gradient number with the coefficient left blank** — filled in
  together at the regroup, not at the start.
- **Back page: the value-capture sum.**

  > Within a 20-minute walk of an M-only station, the average renter household
  > pays about **$96/month** more than they would 20 minutes out. There are
  > **69,047** such households. That's roughly **$79 million a year** in rent
  > attributable to being near these stations. The MTA collects the fare.

  <!-- Jordan's call, Sep 24: the 20-minute reference, not the 30. Say
  "compared to living 20 minutes away" out loud or the number doesn't mean
  anything — it swings to $178M at a 30-minute reference and $361M at 44. -->

- **The model's URL, on two pages.** On the regroup page, where people will
  actually open it on a phone, and again on the back page:
  `ridgewood-rent-gradient.netlify.app`.
- **Closing question, printed on the back page:** **If proximity to a subway
  station generates a premium, who captures it?** Same wording as the Substack
  post, so anyone who came from the post arrives already holding the question.
