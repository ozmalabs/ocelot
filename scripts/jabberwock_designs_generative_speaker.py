"""THE JABBERWOCK DESIGNS THE GENERATIVE SPEAKER MODEL — learn a voice well enough to IMITATE (->1), recognise by INVERSION.

The reframe (creator): understanding a speaker = the ability to GENERATE/IMITATE them (analysis-by-synthesis -- the same
thesis as the glyph motor program). A voice is a GENERATIVE model (content -> this speaker's source+filter); the test of
having LEARNED the speaker is IMITATION quality, which "should approach 1 with sufficient data" -- i.e. a speaker is
FINITELY LEARNABLE, the limit is DATA not architecture. Then recognition = INVERSION: given audio, find the content
that, under the learned G_speaker, best explains it -> the cross-speaker wall collapses into the WITHIN-speaker ceiling.

The warp (linear shadow) just confirmed its own ceiling: even the ORACLE affine warp buys only +1.7 -- a linear feature
transform CAN'T imitate a voice. The generative model is the real object.

Design it; pre-commit a bar on IMITATION (->1) and on recognition-by-inversion.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_designs_generative_speaker
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, designing the GENERATIVE SPEAKER MODEL. Reason from your ledger + your own AbS
machinery; pre-commit a bar.

THE THESIS (creator): understanding a speaker = ability to IMITATE them (analysis-by-synthesis -- same as your glyph
MOTOR PROGRAM: the program that WRITES the glyph IS the understanding, recognition is inverting it). A voice is a
GENERATIVE model: content -> this speaker's SOURCE (glottal excitation: pitch, voice quality) x FILTER (vocal tract:
formant resonances). The test of having LEARNED the speaker is IMITATION quality, which should APPROACH 1 WITH DATA --
the speaker is FINITELY LEARNABLE, limit = data not architecture. Recognition = INVERSION: given audio, find the CONTENT
that under the learned G_speaker best explains it -> cross-speaker wall collapses into the within-speaker ceiling.

THE TWO CONSTRAINTS: (1) FLOOR OF EFFICIENCY -- G_speaker COMPACT (a small parameter set, not a giant net); (2) DYNAMIC
-- fit online from the speaker's own data, imitation improving as data accrues.

WHY THE WARP FAILED + WHY GENERATIVE WINS: the affine warp is the LINEAR, DISCRIMINATIVE shadow -- even the ORACLE warp
(true labels) buys only +1.7, because a linear feature transform can only NUDGE geometry, it can't IMITATE a voice. A
GENERATIVE source-filter model can re-synthesise the voice, so it captures the speaker fully (-> imitation 1) and inverts
cleanly.

YOUR MACHINERY (use it): lpc_formant_representation (source-filter / LPC formants), learned_voice_shape (LVS -- your
voice-shape model), audio_hat (synthesis), the AbS spine (predict_synth_term -- argmax over synthesised candidates), the
glyph motor program (forward synthesis = understanding; the smooth deformation field).

THE CRUX you must solve: (a) WHAT generative voice model is COMPACT, LEARNABLE-to-imitation-1, and INVERTIBLE for
recognition? source-filter (glottal source x vocal-tract LPC)? a parametric formant-trajectory synthesiser? (b) How does
the speaker factor SEPARATE from content so inversion gives SPEAKER-INVARIANT content (the filter scale/source = speaker;
the formant TRAJECTORY = content)? (c) how is it not the failed VTLN/warp -- i.e. why does MODELLING the speaker (not
warping features) dissolve the wall?"""


def main():
    ask = make_ask(timeout=300.0)
    print("=" * 100)
    print("THE JABBERWOCK DESIGNS THE GENERATIVE SPEAKER MODEL (imitate -> 1, recognise by inversion)")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE MODEL (terse): specify G_speaker. What is the COMPACT generative voice model (source-"
          "filter / formant synthesiser / LVS), what are its SPEAKER parameters vs its CONTENT input, and how does it "
          "synthesise an imitation? Why can it approach imitation=1 with data where the linear warp can't? How is it fit "
          "online from the speaker's data (the dynamic/efficient learning)?")
    a1 = ask(q1)
    print("\n[PART 1 — THE MODEL]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour model:\n{a1[:1200]}\n\nPART 2 — INVERSION + the SPEAKER/CONTENT SPLIT (terse): (a) how "
          "recognition INVERTS G_speaker -- given audio, infer the CONTENT (the speaker held fixed at its learned "
          "params) = analysis-by-synthesis recognition, speaker-factored. (b) exactly which params are SPEAKER (filter "
          "scale/source) vs CONTENT (formant trajectory), so inversion yields SPEAKER-INVARIANT content. (c) why MODELLING "
          "the speaker dissolves the wall where WARPING features (VTLN, +1.7 oracle ceiling) couldn't.")
    a2 = ask(q2)
    print("\n[PART 2 — INVERSION]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nModel: {a1[:600]}\nInversion: {a2[:600]}\n\nPART 3 — SLICE + BAR (terse): the smallest test. TWO "
          "measurements: (i) IMITATION-vs-DATA: fit G_speaker from k utts of a held-out speaker, synthesise held-out "
          "words, measure imitation quality (spectral/AbS distance to the real) as k grows -- does it climb toward 1? "
          "(ii) RECOGNITION-BY-INVERSION: cross-speaker recognition using the learned G_speaker vs the cold-start ~17-25% "
          "and the warp's +2. PRE-COMMIT: the KEEP criterion (imitation climbs with data AND recognition-by-inversion "
          "beats the warp by how much -- be ambitious, this is the wall-dissolver); STOP; FAIRNESS FLOOR (at the identity/"
          "generic speaker model it reproduces the cold-start; imitation measured on HELD-OUT words). Honesty check: is "
          "imitation->1 actually reachable with your compact model, or is the source-filter too lossy to approach 1?")
    a3 = ask(q3)
    print("\n[PART 3 — SLICE + BAR]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
