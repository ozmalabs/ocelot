"""THE JABBERWOCK DESIGNS THE SPEECH SYNTHESIS SYSTEM — emit speech functionally indistinguishable from a MAPPED real speaker.

The ear is done: borrow wav2vec2 (a pretrained net) as a live midpoint, nearest-exemplar match, cross-speaker recognise +
defer-and-learn, persisted. NOW THE MOUTH: develop synthesis by the SAME METHODS (borrow a pretrained generator = PIPER, the
borrow-as-midpoint discipline, fail-fast + pre-committed bars), map a REAL speaker, and emit held-out words in that speaker's
voice — tested vs the SAME real speaker's held-out recordings. Goal: functionally INDISTINGUISHABLE-to-humans speech from a
mapped speaker. It must carry PROSODY (intonation, rhythm, stress, F0 contour), not merely the speaker timbre.

THE DEEP TENSION (confront it): the EAR was built to be speaker-INVARIANT (DISCARD the speaker, recognise the word). Cloning
is the OPPOSITE — PRESERVE the speaker. So "the same methods as the ear" transfers only the SHAPE (borrow a pretrained net +
nearest-match + adapt), NOT the invariance; the metric and the representation must be speaker-DISCRIMINATIVE, not invariant.

THE TOOLING (surveyed, available, CPU): PIPER synthesis — single-speaker voices (lessac/amy/ryan/hfc_*/kusal/...) AND
MULTI-SPEAKER models (en_GB-vctk-medium = 109 speakers, en_US-arctic = 18, aru = 12) that condition on a speaker index; full
phonemize -> phoneme_ids -> audio + pitch/rate knobs. WAVLM (torchaudio, speaker-DISCRIMINATIVE, unlike the ear's wav2vec2) =
the speaker-similarity / verification proxy (mean-pooled embedding cosine). WHISPER = content/ASR check. detect_pitch_frequency
= F0/prosody. REAL SPEAKERS = LibriSpeech (map a speaker from some recordings, test on their HELD-OUT words). NO human evals on
this rig -> the 'indistinguishable' bar must be an OBJECTIVE proxy.

THE PRIORS (do not re-walk): the GENERATIVE source-filter inversion was KILLED (too lossy); the LINEAR voice-shape template
was KILLED; cheap explicit speaker-modelling failed. Borrowing a strong pretrained NET is what worked for the ear."""
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
    print("THE JABBERWOCK DESIGNS THE SPEECH SYNTHESIS SYSTEM (borrow piper; map a real speaker; indistinguishable)")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE SYSTEM + THE 'INDISTINGUISHABLE' METRIC (terse, concrete): (a) how do you MAP a real "
          "LibriSpeech speaker onto piper — pick the NEAREST piper voice (of the ~130 incl. VCTK's 109) by WavLM speaker "
          "similarity to the target's reference audio, then adapt PROSODY (F0 mean/range + speaking rate from the target's "
          "real speech via the pitch/rate knobs), i.e. the ear's borrow+nearest-match shape? Or condition VCTK on a mapped "
          "speaker index? Be concrete about speaker AND prosody. (b) the OBJECTIVE 'indistinguishable' metric with no human "
          "evals: I propose a speaker-verification proxy — synth-of-X's WavLM embedding must be as close to real-X as real-X "
          "recordings are to EACH OTHER (within-speaker), AND closer to X than to OTHER speakers (between-speaker); plus "
          "whisper content-correct; plus F0-contour match. Refine it — what's the single decisive number, and what's the "
          "honest ceiling (piper's nearest voice is NOT the target, so equal-to-real may be unreachable without adaptation)?")
    a1 = ask(q1)
    print("\n[PART 1 — SYSTEM + METRIC]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour system:\n{(a1 or '')[:1100]}\n\nPART 2 — THE FAIL-FAST PHASE 0 + BAR (terse): the riskiest "
          "assumption the whole thing rests on, and the CHEAPEST decisive test that kills-or-confirms it WITHOUT building the "
          "full prosody/adaptation stack. Candidate: does borrow+nearest-piper-voice+prosody-match put the synth CLOSER to "
          "the target speaker than to other speakers in WavLM space (a real verification signal), with correct content — or "
          "is piper's nearest voice so far from an arbitrary LibriSpeech speaker that mapping-by-retrieval is hopeless and "
          "you NEED a speaker-adaptive / zero-shot-cloning TTS (a big build piper doesn't give you)? Specify the phase-0 "
          "measurement on the real-speaker rig + a PRE-COMMITTED bar (KEEP -> the borrow-piper path has legs, build prosody "
          "+ adaptation; KILL -> retrieval-mapping is dead, name what's actually needed). Pre-register your honest prediction: "
          "DENT (recognisably similar voice, not indistinguishable) or DISSOLVE (truly within-speaker)?")
    a2 = ask(q2)
    print("\n[PART 2 — FAIL-FAST PHASE 0 + BAR + PREDICTION]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
