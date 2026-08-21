#!/usr/bin/env python3
"""Figure EYE-2 -- illumination invariance: the log receptor, measured.

Reads   : results/eye_confirm.log  (H1, seeds 11000-11011, n=12)
Writes  : book/figures/eye_2_invariance.svg
Chapter : 1 (The Eye), claim 1 -- every constant falls out.

The gate was CONJUNCTIVE and pre-registered: the log arm must sit under the
SESOI at every k AND the linear arm must sit above it -- the second half is
the positive control that says the measure is not inert. Both halves are drawn,
because a figure of the log arm alone would be the inert-instrument defect.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eye_confirm
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "eye_2_invariance.svg")


def main():
    d = eye_confirm.load()
    n = len(d["seeds"]["LOG"])

    W, H = 760, 470
    f = sp.Fig(W, H)
    f.title(46, 34, "The log receptor buys illumination invariance",
            f"H1 · {n} seeds · patdiff as a percentage of the same-scene floor "
            f"· pre-registered gate")

    # log scale on x: 0.1% .. 200% of floor
    import math
    lo, hi = math.log10(0.05), math.log10(300)
    ax = sp.Axes(f, 150, 92, 520, 132, xlim=(lo, hi), ylim=(0, 1))
    ax.frame(left=False)
    ticks = [0.1, 1, 10, 100]
    for t in ticks:
        x = ax.px(math.log10(t))
        f.line(x, ax.y0, x, ax.y0 + ax.h, sp.RULE, 0.6, dash="2 4")
        f.line(x, ax.y0 + ax.h, x, ax.y0 + ax.h + 4, sp.RULE, 1.0)
        f.text(x, ax.y0 + ax.h + 17, f"{t:g}%", cls="tick", anchor="middle")
    f.text(ax.x0 + ax.w / 2, ax.y0 + ax.h + 36,
           "difference between illuminations, as % of the floor",
           cls="lbl", anchor="middle")

    # SESOI = 10% of floor, the pre-registered line
    xs = ax.px(math.log10(10))
    f.line(xs, ax.y0 - 8, xs, ax.y0 + ax.h, sp.ACCENT, 1.4, dash="5 3")
    f.text(xs, ax.y0 - 14, "SESOI (10% of floor)", cls="note", anchor="middle",
           fill=sp.ACCENT)

    rows = (("log receptor", "LOG", sp.ARM_A),
            ("linear receptor", "LINEAR", sp.ARM_B))
    for i, (lab, arm, col) in enumerate(rows):
        yy = ax.y0 + 34 + i * 58
        f.text(144, yy + 4, lab, cls="lbl", anchor="end")
        for k, r in ((1000, 3.6), (10000, 3.6)):
            s = d["summary"][(arm, k)]
            f.circle(ax.px(math.log10(s["pct_of_floor"])), yy, r, fill=col,
                     opacity=0.9)
        s1 = d["summary"][(arm, 1000)]
        s2 = d["summary"][(arm, 10000)]
        f.text(ax.px(math.log10(s1["pct_of_floor"])), yy - 12,
               f"{s1['pct_of_floor']:.2f}%  /  {s2['pct_of_floor']:.2f}%",
               cls="val", anchor="middle" if arm == "LOG" else "end")
        f.text(144, yy + 20, "k = 1000 and k = 10000", cls="note", anchor="end")

    f.text(46, 282, "Why this is a derivation and not a design choice",
           cls="lbl")
    for i, ln in enumerate((
            "Weber's law IS a logarithm of an intensity ratio. Take the log at "
            "the receptor and the ratio survives",
            "a change of illumination while the absolute level does not — so "
            "invariance is not a feature added to",
            "the eye, it is what taking the log already means. The measured "
            "gap is a factor of about 1000.")):
        f.text(46, 302 + i * 15, ln, cls="note")

    f.text(46, 362, "The half of the gate that makes it a result", cls="lbl")
    f.text(46, 382,
           "The linear arm sits at 100% of floor — a full mismatch. That is "
           "the positive control:", cls="note")
    f.text(46, 397,
           "a measure that reported near-zero for BOTH arms would be inert, "
           "and would prove nothing.", cls="note")

    f.caption(46, 430, [
        f"Floor = patdiff between two DIFFERENT probe scenes at the same "
        f"illumination (log arm: {d['floor']['LOG']['mean']:.5f}).",
        "Source: results/eye_confirm.log · prereg VISION_EYE_PREREG.md, "
        "committed before the run · generator: book/figures/"
        "fig_eye_invariance.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
