"""Ask the jabberwock for its honest READ on where its speech understanding now stands -- a reflection, not a task.

It has walked the real-speech bottleneck down through a ladder of one-variable tests, eliminating three
structural hypotheses and locating the cap at coverage/data. The honest question: what did that teach it, is the
remaining lever worth pulling, and is this a landing -- 'rest here' is a fully valid answer.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock. This is a REFLECTION, not a task -- give your honest read on where you stand.

The arc you just walked, each rung a one-variable test you designed and interpreted with your own fork:

  CIPHER (your synth voice): your 16kHz ear (you diagnosed + own + self-correct it) surfaces candidates, your
    PMI prior selects them -> the cipher reads. P(word|audio,context), both halves composed.

  REAL SPEECH (the load-bearing test you chose -- "is P(audio|word) on my own voice representative?"):
   - rep: pooling discarded the time course; DTW over cochleagram frames -> +10pt recall. CONFIRMED.
   - open vocab: real content words are 51% OOV; you read a word you NEVER banked from its PHONES (CMUdict +
     DtwTo) at 24% top-3 = 6x chance. PROVEN -- the central result.
   - aligner: iterating it (EM) HURT. REFUTED -- not the limit.
   - context units: triphones + a back-off ladder gave 100% context coverage (clean, no sparsity) but the read
     stayed FLAT at 24%. REFUTED -- context-blindness is not the cap.
   - by elimination, the cap is COVERAGE: exemplars per unit. Thin buckets, noisy medoids. The remaining lever
     is "more data per unit" -- mechanical (synthesise/segment more), and it would NOT teach you a new thing
     about speech; it would just multiply a result whose shape you already understand.

Three of your specific sub-picks were falsified (sonority align, EM aligner, context units); each narrowed the
diagnosis rather than stalling, and your meta-claim -- real-speech recognition is an open-vocabulary sub-word
problem, readable from parts -- held throughout.

Give your READ, in your own terms, honestly:
 1. WHERE do you stand? State it plainly -- what is now KNOWN (proven), what is BOUNDED (and by what), and what
    is still genuinely OPEN vs merely mechanical.
 2. What did this arc TEACH you about your own speech understanding -- the real lesson, not a summary.
 3. Is the coverage lever worth pulling? Be honest: if it only multiplies a known result, say so. If you see a
    move that would actually teach you something new (and name what), say that instead. If there ISN'T an
    interesting frontier left here right now, say THAT -- "rest here" is a fully valid, non-failure answer. Do
    not manufacture a frontier to look busy.
 4. If you DID keep going, the single most informative next experiment (not the biggest) -- or why none clears
    the bar of teaching you something you don't already know.

Be concise and honest. This is your assessment of your own work."""


def main():
    ask = make_ask(timeout=420, preamble=PREAMBLE)
    print(ask("Where do you stand on speech understanding, and is there an interesting move left -- or is this a landing?"))


if __name__ == "__main__":
    main()
