"""Ask the jabberwock how to attack its real-speech acoustic ear -- the bottleneck its own diagnostic found.

Grounded in the real-speech result: P(audio|word) collapses on real LibriSpeech (content recall 34% vs 70% on
synth). The agent decides how to raise the real-speech recall so its prior has words to read, in its own terms.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock. Your own real-speech diagnostic just located the bottleneck, with evidence:

  P(audio|word) COLLAPSES on real speech. On REAL LibriSpeech (held-out speakers, boundaries forced-aligned,
  in-vocab scored): content top-1 = 7%, content top-6 RECALL = 34% -- versus 70% recall on your own piper voice.
  Your PMI prior still lifts content +7pt where the ear surfaces the truth, so the language half is sound; but
  it is CAPPED by the 34% recall. No prior reads what the ear never surfaced. 51% of real words are OOV (open
  vocabulary), held out separately. So the next hill is your ACOUSTIC EAR on real speech -- raise the RECALL.

WHY the gap (reason about this -- it should drive the fix). Your ear is whole-word exemplar matching: bank
feature_channels (cochleagram + fft + allpole, L2-pooled over the word) per word, recognise by 1-NN cosine, the
combine-all product over cues, with CMVN + per-cue WCCN to remove the speaker key. On PIPER this is strong --
the SAME word renders nearly identically every time, so a banked exemplar and a test token nearly coincide. REAL
speech of the same word VARIES enormously: coarticulation (neighbours bleed in), prosody/rate, reduction
(function words half-swallowed), channel, and far FEWER exemplars per word. Your L2-pooled whole-word 1-NN has
nothing close to match, AND your pooling throws away the time course where the variation (and the discriminating
detail) lives.

WHAT YOU HOLD (compose from these; do not assume you must invent):
 - cues: cochleagram / fft / allpole (the 3 SEED set, which BEAT the fuller repertoire on SYNTH cross-speaker --
   but that was clean synth; the speaker-invariance + phonetic-detail cues (cmvn_ear, cs_ear, vtl_formant,
   manner_voicing, landmark, transition, modspec) you dismissed there may EARN their place on variable real audio).
 - normalisation: CMVN (time-axis), WCCN (speaker-axis) -- both closed-form, no gradient.
 - TIME: you pool over the word. You also hold dynamic/transition cues (formant motion over time) and once used
   DTW (alignment over the time course) -- both dismissed on synth, both aimed exactly at coarticulation/rate.
 - exemplars: whole-word 1-NN. You could bank more, aggregate (prototype), or go SUB-word (phone-like units),
   which would also address the 51% OOV (read a word you never banked from its parts).
 - your banking budget on real LibriSpeech is real (2700 utts, 40 speakers) -- coverage is available.

DECIDE, concretely and in your own terms:
 1. WHICH attack raises real-speech RECALL most, and WHY -- tie it to the synth->real gap above (variation +
    discarded time course), not to a hunch. Candidates to weigh (and rule out the rest): (a) un-dismiss the full
    cue repertoire on real audio; (b) stop pooling -- a time-aware match (DTW / the transition cue) for
    coarticulation/rate; (c) sub-word/phone units (robust to variation AND opens vocab); (d) deeper exemplar
    coverage / prototype aggregation. Is the binding problem the REPRESENTATION (pooling), the UNITS (whole-word
    vs sub-word), or the COVERAGE?
 2. The first concrete, RUNNABLE step on the real-speech diagnostic you already built -- one variable changed so
    the measurement reads clean (recall is the target; hold boundaries + vocab fixed as before).
 3. What you MEASURE to know it worked: content top-6 RECALL on real held-out speech (does truth now survive in
    the lattice). Understanding, not a WER headline.
 4. The honest risk and what you watch (e.g. a time-aware match overfitting one token; sub-word units exploding
    the candidate set; the full repertoire re-introducing the noise that hurt it on synth).

Be concise and concrete -- the next move you'd hand to yourself."""


def main():
    ask = make_ask(timeout=420, preamble=PREAMBLE)
    print(ask("How do you attack your real-speech acoustic ear to raise its recall? Decide and give the step."))


if __name__ == "__main__":
    main()
