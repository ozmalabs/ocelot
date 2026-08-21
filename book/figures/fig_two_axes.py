#!/usr/bin/env python3
"""Figure FR-2 -- two orthogonal unbounded directions.

Conceptual. Chapter 2 states it and the epilogue collects on it: the graph is
unbounded in two directions at once, for the same reason (unknowability) and
with different cardinalities. You cannot reach the second by extending the
first, which is why the continuum needs a separate axis rather than more steps.

Source of truth: CLAUDE.md, "BASE-AS-DIMENSION + the frame/continuum
invariant" (two orthogonal unbounded axes).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "frame_2_two_axes.svg")


def main():
    W, H = 780, 500
    f = sp.Fig(W, H)
    f.title(46, 34, "Two unbounded directions, and you cannot get from one "
                    "to the other",
            "Both are unbounded for the same reason. Only one of them can "
            "reach a continuum.")

    ox, oy = 150, 268
    # --- extensive axis: the frontier, countable --------------------------
    f.line(ox, oy, 640, oy, sp.INK, 1.4)
    for i in range(9):
        x = ox + i * 52
        f.circle(x, oy, 4.0 if i < 7 else 3.0, fill=sp.ARM_A,
                 opacity=1.0 if i < 7 else 0.35)
    f.text(648, oy + 4, "…", cls="lbl", fill=sp.MUTED)
    f.text(ox, oy + 26, "EXTENSIVE — the frontier", cls="lbl")
    f.text(ox, oy + 42, "one more step outward · unknown = absence, "
                        "first-class", cls="note")
    f.text(ox, oy + 57, "countable (ℕ)", cls="val", fill=sp.ARM_A)

    # --- intensive axis: refinement, between two steps --------------------
    f.line(ox, oy, ox, 88, sp.INK, 1.4)
    lo, hi = 96, oy - 8
    depth, y = 0, oy
    span = oy - lo
    for d in range(6):
        y = oy - span * (1 - 0.5 ** (d + 1))
        f.line(ox - 7, y, ox + 7, y, sp.ARM_B, 1.4)
        if d < 2:
            f.text(ox - 14, y + 4, f"depth {d + 1}", cls="note", anchor="end",
                   fill=sp.MUTED)
    f.text(ox - 14, lo + 6, "⋮", cls="lbl", anchor="end", fill=sp.MUTED)
    f.text(ox + 18, 100, "INTENSIVE — refinement", cls="lbl")
    f.text(ox + 18, 116, "always another step BETWEEN two you have",
           cls="note")
    f.text(ox + 18, 131, "its unreachable limit is the continuum (𝔠)",
           cls="val", fill=sp.ARM_B)

    # the impossibility, drawn where a reader would try it
    f.path(f"M 400 {oy - 14} C 400 200, 300 170, {ox + 16} 150",
           stroke=sp.NULLC, width=1.4, dash="5 4")
    f.circle(333, 189, 9, fill="none", stroke=sp.NULLC, sw=1.5)
    f.line(327, 183, 339, 195, sp.NULLC, 1.5)
    f.line(339, 183, 327, 195, sp.NULLC, 1.5)
    f.text(350, 186, "no amount of stepping outward arrives here",
           cls="note", fill=sp.MUTED)
    f.text(350, 201, "a countable union of countable steps stays countable",
           cls="note", fill=sp.MUTED)

    f.line(46, 358, 734, 358, sp.RULE, 0.8)
    f.text(46, 380, "Why both are unbounded, and why it is the same reason",
           cls="lbl")
    for i, ln in enumerate((
            "Neither is stored complete. What is held is the finite observed "
            "part, plus the fact that it does not",
            "end — which is a representable fact, not a gap in the "
            "representation. Unknowability is the shared",
            "cause; cardinality is what separates them. This is also the "
            "epilogue's argument in miniature: a",
            "substrate with two unbounded axes has no completion condition, so "
            "any ending is a chosen cut.")):
        f.text(46, 400 + i * 15, ln, cls="note")

    f.caption(46, 476, [
        "Conceptual figure — no data behind it. Source: CLAUDE.md "
        "§ BASE-AS-DIMENSION. Generator: book/figures/fig_two_axes.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
