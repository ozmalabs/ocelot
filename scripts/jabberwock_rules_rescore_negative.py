"""THE JABBERWOCK RULES ON THE RESCORING NEGATIVE + PICKS THE NEXT DOWNSTREAM MOVE (or lands).

You designed downstream test (b) meaning-prior rescoring to prove the strong (borrowed-midpoint) ear unlocks the gemma prior.
It came back a ROBUST, well-controlled NEGATIVE:

  STRONG ear (raw wav2vec, 80.5% — your premised 81% regime, WITH headroom): rescored 77.4 (-3.2).
  STRONG ear at 95.5% (per-speaker CMVN, near-ceiling): rescored 94.0 (-1.5).
  ORACLE-context rescored (centroid from GOLD neighbour words, the upper bound): 77.8 (-2.7) — STILL HURTS.
  WEAK ear 12.9 -> 11.9 (-1.0). Cross-ear unlock delta -2.1. lambda>0.25 collapses accuracy.

So even with the right word PRESENT (your premise held) and PERFECT context, the gemma topic-coherence prior CANNOT correct
the acoustic ear — it overrides a mostly-right acoustic ranking with a weak topic signal and loses more than it rescues.
HONEST WHY: acoustic word-confusions are usually between words that are ALSO topically plausible, so topic coherence does
not discriminate them. A bag-of-words meaning prior is the wrong tool for clean read-speech.

THE REFRAME: the strong ear SOLVES clean-speech recognition (80-95% cross-speaker, up from ~20-25). Its downstream value is
NOT error-correction (the prior can't help, and the ear doesn't need it) but RELIABLE speech->word — which enables
UNDERSTANDING (acting on reliable recognitions), not recognition-improvement. The "prior was starved" is now "prior is
usable but UNNEEDED for clean recognition."

YOUR UNTRIED DOWNSTREAM CANDIDATES: (a) speech->meaning grounding — a meaning TASK on reliable recognitions (not error-
correction); (c) routing-confidence that now generalises — a teacher-free correctness signal (the cross-cue agreement gate
that COLLAPSED on speaker-match; a speaker-invariant ear may give a confidence that holds). THE CONSTRAINTS unchanged
(floor of efficiency; dynamic>=human; borrow as live midpoint). Architecture: the ear is perception; downstream is graph faculty."""
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
    print("THE JABBERWOCK RULES ON THE RESCORING NEGATIVE + PICKS THE NEXT DOWNSTREAM MOVE")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — RULE + PICK (terse, honest, decisive): accept the rescoring negative as final (it is well-"
          "controlled: two ear regimes + oracle-context upper bound). Then: is there a GENUINELY VALUABLE downstream use of "
          "the strong ear worth building now — or is the honest truth that the strong ear's contribution IS the recognition "
          "(80-95 from 20-25) and the downstream extras are marginal, so we LAND the exploitation thread? If you pick a use, "
          "say which — (a) speech->meaning grounding, (c) routing-confidence-that-now-generalises, or something else — and "
          "WHY it produces value the weak ear couldn't, NOT just a capability demo. Be ruthless: if (a)/(c) are <50/50 to "
          "show a real pre/post delta, say LAND and name the net contribution.")
    a1 = ask(q1)
    print("\n[PART 1 — RULE + PICK]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour pick:\n{(a1 or '')[:1100]}\n\nPART 2 — DECIDE (terse): if you picked a downstream use, spec the "
          "ONE cheapest decisive test on the cached rig — what it measures, the pre/post control (strong ear vs weak ear, "
          "the delta that the weak ear could not produce), and a PRE-COMMITTED bar (value shown vs not); bind the runs. If "
          "you LAND, give the one-line durable conclusion of the strong-ear-downstream thread and what (if anything) the "
          "borrowed-midpoint ear is now READY to be wired into (the agent's real speech pipeline), vs what stays open.")
    a2 = ask(q2)
    print("\n[PART 2 — TEST OR LAND]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
