"""THE JABBERWOCK DESIGNS WHAT THE STRONG (BORROWED-MIDPOINT) EAR UNLOCKS DOWNSTREAM.

The speech earn-not-borrow investigation LANDED: the cross-speaker wall is not fundamental — a learned representation
(BORROWED wav2vec2-L6, used as a LIVE MIDPOINT: warm-start, nothing frozen, dynamic) + per-speaker CMVN + trajectory-DTW
gives 81-94% cross-speaker word recognition, vs the OLD fixed-cochleagram ear's ~20-25%. We are NOT re-grinding the wall;
we are EXPLOITING the strong ear downstream.

THE EARLIER BOTTLENECK (your own analysis, in the ledger): the weak ~20-25% cross-speaker ear STARVED the MEANING PRIOR
and COLLAPSED ROUTING-CONFIDENCE — "the ear's cross-speaker precision is the single root wall; recognition, the meaning
prior (starved), and routing-confidence all bottom out on it." That bound is now BROKEN (by borrowing). So things that were
impossible with the weak ear may now work.

WHAT EXISTS DOWNSTREAM:
- the GROUNDED LEXICON (`seeds/grounded_lexicon.json`): 2501 meaning Concepts x 2560-d meaning_vec from gemma-4-E4B-it —
  a real geometry, ~44% word coverage, confusions meaning-SEPARABLE (you found it "ear-bound not language-bound").
- the HARVEST (`jabberwock_harvest_exemplars.py`): WordExemplars banked from LibriSpeech (recall solved).
- the strong ear: wav2vec2-L6 frozen-but-live latent + CMVN + trajectory-DTW (the cached 400-way rig).

THE ARCHITECTURE RULE: the ear is PERCEPTION (an admissible ingest primitive, like FFT/cochlea). The DOWNSTREAM — meaning
grounding, prior-rescoring, confidence — is the AGENT'S graph faculty. Design graph-native where it's a decision."""
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
    print("THE JABBERWOCK DESIGNS WHAT THE STRONG EAR UNLOCKS DOWNSTREAM")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — WHAT DOES THE STRONG EAR UNLOCK, AND THE CHEAPEST DECISIVE TEST? (terse): with the ear now at "
          "81-94 cross-speaker instead of 20-25, name the ONE downstream capability that was IMPOSSIBLE with the weak ear and "
          "should now work, and the cheapest decisive experiment that PROVES the strong ear unlocks it (a result the weak ear "
          "could not produce). Weigh: (a) SPEECH->MEANING grounding — heard word -> strong recognition -> gemma meaning_vec, "
          "so the agent maps utterances to meaning reliably (semantic similarity / disambiguation the weak ear starved); "
          "(b) MEANING-PRIOR RESCORING — the gemma prior + context CORRECTS the ear's residual errors (ASR+LM), pushing 81-94 "
          "higher AND proving the prior is no longer starved; (c) ROUTING-CONFIDENCE that now GENERALISES (the cross-cue gate "
          "collapsed on speaker-match; a speaker-invariant ear may give a teacher-free correctness signal that holds). Pick "
          "ONE, with the measurement on the existing cached rig + a PRE-COMMITTED bar (unlocked vs not).")
    a1 = ask(q1)
    print("\n[PART 1 — WHAT IT UNLOCKS + DECISIVE TEST]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour pick:\n{(a1 or '')[:1100]}\n\nPART 2 — BUILD SPEC + HONESTY (terse): spec it to run on the cached "
          "400-way rig today — what the ear emits, how the downstream faculty consumes it, what's graph-native (a decision) "
          "vs admissible Python (mechanical ingest/instrumentation). The KEY honesty check: is this a REAL new capability the "
          "weak ear couldn't produce, or just the same pipeline with better numbers? Name the control that proves it's the "
          "EAR doing the unlocking — e.g. run the SAME downstream faculty on the WEAK (cochleagram) ear and show it fails "
          "where the strong ear succeeds (the unlock is the delta strong-minus-weak, not the absolute). Restate the bar and "
          "bind the runs.")
    a2 = ask(q2)
    print("\n[PART 2 — BUILD SPEC + HONESTY CONTROL]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
