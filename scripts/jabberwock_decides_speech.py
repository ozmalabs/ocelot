"""THE JABBERWOCK DECIDES THE NEXT SPEECH MOVE — by EV from its OWN track record, with a pre-committed stopping rule.

The deep path is fixed at RECALL (triphone units, top-3 ~30% @100-way, ~10x chance) but top-1 PRECISION plateaus
(~13% after one realignment pass; iterating/damping does NOT compound -- overfitting). Three candidate moves to push
top-1 past 13, plus the option to land. The agent ranks them by EXPECTED VALUE from its own history (not vibes), picks
ONE, predicts a number, and pre-commits a stopping rule.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_decides_speech
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock. Decide your next speech move by EXPECTED VALUE from your OWN track record, not
vibes. State the EV reasoning per option, pick ONE, predict the number, pre-commit a stopping rule.

WHERE SPEECH STANDS:
 - Held-vocab: solved. OOV/content: the open gap. Deep path (read a never-banked word from phones) FIXED at RECALL:
   context-dependent TRIPHONE units (500k MMS_FA-aligned words) hold top-3 ~30% @100-way (~10x chance), surviving
   many-way where monophone collapses. But top-1 PRECISION plateaus at ~13% (chance 1%): the emission keeps the
   truth in the top-K, can't pin it to top-1.
 - One flat-start REALIGNMENT pass doubled top-1 (6->13) -- data-driven phone boundaries vs the uniform np.linspace
   blur. But ITERATING it (EM) DRIFTS (13->11->11) and DAMPING does NOT help -- the drift is OVERFITTING (alignment
   co-adapting with the model), not over-driving.
 - The robust lever all session was the SOURCE/CONTEXT-PRIOR (helped every condition with a kill control); the
   EMISSION sharpening (realignment) helped on matched clips but was BRITTLE to channel shift (band-limit).

YOUR TRACK RECORD (the EV evidence -- USE IT):
 - DENSITY/MORE-DATA: positive, repeatedly (phone-bank context units climbed with data 33->39%; function-word recall
   rose with exemplars; triphone reach 100% only at 500k). BUT realignment just showed more-of-the-same-process can
   OVERFIT.
 - MARGINALISE-over-uncertain-structure: WON big (glyph soft-min over parses = your 79.9% peak; the phone-marginal
   FORWARD algorithm read never-banked words). "marginalise, don't commit."
 - COMMIT-to-one: your current read commits (one medoid per phone + hard DTW); iterated realignment overfit by
   over-committing.
 - STRUCTURE-DISCARDING LEARNED reps: FOUR honest negatives (k-means codebook, bag-of-primitives, soft-membership,
   WCCN) -- each threw away layout/order. Structure-preserving wins; lossy compression loses.

THE CANDIDATE MOVES:
 (A) MORE DATA -- realign on the full 500k (vs the 60k sample); brute density lever. EV: density-positive, but
     realignment-overfitting is a fresh caution, and it's the same process, not a new structure.
 (B) MARGINAL-FORWARD EMISSION -- the named #2 headroom: replace the single-medoid + hard-DTW read with a marginal
     forward over context units (MULTIPLE exemplars per triphone, SOFT alignment / log-sum-exp), so the emission
     marginalises over the uncertain exemplar+alignment instead of committing to one. EV: this is "marginalise don't
     commit" (your big winner) -- but you must disambiguate it from "soft-membership codebook" (a 4x loser): is a
     soft forward over STRUCTURE-PRESERVING exemplars the winning marginalisation, or the losing lossy soft compress?
 (C) MULTI-CONDITION ROBUSTNESS -- band-limit-augment the units so the realigned emission survives channel shift (it
     was brittle). EV: fixes a known brittleness, but doesn't raise the matched-clip top-1 ceiling.
 (D) LAND IT -- the loop is finished, top-1 doubled and confirmed; stop.
"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK DECIDES THE NEXT SPEECH MOVE — EV from its own track record")
    print("=" * 100)

    q1 = (GROUND + "\n\nSCORE + DECIDE (terse): give the EV of each move (A/B/C/D) grounded in a SPECIFIC past result, "
          "then PICK ONE. For (B) the crux: is a soft marginal-forward over your structure-preserving triphone "
          "exemplars the WINNING 'marginalise-don't-commit' (glyph 79.9, phone-forward) or the LOSING soft-membership "
          "compression (4 negatives)? Decide which it is and why -- that disambiguation IS the decision. State the move, "
          "the predicted top-1 (a number), and the SMALLEST test that confirms or kills it.")
    a1 = ask(q1)
    print("\n[DECISION]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour decision so far:\n{a1[:1500]}\n\nPRE-COMMIT THE STOPPING RULE. You have a history of "
          "chasing a lever past its payoff (iterated realignment drifted; you only stopped when it degraded). So, "
          "BEFORE running: state the number that would make you KEEP this move, the number that would make you STOP "
          "and revert to the single-pass 13%, and the number that would make you ABANDON the whole top-1-precision "
          "push and accept that recall+context-prior is the ceiling. One line each. Terse.")
    a2 = ask(q2)
    print("\n[PRE-COMMITTED STOPPING RULE]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
