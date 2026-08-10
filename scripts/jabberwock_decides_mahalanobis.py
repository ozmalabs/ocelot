"""THE JABBERWOCK DECIDES: should the freshly-minted Mahalanobis primitive go into the speech read? Which FORM?

The handwriting session minted a Mahalanobis primitive. But there are TWO Mahalanobis objects in the codebase with
OPPOSITE track records, and the decision is which (if either) applies to the speech emission -- with a pre-committed
floor (the discipline that just stopped a 3rd wasted marginal-forward run).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_decides_mahalanobis
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock. Decide whether to use a Mahalanobis distance in your SPEECH read, and in which
FORM, by EV from your OWN track record. Pre-commit a falsifiable floor. Be disciplined: you just abandoned a
marginal-forward emission move when its pre-committed floor failed -- the floor is what stops motivated reasoning.

THE TWO MAHALANOBIS OBJECTS (opposite results -- this split IS the decision):

 (1) MahalLeaf Term (the freshly-minted primitive) -- a LEARNED PER-PRIMITIVE GENERATIVE LEAF. Its `b` argument is a
     LEARNED diagonal Gaussian [mean ++ inv_std] of the nearest background primitive; it returns the neg-log-
     likelihood of an observed leaf under that learned Gaussian. In handwriting this was your FIFTH consecutive
     LEARNED NEGATIVE ("at every weight the learned cue only SUBTRACTS; bag-of-parts, soft-membership, WCCN, learned-
     part-membership, now per-primitive Mahalanobis"). To use it in speech you'd learn a Gaussian per triphone unit --
     a learned generative per-unit model.

 (2) WHITENING Mahalanobis (the whitened matched filter, already built + CONFIRMED in audio) -- NOT learned-
     generative. Estimate the within-word NUISANCE covariance S_n (variation of the SAME word across speakers /
     channels; WORD labels only, no speaker labels), whiten W = S_n^{-1/2}, map each frame f -> Wf, and run the
     UNCHANGED DTW so it computes ||W(a-b)||. This PAID: +0.015 past same-split CMVN (your FIRST loop result above
     baseline all session) and the true-vs-wrong separation went +0.057 -> +0.288. "Mechanism confirmed: Mahalanobis
     > Euclidean." It down-weights the nuisance directions -- structure-PRESERVING (it only re-weights feature dims;
     it does not blend exemplars or discard layout/order).

YOUR SPEECH STATE (the read this would change):
 - Deep OOV path: context-dependent TRIPHONE units; the COMMITTED read = one medoid/unit + hard DTW with a per-frame
   Euclidean/cosine distance (1 - f.b).
 - One realignment pass DOUBLED top-1 (6 -> 13 @100-way; top-3 ~30) = the confirmed emission win. BUT it was BRITTLE
   to channel/speaker SHIFT (band-limit) -- the exact nuisance the whitening (2) is built to remove.
 - The marginal-forward move just FAILED its floor (volume bias + topology); recall+context-prior is the current
   top-1 ceiling.

THE CANDIDATE EXPERIMENT (not yet run by anyone): COMPOSE the two separately-confirmed wins -- whiten the features by
within-word nuisance covariance (2), THEN run the REALIGNED-triphone read. Realignment = the emission win; whitening =
the confirmed shift fix; never combined.

YOUR TRACK RECORD (EV evidence): learned-generative/structure-discarding reps = 0 for 5 (all SUBTRACT). Structure-
PRESERVING re-weights/distances = the whitening PAID in audio; geometric/structure-preserving cues win. Composing two
already-confirmed structure-preserving cues = your "combine-all" winners (glyph fusions).
"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK DECIDES — Mahalanobis in the speech read: which form, and the floor")
    print("=" * 100)

    q1 = (GROUND + "\n\nDECIDE (terse): (a) USE MahalLeaf-Term-as-is (learned per-triphone Gaussian), (b) USE the "
          "WHITENING Mahalanobis composed with the realigned read, or (c) NEITHER (the Euclidean read is right). "
          "Ground the pick in a SPECIFIC past result. The crux you must rule on: is form (2) the WINNING structure-"
          "preserving re-weight (whitened matched filter PAID; geometric cues win) or does it collapse into the "
          "learned-negative family (0/5)? State which it is and why. Then PREDICT top-1 for your chosen move (a number) "
          "and name the SMALLEST test that confirms or kills it.")
    a1 = ask(q1)
    print("\n[DECISION]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour decision so far:\n{a1[:1500]}\n\nPRE-COMMIT THE FLOOR + STOPPING RULE (one line each), "
          "the un-fudgeable kind that just made you abandon marginal-forward honestly: the number that makes you KEEP "
          "this Mahalanobis move; the number that makes you STOP and revert to the plain realigned 13% read; and -- if "
          "your move is the WHITENING -- the FAIRNESS FLOOR (at zero/identity whitening it MUST reproduce the 13% "
          "realigned read, else the harness is broken not the idea). Terse.")
    a2 = ask(q2)
    print("\n[PRE-COMMITTED FLOOR + STOPPING RULE]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
