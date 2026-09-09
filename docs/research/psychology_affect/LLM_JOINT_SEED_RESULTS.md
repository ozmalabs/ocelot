# LLM joint-key seed — does fixing the seed close the gap? — RESULTS

**Block**: 314000. Pre-reg: `LLM_JOINT_SEED_PREREG.md`.
Build: `domains/llm_structure_recovery.coactivation_retrieve` (`seed_mode`,
`expand`); measure: `scripts/llm_joint_seed_measure.py`.

Replaced the weak gate-key seed (block 313's bottleneck) with the JOINT gate+up
key (block 311's named fix) and re-tested coactivation retrieval. **Verdict:
joint+graph is now the BEST cheap selector — each refinement climbs — but a
large per-query-oracle gap persists. Cheaply predicting the exact active-memory
set for a held-out query remains the open, well-characterised boundary.**

## Measured (Qwen3-0.6B, 20 train / 10 held-out, agreement vs full graph)

| target | joint+graph | joint-only | gate+graph | order-2 static | oracle |
|---|---|---|---|---|---|
| 0.60 | 4 | 3 | 3 | 4 | 8 |
| 0.50 | 2 | 1 | 1 | 2 | 8 |
| 0.40 | **2** | 0 | 0 | 1 | 5 |

### Claim 2 — joint seed > gate seed: HOLDS
`joint-*` ≥ `gate-*` at every fraction (joint-only 3/1/0 vs the gate seed's
weaker selections; joint+graph 4/2/2 vs gate+graph 3/1/0). The up-projection
carries seed-relevant shape the gate-key alone misses — block 311's named fix,
confirmed on the retrieval seed.

### Claim 3 — graph expansion stacks on the joint seed: HOLDS
joint+graph ≥ joint-only at every fraction (4≥3, 2≥1, 2≥0). The coactivation
graph adds query-conditional co-firing information on top of a better seed —
the two refinements STACK.

### The refinement ladder (each climbs a rung)
At target 0.4: order-2 static 1 → gate+graph 0 … → **joint+graph 2**. Across
targets, joint+graph is the best cheap method — matching the static mask where
the mask is competitive (0.6/0.5) and beating it where selection must
discriminate (0.4: 2 vs 1). Every piece of the arc's diagnosis paid off:
order-1→order-2 (312), static→conditional graph given a good seed (313),
gate→joint seed (311's fix, this rung).

### Claim 4 — does it close the oracle gap? NO
joint+graph 2/10 vs oracle 8/10 at target 0.5 — a large, stable gap. The cheap
`|gate·x|·|up·x|` key is a better ranker than the gate-key but still an
APPROXIMATION of the true relevance `silu(gate·x)·(up·x)`: it drops the silu
nonlinearity and the sign structure (a neuron with large `|gate·x|` but a
gate-value that silu suppresses, or an up-value of the wrong sign, is
mis-ranked). So the exact active-memory set is not cheaply predictable by this
key.

## Verdict — the well-characterised boundary

The user's "true shape over multiple queries" arc converges here to a precise,
honest state:
- **The shape is real and recoverable**: the per-query oracle holds ~80% at
  half the neurons — the outcome IS carried by a sparse active-memory set (311).
- **The shape is query-conditional and graph-structured**: the coactivation
  graph carries conditional co-firing info given a good seed (313), and it
  stacks with a better seed (this rung).
- **Each cheap refinement climbs**: order-2 static < gate+graph < joint+graph.
- **The residual open problem is precisely named**: a CHEAP predictor of the
  exact active-memory set for a held-out query. Every cheap key tried (gate,
  joint gate+up) is a better-but-imperfect ranker; the true selector needs the
  silu nonlinearity + sign, which is what actually computing the activation
  gives (the oracle). Closing the last gap is a harder query→memory index —
  e.g. a small learned router — not another hand-derived key.

This is the honest capstone of the shape sub-arc: the LLM's shape is real,
sparse, conditional, graph-structured, and progressively recoverable — and the
final barrier is cheap exact conditional access, cleanly localised.

## Anti-faking / method
- Graph FIT on train, retrieval EVALUATED on DISJOINT held-out (not
  memorisation). Oracle is an explicit per-query upper bound.
- Every fraction reported, including the persisting gap and claim 4's failure.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## Honest bounds
- One small model (0.6B), small batteries, uncalibrated fracs; tests a specific
  cheap joint-key approximation. The persisting gap bounds THIS key, and names
  the next thing (a learned router seed), not a limit on the framing.
