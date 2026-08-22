#!/usr/bin/env python3
"""Figure SPACE-1 -- understanding converges, and surprise alone would not show it.

Source  : docs/research/ls20/LS20_UNDERSTANDING_RESULTS.md (block 221000),
          powered run, 25 episodes x 200 levels, sigma in {0, 8, 16}.
Writes  : book/figures/space_1_convergence.svg
Chapter : 7 (Space as a belief)

Two panels because one would mislead. Clean: model accuracy RAMPS as stations
are modelled, surprise STEPS to zero once all of them are. Broken (sigma=16):
accuracy is flat at zero and surprise STILL self-converges -- the agent
confidently re-predicts its own wrong recognition. A surprise-only gate passes
that. The accuracy gate is what has teeth.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "space_1_convergence.svg")

# transcribed from the results table, cycles 0..11
SURPRISE = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
ACCURACY = [0.17, 0.33, 0.50, 0.67, 0.83, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]


def panel(f, x, y, w, h, title, sub, surprise, accuracy, note):
    f.text(x, y - 14, title, cls="lbl")
    f.text(x, y - 2, sub, cls="note")
    ax = sp.Axes(f, x, y + 10, w, h, xlim=(-0.4, 11.4), ylim=(-0.06, 1.08))
    ax.frame()
    ax.xticks([0, 2, 4, 6, 8, 10], fmt=lambda v: f"{int(v)}", label="cycle")
    ax.yticks([0, 0.5, 1.0], fmt=lambda v: f"{v:g}", grid=True)

    for series, col, r in ((accuracy, sp.ARM_A, 3.4), (surprise, sp.ARM_B, 3.4)):
        d = " ".join(f"{'M' if i == 0 else 'L'} {ax.px(i):.2f} {ax.py(v):.2f}"
                     for i, v in enumerate(series))
        f.path(d, stroke=col, width=1.6)
        for i, v in enumerate(series):
            f.circle(ax.px(i), ax.py(v), r, fill=col)
    for i, ln in enumerate(note):
        f.text(x, y + h + 64 + i * 14, ln, cls="note")
    return ax


def main():
    W, H = 780, 522
    f = sp.Fig(W, H)
    f.title(46, 34, "Understanding converges — and surprise alone would miss it",
            "25 episodes × 200 levels · six stations · zero variance across "
            "episodes")

    ax1 = panel(f, 96, 96, 260, 130,
                "Clean perception (σ = 0)",
                "the model is learned by curiosity and predict-residual",
                SURPRISE, ACCURACY,
                ["Accuracy RAMPS: one more station modelled",
                 "each cycle. Surprise STEPS: it stays at 1.0",
                 "until every station is modelled, then goes to",
                 "0 and stays. Different shapes, one cause."])

    panel(f, 452, 96, 260, 130,
          "Broken perception (σ = 16)",
          "the same machinery, with the input degraded",
          SURPRISE, [0.0] * 12,
          ["Accuracy is flat at zero — nothing was",
           "learned. And surprise converges ANYWAY:",
           "the agent confidently re-predicts its own",
           "wrong recognition."])

    for i, (lab, col) in enumerate((("model accuracy, against ground truth",
                                     sp.ARM_A),
                                    ("surprise (predict − observe residual)",
                                     sp.ARM_B))):
        f.circle(100 + i * 300, 352, 3.6, fill=col)
        f.text(110 + i * 300, 356, lab, cls="note")

    f.line(46, 376, 734, 376, sp.RULE, 0.8)
    f.text(46, 398, "Why the second panel is the result", cls="lbl")
    for i, ln in enumerate((
            "A system that stops being surprised has not thereby learned "
            "anything. Under heavy noise this one",
            "converges on its own mistake and reports no surprise at all — so a "
            "surprise-only gate would pass a",
            "run in which perception had failed completely. The accuracy gate "
            "catches it, and that is what makes",
            "the clean panel evidence rather than a curve: the instrument can "
            "fail, and it was shown failing.")):
        f.text(46, 418 + i * 15, ln, cls="note")

    f.caption(46, 494, [
        "Confirmed hypotheses 6.000 [6.000, 6.000]; frac_model_complete 1.000 "
        "[0.867, 1.000]; median complete-cycle 5.",
        "Source: docs/research/ls20/LS20_UNDERSTANDING_RESULTS.md (block "
        "221000) · generator: book/figures/fig_space_convergence.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
