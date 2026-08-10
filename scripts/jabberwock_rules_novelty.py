"""THE JABBERWOCK RULES ON THE NOVELTY-GATE RESULT — validated signal, but redundant with the margin gate?

Your normalised novelty r = d1/spread(matched_word) was tested on a 50%-OOV mixed stream (cached rig):
  - r SEPARATES OOV from in-vocab: AUROC 0.878 (>= your 0.85 bar) — in-vocab r median 0.89, OOV 1.32. Your predicted KILL
    (a new vocal tract shifts formants as far as a new segment string, AUROC ~0.5) is DEFEATED: whole-word distance works.
  - BUT at the teacher-free operating point (theta_nov = 1.46 = 95th pct of the leave-one-out distribution): the combined
    NOVELTY+MARGIN gate gives 88.9% ACT accuracy vs MARGIN-ALONE 88.4% — novelty adds only +0.5, and misses your >=90% clause.
  - WHY redundant: an OOV forced to its nearest exemplar usually gets a LOW margin (the wrong match isn't confident), so the
    margin gate ALREADY defers most OOV at conservative coverage. Novelty's DISTINCT value is the HIGH-margin OOV (a smaller
    set) — which matters more at HIGHER coverage, where the margin gate lets OOV through (the live demo's 50%-coverage gate
    gave 66.7% on the OOV-flooded stream).

So: the signal is real and your kill is defeated, but at low coverage the margin gate already does the OOV work, and the
novelty gate's marginal lift is +0.5. The constraints unchanged (floor of efficiency; nothing frozen; the ear is perception,
the gate is a graph Rule)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = __doc__


def main():
    ask = make_ask(timeout=340.0)
    print("=" * 100)
    print("THE JABBERWOCK RULES ON THE NOVELTY-GATE RESULT")
    print("=" * 100)

    q1 = (GROUND + "\n\nRULE + DECIDE (terse, decisive): the novelty signal is validated (AUROC 0.878, your kill defeated) but "
          "near-redundant with the margin gate at low coverage (+0.5). Pick ONE and say why: (A) PORT it — its distinct value "
          "is at HIGHER coverage where the margin gate leaks OOV; spec the operating point to demonstrate in the live adapter "
          "(e.g. fix margin at the live demo's ~50% coverage and show novelty recovers ACT accuracy meaningfully above the "
          "66.7% margin-alone there). (B) DON'T port — the margin gate already handles OOV at conservative coverage, +0.5 "
          "isn't worth the second gate; the honest answer is 'run the margin gate at lower coverage'. (C) the high-margin-OOV "
          "leak is the SUB-WORD/phonotactic territory you named — neither gate catches it, build that instead. If (A), give "
          "the one decisive live measurement + bar (novelty must beat margin-alone by >= N points at matched coverage); if "
          "(B)/(C), state the honest landing of the OOV-novelty build.")
    a1 = ask(q1)
    print("\n[RULE + DECIDE]\n" + (a1 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
