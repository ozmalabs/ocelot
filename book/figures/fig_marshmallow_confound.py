#!/usr/bin/env python3
"""Figure EMO-1 -- the marshmallow confound, exhibited in both directions.

Reads   : results/marshmallow_delay/results.json  (N=60 per cohort, block 240000)
Writes  : book/figures/emotion_1_marshmallow_confound.svg
Chapter : 10 (Emotion, and what it is for)

The headline is not "the agent waits". It is that the substrate SEPARATES
temperament from the reliability-prior -- the causally clean dissolution the
human experiment cannot run -- and can therefore show the confound running
both ways. Numbers are read from the results file, never recomputed.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "results", "marshmallow_delay", "results.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "emotion_1_marshmallow_confound.svg")
MAXW = 26.0


def panel(f, x, y, w, title, sub, rows, reading, colour):
    """Label gutter | bar track | value, so nothing can collide."""
    f.text(x, y, title, cls="lbl")
    f.text(x, y + 15, sub, cls="note")
    gut, valw = 118, 30
    bx, bw = x + gut, w - gut - valw
    for i, (lab, val) in enumerate(rows):
        yy = y + 32 + i * 24
        f.text(x + gut - 8, yy + 12, lab, cls="note", anchor="end")
        f.rect(bx, yy, bw, 15, fill=sp.RULE, opacity=0.25, rx=1.5)
        f.rect(bx, yy, bw * (val / MAXW), 15, fill=colour, opacity=0.55)
        f.text(x + w, yy + 12, f"{val:g}", cls="val", anchor="end")
    base = y + 32 + 24 * len(rows)
    for i, ln in enumerate(reading):
        f.text(x, base + 16 + i * 14, ln, cls="note")
    return base + 16 + 14 * len(reading)


def main():
    d = json.load(open(SRC))
    n = d["n_per_cohort"]
    c = d["g_confound"]
    a = c["same_temperament_different_prior"]
    b = c["different_temperament_compensating_prior"]

    W, H = 780, 512
    f = sp.Fig(W, H)
    f.title(46, 34, "The marshmallow confound, exhibited in both directions",
            f"N = {n} per cohort · bootstrap 95% intervals · "
            f"pre-registered analytic grid")

    panel(f, 46, 76,
          300,
          "Same temperament, three reliability-priors",
          f"temperament held at {a['temperament']} · prior varies",
          [(f"prior {p}", w) for p, w in zip(a["priors"], a["wait_times"])],
          ["A naive marshmallow score reads these as three",
           "DIFFERENT levels of self-control. The temperament",
           "is identical. Only the world changed."],
          sp.ARM_A)

    panel(f, 424, 76,
          300,
          "Temperament differs 4×, priors compensate",
          "temperament and prior both vary",
          [(f"temp {t} · prior {p}", w)
           for t, p, w in zip(b["temperaments"], b["priors"], b["wait_times"])],
          ["All three wait EXACTLY the same. A naive score",
           "reads them as IDENTICAL children. Their",
           "temperaments differ by a factor of four."],
          sp.ARM_B)

    diss = d["g_dissolution"]
    f.line(46, 268, 734, 268, sp.RULE, 0.8)
    f.text(46, 290, "Both main effects are present and interval-separated",
           cls="lbl")

    ax = sp.Axes(f, 236, 302, 400, 62, xlim=(0, MAXW), ylim=(0, 1))
    ax.frame(left=False)
    ax.xticks([0, 5, 10, 15, 20, 25], label="wait time (ticks)")
    pt, pp = diss["pure_temperament"], diss["pure_prior"]
    for i, (lab, mean, ci, col) in enumerate((
            ("temperament: low weight", pt["low_weight_mean"],
             pt["low_weight_ci"], sp.ARM_A),
            ("temperament: high weight", pt["high_weight_mean"],
             pt["high_weight_ci"], sp.ARM_A),
            ("prior: low", pp["low_prior_mean"], pp["low_prior_ci"], sp.ARM_B),
            ("prior: high", pp["high_prior_mean"], pp["high_prior_ci"],
             sp.ARM_B))):
        yy = 310 + i * 14
        ax.interval_h(yy, ci[0], ci[1], mean, colour=col, r=3.4, capsize=3.5)
        f.text(230, yy + 4, lab, cls="note", anchor="end")

    f.caption(46, 424, [
        "Each arm holds one cause FIXED and varies the other — the "
        "dissolution the human experiment cannot run, because in",
        "children temperament and learned reliability arrive together. Both "
        "null controls behaved: hold the varying cause",
        "constant and the intervals overlap, as pre-registered.",
        "This is a CAPABILITY demonstration — that the substrate can "
        "separate the two causes over one value economy — and",
        "NOT an empirical claim about real children.",
        "Source: results/marshmallow_delay/results.json · generator: "
        "book/figures/fig_marshmallow_confound.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
