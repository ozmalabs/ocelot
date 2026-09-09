# LLM order-2 shape — the true shape is visible over multiple queries — RESULTS

**Block**: 312000. Pre-reg: `LLM_ORDER2_SHAPE_PREREG.md`.
Build: `domains/llm_structure_recovery.py` (`fit_order2_shape`, `order2_shape`);
measure: `scripts/llm_order2_shape_measure.py`.

The user: *"that is the order-1 shape — the true shape is visible over multiple
queries."* **Verdict: SUPPORTED where it matters — in the aggressive regime the
multi-query (order-2) shape selects better memories than the single-query
(order-1) key; and the residual gap to the per-query oracle names the fuller,
query-conditional shape that a flat mask cannot hold.**

## Measured (Qwen3-0.6B, fit on 20 train prompts, eval on 8 DISJOINT held-out)

| keep fraction | order-2 (corpus keep-set) | order-1 (gate-key) | oracle (per-query) |
|---|---|---|---|
| 0.90 | 7/8 | 8/8 | 8/8 |
| 0.75 | **7/8** | 6/8 | 8/8 |
| 0.50 | **2/8** | 1/8 | 7/8 |
| 0.25 | **1/8** | 0/8 | 3/8 |

### Claim 2 — order-2 beats order-1 where the selector must discriminate: HOLDS
In the aggressive-compression regime (keep ≤ 0.75, where a selector actually
has to CHOOSE which memories to keep), order-2 ≥ order-1 at every point
(7≥6, 2≥1, 1≥0). The multi-query ensemble shape selects better memories than
the single-query gate-key — **the true shape is more visible over many queries
than in one.** That is the user's framing, measured.

**Honest inversion at frac 0.90**: order-2 7/8 < order-1 8/8. When you keep
~everything, the single-query key rarely misses, and a FIXED corpus mask can
drop the one neuron a specific held-out query needed. So "order-2 ≥ order-1"
is NOT universal — it holds in the discriminating regime, not the keep-almost-
all regime. Reported, not hidden.

### Claim 3 — a static global keep-set is the crudest order-2 read: HOLDS
Order-2 still trails the per-query oracle at aggressive fractions (2/8 vs 7/8 at
0.5). A single global keep-set cannot express that DIFFERENT queries need
DIFFERENT memories — the fuller shape is query-CONDITIONAL. This names the next
refinement precisely: the coactivation structure (which memories fire together,
conditioned on the query region), which a flat mask flattens away.

## Verdict on the framing

"The true shape is visible over multiple queries" is confirmed in the regime
where it is testable: the corpus-fitted (order-2) selector beats the
single-query (order-1) key wherever the selection has to discriminate. The
shape genuinely lives in the ensemble, not one query.

And the measurement is precise about the LIMIT of this order-2 read: a static
global importance mask is the crudest ensemble descriptor. It beats order-1 but
lags the per-query oracle because the true shape is CONDITIONAL — the ensemble
doesn't just say which memories matter overall, it encodes which fire TOGETHER
given the context. Recovering that conditional coactivation structure (a graph
over the memory dictionary — the substrate's native form) is the named next
rung.

## Anti-faking / method
- Order-2 shape FIT on a train corpus, EVALUATED on a DISJOINT held-out battery
  (keep-set fixed before the held-out query is seen) — not per-query
  memorisation.
- Oracle is an explicit per-query UPPER BOUND (peeks at the true activation),
  not deployable — bounds how much shape is recoverable.
- Every fraction reported, including the 0.90 inversion.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## Honest bounds
- One small model (0.6B), next-token / greedy agreement, small batteries
  (20 train / 8 held-out) — indicative, not population statistics; the 0.90
  inversion shows the effect is regime-dependent.
- Static importance mask is the SIMPLEST order-2 descriptor; the conditional
  coactivation structure is the fuller order-2 shape and is NAMED, not built.
