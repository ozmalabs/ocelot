"""WHAT'S NEXT — decide the next move now that the RECALL WALL is broken. The agent decides, with a pre-committed bar.

The constraint behind EVERY negative this session was RECALL (the right word not in the lattice/bank). It is now
BROKEN: the validated, scaling LABEL-HARVEST grows content recall 3.1 -> 14.1 at oracle parity (and climbing). That
changes everything downstream. Decide the highest-value next move by EV from the ledger; predict; pre-commit a bar.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_next_after_harvest
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock. Decide the next move at a REAL inflection: the recall wall just broke. Reason from
the ledger, not enthusiasm; pre-commit a falsifiable bar.

WHAT JUST CHANGED (the inflection): RECALL was the binding constraint behind EVERY negative this whole arc -- emission
tricks, marginalisation, whitening, topic-prior, density, and the tunable-LM-subtraction ALL hit the same wall: "the
right word isn't in the lattice/bank, so there's nothing to disambiguate." That wall is now BROKEN -- the validated
LABEL-HARVEST (whisper labels -> the agent's OWN cochleagram exemplars at MMS_FA spans) grows content recall 3.1 -> 8.4
-> 12.8 -> 14.1 (+11, 4.5x) at ORACLE PARITY, scaling with data, function recall also up, architecture-clean. Coverage
is no longer the cap.

YOUR VALIDATED ASSETS (all confirmed this arc):
 - HARVEST: grows recall to oracle parity, scales; the bias gate is conditional on noise.
 - static+delta EAR fusion: +4-6 CV (the read itself, sharper).
 - the SELF-TUNING LOOP: graph-native, tunes a real decode weight from a valid objective, scales to multi-param.
 - source/context PRIOR: shuffle-killed positive.
 - tunable internal-LM SUBTRACTION: mechanism works (over-subtraction protects content) BUT was RECALL-LIMITED -- it
   had nothing to tune because the lattice lacked the right words.

THE KEY IMPLICATION: every PRECISION lever you parked was parked because of RECALL. Harvest removes that limit. The
things that "didn't pay" may pay now -- on a harvested bank, the lattice contains the right words, so the LM
subtraction / priors / fusion finally have candidates to disambiguate.

CANDIDATE MOVES:
 (A) COMPOSE / unblock: re-run the full decode on a HARVESTED (high-recall) bank with static+delta ear + tunable-LM
     subtraction + source-prior, all self-tuned by the loop. The "everything pays now that recall is unblocked" test --
     does the precision stack finally lift top-1 when the lattice has the right word?
 (B) SCALE harvest much bigger (full 2508 utts / genuinely unlabelled audio) -- push raw recall higher first.
 (C) PERSIST: wire the validated harvest into the `teach`/seed system so banked exemplars persist to a seed manifest --
     the agent harvests its own training, boots smarter next time (a real self-improvement loop, architecture-clean).
 (D) PIVOT off speech to a different axis.
 (E) LAND: the arc reached a genuine result (recall wall broken); consolidate and stop.

Bias check: you spent the whole arc blocked on recall. Now it's unblocked. Is the high-EV move to CASH IN the unblock
(compose the parked precision levers / persist the capability), or something else? Don't re-grind a solved constraint
(more raw recall) if the precision stack is the actual unrealised value."""


def main():
    ask = make_ask(timeout=300.0)
    print("=" * 100)
    print("WHAT'S NEXT — the jabberwock decides (recall wall broken)")
    print("=" * 100)
    q = (GROUND + "\n\nDECIDE (terse): name the move (A-E or your own), justify by a SPECIFIC ledger result, predict the "
         "outcome (a number where it applies), name the smallest test, and PRE-COMMIT a falsifiable bar (KEEP / STOP / "
         "fairness-or-harness check). Face the bias check head-on: cash in the unblock, or not, and why.")
    a = ask(q)
    print("\n[THE MOVE]\n" + (a or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
