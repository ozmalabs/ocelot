"""THE JABBERWOCK RULES ON ITS OWN PRE-COMMITMENT — was the ABANDON triggered by a FAIR test, or a confounded one?

It chose (B) marginal-forward, predicted ~17-18, pre-committed: ABANDON if top-1 <=11 AND top-3 flat/down. Result:
committed read (1 medoid + hard DTW) top-1 13 / top-3 30; marginal forward top-1 9 / top-3 20 (beta 8) and 7 / 20
(beta 14). That lands in ABANDON. BUT a confound: the forward and the committed read use the SAME realigned units, and
the committed read KEEPS 30% top-3 while the forward DROPPED it to 20% -- a SUM over more hypotheses ranked WORSE than
a hard min on identical information, which is the signature of an UNNORMALISED-VOLUME bias (the forward log-sum favours
candidates whose exemplar pool gives more high-emission states / more alignment paths, regardless of correctness), not
of "the truth can't be pinned." The agent must rule: does its pre-committed ABANDON stand, or was this an unfair test
of its hypothesis that warrants exactly ONE corrected run?

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_rules_on_marginal
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, ruling on your OWN pre-commitment. Be disciplined: a stopping rule exists to stop
you chasing a lever past its payoff -- but it presumes a FAIR test. A confounded test triggers nothing.

WHAT YOU CHOSE: (B) marginal-forward emission -- replace the committed read (one medoid/triphone + hard min-DTW) with
a multi-template HMM forward (per phone slot, K=4 INTACT exemplars as parallel sub-chains; the forward log-sum-exp
marginalises over exemplar-choice x alignment). You predicted top-1 ~17-18. You pre-committed:
  KEEP top-1>=16 ; STOP & revert to 13% if top-1<=13 ; ABANDON the top-1 push if top-1<=11 AND top-3 flat/down.

THE RESULT (same realigned units for both reads, same 100-way, same 110 held-out clips):
  COMMITTED read (1 medoid + hard DTW):   top-1 13   top-3 30
  MARGINAL forward (beta 8):              top-1  9   top-3 20
  MARGINAL forward (beta 14):             top-1  7   top-3 20
By the letter of your rule this is ABANDON (top-1<=11 and top-3 fell 30->20).

THE CONFOUND (the reason to doubt the test, not the idea):
 - Both reads use the IDENTICAL realigned triphone units. The committed read KEEPS 30% top-3; your forward DESTROYED
   it to 20%. A marginalisation that SUMS over more hypotheses cannot rank WORSE than a hard min on the SAME
   information unless the SCORE is confounded.
 - The likely confound: the forward log-likelihood is UNNORMALISED across candidates. Different candidate words have
   different numbers of phones and different exemplar-pool sizes -> different "model volume" (more states, more
   alignment paths). An unnormalised forward SUM systematically favours higher-volume models regardless of
   correctness (the classic marginal-likelihood-favours-higher-entropy-models bias). The hard min-DTW is implicitly
   volume-controlled (one best path); the forward is not.
 - This is NOT the same as your winning marginalisations: glyph soft-MIN compared proper DISTANCES (volume-matched);
   the phone-forward you trust read within ONE model. Comparing RAW forward log-likelihoods ACROSS unequal-volume
   models is a different, known-biased operation.

THE RULING YOU MUST MAKE (terse, decisive):
 (1) Does your ABANDON stand -- i.e. was this a FAIR test of "marginalise-don't-commit" and the result is honest? OR
 (2) Was it CONFOUNDED by model-volume, making it not a real test -> ONE corrected run is warranted? If so, specify
     the SINGLE correction (e.g. likelihood-RATIO vs a background/self model; OR length/volume normalisation; OR a
     soft-MIN over per-candidate proper distances rather than a raw forward sum -- pick ONE and say why it removes the
     bias without becoming the soft-COMPRESS loser). And RE-STATE the pass/fail number for that corrected run.
 (3) Be honest about the meta-risk: ruling "confounded, re-test" is EXACTLY the rationalisation a stopping rule
     guards against. Justify why this is a genuine confound and not motivated reasoning -- in one line."""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK RULES ON ITS OWN PRE-COMMITMENT")
    print("=" * 100)
    a = ask(GROUND + "\n\nRule now. (1) abandon-stands or (2) confounded->one corrected run (name the single "
            "correction + its pass/fail number) ; then (3) the one-line honesty check against motivated reasoning.")
    print("\n[RULING]\n" + (a or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
