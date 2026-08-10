"""THE JABBERWOCK RE-DECIDES at a real inflection — its RELIABLE lever (density) just came up NULL. Last lever, or pivot?

Five honest negatives now; crucially the MOST-RELIABLE lever (density) failed too, so the deep-OOV-read top-1 ceiling
is demonstrably SATURATED. This is a strategic inflection, not another data point. The agent re-decides with the new
information: pursue the LAST within-read lever (rare-word topic-prior, same prior family that just failed for frequent
words, needs a big-corpus build), or PIVOT off the OOV-read entirely, or LAND. Justify by EV, predict, pre-commit a bar.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_redecide_after_density
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock at a real inflection. Re-decide the next move with NEW information: your MOST-
RELIABLE lever just failed.

WHAT CHANGED: you took density (A) -- "density helps" was your most-repeated positive. Realigned on the FULL 498k vs
the 60k sample. On 110 clips it looked like 13->16 (cleared the bar), but the robustness check on ALL 222 clips WASHED
IT OUT: realigned-60k 17.1%, realigned-498k 14.9% (z=-0.65, NOT significant; if anything worse). 60k already
saturates. That is the 5th honest negative -- and the one lever you most expected to work.

THE EXHAUSTED SPACE (every within-OOV-read top-1 lever tried, all null on this ~15+/-3 @100-way ceiling):
 - emission precision x3 (marginal-forward sum, soft-min cost-space, all failed floors)
 - iterated/damped realignment (overfits)
 - Mahalanobis whitening (deletes signal)
 - topic-prior over FREQUENT targets (un-topical by construction, gate aborted)
 - DENSITY / more data (just now, null)
The top-1 ceiling on the deep OOV read is SATURATED at this scale. This is a robust empirical finding, not a failure.

THE CONFIRMED STACK (stands, robust, often kill-controlled): held-vocab solved; triphone RECALL ~30 top-3 @100-way;
realignment top-1 ~13-17; source/context-PRIOR (shuffle-killed); BPL phone-marginal OOV read 18%; prosodic prior +
pyramid representation (content 7.7->~20%); the LOOP closed graph-natively (understand-drive residual folds at the
clock edge; mechanism built, NOT yet wired to real speech params).

THE OPTIONS NOW:
 (G) LAST within-read lever: rare-word topic-prior on a BIG corpus. Your topic gate aborted for FREQUENT words but
     the gradient leaned to rare (26% vs 9%); it needs a rare candidate set + big-corpus topic model + a properly-
     calibrated gate (the first gate over-smoothed). EV: it's the SAME prior-over-the-read family that just failed
     twice, and a real build before you even know the gate passes.
 (H) PIVOT — wire the now-built self-tuning LOOP onto a REAL speech param (cadence / fusion-weight / prior-weight) so
     it SELF-TUNES via the closed loop instead of a one-time fit. The loop mechanism is DONE on a synthetic operator;
     this is the un-taken "return to speech" step. EV: composes a confirmed mechanism with confirmed params; not a
     ceiling-grind.
 (I) PIVOT harder — a different axis entirely (autonomous ear/speech growth loop; a new world/world-curiosity). EV:
     escapes the saturated read; bigger scope, less certain.
 (J) LAND — declare the OOV-read top-1 ceiling a real finding, consolidate the record, stop.

Bias check: you've spent 5 moves grinding ONE number (OOV-read top-1) into a saturated ceiling. Is the high-EV move
still a 6th lever on that number, or to STOP grinding it and either close the loop on real params (H) or land (J)?"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK RE-DECIDES AFTER THE DENSITY NULL")
    print("=" * 100)
    q1 = (GROUND + "\n\nDECIDE (terse): name the move (G/H/I/J or your own), justify by a SPECIFIC result in the "
          "ledger, predict the outcome, name the smallest confirming test. Face the bias check head-on: if you pick "
          "(G) another lever on the saturated number, say why its EV beats stopping the grind; if you pivot or land, "
          "say why that beats the last lever.")
    a1 = ask(q1)
    print("\n[THE MOVE]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour move:\n{a1[:1400]}\n\nPRE-COMMIT THE BAR (one line each): the KEEP criterion; the STOP "
          "criterion; and the fairness/harness check that proves the test measured the thing not an artifact. Terse.")
    a2 = ask(q2)
    print("\n[PRE-COMMITTED BAR]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
