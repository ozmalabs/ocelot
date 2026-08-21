#!/usr/bin/env python3
"""Figure EYE-1 — Troxler fading: a stabilised image fades while 100% alive.

Reads   : results/troxler_confirm.json   (8 seeds, vis_steps=3200)
Writes  : book/figures/eye_1_troxler.svg
Chapter : 1 (The Eye), claim 4 -- failure modes are the real tell.

The figure reads the results file and plots it. It does not recompute any
statistic: the sign test, the mean difference and its interval are taken as
recorded. If this plot ever disagrees with the results document, this script
is wrong.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "results", "troxler_confirm.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_1_troxler.svg")


def main():
    d = json.load(open(SRC))
    rows = d["rows"]
    n = len(rows)

    W, H = 760, 512
    f = sp.Fig(W, H)
    f.title(46, 34, "Troxler fading, replicated",
            f"Stabilised vs drifting retinal image · {n} seeds · "
            f"{d['vis_steps']} steps")

    # --- left panel: paired final contrast, drifting vs stabilised --------
    ax = sp.Axes(f, 92, 84, 250, 246, xlim=(0, 1), ylim=(0, 0.19))
    ax.frame()
    ax.yticks(sp.nice_ticks(0, 0.19, 4), fmt=lambda v: f"{v:.2f}",
              label="final contrast", grid=True)
    xd, xs = ax.px(0.28), ax.px(0.72)
    f.text(xd, 84 + 246 + 17, "drifting", cls="tick", anchor="middle")
    f.text(xs, 84 + 246 + 17, "stabilised", cls="tick", anchor="middle")

    t0 = rows[0]["drift_contrast_t0"]
    f.line(ax.x0, ax.py(t0), ax.x0 + ax.w, ax.py(t0), sp.MUTED, 0.9, dash="3 4")
    f.text(ax.x0 + ax.w - 2, ax.py(t0) - 6, "contrast at t\u2080", cls="note",
           anchor="end")

    for r in rows:
        yd, ys = ax.py(r["drift_contrast_final"]), ax.py(r["stab_contrast_final"])
        f.line(xd + 8, yd, xs - 8, ys, sp.RULE, 0.9)
        f.circle(xd, yd, 4.5, fill=sp.ARM_A, opacity=0.85)
        f.circle(xs, ys, 4.5, fill=sp.ARM_B, opacity=0.85)
    f.text(xs, ax.py(0.0) - 14, "\u2192 0", cls="val", anchor="middle",
           fill=sp.ARM_B)

    # --- right, top: the difference with its interval ---------------------
    lo, hi = d["ci"]
    f.text(452, 84, "The difference, with its interval", cls="lbl")
    ax2 = sp.Axes(f, 452, 92, 250, 46, xlim=(0, 0.16), ylim=(0, 1))
    ax2.frame(left=False)
    ax2.xticks(sp.nice_ticks(0, 0.16, 4), fmt=lambda v: f"{v:.2f}",
               label="drifting \u2212 stabilised (contrast)")
    ax2.interval_h(ax2.y0 + 22, lo, hi, d["diff_mean"], colour=sp.ARM_A, r=5)
    f.text(452, ax2.y0 + 12,
           f"{d['diff_mean']:.4f}  [{lo:.4f}, {hi:.4f}]  \u00b7  sign test "
           f"{d['sign_k']}/{d['sign_n']}, p = {d['p']:.4f}", cls="val")

    # --- right, middle: WHERE it fades to (the mechanism) ------------------
    f.text(452, 196, "What it fades to \u2014 its own setpoint", cls="lbl")
    mu = sum(r["mu_endo"] for r in rows) / n
    resp = sum(r["stab_mean_resp_final"] for r in rows) / n
    ax3 = sp.Axes(f, 452, 206, 250, 34, xlim=(0.10, 0.19), ylim=(0, 1))
    ax3.frame(left=False)
    ax3.xticks([0.10, 0.13, 0.16, 0.19], fmt=lambda v: f"{v:.2f}",
               label="mean response of the stabilised sheet")
    f.circle(ax3.px(mu), ax3.y0 + 17, 6.5, fill="none", stroke=sp.ACCENT, sw=1.8)
    f.circle(ax3.px(resp), ax3.y0 + 17, 3.2, fill=sp.ARM_B)
    f.text(ax3.px(mu), ax3.y0 + 6, f"\u03bc_endo = {mu:.5f}", cls="note",
           anchor="middle", fill=sp.ACCENT)
    f.text(452, ax3.y0 + 94, "the two coincide \u2014 every cell sits at the",
           cls="note")
    f.text(452, ax3.y0 + 108, "setpoint it derived from itself, so the sheet",
           cls="note")
    f.text(452, ax3.y0 + 122, "is uniform, and uniform has no contrast.",
           cls="note")

    # --- right, bottom: the control that makes it a fade, not a death -----
    alive_stab = min(r["stab_alive_min"] for r in rows)
    alive_drift = min(r["drift_alive_min"] for r in rows)
    f.text(452, 350, "The control: it is not dead", cls="lbl")
    for i, (lab, v, c) in enumerate((
            ("stabilised", alive_stab, sp.ARM_B),
            ("drifting", alive_drift, sp.ARM_A))):
        y = 360 + i * 24
        f.rect(452, y, 250 * v, 15, fill=c, opacity=0.25)
        f.rect(452, y, 250 * v, 15, fill="none", stroke=c)
        f.text(456, y + 11.5, f"{lab} \u2014 {v * 100:.1f}% of cells alive",
               cls="note", fill=sp.INK)

    f.caption(46, 424, [
        "Two timescales, derived independently and never tuned to each other: "
        "τ_drift = 3 (the self-avoiding walk)",
        "and τ_adapt = 160 (from μ_endo) — a factor of 53 apart. The fade here "
        "is retinal; the biological locus is",
        "multi-level (retinal-transient, retinal-sustained, cortical "
        "filling-in), so the eye is an instrument for",
        "weighting those contributions, not a claim that one of them wins.",
        f"Source: results/troxler_confirm.json · verdict recorded True · "
        f"generator: book/figures/{os.path.basename(__file__)}",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
