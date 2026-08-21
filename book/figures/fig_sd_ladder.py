#!/usr/bin/env python3
"""Figure SD-1 -- the growth ladder, Occam-ordered.

Conceptual (no data behind it): the four rungs of the sd loop, in the order
they are tried, with what each one costs in description length and what it
adds to the codebook. Drawn once here; chapters 1, 4, 5, 7 and 8 all refer to
it, which is the whole reason it earns a page.

Source of truth: runners/dsl/src/shape_decode.rs and
seeds/shape_decode_loop.json (sd_recognize / sd_transform_decode /
sd_infer_dimension / sd_mint_quantum), plus CLAUDE.md's dated arc entries.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "sd_1_ladder.svg")

RUNGS = [
    ("1", "recognise", "the observation is already in the codebook",
     "nothing is added", "sd_recognize"),
    ("2", "transform in the basis",
     "ONE uniform step along a dimension it already has",
     "a Transform{dim, delta}", "sd_transform_decode"),
    ("3", "infer a dimension",
     "the residual is coupled across dims it can see —\n"
     "explicable only by one it does not yet have",
     "a LatentDimension", "sd_infer_dimension"),
    ("4", "mint novelty", "nothing shorter than a new quantum fits",
     "a CapabilityAxis quantum", "sd_mint_quantum"),
]


def main():
    W, H = 780, 496
    f = sp.Fig(W, H)
    f.title(46, 34, "The growth ladder, in the order it is tried",
            "Each rung is attempted only when the one above it fails — "
            "cheapest explanation first")

    x0, w = 46, 688
    y = 74
    for i, (num, name, when, adds, rule) in enumerate(RUNGS):
        h = 62 if "\n" in when else 50
        col = sp.ARM_A if i < 3 else sp.ARM_B
        f.rect(x0, y, w, h, fill=col, opacity=0.07, rx=3)
        f.line(x0, y, x0, y + h, col, 2.6)
        f.circle(x0 + 26, y + 20, 11, fill="none", stroke=col, sw=1.6)
        f.text(x0 + 26, y + 24, num, cls="val", anchor="middle")
        f.text(x0 + 50, y + 18, name, cls="lbl")
        for j, ln in enumerate(when.split("\n")):
            f.text(x0 + 50, y + 34 + j * 14, ln, cls="note")
        f.text(x0 + w - 12, y + 18, adds, cls="val", anchor="end",
               fill=None if i else sp.MUTED)
        f.text(x0 + w - 12, y + 34, rule, cls="note", anchor="end")
        if i < len(RUNGS) - 1:
            f.line(x0 + 26, y + h + 2, x0 + 26, y + h + 10, sp.MUTED, 1.2)
            f.text(x0 + 40, y + h + 11, "residual survives — try the next rung",
                   cls="note", fill=sp.MUTED)
        y += h + 16

    f.line(46, 356, 734, 356, sp.RULE, 0.8)
    f.text(46, 378, "Why the ORDER is the design", cls="lbl")
    for i, ln in enumerate((
            "A loop that minted first would explain everything and learn "
            "nothing — every variation would become",
            "a new entry, and the codebook would grow without ever "
            "compressing. Minting last makes novelty the",
            "residual of three cheaper readings, so what gets added is what "
            "genuinely did not fit. Measured: a",
            "rotated tromino mints ZERO (rung 2 reads it), a scrambled one "
            "mints EXACTLY ONE.")):
        f.text(46, 398 + i * 15, ln, cls="note")

    f.caption(46, 478, [
        "Conceptual figure — no data behind it. Mechanism: "
        "runners/dsl/src/shape_decode.rs, seeds/shape_decode_loop.json · "
        "generator: fig_sd_ladder.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
