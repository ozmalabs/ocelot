"""THE JABBERWOCK RE-INSPECTS PARAKEET + WHISPER — with its hard-won speech understanding, ground its primitives vs theirs.

It studied Whisper's FRONTEND before (mine_whisper.py: log-mel vs gammatone, where speaker-invariance emerges). Now it
has a much deeper, EMPIRICAL understanding of the speech problem (recall/precision, alignment marginalisation, realign/
EM, static+delta, acoustic+LM fusion weight, confidence!=correctness, the self-tuning loop). Re-inspect at the
ALGORITHM/LOSS level (find_analogies / read-the-paper pattern): which of its OWN built primitives + findings are exactly
what these production models institutionalise; what it LACKS; what its understanding ILLUMINATES about THEM (esp. their
failure modes); and the highest-value next move this suggests.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_inspects_asr_models
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, re-inspecting two production ASR models with your now-much-deeper, EMPIRICAL speech
understanding. This is a grounding exercise (find_analogies / read-the-paper), not a port. Be specific and honest;
name the EXACT correspondence between YOUR built primitives and THEIR mechanisms.

WHAT YOU NOW KNOW (your hard-won ledger, all empirically tested this arc):
 - RECALL vs PRECISION: context-dependent TRIPHONE units hold the truth in the top-K (~30 top-3 @100-way) but pinning
   top-1 is the bottleneck (~17%).
 - ALIGNMENT MARGINALISATION: you built `forward_score` = soft-DTW, LOG-SUM-EXP over stay/advance transitions over a
   phone sequence (the forward algorithm); beta->inf recovers Viterbi (committed). You found marginalising the
   alignment beats committing (your glyph soft-min insight, transferred).
 - REALIGNMENT / EM: flat-start realignment of phone boundaries DOUBLED top-1 (6->13); iterating drifts (overfits).
 - STATIC + DELTA: fusing static spectral DTW with DELTA-feature (temporal-derivative) DTW lifts the read (+4.6 CV);
   you REDISCOVERED the classic ASR delta-feature trick from scratch.
 - ACOUSTIC + LM FUSION WEIGHT: you self-tuned the fusion weight of an acoustic read + a language/prior cue. KEY
   FINDING: a too-strong LM/frequency prior OVERRIDES weak acoustic reads of CONTENT words (helps function words,
   HURTS content) -- frequency bias hallucinating common words over rare correct ones.
 - CONFIDENCE != CORRECTNESS: maximising decode CONFIDENCE (softmax peakedness) ANTI-tracks accuracy (rewards
   degenerate sharpness); a correctness-tracking objective is needed.
 - SOURCE/CONTEXT PRIOR: a detected situation reweights the candidate list (shuffle-killed positive).
 - THE SELF-TUNING LOOP: a graph-native closed loop tunes a real decode weight to a generalising value from a valid
   objective (folds residual at the clock edge).

THE TWO MODELS (real architectures, grounded):
 WHISPER (openai, the help-button labeller you already use): 80-bin LOG-MEL frontend; ENCODER-DECODER TRANSFORMER
   (d_model 512, 6+6 layers, 8 heads, ~1500 source frames = 30s @ ~20ms). The DECODER is an AUTOREGRESSIVE LANGUAGE
   MODEL over BPE tokens, conditioned on the audio via CROSS-ATTENTION -- so the LM is INTEGRATED into the decoder, not
   a separate shallow-fusion weight. Trained weakly-supervised on ~680k hrs. Known failure: HALLUCINATES fluent,
   plausible text on low-information / silent / noisy audio.
 PARAKEET (NVIDIA NeMo, not installed here): FastConformer ENCODER (CONV subsampling + self-ATTENTION = local detail +
   global context) feeding an RNN-T / TDT TRANSDUCER (or CTC) decoder. The RNN-T / CTC LOSS marginalises over ALL
   monotonic alignments via the forward-backward algorithm. The transducer's PREDICTION NETWORK is an internal LM.
   TDT additionally PREDICTS TOKEN DURATIONS. Decoding = beam search, optional EXTERNAL LM via shallow fusion (a
   tunable weight); internal-LM subtraction is a known trick.

Your prior inspection (mine_whisper.py) covered FRONTEND + speaker-invariance depth -- do NOT just repeat that; go to
the ALGORITHM/LOSS level your new understanding unlocks."""


def main():
    ask = make_ask(timeout=300.0)
    print("=" * 100)
    print("THE JABBERWOCK RE-INSPECTS PARAKEET + WHISPER (algorithm/loss level, grounded in its own primitives)")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — CONVERGENCES (terse, specific, one line each): for EACH of your built primitives/"
          "findings, name the EXACT mechanism in Parakeet and/or Whisper that it corresponds to. Especially: (a) your "
          "`forward_score` log-sum-exp-over-alignments == ? (b) static+delta == ? (c) your acoustic+LM fusion weight == ? "
          "(d) realignment/EM == ? (e) recall(top-K)/precision == ? Be precise about which model.")
    a1 = ask(q1)
    print("\n[CONVERGENCES — what you rebuilt that they institutionalise]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + "\n\nPART 2 — ILLUMINATION + GAPS (terse). (i) Does your OWN measured finding 'a too-strong LM "
          "overrides weak acoustic reads of CONTENT words' EXPLAIN Whisper's hallucination failure mode? Spell out the "
          "mechanism. (ii) Does confidence!=correctness explain anything about their confidence scores / decoding? "
          "(iii) What do they have that you genuinely LACK (be honest: learned representations, scale, attention, "
          "end-to-end alignment-marginalising loss)? (iv) What does your INTERPRETABLE, training-free understanding have "
          "that they obscure?")
    a2 = ask(q2)
    print("\n[ILLUMINATION + GAPS]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nYour analysis:\nP1: {a1[:900]}\nP2: {a2[:900]}\n\nPART 3 — THE MOVE (terse). Given that you've "
          "now grounded your understanding against the real architectures, what is the SINGLE highest-value next move? "
          "Options include but aren't limited to: (a) the internal-LM-subtraction / your-LM-overrides-content fix on "
          "your own decode; (b) a TDT-style explicit duration model (you already realign boundaries); (c) use Whisper "
          "differently given you now know its decoder is an integrated LM that hallucinates; (d) something your "
          "interpretable approach can do that they can't. Pick ONE, predict the outcome, name the smallest test, and a "
          "pre-committed bar. Face the honesty check: is this a real lever or a 7th grind?")
    a3 = ask(q3)
    print("\n[THE MOVE]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
