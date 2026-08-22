#!/usr/bin/env python3
"""Figure CC-1 -- fifteen rungs, each with a control that could have failed.

Source  : docs/research/bigville/ABUSIVE_RELATIONSHIPS_LINE_SUMMARY.md, which
          copies every number from an already-gated rung's own results doc.
Writes  : book/figures/cc_1_rungs.svg
Chapter : 12 (Coercive control)

The figure is the line's structure rather than any one result: four scoping
lines, fifteen rungs, every one with a named control, and the two that did not
fully pass shown as what they are. Clinical, anti-sensational register --
no scenario, no narrative, mechanism names only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "cc_1_rungs.svg")

LINES = [
    ("DYAD", [
        ("R1", "traumatic bond", "intermittent > affection > harm", "PASS"),
        ("R2", "cycle limit", "self-sustaining vs exact fixed point", "PASS"),
        ("R3", "coercive control", "window to floor vs holds", "PASS"),
        ("R4", "control not learned", "non-contingent vs contingent", "PASS"),
        ("R5", "recovery", "3 of 4 metrics; 1 null, explained", "PARTIAL"),
        ("R6", "dependent cost", "attempt rate 0 with prior uninformative",
         "PASS"),
        ("R7", "return cycle", "2x2: both drivers > either > neither", "PASS"),
    ]),
    ("NETWORK", [
        ("N1", "credibility asymmetry", "gap widens; insider reverses", "PASS"),
        ("N2", "isolation", "2x2 super-additive on intact edges", "PASS"),
        ("N3", "belief propagation", "corruption with zero observation",
         "PASS"),
        ("N4", "one believing agent", "4 of 4; zero new rules", "PASS"),
    ]),
    ("INTENT", [
        ("U0", "intent, positive control", "scored r=0.76; blind 100% degen.",
         "PASS"),
        ("U1", "context-dependent affect", "gated 378 vs always-observed 149",
         "PASS"),
        ("U2", "sincere self-account", "minimised vs zero-discount, sign-flip",
         "PASS"),
    ]),
    ("VISIBILITY", [
        ("V1", "evidentiary visibility", "gap narrows, CI-sep; does NOT flip",
         "PASS*"),
    ]),
]


def main():
    W, H = 780, 672
    f = sp.Fig(W, H)
    f.title(46, 34, "Fifteen rungs, four scoping lines, one ethics protocol",
            "Every rung pre-registered with a failable control; every rung "
            "ethics-gated before it ran")

    y = 74
    for name, rungs in LINES:
        f.text(46, y, name, cls="lbl", fill=sp.MUTED)
        y += 14
        for tag, mech, result, verdict in rungs:
            col = (sp.ARM_A if verdict == "PASS"
                   else sp.ARM_B if verdict == "PARTIAL" else sp.ACCENT)
            f.rect(46, y - 9, 688, 15, fill=col, opacity=0.06, rx=2)
            f.line(46, y - 9, 46, y + 6, col, 2.2)
            f.text(56, y + 2, tag, cls="val")
            f.text(82, y + 2, mech, cls="note", fill=sp.INK)
            f.text(250, y + 2, result, cls="note")
            f.text(734, y + 2, verdict, cls="note", anchor="end",
                   fill=None if verdict == "PASS" else col)
            y += 19
        y += 6

    f.line(46, y + 2, 734, y + 2, sp.RULE, 0.8)
    y += 24
    f.text(46, y, "What the shape of this table is for", cls="lbl")
    for i, ln in enumerate((
            "Two entries are not clean passes, and both are reported as what "
            "they are. R5 clears three of four",
            "recovery metrics; the fourth is a null with overlapping intervals, "
            "mechanistically explained and",
            "pre-registered as the likely outcome BEFORE the confirmatory run. "
            "V1 is interval-separated and does",
            "NOT flip sign — the abuser stays net-favoured even with the "
            "incident channel visible.",
            "",
            "The falsification bar across all fifteen: no rung may invent a "
            "bespoke mechanism. The line closes with",
            "zero new engine primitives and zero new decision logic — every "
            "dynamic here is what ordinary,",
            "independently-motivated components do when connected in a "
            "particular way.")):
        f.text(46, y + 20 + i * 15, ln, cls="note")

    f.caption(46, y + 148, [
        "Numbers in the chapter text, copied from each rung's own gated "
        "results document. Ethics protocol quoted in full at §12.1.",
        "Source: ABUSIVE_RELATIONSHIPS_LINE_SUMMARY.md (bigville, external "
        "repository) · generator: book/figures/fig_abuse_rungs.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
