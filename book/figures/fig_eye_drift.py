#!/usr/bin/env python3
"""Figure EYE-4 -- fixational drift: the crossover, and what removes it.

Reads   : results/eye_confirm.log  (H3, Engbert 2011 PNAS 108:E765)
Writes  : book/figures/eye_4_drift.svg
Chapter : 1 (The Eye), claim 2 -- the eye moves, and the motion is load-bearing.

The gate was CONJUNCTIVE and pre-registered: alpha_short > 1 AND alpha_long < 1
AND alpha_short > alpha_long AND anisotropy < 0.25. The published values are
drawn as bands so the reader can see the claim is a crossover, not a fit -- and
the ablated arm is drawn because removing the self-avoiding term removes the
crossover, which is what makes the drift a mechanism rather than a decoration.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eye_confirm
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "eye_4_drift.svg")

# From the log's own header -- the published reference values it was gated on.
PUBLISHED = (("Engbert model", 1.32, 0.02, 0.71, 0.06),
             ("Engbert experiment", 1.38, 0.05, 0.79, 0.11))


def main():
    d = eye_confirm.load()
    saw, abl = d["alpha"]["SAW"], d["alpha"]["ABLATED"]

    W, H = 760, 560
    f = sp.Fig(W, H)
    f.title(46, 34, "Fixational drift: a crossover, not a fit",
            "H3 · self-avoiding walk · scaling exponent α at short and long lag")

    ax = sp.Axes(f, 210, 92, 440, 196, xlim=(0.6, 1.5), ylim=(0, 1))
    ax.frame(left=False)
    ax.xticks([0.7, 0.9, 1.1, 1.3, 1.5], fmt=lambda v: f"{v:.1f}",
              label="scaling exponent α")

    x1 = ax.px(1.0)
    f.line(x1, ax.y0 - 8, x1, ax.y0 + ax.h, sp.INK, 1.2, dash="4 3")
    f.text(x1, ax.y0 - 14, "α = 1", cls="note", anchor="middle")

    # published reference bands, drawn behind everything
    for name, s_m, s_sd, l_m, l_sd, in PUBLISHED:
        for m, sd in ((s_m, s_sd), (l_m, l_sd)):
            f.rect(ax.px(m - sd), ax.y0, ax.px(m + sd) - ax.px(m - sd), ax.h,
                   fill=sp.MUTED, opacity=0.10, rx=1)
    f.text(ax.px(0.75), ax.y0 + 10, "published, long lag", cls="note",
           anchor="middle", fill=sp.MUTED)
    f.text(ax.px(1.35), ax.y0 + 10, "published, short lag", cls="note",
           anchor="middle", fill=sp.MUTED)

    rows = (("short lag", "alpha_short"), ("long lag", "alpha_long"))
    arms = (("this eye — full walk", saw, sp.ARM_A),
            ("ablated — no self-avoidance", abl, sp.NULLC))
    y = ax.y0 + 30
    for lab, key in rows:
        f.text(204, y + 4, lab, cls="lbl", anchor="end")
        for i, (albl, arm, col) in enumerate(arms):
            st = arm[key]
            yy = y + i * 26
            ax.interval_h(yy, st["ci"][0], st["ci"][1], st["mean"], colour=col,
                          r=4.4, capsize=4.5)
            f.text(ax.px(st["ci"][1]) + 10, yy + 4,
                   f"{st['mean']:.4f}  [{st['ci'][0]:.4f}, {st['ci'][1]:.4f}]",
                   cls="val" if i == 0 else "note",
                   fill=None if i == 0 else sp.MUTED)
        y += 84

    for i, (albl, arm, col) in enumerate(arms):
        f.circle(214 + i * 230, 336, 4.4, fill=col)
        f.text(224 + i * 230, 340, albl, cls="note")

    f.text(46, 372, "What the ablation shows", cls="lbl")
    for i, ln in enumerate((
            "Remove the self-avoiding term and the short lag barely moves "
            "(1.1553 → 1.1944) while the long lag",
            "crosses back over one (0.7590 → 1.1301). The walk stops "
            "anti-correlating at long lag — it becomes",
            "ordinary diffusion. So the crossover is carried by that term "
            "specifically, and the drift is doing",
            "work rather than decorating the retina.")):
        f.text(46, 392 + i * 15, ln, cls="note")

    f.text(46, 464, "The retraction behind this figure", cls="lbl")
    f.text(46, 482,
           "This drift reproduced the published signature to two decimals "
           "while driving NOTHING — its only", cls="note")
    f.text(46, 496,
           "consumer was the ruler that measured it — until it was wired into "
           "the image. Kept in the record.", cls="note")

    f.caption(46, 530, [
        "Source: results/eye_confirm.log (H3) · generator: "
        "book/figures/fig_eye_drift.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
