# LLM coactivation shape — does the conditional graph close the gap? — PREREG

**Block**: 313000

**Task**: Block 312000 showed the order-2 STATIC mask (query-unconditional)
beats order-1 but trails the per-query oracle, because different queries need
different memories — the fuller shape is query-CONDITIONAL. The named next
rung: build the COACTIVATION GRAPH over the FFN memory dictionary (which
neurons fire together across a corpus) — the substrate-native form — and test
whether query-conditional retrieval against it closes the order-2 → oracle gap.

## 1. The coactivation graph + conditional retrieval

`domains/llm_structure_recovery.py`:
- `fit_coactivation_graph(model, corpus, per_query_frac, pool_frac)` — over the
  corpus, record each query's top-active neurons per layer; count co-firing
  among the layer's most-frequently-active pool; return a `CoactivationGraph`
  (per-layer sparse `neuron → {partner → count}`). This is a graph over the
  memory dictionary — nodes = memories, edges = fire-together.
- `coactivation_retrieve(model, graph, ids, seed_frac, target_frac)` — for a
  held-out query: take a cheap SEED (top `seed_frac` neurons by gate-key on
  this query) and EXPAND along the graph to the seed's frequent co-firing
  partners until `target_frac` are selected. Query-CONDITIONAL (seed) +
  ENSEMBLE (graph). This is the substrate primitive: spread from a seed over a
  coactivation graph.

## 2. Comparison

At matched neuron-fraction, held-out agreement vs the full graph:
- **coactivation** (seed + graph expand, this rung),
- **order-2 static mask** (block 312),
- **order-1 gate-key** (block 311),
- **oracle** per-query true-activation top-k (upper bound, block 310).

Plus a **diagnostic**: given a GOOD (true-activation) seed, does graph
expansion beat naive top-up? — isolating whether the graph carries conditional
information independent of seed quality.

## 3. Falsifiable claims

1. **`order2_shape=None` bit-exact** (default==today).
2. **Coactivation retrieval closes the gap**: conditional coactivation
   retrieval beats the static order-2 mask and approaches the oracle on
   held-out. (Registered as the hypothesis; may FAIL.)
3. **Diagnostic**: given a good seed, graph expansion beats naive top-up — the
   graph carries query-conditional shape.

Reported with measured outcomes; a failed claim 2 is reported as a failure and
its cause diagnosed (claim 3 isolates whether the failure is the graph or the
seed).

## 4. Anti-faking

- Graph FIT on a train corpus, retrieval EVALUATED on a DISJOINT held-out
  battery — not per-query memorisation.
- The oracle peeks at the true activation — an explicit per-query UPPER BOUND,
  not deployable.
- Held-out agreement vs the full graph; every fraction reported.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## 5. Honest bounds

- One small model (0.6B), next-token / greedy agreement, small batteries;
  the seed_frac/target_frac/pool_frac are uncalibrated.
- This tests ONE conditional-retrieval design (gate-key seed + co-firing
  expansion); a negative result bounds THIS design, not every possible
  coactivation-based selector.
