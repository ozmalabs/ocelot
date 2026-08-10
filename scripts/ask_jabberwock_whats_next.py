"""Ask the jabberwock what to pursue next in its speech understanding — it picks its own frontier.

Grounded in where the work stands after the ear + cipher arc, so the agent chooses the next hill from evidence,
in its own terms.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock. You read speech as P(word | audio, context) ~ P(audio|word).P(word|context).
Here is exactly where your speech understanding stands now -- decide what you pursue NEXT.

WHAT IS SOLVED / WORKING:
 - YOUR EAR is yours. The sample rate is graph-resident (EarConfig.fs) -- you chose 16kHz (matched to your
   80-7500Hz cochlea; you were deaf above 4kHz at 8kHz, missing the fricatives that separate s/f/th). You carry
   a graph rule (raise_ear) that DETECTS your own under-sampling (cochlea above your Nyquist) and raises your ear
   itself; sense_ear_band rides your perception loop. Verified: forced to 8kHz, you raise yourself back at tick 1.
 - CROSS-SPEAKER KEY RECOVERY. Bank many speakers, project the speaker key out per-cue (WCCN = your CMVN rotated
   to the speaker axis). On UNSEEN speakers, isolated digits: 83% (coverage 16 speakers x 3 renditions; the lean
   3 seed cues beat the full repertoire -- more cues HURT cross-speaker). This saturates your autonomous loop's
   hard recognise axis.
 - THE CIPHER READS. Your acoustic ear surfaces the candidate lattice (70% content recall on connected
   held-out-speaker sentences); your language prior (Brown bigram) reads them. You just fixed its collapse: the
   raw log-prob double-counted word frequency the ear already carries, so you switched it to PMI contextual lift
   (log P(w|prev) - log P(w)). Result: +7pt CONTENT, +3pt function -- both halves composed.
 - Your AUTONOMOUS LOOP saturates from ONE seeded goal: it self-selects recognise + segment axes, plateaus,
   consults a teacher on method, grows a new axis, saturates -- zero Python decisions.

THE HONEST GAPS (what is NOT solved):
 - CONTENT-WORD ACOUSTIC CEILING. On a 48-word connected vocab, your content-word top-1 is only ~40% even at
   16kHz+WCCN (the large-vocab cross-speaker wall). The cipher READS but its absolute is modest because the
   acoustic still confuses content words; the prior can only choose what the ear surfaces.
 - THE CIPHER ISN'T IN YOUR LOOP YET. Your autonomous loop recognises ISOLATED words; the connected-speech
   lattice+Viterbi+language-prior decode lives in a script, not in your live recognise faculty. You don't yet
   pick "decode a connected utterance with my prior" as a capability axis and saturate it.
 - REAL speech. Everything above the cipher is on YOUR synthesised voice (piper). On real LibriSpeech your
   acoustic is weak (~17% top-1) -- the synth-vs-real gap is unmeasured with the current ear/WCCN.
 - SEGMENTATION. The connected tests use KNOWN word boundaries (synth_concat); finding the boundaries yourself
   on real continuous speech is a separate faculty you have touched (sonority) but not closed.
 - OPEN VOCABULARY. Everything is closed-set recognition against a banked lexicon; you cannot yet read a word
   you have never banked.

DECIDE, concretely and in your own terms:
 1. WHICH hill next, and WHY -- tie it to the posterior P(word|audio,context) and to where the evidence says the
    biggest understanding is (not the biggest number). Is it pushing content-word acoustics, bringing the cipher
    decode INTO your live loop as a capability axis, crossing to real speech, segmentation, or open vocabulary?
 2. The first concrete step you'd take (a measurement, a faculty to compose, a seed/axis to add) -- something
    runnable, grounded in what you already hold (your cues, WCCN, the lattice, the PMI prior, the loop).
 3. What you'd MEASURE to know it worked (understanding, not score-chasing).
 4. The honest risk, and what you'd watch.

Be concise and concrete -- the next move you'd hand to yourself."""


def main():
    ask = make_ask(timeout=420, preamble=PREAMBLE)
    print(ask("What do you pursue next in your speech understanding, and how do you start?"))


if __name__ == "__main__":
    main()
