# Mode-grain recovery — the wrong grain was the neuron set — PRE-REG

**Block**: 318000. Build target: `domains/llm_structure_recovery.py`
(`ModeRouter`, `fit_mode_router`); measure: `scripts/llm_mode_router_measure.py`.

## Motivation

Blocks 315–317 tried to recover cheap conditional ACCESS to the FFN active set
with progressively richer routers (linear → random-feature nonlinear → trained
nonlinear). They all plateaued well short of the oracle, and — the tell —
**rank 64 performed identically to rank 256**: adding router capacity did not
help. The user's diagnosis: *"we are not understanding the structure — we need
to pull the model apart more. This is a demonstration that we're looking at the
wrong grain to recover the data."*

The hypothesis: the FFN activation over a corpus is **low-rank**. If the active
set lives in a few dozen MODES, then predicting the full 3072-dim neuron
activation is predicting in the wrong dimension — the router was fitting
3072 outputs when the target only has ~20 degrees of freedom. That would
explain the rank-insensitive plateau exactly.

## Claims (falsifiable)

**Claim 1 — the activation is low-rank (wrong-grain diagnostic).**
The per-layer FFN activation matrix over the corpus [N, ff=3072] has effective
rank (participation ratio) ≪ ff. Prediction: PR in the low tens, not hundreds.
FALSIFIED IF PR is a large fraction of ff (then neuron-set grain was fine and
the plateau is something else).

**Claim 2 — the mode grain closes the router gap.**
A router that predicts k~32 MODE COEFFICIENTS (SVD modes of the corpus
activation + ridge-regressed input→coefficients, reconstruct
`act = mean + coeffs·modes`) matches or beats the neuron-set routers of blocks
315–317, AND reaches the per-query oracle THROUGH THE SAME coactivation
retrieval path. Prediction: mode-router agreement ≥ neuron-set routers and
≥ retrieval-path oracle at matched fraction. FALSIFIED IF the mode-router does
no better than the neuron-set routers (grain was not the issue).

**Claim 3 — the bottleneck moves.**
If Claim 2 holds, the residual gap to the FULL graph is no longer in the router
but in the SELECTION/RETRIEVAL path (seed + coactivation expand). Prediction:
retrieval-path oracle (peek at true activation, select through seed+expand) is
much lower than the global keep-fraction oracle — the retrieval mechanism, not
the router, becomes the ceiling.

## Method

- Diagnostic: SVD the centred per-layer activation matrix, report participation
  ratio `PR = (Σλ)²/Σλ²` and entropy effective rank `exp(-Σ p log p)`.
- Mode router: per layer, top-k right singular vectors of the centred corpus
  activation = modes (k×ff); ridge-regress input xg → true mode coefficients
  (k, not ff); `score = mean + (Wc·x)·modes`. Pure numpy at test.
- Drops into the existing retrieval path via `seed_mode='router'`.
- Compared against random-feature nonlinear router (block 316) and linear
  router (block 315) at matched fractions, plus a per-query oracle router
  (peeks at the true held-out activation, not deployable) and the global
  keep-fraction oracle.

## Anti-faking

- Routers FIT on the 60-prompt train corpus; EVALUATED on 10 DISJOINT held-out
  prompts (agreement vs the full graph's next token). No prompt→output memory.
- The mode router is genuinely cheap: it predicts k≈32 coefficients and
  reconstructs, `d·k + k·ff` ≪ the FFN's `2·d·ff`.
- Oracle is an explicit per-query UPPER BOUND (peeks at true activation).
- Every fraction reported including honest negatives and small-N caveats.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals untouched; models
  + venv under `/applications`, NOT committed.
