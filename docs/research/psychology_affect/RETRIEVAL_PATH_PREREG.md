# Retrieval path — the ceiling was one neuron set per sequence — PRE-REG

**Block**: 319000. Build target: `domains/llm_structure_recovery.py`
(`_ffn_io_all`, `mode_retrieve_per_position`, per-position `order2_shape` branch
in the forward pass); measure: `scripts/llm_retrieval_path_measure.py`.

## Motivation

Block 318 fixed the router GRAIN: the mode-grain router (k~32 SVD coefficients)
caught the per-query retrieval-oracle, and the residual gap to identical
outcomes moved into the RETRIEVAL/SELECTION path — the retrieval-oracle sat at
2/1/0 while the global keep-fraction oracle reached 8/5/4. This block asks WHY
the retrieval path caps so low and fixes it.

The suspect: `order2_shape` applies ONE neuron set to ALL token positions in a
sequence, and `coactivation_retrieve` derives that set from the LAST token only.
But the FFN's active set is a per-TOKEN object — the neurons that fire at
position 3 differ from those at the final position. A single fixed set across
the sequence starves the earlier positions of the neurons they need.

## Claims (falsifiable)

**Claim 1 — the ceiling is fixed-set-across-positions (H1).**
Applying even the TRUE last-token active set as ONE fixed order2 set across the
whole sequence agrees far less than per-token selection at the same fraction.
Prediction: TRUE-fixed order2 ≈ 2/1/0 at frac 0.5/0.4/0.3, while per-token
keep-frac ≈ 8/5/4. FALSIFIED IF a perfect fixed set already matches per-token
(then the ceiling is something else — seed, graph, or target budget).

**Claim 2 — per-position retrieval removes the ceiling.**
Selecting a DIFFERENT active set per token position (each position scored by the
router / oracle and top-frac kept) lifts the retrieval path to the per-token
level. Prediction: the per-position ORACLE ≈ the global keep-frac oracle
(≈ 9/6/4 vs 8/5/4). FALSIFIED IF per-position oracle stays near the fixed-set
2/1/0 (then position was not the axis).

**Claim 3 — the deployable router improves, gap becomes router quality.**
A deployable per-position mode router (no peeking) improves over the fixed-set
mode router at every fraction; the remaining gap to the now-unlocked oracle is
per-position ROUTER QUALITY (the mode router was fit on last-token activations,
so its per-position predictions are weaker than its last-token ones).
Prediction: per-position mode ≥ fixed mode at every frac, and < per-position
oracle. Reported honestly whichever way.

## Method

- H1 diagnostic: `_true_fixed_shape` builds the TRUE last-token active set as a
  fixed order2 set; compare its agreement to `ffn_keep_frac` (per-token, same
  magnitude criterion) at matched fraction.
- Fix: the forward `order2_shape` branch now accepts either a 1D fixed set
  (back-compatible) or a per-position list/2D `[T][k]`; `_ffn_io_all` exposes
  the post-attention-norm input at every position; `mode_retrieve_per_position`
  scores each position with the router and keeps that position's top-frac.
- Compared: per-position mode router (deployable), per-position oracle (peek at
  true activation per position), fixed-set mode retrieval (block 318 baseline),
  global keep-frac oracle. Matched fractions 0.5 / 0.4 / 0.3.

## Anti-faking

- Routers FIT on the 60-prompt train corpus; agreement measured on 10 DISJOINT
  held-out prompts (vs the full graph's next token). No prompt→output memory.
- Both oracles peek at the true activation (per-position and global) — explicit
  UPPER BOUNDS, not deployable — reported so a "win" cannot be the oracle in
  disguise.
- HONEST COST CAVEAT: per-position mode retrieval recomputes `xg` at all
  positions, so it is NOT cheaper than the FFN at eval. This rung proves the
  MECHANISM/grain of the selection path, not a cheapness win — reported plainly.
- Every fraction reported, including honest negatives and small-N caveats.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals untouched; models
  + venv under `/applications`, NOT committed.
