#!/usr/bin/env python3
"""Figure CHAR-1 -- an arc of improvements, and what power did to it.

Sources : results/omniglot_gate_run15_power_b.log, run16_reconcile.log
Writes  : book/figures/char_1_arc.svg
Chapter : 5 (One-shot characters)

Left: the arc as it was reported, run by run, on a four-alphabet evaluation --
point estimates, no intervals, each delta a decision. Right: the same
configurations at power with intervals, plus the run-16 comparator transplant.
The figure is the chapter: the left panel is what noise looks like when you
plot it without error bars.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "char_1_arc.svg")

# as reported, small eval, no intervals (from the run logs' own control lines)
ARC = [("multiset", 12.5), ("composition", 33.8), ("rel2", 30.0),
       ("AbS", 37.5), ("full dwell", 27.5), ("+appearance", 41.2),
       ("instance", 41.2), ("sub-stroke", 40.0)]

# at power, n=400 / n=200, with intervals
POWERED = [
    ("adopted config, n=400", 26.8, 22.6, 31.3, sp.ARM_A),
    ("+ junction blend, n=400", 26.8, 22.6, 31.3, sp.ARM_A),
    ("adopted, reproduced n=200", 22.0, 16.8, 28.2, sp.NULLC),
    ("SC+TPS shortlist", 48.0, 41.1, 55.0, sp.ARM_B),
    ("SC+TPS full dwell", 73.5, 67.0, 79.1, sp.ARM_B),
]


def main():
    W, H = 780, 552
    f = sp.Fig(W, H)
    f.title(46, 34, "Fifteen runs of improvement, and one powered measurement",
            "One-shot 20-way accuracy · left: as reported · right: at power, "
            "with intervals")

    # --- left: the arc, no intervals -------------------------------------
    f.text(46, 78, "As reported — four alphabets, point estimates", cls="lbl")
    ax = sp.Axes(f, 150, 92, 200, 190, xlim=(0, 50), ylim=(-0.6, len(ARC) - 0.4))
    ax.frame(left=False)
    ax.xticks([0, 25, 50], fmt=lambda v: f"{v:g}%")
    for i, (lab, v) in enumerate(ARC):
        yy = ax.py(len(ARC) - 1 - i)
        f.rect(ax.x0, yy - 5, ax.px(v) - ax.x0, 10, fill=sp.ARM_A, opacity=0.30)
        f.text(144, yy + 4, lab, cls="note", anchor="end")
        f.text(ax.px(v) + 6, yy + 4, f"{v:g}", cls="note")
    f.text(46, 322, "Every step here was a decision: adopt, discard, or",
           cls="note")
    f.text(46, 336, "branch. None of them carries an interval.", cls="note")

    # --- right: at power --------------------------------------------------
    f.text(430, 78, "At power — with intervals", cls="lbl")
    ax2 = sp.Axes(f, 500, 92, 200, 190, xlim=(0, 85),
                  ylim=(-0.6, len(POWERED) - 0.4))
    ax2.frame(left=False)
    ax2.xticks([0, 25, 50, 75], fmt=lambda v: f"{v:g}%")
    for i, (lab, m, lo, hi, col) in enumerate(POWERED):
        yy = ax2.py(len(POWERED) - 1 - i)
        ax2.interval_h(yy, lo, hi, m, colour=col, r=4.0, capsize=4)
        f.text(494, yy + 4, lab, cls="note", anchor="end")
        f.text(ax2.px(hi) + 8, yy + 4, f"{m:g}", cls="val")
    f.text(430, 322, "The first two overlap completely. The last is the same",
           cls="note")
    f.text(430, 336, "representation with a different verdict comparator.",
           cls="note")

    f.line(46, 362, 734, 362, sp.RULE, 0.8)
    f.text(46, 384, "What the powered run did to the arc", cls="lbl")
    for i, ln in enumerate((
            "Every post-composition delta — AbS +3.7, dwell, appearance +2.5, "
            "rel2 −3.8, sub-stroke −1.2 — sits",
            "inside the intervals at power. One change recorded as a LOSER "
            "(rel2) is numerically on top. What",
            "survives is composition, +21pp over multiset, and it survives "
            "because it was large enough to be",
            "visible without error bars — which is luck, not method.",
            "",
            "Then run 16: the same earned representation, judged by strong "
            "continuous geometry instead of a weak",
            "render-and-compare, reaches 73.5% [67.0, 79.1] — +51.5pp, "
            "CI-separated, and CHEAPER per comparison.",
            "Bins propose; continuous decides.")):
        f.text(46, 404 + i * 15, ln, cls="note")

    f.caption(46, 524, [
        "Sources: results/omniglot_gate_run15_power_b.log, "
        "results/omniglot_gate_run16_reconcile.log · generator: "
        "book/figures/fig_char_arc.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
