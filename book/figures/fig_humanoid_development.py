#!/usr/bin/env python3
"""Figure BODY-1 -- where the humanoid actually is on its own curriculum.

Source  : results/humanoid_child_somatomotor_waves_cold_v8.json (latest run in
          the record), and docs/research/humanoid/humanoid_developmental_curriculum.md
Writes  : book/figures/body_1_development.svg
Chapter : 9 (One core, six bodies)

The point of this figure is that it can report standing still. A stage number
would say "60% of the way to walking". This says which capability, in which
ecology, with which prerequisites unmet -- which is the difference between a
progress bar and a measurement.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "results",
                   "humanoid_child_somatomotor_waves_cold_v8.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "body_1_development.svg")

STAGES = [
    (1, "spontaneous variation, effector consequences,\ncontact, reversible action"),
    (2, "side lying, rolling, prone support,\nreaching, sitting"),
    (3, "transitions, belly mobility, quadruped\nsupport, crawling"),
    (4, "kneeling, pull to stand, cruising,\nstanding, stepping, WALKING"),
    (5, "running, jumping, stairs, hopping"),
]


def main():
    d = json.load(open(SRC))
    reached = int(d["active_stage_ordinal"])
    caps = len(d["demonstrated_capabilities"])
    analogues = len(d["demonstrated_human_analogues"])
    milestones = len(d["demonstrated_clinical_milestones"])

    W, H = 780, 546
    f = sp.Fig(W, H)
    f.title(46, 34, "Where it actually is on its own curriculum",
            f"Latest run in the record · active stage ordinal {reached} · "
            f"ecology: {d['active_developmental_ecology']}")

    y = 84
    for n, label in STAGES:
        done = n < reached
        here = n == reached
        col = sp.ARM_A if done else (sp.ARM_B if here else sp.NULLC)
        rows = label.count("\n") + 1
        h = 16 + rows * 13
        f.rect(46, y, 470, h, fill=col, opacity=0.14 if (done or here) else 0.05,
               rx=3)
        f.line(46, y, 46, y + h, col, 2.6)
        f.circle(66, y + 15, 9, fill="none", stroke=col, sw=1.6)
        f.text(66, y + 19, str(n), cls="val", anchor="middle")
        for i, ln in enumerate(label.split("\n")):
            f.text(86, y + 14 + i * 13, ln, cls="note", fill=sp.INK)
        if here:
            f.text(506, y + 14, "← here", cls="val", anchor="end", fill=sp.ARM_B)
        y += h + 7

    f.text(524, 96, "Demonstrated", cls="lbl")
    for i, (lab, v) in enumerate((("capabilities", caps),
                                  ("human analogues", analogues),
                                  ("clinical milestones", milestones))):
        col = sp.NULLC if v == 0 else sp.ARM_A
        f.text(524, 116 + i * 18, f"{v}", cls="val", fill=col)
        f.text(544, 116 + i * 18, lab, cls="note")
    f.text(524, 180, "active capability", cls="note", fill=sp.MUTED)
    f.text(524, 194, d["active_capability"].replace("_", " "), cls="note",
           fill=sp.INK)
    f.text(524, 212, "human analogue", cls="note", fill=sp.MUTED)
    f.text(524, 226, d["active_human_analogue"].replace("_", " "), cls="note",
           fill=sp.INK)

    f.line(46, 336, 734, 336, sp.RULE, 0.8)
    f.text(46, 358, "It is not walking, and the figure is built to say so",
           cls="lbl")
    for i, ln in enumerate((
            "Walking sits in stage 4, behind rolling, sitting, quadruped "
            "support and pulling to stand — and the",
            "ordering is a dependency graph rather than an age clock, so "
            "crawling is an optional route rather than",
            "a gate. Nothing is 60% of the way anywhere.",
            "",
            "Every capability requires all four: causally bound verified "
            "receipts; repeated success over a",
            "body-derived evidence window; more distinct situated contexts than "
            "its prerequisites; and a successful",
            "DELAYED RETENTION probe. Clinical milestones are reported "
            "separately from precursor capabilities, so",
            "partial progress cannot be laundered into an achievement — which "
            "is why the third count reads zero.")):
        f.text(46, 378 + i * 15, ln, cls="note")

    f.caption(46, 502, [
        "Source: results/humanoid_child_somatomotor_waves_cold_v8.json · "
        "curriculum: docs/research/humanoid/humanoid_developmental_curriculum.md",
        "Generator: book/figures/fig_humanoid_development.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
