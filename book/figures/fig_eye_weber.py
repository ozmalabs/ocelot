#!/usr/bin/env python3
"""Figure EYE-3 -- Weber-Fechner: the slope nobody chose.

Reads   : results/eye_confirm.log  (H2)
Writes  : book/figures/eye_3_weber.svg
Chapter : 1 (The Eye), claim 1.

Prediction stated IN ADVANCE: slope = 1.000 +/- 0.05 over four decades.
Measured: 0.9991. The per-decade steps are the same fact told a second way --
each decade of intensity adds a constant amount of drive, and that constant is
ln 10. Nothing was fitted to hit it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eye_confirm
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "eye_3_weber.svg")
LN10 = 2.302585


def main():
    d = eye_confirm.load()
    log = d["slope"]["LOG"]
    lin = d["slope"]["LINEAR"]
    drives = log["drives"]
    steps = log["steps"]
    # intensities are the linear arm's own drive values: 1e2 .. 1e6
    inten = lin["drives"]
    lnI = [math.log(v) for v in inten]

    W, H = 760, 500
    f = sp.Fig(W, H)
    f.title(46, 34, "Weber–Fechner, predicted in advance and then measured",
            "H2 · drive against ln(intensity) over four decades above i₀")

    ax = sp.Axes(f, 96, 82, 300, 190,
                 xlim=(min(lnI) - 0.8, max(lnI) + 0.8),
                 ylim=(min(drives) - 1.2, max(drives) + 1.2))
    ax.frame()
    ax.xticks([math.log(v) for v in inten],
              fmt=lambda v: f"1e{round(v / math.log(10)):d}",
              label="intensity (log scale)")
    ax.yticks(sp.nice_ticks(min(drives), max(drives), 4),
              fmt=lambda v: f"{v:.0f}", label="drive", grid=True)

    f.path(f"M {ax.px(lnI[0]):.2f} {ax.py(drives[0]):.2f} "
           f"L {ax.px(lnI[-1]):.2f} {ax.py(drives[-1]):.2f}",
           stroke=sp.ARM_A, width=1.4)
    for x, y in zip(lnI, drives):
        f.circle(ax.px(x), ax.py(y), 4.2, fill=sp.ARM_A)
    f.text(ax.px(lnI[1]) + 8, ax.py(drives[3]),
           f"slope = {log['slope']:.4f}", cls="val", fill=sp.ARM_A)
    f.text(ax.px(lnI[1]) + 8, ax.py(drives[3]) + 15,
           "predicted 1.000 ± 0.05,", cls="note")
    f.text(ax.px(lnI[1]) + 8, ax.py(drives[3]) + 29,
           "stated before the run", cls="note")

    # right: the per-decade steps against ln 10
    f.text(452, 96, "The same fact, told a second way", cls="lbl")
    f.text(452, 112, "each decade of intensity adds a constant drive",
           cls="note")
    ax2 = sp.Axes(f, 452, 146, 250, 92, xlim=(2.28, 2.315), ylim=(0, 1))
    ax2.frame(left=False)
    ax2.xticks([2.29, 2.30, 2.31], fmt=lambda v: f"{v:.2f}",
               label="drive added per decade")
    xl = ax2.px(LN10)
    f.line(xl, ax2.y0 - 6, xl, ax2.y0 + ax2.h, sp.ACCENT, 1.3, dash="4 3")
    f.text(xl, ax2.y0 - 12, "ln 10", cls="note", anchor="middle",
           fill=sp.ACCENT)
    for i, s in enumerate(steps):
        yy = ax2.y0 + 16 + i * 18
        f.circle(ax2.px(s), yy, 3.6, fill=sp.ARM_A, opacity=0.9)
        f.text(448, yy + 4, f"decade {i + 1}", cls="note", anchor="end")

    f.text(46, 322, "What this is evidence OF", cls="lbl")
    for i, ln_ in enumerate((
            "Three categories of constant, and only the first is evidence: one "
            "that FELL OUT of a natural process;",
            "one PUT IN as a constant, which fails on distribution shift; and "
            "one put in AS ARCHITECTURE — a",
            "signature exactly one rule is solely responsible for, which is "
            "silently unfalsifiable and the worst",
            "of the three. This slope is the first kind. The receptor was "
            "given a logarithm because Weber's law",
            "is one; the slope of 0.9991 is what that choice already implied, "
            "measured afterwards.")):
        f.text(46, 342 + i * 15, ln_, cls="note")

    f.text(46, 432, "The contrast arm", cls="lbl")
    f.text(46, 450,
           f"The linear receptor's slope on the same axes is "
           f"{lin['slope']:,.0f} — it does not encode a ratio at all.",
           cls="note")

    f.caption(46, 476, [
        "Source: results/eye_confirm.log (H2) · generator: "
        "book/figures/fig_eye_weber.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
