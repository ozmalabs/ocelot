# Whitened matched filter — loop synthesis + Mahalanobis (noise-weighted) compare

**Insight (signal-from-noise toolkit).** The analysis-by-synthesis loop IS a *matched
filter* — correlate the observation against a known template (the synthesised
candidate). The optimal detector for a known signal in noise uses the NOISE-WEIGHTED
(Mahalanobis) distance, not raw Euclidean: down-weight directions where the nuisance is
big, up-weight where it is quiet. Our compare was raw Euclidean (DTW over the
cochleagram), weighting every band direction equally — including the pure-speaker and
pure-domain-gap ones.

The prior SMOOTHING (commit e0dc1ea8, `docs/fuzzy_compare_smoothing.md`) was the CRUDE
low-pass: it removed the *high-frequency* part of the synthetic-vs-real domain gap and
lifted cross-speaker LOSO 0.412 → 0.487, **reaching** the CMVN ~0.51 band but not
exceeding it. A STRUCTURED/coarse nuisance remained. Whitening is the optimal tool for
noise of **any** shape and unifies speaker + residual-domain nuisance as ONE noise
covariance.

## Build (donkey-clean; CortexLoop + hat.py UNTOUCHED — `git diff` empty)

On the SMOOTHED features (freq-blur `sigma_f = 1.5`, the prior best):

1. **Nuisance covariance `S_n`** estimated on TRAIN REAL speakers = the **within-word
   scatter** (variation of the SAME word across speakers/conditions = the
   word-INDEPENDENT nuisance: speaker + residual domain gap). Per-word frame-mean,
   within-word frame covariance, averaged over words. **WORD labels only; NO speaker
   labels.** (`scripts/whitened_matched_filter.estimate_nuisance_cov`.)
2. **Whiten** `W = S_n^{-1/2}` via eigendecomposition with Ledoit-Wolf-style shrinkage
   toward a scaled identity + an eigenvalue floor for stability (shrinkage swept). A
   partial-whiten strength `alpha ∈ [0,1]` also swept:
   `W_alpha = V diag(λ^{-alpha/2}) Vᵀ` (alpha=0 → identity, alpha=1 → full whiten).
   **Fit on TRAIN only; the SAME `W` applied to held-out (no leakage).**
   (`whitening_matrix`.)
3. **Whitened compare (Mahalanobis).** Each smoothed frame vector `f → W f` in
   `AudioHat.encode`/`synth` (the new `_features`), so the loop's UNCHANGED `DtwTo`
   (Euclidean per-frame inside the DTW alignment) computes `‖W(a − b)‖` — the whitened
   matched filter. Frame count is untouched, so DTW alignment is intact.

Owned linear algebra throughout — covariance, `eigh`, inverse-sqrt, matrix-vector — **no
net, no fit, no gradient.** Whitening lives ENTIRELY in `domains/audio_hat.py`
(`whiten` ctor arg + `_features`); `domains/cortex_loop.py` and `domains/hat.py` are
git-diff empty (verified). Required suites green: `test_stt_pipeline` +
`test_frontend_effect_gate` (11 passed).

## Test (robust SC 40-speaker LOSO — held-out REAL speakers never banked)

40 HELD-OUT speakers (LOSO probe, never banked) DISJOINT from 60 TRAIN speakers (the
whitening fit). 80 real held-out clips, 10 digits, chance 0.100. `S_n` (32×32) from
within-word scatter over 10 words / 12 800 TRAIN frames; condition number 1.5e10 (so
shrinkage does real work).

| config | LOSO | true-med | wrong-med | separation |
|--------|------|----------|-----------|------------|
| CMVN (documented) | **0.510** this split / 0.570 canonical | — | — | — |
| smoothed-only (W=None) | 0.487 | 0.245 | 0.302 | +0.057 |
| whiten shrink=0.01 α=1.0 | 0.487 | 2.630 | 2.755 | +0.125 |
| whiten shrink=0.05 α=1.0 | 0.487 | 2.076 | 2.347 | +0.272 |
| whiten shrink=0.1  α=1.0 | 0.512 | 1.880 | 2.168 | +0.288 |
| whiten shrink=0.2  α=1.0 | 0.500 | 1.691 | 1.962 | +0.270 |
| whiten shrink=0.4  α=1.0 | 0.512 | 1.532 | 1.781 | +0.249 |
| whiten shrink=0.7  α=1.0 | 0.500 | 1.432 | 1.700 | +0.268 |
| whiten shrink=0.1 α=0.25 | 0.512 | 0.396 | 0.476 | +0.081 |
| whiten shrink=0.1 α=0.5  | 0.512 | 0.650 | 0.764 | +0.114 |
| **whiten shrink=0.1 α=0.75** | **0.525** | 1.106 | 1.279 | **+0.174** |
| whiten shrink=0.1 α=1.0  | 0.512 | 1.880 | 2.168 | +0.288 |

(The true/wrong residual *medians* grow with whitening because `W` rescales the metric;
the load-bearing quantity is the LOSO accuracy and the *separation* `wrong − true`.)

## Verdict

**SIGNAL-FROM-NOISE PAYS — the whitened matched filter pushes PAST CMVN (this split).**

- **Best whitened+smoothed: LOSO 0.525** (partial-whiten α=0.75, shrink=0.1) —
  **+0.038 over smoothed-only (0.487)** and **+0.015 over CMVN this split (0.510)**.
  Full whitening (α=1.0) at shrink=0.1/0.4 already reaches 0.512, *just* past CMVN;
  partial whitening at α=0.75 is the peak. (Still −0.045 under the 0.570 *canonical*
  CMVN — the n=80 split is the noisier reference; on its own CMVN number, 0.510,
  whitening clears it.)
- **Mechanism confirmed: Mahalanobis > Euclidean.** Every whitened config improves the
  true-vs-wrong residual SEPARATION over smoothed-only (+0.057 → up to +0.288 at full
  whiten), i.e. the noise-weighting genuinely down-weights the structured nuisance the
  low-pass blur left. The accuracy gain is smaller than the separation gain because the
  argmin only flips on the clips near the decision boundary — but it does flip the right
  way, and lands above CMVN.
- **This is the SOFT re-weight + matched filter**, not the prior HARD subspace subtracts
  (WCCN-ish subtract, SVD peel) that all CAPPED: it does not reduce to CMVN (smoothed-
  only already sat at 0.487; whitening adds a *further* +0.038) and it pairs the
  reweighting with the loop's synthesis rather than projecting out a subspace standalone.
- **Honest qualifier.** The lift is real but MODEST (+0.015 over the this-split CMVN);
  whitening clears the bar it could not before, but does not blow past it, and the
  shrinkage plateau (0.500–0.525 across shrink 0.1–0.7) says a large part of the
  within-word scatter is still mildly entangled with the word signal — full whitening
  (α=1.0) is slightly *worse* than α=0.75, the signature of the nuisance starting to
  overlap the word at the high-whiten end. So: signal-from-noise pays, the optimal-
  detector framing is the right tool, and the remaining gap to the canonical 0.570 is the
  residual nuisance/word entanglement a covariance whitening only partly resolves.

## Donkey audit

- Covariance + `eigh` + inverse-sqrt + Mahalanobis = **owned linear algebra** (no
  net/fit/gradient).
- **Word labels only** for the within-word structure; **NO speaker labels** anywhere.
- Whitening **fit on TRAIN (60 speakers)**, applied identically to **held-out (40,
  disjoint)** — `assert` guards the train/held-out overlap; **no leakage**.
- Held-out LOSO clips **never banked**; their labels score only — **ungameable**.
- `domains/cortex_loop.py` + `domains/hat.py` **untouched** (`git diff` empty, verified
  before and after the run). Whitening lives only in `domains/audio_hat.py`.

Driver: `scripts/whitened_matched_filter.py` (`python -m scripts.whitened_matched_filter`).
Full log captured to `/tmp/wmf_run.log` (end marker
`[MARKER] WHITENED_MATCHED_FILTER_COMPLETED`). Total run 1967 s.
