"""THE JABBERWOCK RULES THE SYNTHESIS KILL + PICKS THE PATH — piper-by-retrieval is dead; piper is still 'the start'.

Phase 0 (borrow-piper-by-retrieval + prosody, FFT-compare vs the real held-out speaker) KILLED, and the diagnostic CONFIRMS
it cleanly: the FFT metric IS speaker-discriminative (76% on real same-word pairs, not content-dominated), the synth-vs-real
DOMAIN gap is modest (1.65x, not swamping), yet the synth verifies only ~40% -- so it is the MAPPING: piper's discrete voice
grid (even VCTK's 109) cannot reach an arbitrary LibriSpeech identity by RETRIEVAL. (The ear arc inverted: wav2vec2's
representation generalised across speakers because it was trained speaker-invariant; piper's generation is a fixed set of
trained voices that does NOT generalise to a new identity.)

THE CREATOR'S FRAME: "piper is the start" / "piper extraction, using the same methods as the ear" -> build ON piper (borrow
+ ADAPT), not replace it. The ear's method = borrow a pretrained net + adapt toward the target. The synthesis analog of
'adapt' is VOICE CONVERSION: piper gives content-correct phonetics (wrong voice); map its output toward the TARGET speaker's
spectral envelope + prosody, learned from the target's own recordings.

THE RELEVANT PRIOR (weigh it): the source-filter / spectral-envelope approach was KILLED for the EAR (recognition) -- too
lossy to CARRY content for INVERSION. But SYNTHESIS is a different regime: there is NO inversion search; piper already
carries the content, and we only RE-SHAPE the spectrum/prosody toward the target -- a forgiving direction the recognition
kill may not bind. Available on the CPU rig: piper, WavLM, F0 (detect_pitch_frequency), the validated FFT-compare metric +
within/between-speaker rig. NOT on the rig: a zero-shot cloning TTS (XTTS/YourTTS/Bark) -- would need a Coqui/transformers install."""
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
    print("THE JABBERWOCK RULES THE SYNTHESIS KILL + PICKS THE PATH")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — RULE + PICK THE PATH (terse, decisive): accept the retrieval KILL. Then pick: (A) VOICE "
          "CONVERSION on piper -- keep piper as the 'start' (content), learn a map from piper's output spectral envelope to "
          "the TARGET speaker's (from their recordings) + transplant their prosody/F0, then FFT-compare; the 'same methods as "
          "the ear' adapt-the-borrow shape, all on the CPU rig. (B) install a zero-shot CLONING TTS (XTTS/YourTTS, x-vector/"
          "reference-encoder conditioned) -- SOTA, reaches arbitrary identities, but a new dependency and not 'piper is the "
          "start'. (C) fine-tune piper-VITS on the target (hard via onnx). Which, and WHY -- and does the EAR's source-filter "
          "KILL bind synthesis-VC (no inversion, content already carried), or is re-shaping the spectrum toward a target a "
          "genuinely different, more forgiving regime?")
    a1 = ask(q1)
    print("\n[PART 1 — RULE + PATH]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour path:\n{(a1 or '')[:1100]}\n\nPART 2 — THE NEXT FAIL-FAST + BAR (terse): if (A) VC -- the "
          "cheapest decisive test that voice-conversion on piper's output gets the synth FFT-CLOSER to the TARGET than "
          "retrieval did. What's the VC map (a per-speaker spectral-envelope / formant-warp from piper->target learned from "
          "the target's recordings; how prosody rides along), measured on the SAME held-out FFT-compare rig, PRE-COMMITTED "
          "bar (KEEP if FFT-verify >= 60% AND within reach of the real within-speaker band; KILL if it can't beat the 40% "
          "retrieval floor -> piper is too rigid, go to (B)). If (B)/(C) -- the minimal build + its bar. Pre-register your "
          "prediction. Bind the runs; don't grind.")
    a2 = ask(q2)
    print("\n[PART 2 — NEXT FAIL-FAST + BAR]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
