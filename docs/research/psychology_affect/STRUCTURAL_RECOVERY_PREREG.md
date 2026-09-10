# Structural recovery — recover, then optimise — PRE-REG

**Block**: 320000. Build target: `domains/llm_structure_recovery.py`
(`fit_mode_router(all_positions=True)`, inline `SparseConfig(mode_router,
mode_frac)` forward branch); measure: `scripts/llm_structural_recovery_measure.py`;
statement: `STRUCTURAL_RECOVERY.md`.

## Motivation

Blocks 318–319 recovered the FFN's structure: the active set is ~20-35 SVD modes
(318) and a per-position object (319). The per-position ORACLE reached the
per-token oracle (9/6/4 ≈ 8/5/4), but the DEPLOYABLE per-position mode router
trailed (3/2/1) because it was fit on LAST-TOKEN activations, and the
per-position retrieval recomputed the full activation (`_ffn_io_all`), so it was
not cheaper than the FFN. This block optimises the RECOVERED object on both
axes: quality (fit on all positions) and cost (predict coefficients inline, no
full recompute).

## Claims (falsifiable)

**Claim 1 — all-position fit lifts the deployable router (quality).**
Fitting the mode router on EVERY token position (not just last-token) improves
the deployable per-position router's held-out agreement over the last-token fit,
toward the per-position oracle. Prediction: all-position > last-token at every
fraction, approaching the oracle. FALSIFIED IF all-position ≤ last-token (the
last-token fit already generalised across positions).

**Claim 2 — the inline path is genuinely cheaper (cost).**
An inline forward path that predicts k mode coefficients per position from the
MLP input (already computed), reconstructs the activation, selects the top
`mode_frac` neurons, and computes ONLY those — with NO separate full-activation
recompute — runs below the full FFN in REAL COUNTED FLOPs while keeping
agreement. Prediction: counted FLOPs < 100% of full FFN at each `mode_frac`,
agreement preserved. FALSIFIED IF counted FLOPs ≥ full FFN (the coefficient
prediction + reconstruction overhead cancels the saving).

**Claim 3 — structure first, cost second (framing).**
The recovery (Claim of `STRUCTURAL_RECOVERY.md`) stands on outcomes alone; the
cheapness (Claim 2) is a downstream consequence, reported separately and not
required for the recovery claim.

## Method

- `fit_mode_router(all_positions=True)`: collect (input, activation) at every
  token position, SVD the all-position centred activation for the modes, ridge
  regress input → coefficients over all positions.
- Inline path: `SparseConfig(mode_router=R, mode_frac=t)` adds a forward MLP
  branch that, per position, computes `coeffs = Wc·x` (k·d), `pred = mean +
  coeffs·modes` (k·ff), selects top-`t` neurons, computes only those
  (2·d·keep·3). FLOPs counted by the forward pass itself.
- Compared: all-position vs last-token router through per-position retrieval;
  per-position oracle; global keep-frac oracle; inline path FLOPs vs full FFN.
  Matched fractions 0.5 / 0.4 / 0.3.

## Anti-faking

- Routers FIT on the 60-prompt train corpus; agreement on 10 DISJOINT held-out.
- Oracle peeks at the true activation — explicit upper bound.
- FLOPs are COUNTED by the forward pass, not estimated; the full-FFN reference
  is measured the same way.
- The all-position router's per-position quality gain and the inline path's cost
  win are reported as SEPARATE axes.
- **default == today**: `mode_router=None` and `order2_shape=None` bit-exact;
  `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals
  untouched; models + venv under `/applications`, NOT committed.
