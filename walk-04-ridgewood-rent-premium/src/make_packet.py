"""Walk packet -> print-ready PDF, one file per group.

Run:  python src/make_packet.py            (or: make packet)
      python src/make_packet.py --preview  (also writes PNGs, for checking)

Four pages per group, US Letter, portrait:
  1. cover + the rule + the route map
  2. that group's bearing + the prediction table they fill in walking
  3. the regroup page: the coefficient blank, and a grid to plot guesses on
  4. the back page: the value-capture sum and the closing question

Everything printed here is content, not analysis — the numbers are read
from config below so there is one place to change them. Deliberately NOT
printed: the north/south rent expectations. People are predicting; the
packet gives them one piece of intuition only ("Ridgewood is
up-and-coming"), same as the script.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "walk"
MAP = ROOT / "outputs" / "figures" / "route_map.png"

INK, MUTED, BLUE, WASH = "#1a1a1a", "#7a7f88", "#1f77b4", "#eaf2f8"
RULE = "Walk 15 minutes out. Then turn around."
WALK_DATE = "Saturday, September 26"
START = "Seneca Ave & Palmetto St"

GROUPS = {
    "north": ("NORTH", "Up Palmetto St → right on Woodward Ave → left on Putnam Ave,\nheading toward the Fresh Pond Rd station."),
    "south": ("SOUTH", "West on Seneca Ave → a block over, left on Gates Ave,\nheading down toward Knickerbocker Ave."),
    "west":  ("WEST",  "Down Seneca Ave → Grover Cleveland Park → right on Hart St,\nout to the intersections."),
    "east":  ("EAST",  "East along Seneca Ave, toward Evergreen Park."),
}

_PREMIUM_RAW = ("Within a 20-minute walk of an M-only station, the average "
                "renter household pays about $96 a month more than they would "
                "20 minutes out. There are 69,047 such households. That is "
                "roughly $79 million a year in rent attributable to being "
                "near these stations.")
PREMIUM = textwrap.fill(_PREMIUM_RAW, 62) + "\n\nThe MTA collects the fare."
QUESTION = "If proximity to a subway station\ngenerates a premium,\nwho captures it?"


def trimmed_map():
    """The route map PNG carries a wide white margin; crop it so the map
    fills the space it is given on the page."""
    im = Image.open(MAP).convert("RGB")
    a = np.asarray(im)
    ink = (a.min(axis=2) < 245)          # any pixel that isn't near-white
    rows, cols = np.where(ink.any(axis=1))[0], np.where(ink.any(axis=0))[0]
    pad = 12
    top, bot = max(rows[0] - pad, 0), min(rows[-1] + pad, a.shape[0])
    left, right = max(cols[0] - pad, 0), min(cols[-1] + pad, a.shape[1])
    return a[top:bot, left:right]


def page(pdf, draw, preview=None, tag=""):
    fig = plt.figure(figsize=(8.5, 11), dpi=150)
    fig.patch.set_facecolor("white")
    draw(fig)
    pdf.savefig(fig)
    if preview is not None:
        fig.savefig(preview / f"preview_{tag}.png", dpi=110)
    plt.close(fig)


def box(fig, x, y, w, h, fc=WASH, ec="none", lw=0, r=0.012):
    fig.patches.append(FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
        transform=fig.transFigure, facecolor=fc, edgecolor=ec, linewidth=lw,
        zorder=0))


def kicker(fig, text):
    # matplotlib has no letter-spacing; space the characters by hand.
    fig.text(0.08, 0.945, " ".join(text), fontsize=8.5, color=MUTED,
             ha="left", fontweight="bold")


def footer(fig, text):
    fig.text(0.08, 0.042, text, fontsize=8, color=MUTED, ha="left")
    fig.text(0.92, 0.042, "The Walkthrough NYC", fontsize=8, color=MUTED, ha="right")


# ---------------------------------------------------------------- pages

def cover(fig):
    kicker(fig, "WALK NO. 04")
    fig.text(0.08, 0.892, "The Ridgewood\nRent Premium", fontsize=32,
             color=INK, ha="left", va="top", fontweight="bold", linespacing=1.08)
    fig.text(0.08, 0.773, f"{WALK_DATE}   ·   Start: {START}",
             fontsize=11.5, color=MUTED, ha="left", va="top")

    box(fig, 0.08, 0.678, 0.84, 0.062, fc=BLUE)
    fig.text(0.5, 0.709, RULE, fontsize=18, color="white", ha="center",
             va="center", fontweight="bold")

    fig.text(0.08, 0.652, "Not to a destination — to a time. Everyone covers about the same\n"
                          "ground, and everyone gets back here together.",
             fontsize=10.5, color=INK, ha="left", va="top", linespacing=1.5)

    ax = fig.add_axes([0.05, 0.145, 0.90, 0.455])
    ax.imshow(trimmed_map())
    ax.axis("off")

    fig.text(0.08, 0.108, "On your walk you make three predictions about rent: one in the first minute,\n"
                          "one around minutes 7–10, one around minutes 12–15, just before you turn around.",
             fontsize=10, color=INK, ha="left", va="top", linespacing=1.5)
    footer(fig, "Walk No. 04")


def route_page(name, bearing):
    def draw(fig):
        kicker(fig, "YOUR ROUTE")
        fig.text(0.08, 0.90, name, fontsize=46, color=BLUE, ha="left",
                 va="top", fontweight="bold")
        fig.text(0.08, 0.815, bearing, fontsize=13, color=INK, ha="left",
                 va="top", linespacing=1.6)

        box(fig, 0.08, 0.700, 0.84, 0.048, fc=WASH)
        fig.text(0.5, 0.724, RULE, fontsize=13, color=INK, ha="center",
                 va="center", fontweight="bold")

        fig.text(0.08, 0.672, "Your three predictions", fontsize=15,
                 color=INK, ha="left", va="top", fontweight="bold")
        fig.text(0.08, 0.645, "What does a typical apartment rent for, right where you are standing?",
                 fontsize=10, color=MUTED, ha="left", va="top")

        heads = [("When", 0.10), ("Where you are", 0.26),
                 ("Your guess", 0.56), ("Actual", 0.72), ("Off by", 0.845)]
        top = 0.605
        for h, x in heads:
            fig.text(x, top, h, fontsize=9.5, color=MUTED, ha="left",
                     fontweight="bold")
        rows = ["First minute", "Minutes 7–10", "Minutes 12–15"]
        rh = 0.115
        for i, r in enumerate(rows):
            y = top - 0.028 - (i + 1) * rh
            box(fig, 0.08, y, 0.84, rh - 0.014, fc="#f7f7f5")
            fig.text(0.10, y + (rh - 0.014) / 2, r, fontsize=11, color=INK,
                     va="center", fontweight="bold")
            for x in (0.24, 0.54, 0.70, 0.825):
                fig.lines.append(plt.Line2D(
                    [x, x], [y + 0.008, y + rh - 0.022], transform=fig.transFigure,
                    color="#dcdcd8", lw=0.9))
        fig.text(0.08, 0.175, "No looking anything up. The only hint you get: Ridgewood is an\n"
                              "up-and-coming neighborhood.",
                 fontsize=10.5, color=INK, ha="left", va="top", linespacing=1.5)
        footer(fig, f"{name} group")
    return draw


def regroup(fig):
    kicker(fig, "AT THE REGROUP")
    fig.text(0.08, 0.90, "What we found", fontsize=30, color=INK, ha="left",
             va="top", fontweight="bold")
    fig.text(0.08, 0.838, "Fill this in together, once everyone is back.",
             fontsize=11, color=MUTED, ha="left", va="top")

    box(fig, 0.08, 0.735, 0.84, 0.072, fc=WASH)
    fig.text(0.5, 0.771, "Rent falls about ______ % per minute you walk\n"
                         "away from an M-only station.",
             fontsize=14.5, color=INK, ha="center", va="center",
             fontweight="bold", linespacing=1.6)

    fig.text(0.08, 0.700, "Plot your three guesses", fontsize=15, color=INK,
             ha="left", va="top", fontweight="bold")
    fig.text(0.08, 0.674, "Minutes walked, against the rent you guessed.",
             fontsize=10, color=MUTED, ha="left", va="top")

    ax = fig.add_axes([0.13, 0.20, 0.78, 0.44])
    ax.set_xlim(0, 15)
    ax.set_ylim(1400, 3000)
    ax.set_xticks(range(0, 16, 1))
    ax.set_yticks(range(1400, 3001, 200))
    ax.set_yticklabels([f"${v:,}" for v in range(1400, 3001, 200)], fontsize=9)
    ax.tick_params(axis="x", labelsize=9)
    ax.grid(True, color="#e2e2de", lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c9c9c4")
    ax.set_xlabel("Minutes walked from the start", fontsize=10.5, color=INK)
    ax.set_ylabel("Rent you guessed ($/mo)", fontsize=10.5, color=INK)

    fig.text(0.08, 0.148, "Then we put everyone's guesses on one chart against the model —\n"
                          "four directions, same fifteen minutes.",
             fontsize=10.5, color=INK, ha="left", va="top", linespacing=1.5)
    footer(fig, "Regroup")


def back(fig):
    kicker(fig, "THE NUMBER")
    fig.text(0.08, 0.90, "What the premium\nadds up to", fontsize=30, color=INK,
             ha="left", va="top", fontweight="bold", linespacing=1.1)

    box(fig, 0.08, 0.523, 0.84, 0.237, fc=WASH)
    fig.text(0.12, 0.735, PREMIUM, fontsize=12.5, color=INK, ha="left",
             va="top", linespacing=1.75)

    fig.text(0.08, 0.492, "Compared to living 20 minutes away — the comparison is the number.",
             fontsize=9.5, color=MUTED, ha="left", va="top", style="italic")

    fig.text(0.5, 0.36, QUESTION, fontsize=25, color=BLUE, ha="center",
             va="center", fontweight="bold", linespacing=1.5)

    fig.text(0.08, 0.175, "The analysis behind this walk — every number, every judgment call —\n"
                          "is public:",
             fontsize=10.5, color=INK, ha="left", va="top", linespacing=1.5)
    fig.text(0.08, 0.132, "thewalkthroughnyc.substack.com", fontsize=12,
             color=BLUE, ha="left", va="top", fontweight="bold")
    fig.text(0.08, 0.098, "Try the model yourself:  " + "_" * 34, fontsize=10.5,
             color=MUTED, ha="left", va="top")
    footer(fig, "Rent data: ACS 2020–2024 5-year, median gross rent")


def build(key, preview_dir=None):
    name, bearing = GROUPS[key]
    out = OUT / f"packet_{key}.pdf"
    with PdfPages(out) as pdf:
        page(pdf, cover, preview_dir, f"{key}_1")
        page(pdf, route_page(name, bearing), preview_dir, f"{key}_2")
        page(pdf, regroup, preview_dir, f"{key}_3")
        page(pdf, back, preview_dir, f"{key}_4")
        d = pdf.infodict()
        d["Title"] = f"Walk No. 04 — The Ridgewood Rent Premium ({name} group)"
        d["Author"] = "The Walkthrough NYC"
    print(f"  walk/{out.name}")


def main() -> None:
    preview = None
    if "--preview" in sys.argv:
        preview = ROOT / "outputs" / "packet_preview"
        preview.mkdir(parents=True, exist_ok=True)
    if not MAP.exists():
        sys.exit(f"missing {MAP} — run 'make clean_join' or regenerate the route map")
    print("Packets (US Letter, 4 pages each):")
    for key in GROUPS:
        build(key, preview)


if __name__ == "__main__":
    main()
