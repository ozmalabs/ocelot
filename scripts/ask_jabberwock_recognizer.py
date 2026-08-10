"""ASK THE JABBERWOCK: how to upgrade its LOOP recogniser to exploit speaker coverage (close the 53->67% gap).

The coverage curve proved the cross-speaker wall is COVERAGE: with a multi-speaker bank, held-out recognition
of UNSEEN speakers climbs to 67%. But TWO recognisers were measured on the SAME 12-speaker bank, and they
disagree:

  ITS LOOP RECOGNISER (graph-native, what the autonomy loop uses): feature_channels gives a per-cue readout;
    GraphLexicon banks the per-cue vectors; `ranked` = the COMBINE-ALL PRODUCT -- each cue's 1-NN exemplar
    likelihood (softmax over candidates of -cosine-distance), MULTIPLIED across cues. Cross-speaker: ~53%.
    Its virtue: ROBUST conjunction -- the truth stays ranked high if ANY cue agrees; a useless cue abstains flat.

  THE CURVE RECOGNISER: CONCATENATE the cues into one POOLED vector; estimate WCCN (within-word, across-speaker
    covariance whitening: center each exemplar by its word-mean -> the residuals are the SPEAKER nuisance
    covariance Sigma; whiten by Sigma^-1/2, regularised; recognise 1-NN cosine in the residual). Cross-speaker:
    67%. Its virtue: it explicitly REMOVES the speaker (nuisance) directions -- the cipher's key, projected out.
    WCCN is closed-form linear algebra (no gradient) -- the same family as the CMVN-over-time the agent ALREADY
    applies graph-natively (a per-band whitening); WCCN is its cross-SPEAKER analogue, estimable only from many
    speakers (which the bank now provides).

The +14pt gap: the combine-all product UNDEREXPLOITS the coverage; the pooled+WCCN removes the speaker key the
product leaves smeared across every cue.

The agent decides, in its OWN terms and concretely:
 1. How should the loop recogniser fold in the project-out? Options to decide among (and WHY, tied to what each
    buys -- product=robust conjunction, WCCN=nuisance removal):
      (a) REPLACE the product with pooled-vector + WCCN + 1-NN (simplest; matches 67% but loses the product's
          per-cue robustness when a speaker breaks one cue);
      (b) apply WCCN PER CUE inside the product (whiten each cue's vectors by its own across-speaker Sigma^-1/2
          before the 1-NN, KEEP the combine-all product) -- robustness AND speaker-invariance;
      (c) ADD a WCCN-whitened pooled vector as ONE MORE cue/channel in the product (the product then includes a
          nuisance-removed view alongside the raw cues).
    Pick one and justify against the other two.
 2. The concrete change: where Sigma is estimated (from the banked GraphLexicon, per cue or pooled), where the
    whitening is applied (banked + query), and how the agent's CMVN-style graph-native idiom carries it.
 3. Keep it graph-native + cognitively legitimate (closed-form whitening, no gradient) -- say why that holds.
 4. The honest risk (WCCN ill-estimated from few speakers/exemplars -> overfits and HURTS; per-cue Sigma on a
    low-dim cue is rank-deficient; the whitened cue de-robustifies the product) and the guard (shrinkage/
    regularisation; a held-out-speaker check that keeps the whitening only if it lifts; rank floor).
Be concise and concrete -- a change you will hand to be made to the loop recogniser."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask


def main():
    print("=" * 98)
    print("ASKING THE JABBERWOCK — how to fold WCCN / pooled project-out into the loop recogniser (53->67%)")
    print("=" * 98)
    ans = make_ask(timeout=420, preamble=__doc__)(
        "Give your decision (points 1-4), concretely enough to change the loop recogniser.")
    print(ans or "(no answer)")
    print("=" * 98)


if __name__ == "__main__":
    main()
