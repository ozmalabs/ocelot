#!/usr/bin/env python3
"""Figure EYE-6 -- centre-surround, emerged from a zero init.

Reads   : results/rung7_confirm.log
Writes  : book/figures/eye_6_centre_surround.svg
Chapter : 1 (The Eye), claim 1.

Pre-registered, Bonferroni-corrected across five tests, eight seeds, eta frozen
in advance. The lateral gains start at ZERO: nothing centre-surround-shaped was
put in. What comes out reproduces two published readings the retina was never
given -- Miller's spatial-dependence prediction and Atick & Redlich's
SNR-dependent predictive coding.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "results", "rung7_confirm.log")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "eye_6_centre_surround.svg")


def parse(path=SRC):
    t = open(path).read()
    g = {}
    g["cs"] = [float(x) for x in re.search(
        r"CS per seed: \[([^\]]+)\]", t).group(1).split()]
    g["cs_mean"] = float(re.search(r"CS mean ([\d.]+)", t).group(1))
    g["cs_range"] = [float(x) for x in re.search(
        r"range \[([\d.]+), ([\d.]+)\]", t).groups()]
    g["cs_pct"] = float(re.search(r"([\d.]+)% of range", t).group(1))
    m = re.search(r"sigma_ON,ON\s+([\d.]+)\s+sigma_ON,OFF ([\d.]+)\s+ratio "
                  r"([\d.]+)\n\s+diff ([\d.]+)\s+95% CI \[([\d.]+), ([\d.]+)\]",
                  t)
    g["sig"] = dict(zip(("on_on", "on_off", "ratio", "diff", "lo", "hi"),
                        (float(x) for x in m.groups())))
    m = re.search(r"max \|SD_ref\| across (\d+) seeds = ([\de.+-]+)\s+=> (\w+)",
                  t)
    g["instrument"] = {"n": int(m.group(1)), "max": float(m.group(2)),
                       "verdict": m.group(3)}
    m = re.search(r"p=0 ([\d.]+) -> p=0.20 ([\d.]+)\s+diff (-[\d.]+)", t)
    g["h3a"] = dict(zip(("p0", "p20", "diff"), (float(x) for x in m.groups())))
    m = re.search(r"p=0 ([\d.]+) -> p=0.20 ([\d.]+)\s+diff \+([\d.]+)", t)
    g["h3b"] = dict(zip(("p0", "p20", "diff"), (float(x) for x in m.groups())))
    return g


def main():
    g = parse()
    n = len(g["cs"])

    W, H = 780, 560
    f = sp.Fig(W, H)
    f.title(46, 34, "Centre-surround, emerged from a zero init",
            f"Rung 7 · {n} seeds · η frozen in advance · Bonferroni across "
            f"five tests")

    # --- CS per seed, on the 0 (pure centre) .. 1 (balanced DoG) scale ----
    f.text(46, 78, "The gains start at zero. This is what comes out.",
           cls="lbl")
    ax = sp.Axes(f, 190, 92, 480, 74, xlim=(0, 1.25), ylim=(0, 1))
    ax.frame(left=False)
    ax.xticks([0, 0.25, 0.5, 0.75, 1.0, 1.25], fmt=lambda v: f"{v:g}",
              label="centre-surround index")
    for v, lab, col in ((0.0, "pure centre\n(analytic floor)", sp.MUTED),
                        (1.0, "balanced DoG", sp.ACCENT)):
        x = ax.px(v)
        f.line(x, ax.y0, x, ax.y0 + ax.h, col, 1.2, dash="4 3")
    f.text(ax.px(0.0) + 6, ax.y0 + 14, "pure centre (analytic floor)",
           cls="note", anchor="start", fill=sp.MUTED)
    f.text(ax.px(1.0), ax.y0 - 6, "balanced DoG", cls="note", anchor="middle",
           fill=sp.ACCENT)
    for v in g["cs"]:
        f.circle(ax.px(v), ax.y0 + 40, 4.2, fill=sp.ARM_A, opacity=0.75)
    f.text(184, ax.y0 + 44, f"{n} seeds", cls="note", anchor="end")
    f.text(ax.px(g["cs_mean"]), ax.y0 + 24,
           f"{g['cs_mean']:.4f}   ({g['cs_pct']:.1f}% of the range)",
           cls="val", anchor="middle")

    # --- Miller: different spatial dependence -----------------------------
    f.text(46, 214, "Miller's reading: the two spatial dependences differ",
           cls="lbl")
    ax2 = sp.Axes(f, 190, 228, 480, 62, xlim=(0, 4.0), ylim=(0, 1))
    ax2.frame(left=False)
    ax2.xticks([0, 1, 2, 3, 4], label="σ (spatial extent)")
    for i, (lab, key, col) in enumerate((("σ ON,ON", "on_on", sp.ARM_A),
                                         ("σ ON,OFF", "on_off", sp.ARM_B))):
        yy = ax2.y0 + 16 + i * 22
        f.circle(ax2.px(g["sig"][key]), yy, 4.4, fill=col)
        f.text(184, yy + 4, lab, cls="note", anchor="end")
        f.text(ax2.px(g["sig"][key]) + 10, yy + 4, f"{g['sig'][key]:.3f}",
               cls="val")
    f.text(560, ax2.y0 + 16,
           f"ratio {g['sig']['ratio']:.3f} · difference "
           f"{g['sig']['diff']:.3f}", cls="note")
    f.text(560, ax2.y0 + 30,
           f"[{g['sig']['lo']:.3f}, {g['sig']['hi']:.3f}]", cls="note")

    # --- Atick & Redlich --------------------------------------------------
    f.text(46, 340, "Atick & Redlich: the same movie at two signal levels",
           cls="lbl")
    f.text(46, 358,
           f"As noise rises, total gain WEAKENS "
           f"({g['h3a']['p0']:.4f} → {g['h3a']['p20']:.4f}, "
           f"Δ {g['h3a']['diff']:.4f}) and the surround", cls="note")
    f.text(46, 372,
           f"BROADENS — the far-ring share rises "
           f"({g['h3b']['p0']:.4f} → {g['h3b']['p20']:.4f}, "
           f"Δ +{g['h3b']['diff']:.4f}). Both directions were", cls="note")
    f.text(46, 386,
           "predicted by the theory before the run, and neither is a "
           "parameter of this retina.", cls="note")

    # --- the instrument check --------------------------------------------
    f.text(46, 424, "The instrument was checked before the result was believed",
           cls="lbl")
    f.text(46, 442,
           f"An analytic control split that MUST score zero scores "
           f"{g['instrument']['max']:.2e} across "
           f"{g['instrument']['n']} seeds → "
           f"{g['instrument']['verdict']}.", cls="note")
    f.text(46, 456,
           "This tree's standing hazard is the inert instrument — a measure "
           "that passes noise, a reader that", cls="note")
    f.text(46, 470,
           "always says yes. The floor is measured, not assumed.", cls="note")

    f.caption(46, 504, [
        "A later rung qualifies what this retina could go on to SUPPORT — its "
        "input alphabet is binarised downstream",
        "(VISION_FAILURE_MODES_RESULTS.md) — which is why this figure reports "
        "only what emerged here.",
        "Source: results/rung7_confirm.log · runner scripts/rung7_confirm.py "
        "· generator: fig_eye_centre_surround.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
