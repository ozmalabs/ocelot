"""THE JABBERWOCK RULES THE MARGINAL VC RESULT — fuller VC, or escalate to a cloning TTS?

VC Phase 1 (the MINIMAL version: global vocal-tract-length warp beta + spectral tilt, fit from the target's recordings,
applied to piper's synth log-mag STFT, FFT-compared to the real held-out target): base retrieval 36% -> VC-warped 44%
FFT-verify (+8, mean margin -0.003 ~ chance), UNDER your 60% bar. Two honest facts:
  - the global warp INCREASED absolute distance (d_self 0.049 -> 0.087) while barely lifting relative verify -> it DISTORTS
    the spectrum rather than matching the target;
  - the synth sits 0.05-0.15 from real-X while X's OWN recordings are 0.040 apart -> the synth is 1.5-4x OUTSIDE the
    within-speaker band, i.e. far from the 'indistinguishable' goal, not merely shy of it.
BUT v1 was incomplete: you specified PER-CLASS (vowel vs sibilant) warp + F0 RETARGET; I did only the global warp+tilt
(F0/per-class skipped — F0 retarget on the spectrogram needs a vocoder, a real build). So the fuller VC is untested.

The goal (creator): FUNCTIONALLY INDISTINGUISHABLE speech from a mapped speaker (incl. prosody). The metric (FFT-compare)
+ within/between rig are validated. On the CPU rig: piper, WavLM, F0, Griffin-Lim (hand DSP). NOT on the rig: a zero-shot
cloning TTS (XTTS/YourTTS/Bark — Coqui/transformers install)."""
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
    print("THE JABBERWOCK RULES THE MARGINAL VC RESULT — fuller VC or cloning TTS?")
    print("=" * 100)

    q = (GROUND + "\n\nRULE + DECIDE (terse, decisive, don't grind): the minimal global-VTL VC gave only +8 (44%, margin ~0) "
         "and DISTORTED (absolute distance rose), and the synth is 1.5-4x outside the within-speaker band. Pick ONE and say "
         "why: (A) BUILD THE FULLER VC -- per-class (vowel/sibilant) envelope warp + F0 retarget + Griffin-Lim emission, and "
         "predict whether per-class+F0 can plausibly take 44% past 60 AND pull the synth into the within-speaker band, or "
         "whether the global warp's DISTORTION (raising absolute distance) is the tell that piper's fixed envelope can't be "
         "bent to a new identity no matter how many warp params you add. (B) ESCALATE to a zero-shot cloning TTS (accept the "
         "install) -- it reaches arbitrary identities by construction (reference-encoder conditioning), which is what BOTH "
         "retrieval AND warp-VC failed to do; 'piper is the start' got us the phonetics + the validated rig, and that's the "
         "honest handoff point. Be brutal: is INDISTINGUISHABLE reachable by bending piper on a CPU DSP rig, or is a cloning "
         "TTS the only thing that reaches an arbitrary identity -- and if (B), the minimal install + the same FFT-compare bar.")
    a = ask(q)
    print("\n[RULE + DECIDE]\n" + (a or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
