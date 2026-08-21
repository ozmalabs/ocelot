#!/usr/bin/env python3
"""Figure SR-1 -- shape and rule: two axes, not two candidates.

Conceptual. Chapter 3's central claim in one picture: Rule is how a substrate
ACTS on what it holds; Shape is how it decides something is new and ADDS it.
They are orthogonal, and a substrate with only one of them has a specific,
nameable failure.

Source of truth: CLAUDE.md, "SHAPE IS ACQUISITION, RULE IS EXECUTION";
docs/research/engine_substrate/RULES_AS_SHAPE_DESIGN_SPIKE.md.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "shape_1_two_axes.svg")


def main():
    W, H = 780, 520
    f = sp.Fig(W, H)
    f.title(46, 34, "Shape and Rule are two axes, not two candidates",
            "Rule is how a substrate runs. Shape is how it grows.")

    x0, y0, w, h = 190, 76, 420, 220
    f.rect(x0, y0, w, h, fill=sp.RULE, opacity=0.05, rx=3)
    f.line(x0, y0 + h, x0 + w, y0 + h, sp.RULE, 1.2)
    f.line(x0, y0, x0, y0 + h, sp.RULE, 1.2)
    f.text(x0 + w / 2, y0 + h + 22, "RULE  —  execution", cls="lbl",
           anchor="middle")
    f.text(x0 + w / 2, y0 + h + 37,
           "match, where, effects · the run_rules fixpoint", cls="note",
           anchor="middle")
    f.text(x0 - 22, y0 + h / 2, "SHAPE  —  acquisition", cls="lbl",
           anchor="middle", rotate=-90)
    f.text(x0 - 8, y0 + h / 2, "decode, residual, mint", cls="note",
           anchor="middle", rotate=-90)

    quads = (
        (0, 0, "neither", "inert", sp.NULLC,
         ["holds nothing, does nothing"]),
        (1, 0, "rule without shape", "executes, cannot grow itself", sp.ARM_B,
         ["can only be extended by a human", "deciding, by hand, that this",
          "case deserves a new rule"]),
        (0, 1, "shape without rule", "learns, cannot act", sp.ARM_B,
         ["a codebook nobody consults"]),
        (1, 1, "both", "grows its own execution layer", sp.ARM_A,
         ["a residual mints an entry;", "the next decode covers more;",
          "the loop is the growth"]),
    )
    for cx, cy, name, gloss, col, lines in quads:
        px = x0 + cx * (w / 2)
        py = y0 + (1 - cy) * (h / 2)
        f.rect(px + 6, py + 6, w / 2 - 12, h / 2 - 12, fill=col,
               opacity=0.10 if col != sp.NULLC else 0.05, rx=3)
        f.text(px + 18, py + 28, name, cls="lbl")
        f.text(px + 18, py + 44, gloss, cls="val", fill=col)
        for i, ln in enumerate(lines):
            f.text(px + 18, py + 64 + i * 14, ln, cls="note")

    f.line(46, 356, 734, 356, sp.RULE, 0.8)
    f.text(46, 378, "The sharp version of the claim", cls="lbl")
    for i, ln in enumerate((
            "A substrate whose own execution layer has no shape cannot expand "
            "its own execution layer. That is",
            "narrower and more testable than 'rules should be tidier' — and "
            "it was measured: this agent selected",
            "which of its own rules to modify by counting substring matches "
            "against the rule's NAME, with the",
            "rule's body opaque to that selection. Structural and name-keyword "
            "selection differ on both sides of a",
            "hand-verified oracle (11/12 vs 0/12, and 12/12 vs 0/12, N = 40). "
            "Neither subsumes the other.")):
        f.text(46, 398 + i * 15, ln, cls="note")

    f.caption(46, 496, [
        "Conceptual figure — the measured slice behind it is "
        "RULE_SIGNATURE_SLICE_RESULTS.md. Generator: fig_shape_and_rule.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
