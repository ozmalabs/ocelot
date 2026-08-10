"""THE JABBERWOCK RULES ON ITS WHITEN+REALIGN PRE-COMMITMENT — does STOP stand, or was the test under-powered/mis-estimated?

It chose (b) whiten-by-within-word-nuisance + realigned read; pre-committed KEEP iff shifted top-1>=15 AND the shift
penalty narrows; STOP otherwise; fairness floor W=I==13 (held EXACT). The result is STOP -- but with a diagnosis that
could be a harness flaw rather than the idea. The agent must rule, with the explicit motivated-reasoning check (this is
the THIRD negative-with-a-harness-story in a row: marginal-forward volume-bias, then lattice-topology, now this).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_rules_on_whiten
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, ruling on your OWN pre-commitment. Be disciplined: a stopping rule presumes a FAIR,
well-POWERED test; but "the test was under-powered / the estimator was mis-specified" is ALSO the exact rationalisation
a stopping rule guards against -- and this is your THIRD negative-with-a-harness-story in a row (marginal-forward
volume-bias -> lattice-topology -> now this). Weigh that honestly.

YOUR MOVE: (b) whiten features by within-word nuisance covariance S_n, then run the REALIGNED-triphone read. Pre-
committed: KEEP iff shifted top-1>=15 AND shift-penalty(whiten) < shift-penalty(plain); STOP otherwise; fairness floor:
W=I must reproduce the plain realigned 13 (it did, EXACT by construction).

THE RESULT (100-way, 110 held-out clips, squared-Mahalanobis DTW; shift = per-clip smooth spectral coloration):
  PLAIN realigned (W=I):     matched 13/30   shifted 12/27   shift-penalty +1
  WHITEN alpha=0.5 shrink.1: matched 10/25   shifted  8/26   shift-penalty +2   (HURT even matched)
  WHITEN alpha=1.0 shrink.1: matched  1/12   shifted  2/12                       (collapsed)
=> STOP by the letter: shifted 8 < 15, and whitening WIDENED the penalty AND hurt the matched read.

THE DIAGNOSIS (could be harness flaw, could be the idea is just wrong HERE):
 1. Whitening HURT the MATCHED read (13->10->1), with NO shift at all. That is the damning fact: it removes
    DISCRIMINATIVE information, not just nuisance.
 2. WHY (likely): my S_n pooled UNALIGNED within-word frames, so it is dominated by PHONETIC-TRAJECTORY variance --
    which is the WORD SIGNAL for a sequence read, NOT speaker nuisance. Whitening flattened the very directions that
    distinguish words. The confirmed whitened-matched-filter estimated nuisance from POSITION-ALIGNED cross-speaker
    variation (same word, same position, different speakers) -- a different, signal-free S_n.
 3. The shift was WEAK: L2-normalised cochleagram + cosine already absorbs smooth coloration, so plain penalty was
    only +1 -> almost nothing for whitening to "eat" -> under-powered to show the benefit even if real.
 4. CONTEXT: the confirmed whitening win was a DIFFERENT task + metric (speaker-ID SC separation, +0.015 MODEST on
    accuracy; "accuracy moves less than separation"). It may simply not transfer to this word-read ACCURACY.

RULE NOW (terse, decisive):
 (1) Does STOP stand -- i.e. is this a fair-enough verdict that whitening does not help THIS read, given it hurt even
     the matched case? OR
 (2) Was it under-powered + mis-estimated (S_n=signal, weak shift) -> ONE corrected run warranted? If so, name the
     SINGLE corrected estimator (position-aligned cross-speaker S_n, signal-free) AND a shift strong enough to create
     a real penalty, and RE-STATE the pass/fail numbers.
 (3) The honesty check, one line: given fact #1 (whitening hurt the MATCHED read with no shift) and that this is your
     third harness-story negative, is "re-test with aligned S_n" a genuine fix or motivated reasoning? Decide."""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK RULES ON ITS WHITEN+REALIGN PRE-COMMITMENT")
    print("=" * 100)
    a = ask(GROUND + "\n\nRule: (1) STOP-stands or (2) one corrected run (name the single estimator fix + shift + "
            "pass/fail numbers); then (3) the one-line honesty check against motivated reasoning.")
    print("\n[RULING]\n" + (a or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
