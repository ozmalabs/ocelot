"""THE JABBERWOCK DESIGNS DEFER-AND-LEARN — close the speech loop: the DEFER set IS the "teach me" queue.

The OOV investigation landed here: real-word OOV is a LEXICAL question, not acoustically/phonotactically detectable (sub-word
surprise was chance, AUROC 0.50 — real OOV words have legal phonotactics). The honest design is DEFER-AND-LEARN: the agent
acts on confident recognitions and LEARNS the deferred ones, online, nothing frozen.

WHAT EXISTS (wired): the strong cross-speaker EAR (wav2vec2, perception); the BANK of known-word exemplars; the graph-native
SELECTIVE-ACTION faculty (margin gate + delta-rule trainer) whose DEFER set = the low-confidence recognitions; the teach
machinery (the `teach` facility appends graph data to a seed; a PLUGGABLE teacher harness — `set_self_teacher`, the harvest's
whisper-labeller — supplies labels). THE DYNAMISM CONSTRAINT: learn online, nothing frozen, the bank GROWS (warm-start stays live).

THE INTERESTING CLAIMS (not just 'add a labeled exemplar'):
  (i) the agent KNOWS WHEN to ask — its own DEFER gate is the teacher-free trigger, so the teacher is queried only on the
      uncertain, efficiently (cheap-first; don't ask about what you already know).
  (ii) ONE-SHOT — one exemplar appended to the bank makes a previously-OOV word recognisable (the ear is rich enough).
  (iii) CROSS-SPEAKER one-shot — a word learned from ONE speaker is then recognised when a DIFFERENT speaker says it (the
        strong ear's cross-speaker invariance means one-shot GENERALISES — the whole cross-speaker thesis, cashed in).

THE ARCHITECTURE RULE: the ear is perception; the DEFER->LEARN decision is a graph Rule; the bank-append is the mechanical
teach facility; the teacher (label source) is pluggable host I/O (oracle/whisper/human-ask)."""
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
    print("THE JABBERWOCK DESIGNS DEFER-AND-LEARN")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE LOOP (terse, concrete): design defer-and-learn. (a) the TRIGGER — which DEFER becomes a "
          "'teach me'? ALL low-margin defers, or only a subset (and how chosen teacher-free, since OOV isn't acoustically "
          "detectable — do you ask about EVERY deferred token, accepting the teacher cost, or budget it)? (b) the LABEL "
          "source — the pluggable teacher returns the word; what graph node carries the pending question (an Unknown/Query "
          "node), and what's graph-native (the defer->ask decision) vs mechanical (the teacher I/O, the bank-append). (c) the "
          "LEARN — append the labelled exemplar to the bank so the word is in-vocab next time; ONE exemplar or accumulate; "
          "and is the bank-append the `teach` facility (persisted to a seed, survives reboot)?")
    a1 = ask(q1)
    print("\n[PART 1 — THE LOOP]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour loop:\n{(a1 or '')[:1100]}\n\nPART 2 — DEMO + BAR + HONESTY (terse): (a) the demonstration on "
          "the cached rig: stream OOV words; the agent DEFERS them (teacher-free), the teacher labels, the word is appended "
          "to the bank; measure recognition of those words BEFORE (OOV, ~0%) vs AFTER learning. THE KEY TEST — CROSS-SPEAKER "
          "one-shot: learn a word from speaker A's single utterance, then recognise it from speaker B (a DIFFERENT speaker) — "
          "does one-shot GENERALISE cross-speaker? Pre-committed bar: previously-OOV words, after one taught exemplar, "
          "recognised cross-speaker at >= X%. (b) HONESTY: what makes this MORE than supervised online learning — name the "
          "control that proves the value is (i) the agent asking ONLY when uncertain (vs asking always) and (ii) cross-"
          "speaker generalisation from one exemplar (vs needing many). (c) the teacher-cost curve: as the bank grows, the "
          "defer-rate (teacher queries) should FALL — the agent asks less as it learns. State the bar for that too.")
    a2 = ask(q2)
    print("\n[PART 2 — DEMO + BAR + HONESTY]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
