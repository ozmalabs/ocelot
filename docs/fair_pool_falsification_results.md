# Fair-Pool Falsification — results log (Step A)

Independent-review action A: settle whether the historical cross-speaker recall gap between the
from-scratch (donkey=0) encoders and a borrowed pretrained network is a **real** gap or a
**pool-size artifact**. The review noted (i) the historical numbers are pool-size-dependent and
(ii) wav2vec2's quoted 0.668 was measured at a *different* pool than the donkey=0 encoders.

## Method (decisive, fair)

- **One identical pool.** 3000 held-out dev-clean word tokens (10 in-pool speakers, 1239 distinct
  words), the *same* tokens/order for every representation.
- **One identical kernel.** The Rust guaranteed-support banded-DTW NN-recall kernel
  (`apc::nn_recall_and_dprime` / new `apc::nn_recall_detail`), same `cap_q=300`, `n_pos=600`,
  `n_neg=1800`. Bootstrap 95% CIs (B=2000) from the raw per-query hits + pos/neg distance samples.
- **Three representations, scored identically:**
  1. **APC** — earned self-supervised context-predictive encoder (concat-lift BIDIR), donkey=0.
  2. **REF MetricEncoder** — from-scratch numpy triplet encoder, donkey=0 (~0.245-class).
  3. **wav2vec2** — pretrained `WAV2VEC2_BASE`, layers {6,9,12}, per-utt CMN + unsupervised
     PCA→64, **isolated torch subprocess, eval-only** (NOT donkey=0). Best layer reported.
- Harness: `scripts/apc_fair_pool_falsification.py`. Rust tweak: `apc_recall_detail` (returns raw
  per-query hits + pos/neg distances for bootstrapping) in `apc.rs` + `py.rs`.

## Results (held-out dev-clean, TE_CAP=3000, cap_q=300, boot=2000)

| representation | dim | NN-recall [95% CI] | ROC-AUC [95% CI] | d' [95% CI] |
|---|---|---|---|---|
| APC (donkey=0) | 192 | **0.270** [0.220, 0.320] | 0.763 [0.741, 0.785] | 0.98 [0.87, 1.09] |
| REF MetricEncoder (donkey=0) | 24 | 0.230 [0.183, 0.280] | 0.642 [0.617, 0.667] | 0.51 [0.42, 0.61] |
| wav2vec2 **L6** (eval-only) | 64 | **0.817** [0.773, 0.857] | 0.986 [0.981, 0.990] | 3.25 [3.10, 3.42] |
| wav2vec2 L9 (eval-only) | 64 | 0.807 [0.760, 0.853] | 0.985 [0.979, 0.990] | 3.46 [3.25, 3.68] |
| wav2vec2 L12 (eval-only) | 64 | 0.463 [0.410, 0.517] | 0.794 [0.773, 0.814] | 1.16 [1.06, 1.27] |

donkey=0 at inference: torch/torchaudio NOT in the analysis process. Peak RSS 1.73 GiB.

## Decision

**wav2vec2 DOMINATES at the fair pool — the gap is REAL.** Best wav2vec2 (L6) recall
0.817 [0.773, 0.857] vs best donkey=0 (APC) 0.270 [0.220, 0.320]: the 95% CIs do **not**
overlap; gap = **+0.547**. This is *larger* than the historical 0.668 (mid-layer + fair pool),
so the gap was **not** an artifact of an inflated pool — if anything it was previously understated.

Internal sanity: the last wav2vec2 layer (L12) scores far lower (0.463) than the mid layers
(L6/L9 ~0.81) — the expected wav2vec2 phonetic-content-in-mid-layers signature, and evidence the
high scores are not a leakage bug (a leak would lift all layers equally).

**Consequence for the arc:** the note's claim that frame-level word recognition has a *hard
information ceiling that even a borrowed nonlinear network cannot lift* is **falsified** on
cross-speaker recall. There is large representational headroom (~0.27 → ~0.82) that a learned
context-predictive/contrastive frame model captures. This licenses the Step-C representation-gap
build (matched-compute APC variants aiming to close ≥50% of the fair gap from ~0.27 toward ~0.82).
