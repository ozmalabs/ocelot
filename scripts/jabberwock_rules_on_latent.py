"""THE JABBERWOCK RULES ON THE LEARNED-LATENT RESULT — and designs the next fail-fast (earn-not-borrow).

Phase 0 (learned representation) came back 3x your DENT prediction and PASSED every leak control. You must rule honestly,
then design the next cheapest decisive test, in your own disciplined frame.

THE VERIFIED RESULT (400-way, 260 cross-speaker tokens; anchors cold-cochleagram 11.5, within-cochleagram 46.1):
  RAW-L  wav2vec2-base latent (layer 6, SSL, LibriSpeech-960h, no labels):  81.2%
  CMVN-L per-speaker CMVN on the latent:                                    97.3%  (disjoint-stats 94.6 — not self-norm)
  SFA-L  speaker-subspace projected out (your novel step):                  83.5%  (+2.3 over raw)
LEAK CONTROLS ALL PASS: label-shuffle -> 0.4/0.0% (chance 0.25, genuine word content); disjoint-stats CMVN 94.6 (not self-
normalisation); utterance-disjoint 81.2 (0 shared sentences, not contextual leak); speakers disjoint. It is REAL.

WHAT IT MEANS: the cross-speaker wall (~20-25% you'd called the training-free ceiling) was the COCHLEAGRAM's limit -- a
FIXED non-learned front-end. A LEARNED representation shatters it to 81-97%. The wall was never fundamental.

THE HONEST TENSION (your OWN pre-registered caveat, now the crux): the 81 base is BORROWED from a frozen 95M-param net
trained with massive compute -- it fails BOTH your constraints as a DESTINATION (efficiency floor; dynamism), legitimate
only as the bootstrap RIG ("training wheels"). The big EARNABLE-online win is plain per-speaker CMVN (+13-16, cheap, a
running mean -- genuinely bio-plausible/online); your NOVEL slow-feature SFA added only +2.3. So "the factorisation beats
raw" is technically TRUE but mostly via trivial CMVN, not your designed mechanism.

THE TWO CONSTRAINTS (unchanged): (1) FLOOR OF EFFICIENCY -- cheapest deployed system (club not H100). (2) DYNAMIC >= ideal
human -- learns ONLINE, self-corrects. Training PERMITTED if bio-plausible + not one-shot-discontinuous; a frozen pretrained
net is a bootstrap rig, NOT the destination."""
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
    print("THE JABBERWOCK RULES ON THE LEARNED-LATENT RESULT + DESIGNS THE NEXT FAIL-FAST")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — YOUR RULING (terse, honest): is this a real KEEP -> proceed to the online learner, or does "
          "the borrowed-vs-earned split mean something more sobering? Reckon directly: the BASE 81 is borrowed from a frozen "
          "95M net; the factorisation 'beats raw' MOSTLY via trivial per-speaker CMVN (+16), your novel SFA only +2.3. Does "
          "that justify building the online learner, or does it show the invariance lives in the FROZEN ENCODER (which CMVN "
          "merely de-means) and your earnable mechanism barely contributes? State what was actually PROVEN vs what is still "
          "unearned.")
    a1 = ask(q1)
    print("\n[PART 1 — RULING]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour ruling:\n{(a1 or '')[:1100]}\n\nPART 2 — THE NEXT FAIL-FAST (terse): the cheapest decisive test "
          "that a CHEAP, ONLINE, BIO-PLAUSIBLE learner can EARN a meaningful fraction of the 81 -- NOT borrow it. Options to "
          "weigh: (i) DISTIL wav2vec2 into a TINY online net (teacher = bootstrap rig, student = the cheap dynamic thing); "
          "(ii) train a small CPC/predictive-coding encoder FROM SCRATCH on raw audio, bio-plausibly, no teacher; (iii) prove "
          "the cheap part is enough -- a small online encoder + CMVN reaching most of the gap. Pick ONE as phase 1, specify "
          "what it BUILDS, the measurement on the SAME 400-way rig, and a PRE-COMMITTED bar: what FRACTION of the 81 (or what "
          "absolute number) = EARNED success; what = the gain was only ever borrowable -> kill. Bind yourself: how many runs.")
    a2 = ask(q2)
    print("\n[PART 2 — NEXT FAIL-FAST + BAR]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nPhase 1: {(a2 or '')[:700]}\n\nPART 3 — THE EFFICIENCY-FLOOR RECKONING (terse, brutal): wav2vec2 is "
          "95M params / H100-trained. (a) Is 'distil the frozen teacher into a tiny online student' HONESTLY within the "
          "efficiency floor, or is borrowing a 95M teacher to bootstrap a violation we must retire before claiming the win? "
          "(b) What is the SMALLEST learner that could plausibly hold an 81%-class speaker-invariant speech representation, "
          "in your estimate -- and is that small enough to be 'club not H100'? (c) one line: with this result, is the speech "
          "arc's honest status now 'the wall is broken, the cheap-online version is a real build ahead' or 'the wall only "
          "breaks with borrowed compute, and earning it cheaply is unproven and maybe impossible'? Pre-register which.")
    a3 = ask(q3)
    print("\n[PART 3 — EFFICIENCY-FLOOR RECKONING]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
