#!/usr/bin/env python3
"""Figure EMO-2 -- Harlow: contact preference from equal drive weights.

Reads   : results/harlow_d1.json   (N=200 infants per condition, block 233000)
Writes  : book/figures/emotion_2_harlow.svg
Chapter : 10 (Emotion, and what it is for)

The point is not that the preference appears. It is WHY: the drive weights are
EQUAL (1/1). Contact wins because contact is needed continuously and alone
buffers the threat channel -- it is not a weight thumb on the scale. The
ablation arm is the control that says so.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "results", "harlow_d1.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "emotion_2_harlow.svg")


def main():
    d = json.load(open(SRC))
    n = d["n"]
    A, B = d["condition_A_contact_drive"], d["condition_B_ablated"]

    W, H = 760, 436
    f = sp.Fig(W, H)
    f.title(46, 34, "Harlow, on equal drive weights",
            f"N = {n} infants per condition · 95% intervals · "
            f"pre-registered before any number")

    ax = sp.Axes(f, 210, 84, 420, 108, xlim=(0, 1), ylim=(0, 1))
    ax.frame(left=False)
    ax.xticks([0, 0.25, 0.5, 0.75, 1.0],
              fmt=lambda v: f"{v * 100:.0f}%",
              label="time at the contact mother")

    f.line(ax.px(0.5), ax.y0, ax.px(0.5), ax.y0 + ax.h, sp.MUTED, 0.9,
           dash="3 4")
    f.text(ax.px(0.5), ax.y0 - 6, "indifference", cls="note", anchor="middle")

    for i, (lab, cond, col) in enumerate((
            ("contact drive present", A, sp.ARM_A),
            ("contact drive ablated", B, sp.NULLC))):
        cf = cond["cloth_frac"]
        yy = ax.y0 + 34 + i * 44
        ax.interval_h(yy, cf["ci_lo"], cf["ci_hi"], cf["mean"], colour=col, r=5)
        f.text(204, yy + 4, lab, cls="lbl", anchor="end")
        txt = (f"{cf['mean'] * 100:.1f}%  [{cf['ci_lo'] * 100:.1f}, "
               f"{cf['ci_hi'] * 100:.1f}]")
        if cf["mean"] < 0.12:      # hard against the left edge: label right
            f.text(ax.px(cf["ci_hi"]) + 12, yy + 4, txt, cls="val")
        else:
            f.text(ax.px(cf["mean"]), yy - 14, txt, cls="val", anchor="middle")

    f.text(46, 252, "Why it is not a weight thumb", cls="lbl")
    for i, ln in enumerate((
            "Both drives carry weight 1. The infant rides the real drive "
            "system (contact_comfort, hunger,",
            "distress), the real regulator, and the real appraisal Argmax — "
            "nothing in this experiment was",
            "built for it. Contact wins for a structural reason: it is needed "
            "continuously, and it alone",
            "buffers the threat channel.")):
        f.text(46, 272 + i * 15, ln, cls="note")

    f.text(46, 344, "The control", cls="lbl")
    f.text(46, 364,
           f"Ablate the contact drive and the preference does not shrink — it "
           f"goes to {B['cloth_frac']['mean'] * 100:.0f}%, interval width zero.",
           cls="note")
    f.text(46, 379,
           "The behaviour was carried by that drive and nothing else was "
           "quietly supplying it.", cls="note")

    f.caption(46, 406, [
        "Source: results/harlow_d1.json · prereg HARLOW_D1_PREREG.md, "
        "committed before measurement",
        "Generator: book/figures/fig_harlow_preference.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
