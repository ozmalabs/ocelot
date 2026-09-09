# LLM joint-key seed — does fixing the seed close the gap? — PREREG

**Block**: 314000

**Task**: Block 313000 localised the bottleneck of coactivation retrieval to
the SEED (a weak gate-key). Block 311000 named the fix: the JOINT gate+up key —
true per-neuron relevance is `silu(gate·x)·(up·x)`, so BOTH projections should
rank the seed, not the gate alone. This tests whether joint-key seeding (with
and without graph expansion) closes the seed-quality gap toward the per-query
oracle on held-out prompts.

## 1. The joint-key seed

`domains/llm_structure_recovery.coactivation_retrieve(..., seed_mode=)`:
- `seed_mode='gate'` — seed by `|gate·x|` (order-1 gate-key, block 311, weak).
- `seed_mode='joint'` — seed by `|gate·x|·|up·x|` (the joint gate+up key). Same
  cost class (two matmuls, used only to RANK the seed).
- `expand=True/False` — graph-expand the seed along the coactivation graph
  (block 313) or seed-only.

## 2. Comparison (held-out, agreement vs the full graph)

At matched neuron-fractions:
- **joint+graph** — joint seed + coactivation expansion (the best cheap
  candidate).
- **joint-only** — joint seed, no expansion (isolates the seed).
- **gate+graph** — gate seed + expansion (block 313's method).
- **order-2 static** — query-unconditional mask (block 312).
- **oracle** — per-query true-activation top-k (upper bound, block 310).

## 3. Falsifiable claims

1. **`order2_shape=None` bit-exact** (default==today).
2. **Joint seed > gate seed**: `joint-*` ≥ `gate-*` at matched fraction — the
   up-projection carries seed-relevant shape the gate-key misses (block 311's
   named fix, now on the retrieval seed).
3. **Graph expansion stacks on the joint seed**: joint+graph ≥ joint-only.
4. **Does it close the oracle gap?** Registered hypothesis: joint+graph
   approaches the oracle. This MAY fail — the `|gate·x|·|up·x|` key drops the
   silu nonlinearity and sign of the true `silu(gate·x)·(up·x)`. Reported
   whichever way.

## 4. Anti-faking

- Graph FIT on train corpus, retrieval EVALUATED on DISJOINT held-out.
- Oracle peeks at the true activation — explicit per-query UPPER BOUND, not
  deployable.
- Held-out agreement vs the full graph; every fraction reported, including a
  persisting gap.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN-internals / toolbox untouched; models + venv under
  `/applications`, NOT committed.

## 5. Honest bounds

- One small model (0.6B), small batteries, uncalibrated fracs; tests a
  specific cheap joint-key approximation, not every possible query→memory index.
- A persisting oracle gap bounds THIS approximation, and points at the residual
  open problem (a cheap predictor of the exact active-memory set), not at the
  framing.
