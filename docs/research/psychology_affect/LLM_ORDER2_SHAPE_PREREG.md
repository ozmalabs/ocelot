# LLM order-2 shape — the true shape is visible over multiple queries — PREREG

**Block**: 312000

**Task**: The user — *"that is the order-1 shape — the true shape is visible
over multiple queries."* Block 311000 showed the single-query gate-key selector
(order-1) is a poor descriptor of which FFN memories carry the outcome. This
tests the framing directly: fit the ORDER-2 shape — per-neuron importance
accumulated over a query CORPUS — and measure, on a DISJOINT held-out battery,
whether selecting memories by that ensemble shape beats the order-1 key.

## 1. Order-1 vs order-2

- **Order-1**: for a single query `x`, which neurons fire (`|x·gate_key|`, or
  the true activation). A snapshot — one query's local slice of the dictionary.
- **Order-2**: over a CORPUS of queries, which neurons carry weight across the
  ensemble — a query-INDEPENDENT structure. The FFN's memory dictionary has a
  shape that no single query reveals; it emerges in the statistics over many.

## 2. Method

`domains/llm_structure_recovery.py`:
- `fit_order2_shape(model, corpus, frac)` — accumulate per-layer per-neuron mean
  `|silu(gate·x)·(up·x)|` over the corpus; return the top-`frac` neuron set per
  layer (the multi-query keep-set).
- `SparseConfig(order2_shape=…)` — the MLP keeps exactly that corpus-selected
  set (query-INDEPENDENT), computing only those neurons.

Three selectors compared at matched neuron-fractions, agreement vs the full
recovered graph:
- **order-2**: the corpus keep-set (this rung).
- **order-1**: gate-key geometry per query (block 311000).
- **oracle**: true per-query activation top-k (per-query upper bound, block 310).

## 3. Falsifiable claims

1. **`order2_shape=None` is bit-exact** (default==today).
2. **Order-2 beats order-1 where the selector must discriminate**: in the
   aggressive-compression regime (keep-fraction ≤ 0.75, where a selector
   actually has to choose), order-2 held-out agreement ≥ order-1. This is the
   registered test of "the true shape is more visible over multiple queries."
   (At near-full keep-fractions, ~0.9, almost everything is kept so a
   single-query key rarely misses and a fixed corpus mask can drop a neuron a
   specific query needed — that regime is reported, not the basis of the claim.)
3. **A static global keep-set is the CRUDEST order-2 read**: order-2 still
   trails the per-query oracle at aggressive fractions, because different
   queries need different memories — the fuller shape is query-CONDITIONAL
   (coactivation structure), not a flat global mask. Reported as the residual
   gap, naming the next refinement.

## 4. Anti-faking

- The order-2 shape is FIT on a TRAIN corpus and EVALUATED on a DISJOINT
  held-out battery — it is NOT per-query memorisation (the keep-set is fixed
  before seeing the held-out query).
- The oracle is explicitly a per-query UPPER BOUND (it peeks at the true
  activation), not a deployable op — used only to bound how much shape is
  recoverable.
- Agreement vs the full graph; every fraction reported including any inversion.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## 5. Honest bounds

- One small model (0.6B), next-token / greedy agreement, small train (20) +
  held-out (8) batteries — indicative, not population statistics.
- The static importance mask is the SIMPLEST order-2 descriptor; the
  conditional coactivation structure (which memories fire together, given the
  query region) is the fuller order-2 shape and is NAMED, not built here.
