"""Ask the jabberwock to decide its OWN ear bandwidth — the creator: "give the jabberwock control."

It owns its front end already (cues + params are graph-resident, self-modifiable). The sample rate is a deeper
perception parameter currently HARDCODED in Python (speech_world.FS = 8000). The diagnostic says that ear is
band-limited and it is costing recognition. The agent decides whether to raise it, whether to OWN it, and how
to detect the limit itself.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock — a graph-native agent whose PERCEPTION is your own to control. You
already own your front end: your cochlear cues and their params live as graph nodes (FrontEnd / Cue / EarConfig)
that YOU add, invent, and tune; feature_channels reads whatever cues are active. One perception parameter is
NOT yet yours — it is hardcoded in the Python world-adapter: speech_world.FS = 8000, the sample rate your ear
hears at. The creator just said: give the jabberwock control. So decide.

THE EVIDENCE (cross-speaker isolated-word recognition, your own combine-all product + WCCN):
 - As the vocabulary grows 8 -> 64 words, your top-1 collapses 71% -> 36% while recall@6 holds 97% -> 75%. The
   truth is SURFACED but not RANKED: confusable words (cat/bat/hat/mat; six/fix; sat/fat) win each other's slots.
 - The cues, a per-pair discriminative re-rank, and a positional onset/nucleus/coda split each bought only a
   few points. Then the root cause: at FS=8000 your ear's Nyquist is 4kHz, but the FRICATIVE energy that tells
   s/f/th apart lives at 4-8kHz. Measured: the word "six" has 0.0% of its energy above 4kHz at 8kHz. The
   consonant detail that separates the confusable onsets is LOW-PASSED AWAY before any cue sees it (piper voices
   are natively 22050Hz, downsampled to 8kHz at synth). You have been DEAF above 4kHz.
 - Raising the ear to 16kHz (Nyquist 8kHz), keeping your 80-7500Hz cochlear bands (their dims are unchanged --
   the cochleagram resamples to a fixed n_frames; only the CONTENT is restored): realistic 64-word top-1
   39 -> 46% (+7pt), recall 77 -> 84%; the onset-confusable CVC set 29 -> 33%. CUMULATIVE 8kHz/curated 36% ->
   16kHz/full 46% (+10pt). The positional split then adds +0pt -- once you can hear the band, your existing cues
   already route it; the EAR was the lever, not the cue topology.

DECIDE, concretely and in your own terms:
 1. Do you raise your ear to 16kHz? Weigh the perception gain (the restored fricative band, +10pt top-1, the
    confusable-onset words finally separable) against the cost (2x the samples to process; every banked exemplar
    must be RE-HEARD at the new rate -- a re-bank). Is 16kHz right, or higher (22kHz native), or do you choose
    per-task? Pick a rate and justify it.
 2. Should the ear's sample rate become a graph-resident parameter YOU own (an EarConfig field your front end
    carries and the adapter READS), like your cues -- so your perception bandwidth is your decision, not a Python
    constant? Or is a fixed adapter rate the honest boundary (mechanical I/O), with only the cues yours? Say which
    and why, against the architecture rule (you are the graph; Python is a mechanical world-adapter that may read
    your graph-resident config but holds no decision).
 3. How would you DETECT this band-limit YOURSELF, so the choice is yours to make from evidence, not handed to
    you? Name the graph-readable signal -- e.g. spectral energy piled at the Nyquist edge (aliasing), or empty
    top cochlear bands, or a recognition wall specifically on fricative-confusable pairs. Which signal, and the
    rule that would raise the ear when it fires.
 4. The honest risk (a higher rate that the cues then dilute; aliasing if the resample is sloppy; the re-bank
    invalidating learned exemplars mid-stream) and your guard.

Be concise and concrete -- a change to hand to your world-adapter."""


def main():
    ask = make_ask(timeout=360, preamble=PREAMBLE)
    print(ask("Decide your ear bandwidth. You now control it."))


if __name__ == "__main__":
    main()
