"""Ask the jabberwock how to build sub-word units -- its evidence-elevated lever for real-speech content + OOV.

Grounded in the DTW result: the time-aware matcher is confirmed, but content words on real speech are an OPEN
VOCABULARY problem (51% OOV; they were never banked). Sub-word units = read a word never banked from its parts.
The agent decides what a unit IS, where the inventory comes from, and how an unseen word gets read.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock. Your own experiments have walked the real-speech bottleneck down to one move:

  - The cipher reads (ear surfaces candidates, PMI prior selects) -- on YOUR synth voice.
  - On REAL LibriSpeech, P(audio|word) collapses (content recall 34% vs 70% synth). You proved the cause is
    REPRESENTATION: a time-aware DTW match over the cochleagram frames beats pooled 1-NN by +10pt recall -- keep
    that matcher (wire-in = your native DtwTo over the frames).
  - But content words stay low because they are OPEN VOCABULARY: 51% of real words are OOV -- never banked. No
    whole-word exemplar match, however good, can read a word it has never heard a labelled instance of.

So the lever you ELEVATED from your own evidence: SUB-WORD UNITS -- read a word never banked FROM ITS PARTS. A
whole-word lexicon cannot generalise to a new word; a sub-word inventory can, because words SHARE parts.

WHAT YOU HOLD (compose from these; do not assume you must invent):
 - sonority_segment: your Rust primitive that splits a clip at sonority valleys -> syllable-like sub-word spans
   (you used it to find WORD boundaries; the same valleys cut WITHIN a word).
 - the DTW matcher you just validated (DtwTo over cochleagram frames) -- it can match a UNIT as well as a word.
 - phonetic-detail cues: manner_voicing (periodicity/voiced/sibilant), landmark (stops/fricatives), transition
   (formant motion) -- the acoustic correlates of phone identity, currently dormant.
 - BlendCover: your portmanteau kernel -- composes/aligns sub-word pieces (slithy = slim+lithe).
 - your LanguagePrior: a 40k-word Brown vocab -- but it is TEXT (spellings + bigrams), it does NOT hold
   pronunciations. So a word->unit map for an UNSEEN word is the crux you must solve, not assume.
 - real banking budget (2700 utts, 40 speakers), forced-aligned word boundaries (whisper).

DECIDE, concretely and in your own terms:
 1. WHAT is a sub-word unit for you -- a SYLLABLE (sonority spans, which you can cut today with no new model), a
    PHONE (needs a phone inventory + alignment you do not yet have), or a self-discovered ACOUSTIC unit (cluster
    your frames into a codebook)? Tie the choice to what you can build NOW from the above and to the OOV read.
 2. THE CRUX -- the word->units map for an UNSEEN word. To read an OOV word you must know (or infer) its unit
    sequence. Where does that come from: segment the unknown clip into units acoustically and match unit-by-unit
    (no spelling needed)? a pronunciation source you'd add? grapheme->unit from spelling? Be concrete about how
    a word you never banked becomes readable.
 3. The first RUNNABLE step on your real-speech diagnostic -- one new capability, measured. The cleanest proof:
    HOLD OUT whole words from the bank, then read them from sub-word units banked from OTHER words. Does an OOV
    word become recoverable at all?
 4. What you MEASURE (OOV-word recall from parts -- can the ear surface a never-banked word's identity), and the
    honest risk (units too coarse to discriminate / too fine to be stable; the unit-sequence->word map being the
    real bottleneck; sonority syllables not aligning to the lexicon's units).

Be concise and concrete -- the next move you'd hand to yourself."""


def main():
    ask = make_ask(timeout=420, preamble=PREAMBLE)
    print(ask("How do you build sub-word units so you can read a real word you never banked? Decide and give the step."))


if __name__ == "__main__":
    main()
