#!/usr/bin/env python3
"""Figure EYE-8 -- why Oja cannot see it: the eigenspectrum, rendered.

Reads   : results/waveiso_confirm.json
Writes  : book/figures/eye_8_eigenspectrum.svg
Chapter : 1 (The Eye), claim 5 -- the cortex is a diagnosed dead end.

Oja converges to the leading eigenvector of E[xx^T]. This figure shows what
that eigenvector IS for the wave ensemble: a DC blob (DC alignment 0.98,
orientation index 0.09), with the next two eigenvalues near-degenerate
(l2/l3 ~ 1.09) so that removing DC leaves a coin flip between two directions.

That is arithmetic, not a tuning failure. It is the whole reason a five-rung
line was retired rather than re-tuned -- and it is the strongest kind of
negative result: one that says exactly which mechanism cannot work, and why.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "results", "waveiso_confirm.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "eye_8_eigenspectrum.svg")


def main():
    d = json.load(open(SRC))
    S = d["summary"]
    waves = d["waves"]
    arms = {c["arm"]: c for c in d["controls"]}
    n = len(waves)

    # mean spectrum across seeds, as recorded per seed
    k = len(waves[0]["M_eigenvalues"])
    wave_eig = [sum(w["M_eigenvalues"][i] for w in waves) / n for i in range(k)]
    disk_eig = arms["CONTROL_disks_ISO_FLOOR"]["M_eigenvalues"][:k]
    bars_eig = arms["CONTROL_bars_random_theta_DISCRIMINATOR"][
        "M_eigenvalues"][:k]

    W, H = 780, 546
    f = sp.Fig(W, H)
    f.title(46, 34, "Why Oja cannot learn orientation here",
            f"Eigenspectrum of E[xxᵀ] · n = {n} seeds · the rule converges to "
            f"the leading eigenvector")

    top = max(wave_eig + disk_eig + bars_eig)
    ax = sp.Axes(f, 96, 92, 330, 170, xlim=(0.4, k + 0.6), ylim=(0, top * 1.08))
    ax.frame()
    ax.xticks(list(range(1, k + 1)), fmt=lambda v: f"{int(v)}",
              label="eigenvalue index")
    ax.yticks(sp.nice_ticks(0, top, 4), fmt=lambda v: f"{v:g}",
              label="eigenvalue", grid=True)

    for eig, col, w in ((disk_eig, sp.NULLC, 1.2), (bars_eig, sp.ARM_B, 1.2),
                        (wave_eig, sp.ARM_A, 1.8)):
        pts = " ".join(f"{'M' if i == 0 else 'L'} {ax.px(i + 1):.2f} "
                       f"{ax.py(v):.2f}" for i, v in enumerate(eig))
        f.path(pts, stroke=col, width=w)
        for i, v in enumerate(eig):
            f.circle(ax.px(i + 1), ax.py(v), 2.6, fill=col)

    # the near-degenerate pair
    x2, x3 = ax.px(2), ax.px(3)
    f.rect(x2 - 7, ax.y0 + 4, (x3 - x2) + 14, ax.h - 8, fill=sp.ACCENT,
           opacity=0.10, rx=2)
    f.text((x2 + x3) / 2, ax.y0 - 4, "λ₂ ≈ λ₃", cls="note", anchor="middle",
           fill=sp.ACCENT)

    for i, (lab, col) in enumerate((("waves", sp.ARM_A),
                                    ("disks (isotropic)", sp.NULLC),
                                    ("bars, random θ (discriminator)", sp.ARM_B))):
        f.circle(102, 288 + i * 16, 3.4, fill=col)
        f.text(112, 292 + i * 16, lab, cls="note")

    # --- what the leading eigenvector is ---------------------------------
    f.text(470, 96, "What the leading eigenvector IS", cls="lbl")
    ax2 = sp.Axes(f, 560, 112, 170, 76, xlim=(0, 1.05), ylim=(0, 1))
    ax2.frame(left=False)
    ax2.xticks([0, 0.5, 1.0], fmt=lambda v: f"{v:g}")
    for i, (lab, s, col) in enumerate((
            ("DC alignment", S["M_leading_DC"], sp.ARM_B),
            ("orientation index", S["M_leading_OI"], sp.ARM_A))):
        yy = ax2.y0 + 22 + i * 30
        ax2.interval_h(yy, s["ci_lo"], s["ci_hi"], s["mean"], colour=col,
                       r=4.2, capsize=4)
        f.text(554, yy + 4, lab, cls="note", anchor="end")
        f.text(ax2.px(s["mean"]), yy - 12, f"{s['mean']:.3f}", cls="val",
               anchor="middle")
    f.text(470, 218,
           "It is a blob: aligned with DC almost", cls="note")
    f.text(470, 232,
           "perfectly, carrying almost no", cls="note")
    f.text(470, 246,
           "orientation at all.", cls="note")

    f.text(470, 278, "And under it, a tie", cls="lbl")
    f.text(470, 296,
           f"λ₂/λ₃ = {S['M_l2_over_l3']['mean']:.4f} "
           f"[{S['M_l2_over_l3']['ci_lo']:.4f}, "
           f"{S['M_l2_over_l3']['ci_hi']:.4f}]", cls="val")
    f.text(470, 312,
           "Remove DC and what remains is a", cls="note")
    f.text(470, 326,
           "near-degenerate pair — so preferred", cls="note")
    f.text(470, 340,
           "orientation is a coin flip.", cls="note")

    f.text(46, 372, "This is arithmetic, not a tuning failure", cls="lbl")
    for i, ln in enumerate((
            "Oja fits second-order statistics. The orientation in these waves "
            "is local and sign-varying, and it is",
            "not in the second-order statistics — so no learning rate rescues "
            "it, and the missing cortical layer",
            "was BUILT to check whether the published mechanism would, and it "
            "did not. Five pre-registered rungs",
            "were then retired rather than re-tuned.")):
        f.text(46, 392 + i * 15, ln, cls="note")

    f.text(46, 464, "What the null redirected the work TO", cls="lbl")
    f.text(46, 482,
           "The 3D world was never in a still image — it is in the relations "
           "between frames, and those the", cls="note")
    f.text(46, 496,
           "substrate CAN discover (EYE-5). Biology agrees: the motion path is "
           "early and central.", cls="note")

    f.caption(46, 526, [
        "Source: results/waveiso_confirm.json (M_eigenvalues, per seed) · "
        "generator: book/figures/fig_eye_eigenspectrum.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
