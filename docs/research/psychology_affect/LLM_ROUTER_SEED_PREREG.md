# LLM learned-router seed — does a learned cheap seed close the gap? — PREREG

**Block**: 315000

**Task**: Block 314000 left the barrier at the SEED: every HAND-derived key
(gate, joint gate+up) is a better-but-imperfect ranker of which FFN memories
fire, and none closes the per-query-oracle gap. The named next step: a small
LEARNED router — not another hand-key. This tests whether a cheap learned
per-layer predictor of the active set, used as the coactivation-retrieval seed
(then graph-expanded), closes the gap on held-out queries.

## 1. The learned router

`domains/llm_structure_recovery.py`:
- `fit_router(model, corpus, ridge)` — for each layer, collect
  (post-attention-norm INPUT, FFN activation magnitude `|silu(gate·x)·(up·x)|`)
  over the TRAIN corpus and fit a ridge-regression linear map
  `W[L]: input_dim → ff` predicting the activation. A `LearnedRouter`.
- `coactivation_retrieve(..., seed_mode='router', router=R)` — seed by the
  router's predicted activation (one matmul `input · Wᵀ`, same cost class as a
  single projection), then graph-expand.

## 2. Comparison (held-out, agreement vs the full graph)

At matched neuron-fractions:
- **router+graph** — learned router seed + coactivation expansion (candidate).
- **router-only** — router seed, no expansion (isolates the router seed).
- **joint+graph** — joint gate+up key + expansion (block 314's best cheap).
- **oracle** — per-query true-activation top-k (upper bound, block 310).

## 3. Falsifiable claims

1. **`order2_shape=None` bit-exact** (default==today).
2. **Router seed is competitive**: router-* ≈ or > joint-* at matched fraction
   (a learned map should be at least as good as a hand-key).
3. **Does it close the oracle gap?** Registered hypothesis: router+graph
   approaches the oracle. May FAIL — a LINEAR map may be insufficient to
   predict the exact active set cheaply. Reported whichever way.

## 4. What each outcome means

- Router closes the gap → the cheap query→memory index exists (learnable), and
  the shape is cheaply, conditionally accessible — the full payoff.
- Router does NOT close the gap → an ESCALATED negative: even a learned (not
  hand-derived) cheap seed fails, so the barrier is not a wrong-key artifact
  but a real property — a linear input→active-set map is insufficient, and
  cheap exact active-set prediction genuinely needs the nonlinearity (≈
  computing the activation) or a fundamentally different router. Sharply bounds
  the open problem.

## 5. Anti-faking

- Router FIT on the TRAIN corpus, EVALUATED on DISJOINT held-out — not
  per-query memorisation. The router is a fixed linear map applied to the
  held-out query's input.
- The oracle peeks at the true activation — explicit per-query UPPER BOUND.
- Held-out agreement vs the full graph; every fraction + any persisting gap
  reported.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN-internals / toolbox untouched; models + venv under
  `/applications`, NOT committed.

## 6. Honest bounds

- One small model (0.6B), small batteries, a LINEAR ridge router; a negative
  bounds the LINEAR router, not every possible learned router (a nonlinear/MLP
  router is the named further step). Reported as such.
