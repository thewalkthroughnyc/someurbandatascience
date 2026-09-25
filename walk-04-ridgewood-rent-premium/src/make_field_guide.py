"""Leader's field guide -> one print-ready PDF.

Run:  python src/make_field_guide.py           (or: make guide)
      python src/make_field_guide.py --preview

This is the sheet Jordan carries. It is the opposite of the packet: it
holds everything the packet deliberately withholds — what the data
predicts for each bearing, the reveal numbers, and the answers to the
questions a stranger is likely to ask. Layout helpers are shared with
src/make_packet.py so the two look like one family.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_packet import BLUE, INK, MUTED, WASH, box, footer, kicker, page  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "walk" / "field_guide.pdf"

RUN_OF_SHOW = [
    ("0:00", "Gather", "Seneca Ave & Palmetto St. Hand out packets by group."),
    ("0:05", "Opening", "Read it. End on: three predictions, by the clock."),
    ("0:10", "Split", "Four bearings. Everyone walks 15 out, then turns around."),
    ("0:25", "Turnaround", "Wherever they are. Nobody has to reach a landmark."),
    ("0:40", "Back at the start", "Regroup. Guesses on the chart before any numbers."),
    ("0:50", "The reveal", "North and south have real numbers. East and west don't."),
    ("1:05", "Walk to the cafe", "Abracadabra Magic Cafe."),
    ("1:15", "Close", "The gradient, the $79M, then the question. Stop talking."),
]

BEARINGS = [
    ("NORTH", "Palmetto → Woodward → Putnam", "15.8 min: just short of Fresh Pond Rd",
     "FALLS", "$2,083 → $1,913"),
    ("SOUTH", "Seneca → Gates Ave", "15.4 min: about at Knickerbocker Av",
     "RISES, slightly", "$2,083 → $2,116"),
    ("WEST", "Seneca → Grover Cleveland Pk → Hart", "~13 min (map read)",
     "NO PREDICTION", "the live experiment"),
    ("EAST", "Seneca, eastbound", "~15 min (map read)",
     "NO PREDICTION", "the live experiment"),
]

STATIONS = [("Central Av", "$2,278"), ("Myrtle-Wyckoff", "$2,134"),
            ("Knickerbocker Av", "$2,116"), ("Seneca Av  (start)", "$2,083"),
            ("Forest Av", "$1,926"), ("Fresh Pond Rd", "$1,913")]

POINTS = [
    ("Opposite directions, opposite answers.",
     "Same fifteen minutes: north falls about $170, south rises about $33. "
     "That is the whole walk in one line."),
    ("The drop isn't linear.",
     "North loses $157 in the first seven minutes and only $13 in the next "
     "eight. Steepest close in \u2014 what a decay model predicts, and what "
     "nobody guesses."),
    ("The south side is noisier than it looks.",
     "Myrtle-Wyckoff and Knickerbocker swap order depending on the radius. "
     "The honest read is \u201crising, then flat.\u201d Don't over-claim that "
     "dip at minute 15."),
]

QA = [
    ("“Is this StreetEasy?”",
     "No. Census ACS — the government asks people what they actually pay. Rent "
     "plus utilities, averaged over 2020–2024, and mostly people already living "
     "here, not what's listed today. That makes it lower than a new lease, and "
     "more honest about what the neighborhood costs."),
    ("“Why only the M?”",
     "These six stations are M-only — they lose through-service to Manhattan "
     "overnight and shrink to a shuttle. Distance to every other nearby station "
     "is held fixed in the model, so the number means ‘near this tier,’ not "
     "‘near some train.’"),
    ("“Myrtle-Wyckoff is on the M though.”",
     "It is, but it's also the L transfer — so it's a control, not part of the "
     "M-only cluster. The transit feed lists it as two rows, one per line, and "
     "reading it naively makes it look M-only. That correction is the reason the "
     "south group's middle number behaves oddly."),
    ("“Does this prove the train causes it?”",
     "No, and say so plainly. It's a description. Station locations and "
     "neighborhood change are tangled together and one snapshot can't separate "
     "them. That's exactly what east and west are for."),
    ("“What about public housing?”",
     "Seven tracts in the sample sit near $500 a month, fully renter-occupied — "
     "rent set as a share of income, not by the market. They can't respond to a "
     "subway at all. They're in the model, unadjusted. Worth raising as a "
     "question rather than an answer."),
    ("“How far does the effect reach?”",
     "Inside a 30-minute walk it's basically flat — the gradient only shows up "
     "when the far tracts are in the picture. Don't oversell what happens within "
     "the first fifteen minutes; that's the part they just walked."),
]


def header(fig, kick, title, sub=None):
    kicker(fig, kick)
    fig.text(0.07, 0.905, title, fontsize=25, color=INK, ha="left", va="top",
             fontweight="bold")
    if sub:
        fig.text(0.07, 0.858, sub, fontsize=10.5, color=MUTED, ha="left", va="top")


def page1(fig):
    header(fig, "FIELD GUIDE · WALK NO. 04", "Run of show",
           "Sat Sep 26 · Seneca Ave & Palmetto St · rain date Sat Oct 3")
    y = 0.800
    for t, what, note in RUN_OF_SHOW:
        box(fig, 0.07, y - 0.043, 0.86, 0.052, fc="#f7f7f5")
        fig.text(0.095, y - 0.017, t, fontsize=12, color=BLUE, va="center",
                 fontweight="bold")
        fig.text(0.185, y - 0.017, what, fontsize=11, color=INK, va="center",
                 fontweight="bold")
        fig.text(0.40, y - 0.017, note, fontsize=9.5, color=MUTED, va="center")
        y -= 0.062

    box(fig, 0.07, 0.185, 0.86, 0.085, fc=WASH)
    fig.text(0.5, 0.2475, "The rule that holds it together", fontsize=10,
             color=MUTED, ha="center", va="center", fontweight="bold")
    fig.text(0.5, 0.215, "Everyone walks 15 minutes out, then turns around.",
             fontsize=14.5, color=INK, ha="center", va="center", fontweight="bold")

    fig.text(0.07, 0.150, "Time-boxed, not destination-boxed. Holding walk-time constant is what makes\n"
                          "direction the only thing that varies — and it means east and west never need\n"
                          "measuring. Whatever they reach in 15 minutes is the data point.",
             fontsize=9.5, color=INK, ha="left", va="top", linespacing=1.6)
    footer(fig, "Run of show")


def page2(fig):
    header(fig, "FOR YOUR EYES", "The four bearings",
           "The packet does not print any of this. They are predicting.")
    y = 0.790
    for name, route, reach, verdict, nums in BEARINGS:
        live = verdict.startswith("NO")
        box(fig, 0.07, y - 0.094, 0.86, 0.105, fc="#f7f7f5" if not live else WASH)
        fig.text(0.095, y - 0.012, name, fontsize=15, color=BLUE, va="center",
                 fontweight="bold")
        fig.text(0.26, y - 0.012, route, fontsize=10, color=INK, va="center")
        fig.text(0.095, y - 0.045, reach, fontsize=9.5, color=MUTED, va="center")
        fig.text(0.095, y - 0.075, verdict, fontsize=11, color=INK, va="center",
                 fontweight="bold")
        fig.text(0.33, y - 0.075, nums, fontsize=11, color=INK, va="center")
        y -= 0.122

    box(fig, 0.07, 0.140, 0.86, 0.172, fc="#fdf4e8")
    fig.text(0.095, 0.292, "The wrinkle: the south group passes Myrtle-Wyckoff around minute 7",
             fontsize=11, color=INK, va="top", fontweight="bold")
    fig.text(0.095, 0.256, "That is not an M-only station — it's the L transfer the analysis had to\n"
                           "special-case. In the model's terms their middle prediction lands near a local\n"
                           "maximum distance from any M-only station, where the model wants a dip and the\n"
                           "observed rent shows a rise. Don't hide the gap. It is the confound this walk\n"
                           "exists to probe: better transit vs. distance from the M-only cluster.",
             fontsize=9.5, color=INK, va="top", linespacing=1.6)
    footer(fig, "Bearings")


def page3(fig):
    header(fig, "AT THE REGROUP", "The reveal",
           "Guesses on the chart first. Numbers second.")

    fig.text(0.07, 0.815, "Observed median rent within 0.4 mi", fontsize=12,
             color=INK, va="top", fontweight="bold")
    fig.text(0.07, 0.789, "West to east along the line", fontsize=9.5,
             color=MUTED, va="top")
    y = 0.752
    for i, (st, val) in enumerate(STATIONS):
        if i % 2 == 0:
            box(fig, 0.07, y - 0.023, 0.40, 0.030, fc="#f7f7f5")
        fig.text(0.09, y - 0.008, st, fontsize=10.5, color=INK, va="center")
        fig.text(0.44, y - 0.008, val, fontsize=10.5, color=INK, va="center",
                 ha="right", fontweight="bold")
        y -= 0.034

    fig.text(0.53, 0.815, "Matched to their three stops", fontsize=12,
             color=INK, va="top", fontweight="bold")
    rows = [("", "min 1", "~min 7", "~min 15"),
            ("North", "$2,083", "$1,926", "$1,913"),
            ("South", "$2,083", "$2,134", "$2,116")]
    y = 0.767
    for i, r in enumerate(rows):
        for x, cell in zip((0.53, 0.655, 0.755, 0.86), r):
            fig.text(x, y, cell, fontsize=10.5, va="center",
                     color=MUTED if i == 0 else INK,
                     fontweight="bold" if i == 0 or x == 0.53 else "normal")
        y -= 0.038

    fig.text(0.53, 0.640, "North falls ~$170 over the same\nfifteen minutes that south rises ~$33.",
             fontsize=10, color=INK, va="top", linespacing=1.6)

    fig.text(0.07, 0.520, "Say these three things", fontsize=12, color=INK,
             va="top", fontweight="bold")
    y = 0.482
    for head, body in POINTS:
        fig.text(0.085, y, "\u2022", fontsize=11, color=BLUE, va="top",
                 fontweight="bold")
        fig.text(0.11, y, head, fontsize=10.5, color=INK, va="top",
                 fontweight="bold")
        fig.text(0.11, y - 0.025, textwrap.fill(body, 84), fontsize=9.5,
                 color=MUTED, va="top", linespacing=1.6)
        y -= 0.088

    box(fig, 0.07, 0.085, 0.86, 0.130, fc=WASH)
    fig.text(0.095, 0.193, "Then the close", fontsize=10, color=MUTED, va="top",
             fontweight="bold")
    fig.text(0.095, 0.165, "Rent falls about half a percent per minute you walk\n"
                           "away from an M-only station.",
             fontsize=12.5, color=INK, va="top", fontweight="bold", linespacing=1.5)
    fig.text(0.095, 0.108, "Then the $79M, then the question. Say the question last and stop talking.",
             fontsize=9.5, color=MUTED, va="top")
    footer(fig, "The reveal")


def page4(fig):
    header(fig, "IF SOMEONE ASKS", "Answers", None)
    y = 0.850
    for q, a in QA:
        fig.text(0.07, y, q, fontsize=11, color=BLUE, va="top", fontweight="bold")
        fig.text(0.07, y - 0.025, textwrap.fill(a, 92), fontsize=9.5,
                 color=INK, va="top", linespacing=1.65)
        y -= 0.115

    box(fig, 0.07, 0.055, 0.86, 0.125, fc="#f7f7f5")
    fig.text(0.095, 0.166, "The number, said correctly", fontsize=10, color=MUTED,
             va="top", fontweight="bold")
    fig.text(0.095, 0.140, "$79 million a year \u2014 69,047 renter households, about $96/month\n"
                           "each, compared to living twenty minutes away.",
             fontsize=10.5, color=INK, va="top", linespacing=1.6)
    fig.text(0.095, 0.087, "Say the comparison out loud. Without it the number means nothing: "
                           "it's $178M at 30 minutes.",
             fontsize=9, color=MUTED, va="top", style="italic")
    fig.text(0.07, 0.035, "ridgewood-rent-gradient.netlify.app", fontsize=9.5,
             color=BLUE, ha="left", fontweight="bold")
    fig.text(0.93, 0.035, "The Walkthrough NYC", fontsize=8, color=MUTED, ha="right")


def main() -> None:
    preview = None
    if "--preview" in sys.argv:
        preview = ROOT / "outputs" / "packet_preview"
        preview.mkdir(parents=True, exist_ok=True)
    with PdfPages(OUT) as pdf:
        for i, fn in enumerate([page1, page2, page3, page4], start=1):
            page(pdf, fn, preview, f"guide_{i}")
        d = pdf.infodict()
        d["Title"] = "Walk No. 04 — leader's field guide"
        d["Author"] = "The Walkthrough NYC"
    print(f"  walk/{OUT.name}")


if __name__ == "__main__":
    main()
