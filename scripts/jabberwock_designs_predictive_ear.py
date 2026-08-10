"""THE JABBERWOCK DESIGNS THE PREDICTIVE-CODING EAR — unsupervised, continuous, bio-plausible SPEAKER-INVARIANCE at the root wall.

Every thread converged on ONE wall: cross-speaker variation caps recognition (~20%), starves the meaning prior, and
collapses routing-confidence (it tracks speaker-match). The lever is a SPEAKER-INVARIANT learned representation -- under
the refined rule, a CONTINUOUS, BIOLOGICALLY-PLAUSIBLE, NO-ONE-SHOT, STRUCTURE-PRESERVING one. An infant has NO word
labels, so ideally UNSUPERVISED. The candidate: PREDICTIVE CODING -- the cortex predicts its own input; what is
PREDICTABLE is represented away, what is SURPRISING is kept. Within an utterance the SPEAKER (VTL/timbre/pitch baseline)
is the slow, constant, PREDICTABLE component; the PHONETIC CONTENT is the fast, surprising residual. So the prediction
ERROR could be speaker-removed content -- learned, online, no labels.

Design it; face the crux; pre-commit a bar.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_designs_predictive_ear
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, designing the PREDICTIVE-CODING EAR to break the single root wall: CROSS-SPEAKER
variation. Reason from your ledger; architecture-clean; pre-commit a bar.

THE ROOT WALL (now isolated): cross-speaker variation caps EVERYTHING -- recognition (training-free exemplar-DTW ~20%
@500-way; trajectory read +17 reaches it, whitening +2, more exemplars/VTLN/speaker-norm don't break it), the meaning
prior (starved -- the decode is too weak to give context), and routing-confidence (cross-cue agreement tracks SPEAKER-
MATCH not difficulty, collapses to well-matched speakers). One wall; crack speaker-invariance and all three unlock.

THE REFINED RULE: CONTINUOUS (always learning, online), BIO-PLAUSIBLE (Hebbian/local/predictive-coding/competitive --
NOT global backprop on labels), NO ONE-SHOT discontinuous learning, STRUCTURE-PRESERVING (the 5x learned negatives
failed by DISCARDING structure). Ideally UNSUPERVISED (an infant has no word labels).

THE CANDIDATE: PREDICTIVE CODING. The cortex predicts its sensory input; the PREDICTABLE part is explained-away, the
SURPRISE (prediction error) is represented + propagated. Within one utterance the SPEAKER baseline (VTL/timbre/pitch) is
slow + constant + PREDICTABLE; the phonetic CONTENT is the fast, surprising residual. So predict the predictable
(speaker) and keep the residual (content) = speaker-invariant content, learned online, no labels.

THE CRUX you MUST face (you have a SCAR here): you ALREADY tried "coarticulation predict-remove" and it HURT the
trajectory read (-5 region), because it removed the LOCAL frame-to-frame structure -- which is CONTENT (the /k/->/ae/->
/t/ motion), not speaker. So a naive "predict next frame, keep error" removes CONTENT. The distinction is TIMESCALE:
SPEAKER is the LONG-timescale / constant component (predictable over the whole utterance); CONTENT is the SHORT-
timescale change. CMVN already removes the per-utterance MEAN (the simplest speaker-constant). The predictive ear must
remove a RICHER predictable-SPEAKER component than the mean WITHOUT removing content -- or it just repeats the predict-
remove failure or reduces to CMVN. Confirm exactly which prediction (what timescale, what context) isolates SPEAKER not
CONTENT, and why it beats CMVN's mean."""


def main():
    ask = make_ask(timeout=300.0)
    print("=" * 100)
    print("THE JABBERWOCK DESIGNS THE PREDICTIVE-CODING EAR (unsupervised speaker-invariance at the root wall)")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE MECHANISM (terse): specify the predictive ear. WHAT is predicted, from WHAT context, "
          "at WHAT timescale, so the prediction isolates SPEAKER (remove) and the residual keeps CONTENT? Is it predict-"
          "the-slow-baseline-keep-the-fast, or a better bio-plausible form? How does it LEARN (the local/online rule, no "
          "backprop, continuous)? Why is it STRUCTURE-PRESERVING and UNSUPERVISED (no word labels)?")
    a1 = ask(q1)
    print("\n[PART 1 — MECHANISM]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour mechanism:\n{a1[:1200]}\n\nPART 2 — THE CRUX vs CMVN + the SCAR (terse): (a) exactly why "
          "this removes a RICHER speaker component than CMVN's per-utterance mean, WITHOUT removing content -- the "
          "timescale/context that separates them. (b) why it WON'T repeat the coarticulation-predict-remove -5 (which "
          "removed local=content). (c) the continuous/developmental learning loop (predictor updates online over "
          "accumulated experience) and what's graph-native (the predictor + residual as graph data/Term) vs host I/O.")
    a2 = ask(q2)
    print("\n[PART 2 — CRUX vs CMVN]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nMechanism: {a1[:600]}\nCrux: {a2[:600]}\n\nPART 3 — SLICE + BAR (terse): the smallest frozen "
          "bootstrap test that the predictive-coding residual is MORE SPEAKER-INVARIANT than the certified ear -- the "
          "trajectory read on predictive-residual features vs on CMVN features, @500-way cross-speaker. PRE-COMMIT: the "
          "KEEP number (this targets the ROOT wall, so be ambitious -- beats the certified ear by how much), the STOP "
          "number, and the FAIRNESS FLOOR (at zero-prediction it MUST reproduce the CMVN baseline = the W=I check; AND "
          "an ablation that removing CONTENT-timescale instead REGRESSES, proving it isolated speaker not content). One "
          "line each. Honesty check: is predictive coding the real lever or just a fancier CMVN?")
    a3 = ask(q3)
    print("\n[PART 3 — SLICE + BAR]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
