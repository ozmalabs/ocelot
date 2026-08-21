#!/usr/bin/env python3
"""Figure EYE-7 -- retinal waves: globally isotropic, locally oriented.

Reads   : results/waveiso_confirm.json  (seeds 20000-20015, n=16)
Writes  : book/figures/eye_7_waves.svg
Chapter : 1 (The Eye), claims 1 and 5.

Three rungs shared a premise -- "the waves carry no orientation" -- and this
measurement splits it. Globally the ensemble IS isotropic. Locally every front
is oriented. The structure is there; the learning rule cannot see it (EYE-8).
Both halves are true and the second is not caused by the first.

Every statistic is drawn against its own floor and ceiling arms, measured in
the same run: disks (isotropic floor) and fixed bars (oriented ideal).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "results", "waveiso_confirm.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "eye_7_waves.svg")


def stat_row(f, ax, y, label, s, note):
    """One statistic: the waves' interval, with the floor and ideal arms."""
    f.text(ax.x0 - 14, y + 4, label, cls="lbl", anchor="end")
    f.circle(ax.px(s["floor_disks"]), y, 4.6, fill="none", stroke=sp.NULLC,
             sw=1.6)
    f.circle(ax.px(s["ideal_bars"]), y, 4.6, fill="none", stroke=sp.ARM_B,
             sw=1.6)
    ax.interval_h(y, s["ci_lo"], s["ci_hi"], s["mean"], colour=sp.ARM_A,
                  r=4.4, capsize=4.5)
    f.text(ax.x0 - 14, y + 18, note, cls="note", anchor="end")


def main():
    d = json.load(open(SRC))
    S = d["summary"]
    n = len(d["waves"])

    W, H = 780, 530
    f = sp.Fig(W, H)
    f.title(46, 34, "The waves are isotropic — and locally oriented",
            f"n = {n} seeds · every statistic against its own floor and ideal, "
            f"measured in the same run")

    ax = sp.Axes(f, 250, 92, 420, 150, xlim=(-0.04, 1.06), ylim=(0, 1))
    ax.frame(left=False)
    ax.xticks([0, 0.25, 0.5, 0.75, 1.0], fmt=lambda v: f"{v:g}",
              label="0 = isotropic / incoherent      1 = fully oriented")

    stat_row(f, ax, ax.y0 + 30, "global orientation", S["A2_global"],
             "over the whole ensemble")
    stat_row(f, ax, ax.y0 + 86, "local coherence", S["coh_local_RF"],
             "within one receptive field")

    f.text(ax.px(S["A2_global"]["mean"]), ax.y0 + 16,
           f"{S['A2_global']['mean']:.3f}", cls="val", anchor="middle")
    f.text(ax.px(S["coh_local_RF"]["mean"]), ax.y0 + 72,
           f"{S['coh_local_RF']['mean']:.3f}", cls="val", anchor="middle")

    for i, (lab, col, filled) in enumerate((
            ("waves (this eye)", sp.ARM_A, True),
            ("disks — isotropic floor", sp.NULLC, False),
            ("bars — oriented ideal", sp.ARM_B, False))):
        x = 250 + i * 150
        if filled:
            f.circle(x, 306, 4.4, fill=col)
        else:
            f.circle(x, 306, 4.4, fill="none", stroke=col, sw=1.6)
        f.text(x + 10, 310, lab, cls="note")

    f.text(46, 344, "Reading the two rows together", cls="lbl")
    for i, ln in enumerate((
            "Globally, the ensemble sits almost on the isotropic floor: no "
            "orientation is preferred across the",
            "whole field, and that half of the shared premise is CONFIRMED — "
            "measured, for the first time.",
            "Locally, coherence sits far above the disks floor and most of the "
            "way to the bars ideal: the waves",
            "are travelling FRONTS, and a front is oriented where it passes. "
            "That half of the premise is REFUTED.")):
        f.text(46, 364 + i * 15, ln, cls="note")

    f.text(46, 446, "Why this matters two figures later", cls="lbl")
    f.text(46, 464,
           "The inference three rungs had drawn — no orientation in the input, "
           "therefore none can be learned —", cls="note")
    f.text(46, 478,
           "does not follow. The structure is present. The next figure shows "
           "what cannot see it, and why.", cls="note")

    f.caption(46, 506, [
        "Source: results/waveiso_confirm.json · runners "
        "scripts/waveiso_{lib,calibrate,pilot,confirm}.py · generator: "
        "fig_eye_waves.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
