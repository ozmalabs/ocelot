#!/usr/bin/env python3
"""Figure TOWN-1 -- a path forms, and un-forms.

Source  : docs/research/engine_substrate/TERRAIN_WEAR_STIGMERGY_RESULTS.md §2
Writes  : book/figures/town_1_wear.svg
Chapter : 13 (The town)

One accumulator read in two directions. The measured point is not that a path
appears -- it is that the movement cost falls SMOOTHLY as wear accumulates,
because that is what lets traffic recruit traffic. A threshold-only flip would
make wear invisible until it tripped, and nothing would converge.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "town_1_wear.svg")

ROWS = [(0, 0.000, "grass", 1.0000), (10, 0.275, "grass", 0.9038),
        (20, 0.550, "grass", 0.8075), (30, 0.825, "grass", 0.7113),
        (40, 1.000, "path", 0.6500)]
IDLE = (0.003, "grass", 0.9991)


def main():
    W, H = 780, 492
    f = sp.Fig(W, H)
    f.title(46, 34, "A path forms because part-worn ground is already easier",
            "40 crossings of one grass cell, then 400 idle turns")

    ax = sp.Axes(f, 110, 90, 380, 160, xlim=(-2, 42), ylim=(0.60, 1.05))
    ax.frame()
    ax.xticks([0, 10, 20, 30, 40], fmt=lambda v: f"{int(v)}",
              label="crossings")
    ax.yticks([0.65, 0.75, 0.85, 0.95, 1.05], fmt=lambda v: f"{v:.2f}",
              label="movement cost multiplier", grid=True)

    d = " ".join(f"{'M' if i == 0 else 'L'} {ax.px(p):.2f} {ax.py(m):.2f}"
                 for i, (p, _, _, m) in enumerate(ROWS))
    f.path(d, stroke=sp.ARM_A, width=1.8)
    for p, w, terr, m in ROWS:
        col = sp.ARM_B if terr == "path" else sp.ARM_A
        f.circle(ax.px(p), ax.py(m), 4.4, fill=col)
        f.text(ax.px(p), ax.py(m) - 12, f"wear {w:.3f}", cls="note",
               anchor="middle")
    f.text(ax.px(40) - 10, ax.py(0.665), "terrain becomes path", cls="val",
           anchor="end", fill=sp.ARM_B)

    # the return leg
    f.text(516, 104, "…then 400 idle turns", cls="lbl")
    ax2 = sp.Axes(f, 516, 118, 190, 40, xlim=(0.60, 1.05), ylim=(0, 1))
    ax2.frame(left=False)
    ax2.xticks([0.65, 0.85, 1.05], fmt=lambda v: f"{v:.2f}")
    f.circle(ax2.px(0.65), ax2.y0 + 18, 4.4, fill=sp.ARM_B)
    f.circle(ax2.px(IDLE[2]), ax2.y0 + 18, 4.4, fill=sp.ARM_A)
    f.path(f"M {ax2.px(0.66):.1f} {ax2.y0 + 18:.1f} "
           f"L {ax2.px(IDLE[2]) - 6:.1f} {ax2.y0 + 18:.1f}",
           stroke=sp.MUTED, width=1.2, dash="4 3")
    f.text(516, 196, f"wear {IDLE[0]:.3f} · back to {IDLE[1]}", cls="note")
    f.text(516, 212, "Reversion needs no second field: the", cls="note")
    f.text(516, 226, "target is the terrain the cell was", cls="note")
    f.text(516, 240, "seeded as. A formed path is never", cls="note")
    f.text(516, 254, "confused with a built one.", cls="note")

    f.line(46, 300, 734, 300, sp.RULE, 0.8)
    f.text(46, 322, "Why the smooth line is the finding", cls="lbl")
    for i, ln in enumerate((
            "The terrain flips to path at the end, but the cost has been "
            "falling the whole way — 1.0000, 0.9038,",
            "0.8075, 0.7113, 0.6500. That interpolation is the feedback loop: "
            "part-worn ground is already easier",
            "to cross, so traffic recruits traffic. Under a threshold-only "
            "rule the wear would be invisible until it",
            "tripped, and there would be nothing for the population to "
            "converge on.",
            "",
            "Route choice is cognition and lives in a rule. Ground wearing "
            "under load is physics and lives in the",
            "world. The split is the design.")):
        f.text(46, 342 + i * 15, ln, cls="note")

    f.caption(46, 476, [
        "Source: TERRAIN_WEAR_STIGMERGY_RESULTS.md §2 (bigville, external "
        "repository) · generator: book/figures/fig_town_wear.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
