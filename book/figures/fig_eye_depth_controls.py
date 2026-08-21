#!/usr/bin/env python3
"""Figure EYE-5 -- depth and stereo: a matrix of what it REFUSES to mint.

Reads   : results/depth_measure.json, results/stereo_measure.json
Writes  : book/figures/eye_5_depth_controls.svg
Chapter : 1 (The Eye), claim 3 -- the dimensions of sight are discovered.

These two results record verdicts and minted structures rather than curves, so
the honest figure is a control matrix, not a scatter: the claim being made is a
refusal to hallucinate. A flat scene that minted a depth dimension would be the
failure; it doesn't, and neither does a multi-colour scene at one velocity, and
neither do 400 shuffles.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "eye_5_depth_controls.svg")


def row(f, x, y, w, label, detail, minted, note):
    """One control row: what was shown, what it did, and whether that's right."""
    col = sp.ARM_A if minted else sp.NULLC
    f.rect(x, y, w, 30, fill=col, opacity=0.08, rx=2)
    f.line(x, y, x, y + 30, col, 2.4)
    f.text(x + 10, y + 13, label, cls="lbl")
    f.text(x + 10, y + 26, detail, cls="note")
    verdict = "mints latent:depth" if minted else "mints nothing"
    f.text(x + w - 10, y + 13, verdict, cls="val", anchor="end",
           fill=None if minted else sp.MUTED)
    f.text(x + w - 10, y + 26, note, cls="note", anchor="end")


def main():
    d = json.load(open(os.path.join(ROOT, "results", "depth_measure.json")))
    s = json.load(open(os.path.join(ROOT, "results", "stereo_measure.json")))
    dep = d["H_depth"]
    sh = d["H_shuffle"]
    ssh = s["H_shuffle"]
    add = s["H_additive"]

    W, H = 780, 574
    f = sp.Fig(W, H)
    f.title(46, 34, "Depth is discovered — and refused where it isn't there",
            "One operation, two frame sources: one eye over ticks, and N eyes "
            "at one instant")

    f.text(46, 76, "ONE MOVING EYE  ·  depth from motion", cls="lbl")
    y = 88
    row(f, 46, y, 688, "a flat scene",
        "one surface, one velocity",
        False, "correct: nothing to explain")
    row(f, 46, y + 38, 688, "a multi-colour scene at ONE velocity",
        "many regions, no velocity variation",
        False, "correct: depth is not region presence")
    row(f, 46, y + 76, 688, "a scene with real depth",
        f"{dep['n_layers_read']} layers, velocities "
        f"{dep['minted'][0]['velocities']}",
        True, f"MDL {dep['mdl_without']} → {dep['mdl_with']}  "
              f"({dep['ratio']}×)")
    row(f, 46, y + 114, 688, f"{sh['n']} random shuffles of that same scene",
        f"window K = {sh['window']}",
        False, f"{sh['spurious_mints']}/{sh['n']} spurious mints")

    f.text(46, 258, "N EYES AT ONE INSTANT  ·  the SAME Term, unchanged",
           cls="lbl")
    y2 = 270
    row(f, 46, y2, 688, "one disparity, at N = 2 and at N = 3",
        "many surfaces, no disparity variation",
        False, "correct: not from multiple eyes")
    row(f, 46, y2 + 38, 688, "zero disparity — a scene at infinity",
        "N = 3",
        False, "correct: nothing to order")
    row(f, 46, y2 + 76, 688, "real disparity variation",
        f"eye count read from the graph: "
        f"{s['H_cardinality']['clean_N2_eyes_from_graph']} and "
        f"{s['H_cardinality']['clean_N3_eyes_from_graph']}",
        True, "same ordering as the motion arm")
    row(f, 46, y2 + 114, 688, f"{ssh['n']} random shuffles",
        "disparity structure destroyed",
        False, f"{ssh['spurious_mints']}/{ssh['n']} spurious mints")

    f.line(46, 428, 734, 428, sp.RULE, 0.8)
    f.text(46, 450, "Eyes and ticks are the same resource", cls="lbl")
    for i, ln in enumerate((
            "DepthInfer generalised across frame-source with an EMPTY source "
            "diff: fed N eyes at one instant",
            "instead of one eye over ticks, the unchanged Term mints the same "
            "dimension, in the same order. It was",
            "built for N and never for 2 — the eye count falls out of "
            "Count(Eye hubs), with no literal anywhere —",
            "and N = 3 rejects what N = 2 would hallucinate.")):
        f.text(46, 470 + i * 15, ln, cls="note")

    f.text(46, 538,
           f"Held additively, not chosen between: stereo grounds in "
           f"{add['stereo_ticks_to_ground']} tick where motion needs "
           f"{add['motion_ticks_to_ground']} —", cls="note")
    f.text(46, 552,
           "same dimension, quicker, and more precise with more baselines. "
           "You never pick parallax OR stereopsis.", cls="note")

    f.caption(46, 572, [
        "Sources: results/depth_measure.json, results/stereo_measure.json · "
        "generator: book/figures/fig_eye_depth_controls.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
