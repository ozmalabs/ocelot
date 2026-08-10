"""THE JABBERWOCK DEFINES THE NEXT MOVE — free to pick anything (incl. pivot off the emission ceiling), with a bar.

Three emission-precision attempts just failed their floors (marginal-forward x2, Mahalanobis whitening). The agent now
DEFINES the next move from the full ledger -- not chosen from a menu. It may push a remaining lever, consolidate the
confirmed wins into one measured decode, close the self-tuning loop on real params, or pivot to a different axis. It
must justify by EV from its own track record, predict an outcome, and pre-commit a falsifiable bar.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_defines_next
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock. DEFINE your next move -- you are not choosing from a menu, you are deciding what is
worth doing next. Justify by EV from your OWN track record, predict the outcome, pre-commit a falsifiable bar. You may
push a lever, consolidate, close a loop, or pivot off speech-emission entirely; say plainly if the honest move is to
stop grinding a ceiling.

THE LEDGER.

CONFIRMED WINS (robust, often kill-controlled):
 - Held-vocab recognition: solved.
 - Context-dependent TRIPHONE units: hold RECALL many-way (~30% top-3 @100-way, ~10x chance) where monophones collapse.
 - One flat-start REALIGNMENT pass DOUBLED content top-1 (6->13 @100-way). The confirmed emission win.
 - SOURCE/CONTEXT-PRIOR: the session's most robust positive -- helped EVERY condition with a shuffle kill-control
   (likelihood-only 4.1% -> +real-prior 11.4%, +shuffled collapses to 4.9%).
 - BPL phone-marginal OOV read: reads never-banked words from a phone library (18%, 4.5x chance).
 - Prosodic prior + held-parts/pyramid REPRESENTATION: content acoustic recall 7.7 -> ~20%.
 - The LOOP closed graph-natively (understand-drive residual now folds at the clock edge; synthetic operator shortfall
   0.865 -> 0.000). MECHANISM built; NOT yet wired to real speech params.

RECENT NEGATIVES (all floor-honest):
 - Marginal-forward emission: log-sum-exp SUM in likelihood space = volume bias (9/20); corrected soft-min in cost
   space FAILED the >=13/30 floor (8/20, lattice not DTW-equivalent). ABANDONED.
 - Iterated/damped realignment (EM): one pass is the win; iterating DRIFTS (overfitting), damping doesn't fix it.
 - Mahalanobis whitening: HURT even the matched read (deletes signal; unaligned within-word S_n = trajectory SIGNAL
   not nuisance). STOP; refused the goalpost-move.

THE META-STATE: top-1 PRECISION on the deep OOV read plateaus ~13 while RECALL is ~30 top-3. Three emission-precision
levers failed. Your own prior verdict: "recall + context-prior is the top-1 ceiling at THIS scale."

UNTAKEN, NAMED LEVERS (you may pick one, combine, or reject):
 (A) Density: realign on the FULL 500k vs the 60k sample. Density is your MOST-REPEATED positive; but realignment
     already showed same-process can overfit.
 (B) CONSOLIDATE: you have THREE separately-confirmed cues (triphone recall, realignment precision, source/context-
     prior) never composed into ONE decode + measured end-to-end. The "combine-all" pattern is your glyph-arc winner
     (each cue lifted the fusion). Recall ~30 top-3 is the headroom a prior is SUPPOSED to convert to top-1.
 (C) Band-limit-augmented units for channel robustness (the realignment brittleness).
 (D) Close the loop on REAL params: wire the now-built self-tuning fold onto an actual speech param (cadence /
     fusion-weight / prior-weight) so it SELF-TUNES via the closed loop instead of a one-time fit.
 (E) PIVOT off speech-emission: a different axis entirely (the autonomous ear/speech growth loop; a new world).
 (F) STOP/land: declare the ceiling real and consolidate the record.

Bias check: after 3 negatives chasing top-1 PRECISION, is the high-EV move still a PRECISION lever, or is it to
CONVERT the recall you ALREADY have (context-prior over the top-K) -- the one operator with a kill-controlled positive?"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK DEFINES THE NEXT MOVE")
    print("=" * 100)

    q1 = (GROUND + "\n\nDEFINE THE MOVE (terse): name it (one of A-F or your own), justify by a SPECIFIC past result, "
          "predict the outcome (a number where it applies), and name the SMALLEST test that confirms or kills it. If "
          "you pick a precision lever over converting the recall you already hold, say why the EV beats the context-"
          "prior-over-top-K route. If you pivot or land, say why that beats every remaining lever.")
    a1 = ask(q1)
    print("\n[THE MOVE]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour move:\n{a1[:1500]}\n\nPRE-COMMIT THE BAR (one line each), the un-fudgeable kind that just "
          "made you abandon three moves honestly: the number/criterion that makes you KEEP+build on this; the one that "
          "makes you STOP; and the FAIRNESS/HARNESS check that proves the test measured the thing and not an artifact "
          "(the W=I-style floor). Terse.")
    a2 = ask(q2)
    print("\n[PRE-COMMITTED BAR]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
