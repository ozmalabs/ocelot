# iter-44 — INTERPOLATION SUB-NODES (model the token cloud as a manifold)

> The user's insight: "noise is just signal you don't understand; the graph needs
> interpolation sub-nodes." The per-word token cloud (per-speaker + coarticulation
> variation) carries continuous structure. Both reflexes fail on it:
> centroid-AVERAGING (iter-41) HURT (−0.122 FSDD — the cloud IS signal); SHARPENING
> the axis (iter-43 all-pole) was REDUNDANT (drop-it ~+0.00 — resolution isn't the
> wall). The fix is to MODEL the variation: an interpolation sub-node that captures
> the continuous structure BETWEEN the discrete exemplars, so the variation becomes a
> readable COORDINATE (signal), not noise. Working tree only — NOT committed.

---

## (1) What was built — audited

**The manifold model named.** `domains/interpolation_subnodes.py` models each
candidate word's token cloud as a **low-rank AFFINE MANIFOLD**: the cloud centroid
plus the top-`r` principal directions of the centered cloud (closed-form thin-SVD of
the centered cloud matrix). This is the continuous structure BETWEEN the discrete
exemplars — the VTL continuum + the coarticulation continuum the iter-41/iter-43 task
named. A heard token is recognised by **WHERE IT INTERPOLATES** within each word's
manifold: its **reconstruction residual** to the manifold's affine span (the part of
the token the cloud's own directions CANNOT explain), softmaxed by the channel's own
median via the identical `likelihood_from_distances` every channel uses.

The three readings of the SAME token cloud, made explicit:

| read | distance | what it does to the spread |
|---|---|---|
| 1-NN (current) | to the NEAREST raw exemplar | IGNORES the cloud structure |
| centroid (iter-41) | to the cloud's MEAN point | AVERAGES the spread away (HURT) |
| **manifold (iter-44)** | to the cloud's affine SPAN | **MODELS the spread** |

**Key functions:**
- `word_manifold(tokens, rank)` — one word's affine manifold: `centre` (cloud mean) +
  `basis` (top-r orthonormal principal directions, `Vt[:r]` from `np.linalg.svd` of the
  centered cloud) + `scale` (per-direction spread, `S[:r]/sqrt(m-1)`). The effective
  rank is capped at `n_tokens-1` (an affine span of m points has dimension ≤ m−1), so a
  1-exemplar cloud degenerates to a point (= the centroid) and only interpolates where
  the cloud supports it.
- `word_manifolds(train_vecs, train_words, rank)` — per-word manifold from each word's
  TRAIN token cloud (LOSO enforced by the caller).
- `manifold_residual(query, manifold, ridge)` — the interpolated fit = the
  orthogonal-projection residual of the centered query onto the manifold span. The
  in-plane coefficients `basis @ centered` ARE the recovered variation coordinate
  (speaker/coarticulation position); `ridge>0` soft-bounds them to the cloud's own
  observed spread (interpolation, not unbounded extrapolation).
- `manifold_channel_likelihood(query, manifolds, cands, ridge)` — drop-in replacement
  for `channel_likelihood` / `centroid_channel_likelihood`: same `{word: likelihood}`
  shape, softmax-by-own-median, slots into the variadic product unchanged.

**Wiring** (`scripts/iter44_interpolation_subnodes.py`): `heldout_combined_manifold`
is `EH.heldout_combined` with one change — each cosine vector channel's per-candidate
likelihood now comes from the manifold reconstruction residual instead of raw-token
1-NN. The recognition **decision Term is byte-identical** (same variadic
`Argmax`-of-`Times` product, same softmax). The harness also reports the interpolation
sub-node as ONE MORE node ADDED to the existing 1-NN graph (the drop-it contribution),
so "interpolation as a new sub-node feeding combine-all" is measured directly.

**NO-DONKEY / NO-FIT audit (machine-checked, PASS):** the executable code (docstrings
stripped via AST) contains NONE of `fit(`, `backward`, `gradient`, `optimizer`, `nn.`,
`torch`, `sklearn`, `.train(`, `grad`, `loss`; it DOES use `np.linalg.svd` (closed-form
geometry) and the shared `likelihood_from_distances`. The manifold is an
eigen-decomposition of a group's own scatter — the same linear-algebra family as the
agent's owned `_autocorr`/`_levinson` and `canonical_log_centroid`. NO trained
classifier, NO gradient, NO learned weight, NO net. The rank `r` is a fixed small cap
(bounded by cloud size), NOT swept.

## (2) Smoke / synthetic validation (alignment + wiring)

Synthetic contrast — two words sharing the SAME centroid but with ORTHOGONAL cloud
orientations (a pure manifold-direction difference), held-out tokens new points along
each word's direction:

| read | accuracy |
|---|---|
| 1-NN | 1.00 |
| centroid | 0.50 (same centroid → chance) |
| **manifold** | **1.00** |

Confirms the mechanism: where the cloud's STRUCTURE (orientation) carries the word
identity, the centroid (a point) collapses to chance while the manifold recovers it.

## (3) The cross-speaker multi-metric — FSDD LOSO, 6 speakers, with shuffle

_(filled from complete runs — see /tmp/iter44_fsdd_full.txt)_

_pending complete run_

## (4) VERDICT

_pending complete runs — under-claimed, multi-metric, shuffle-controlled, no-fit._

## Files
- `domains/interpolation_subnodes.py` — the affine-manifold interpolation sub-node (no-fit).
- `scripts/iter44_interpolation_subnodes.py` — the FSDD LOSO acceptance harness.
- `docs/agent_loop_iteration44_interpolation_subnodes.md` — this report.

## Reproduce
```
PYTHONUNBUFFERED=1 python -m scripts.iter44_interpolation_subnodes 6 2 3   # n_per rounds rank
```
Required suites green (32): `python -m pytest tests/test_stt_pipeline.py
tests/test_perception_self_assessment.py tests/test_process_meta_assessor.py
tests/test_gap_guidance.py -q`.
