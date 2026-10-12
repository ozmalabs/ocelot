# Edge-matched exact-inference cost v1 preregistration (2026-09-29)

## Question

For the edge-matched known-width grids and sparse partial q-trees, does junction-tree MAP remain exact under both min-fill and supplied width-q orders, and how do graph extraction, ordering, and inference costs differ?

## Cases and oracle

Use q∈{4,5,6}, N=120, and six deterministic replicates per topology/cell (36 fresh workers). Reconstruct the v1 edge-matched graph fixtures and deterministic binary unary/pairwise factors. Extract each model through `can_network_from_mt` and require exact factor parity. Use the min-fill order and the preregistered width-q certificate order. An independent min-sum variable-elimination implementation over explicit factor tables, using the certified order, supplies the exact optimum energy; independently score each returned MAP state against the original generated factors.

Measure graph construction/extraction, min-fill ordering, min-fill JT MAP, certified-order JT MAP, independent oracle work/time, and traced Python allocation per inference call. Preserve full per-worker timing, width, bag size, order, input factors, results, and resource metadata.

## Gates and lock

Lock protocol, runner, graph generator, `can_junction_tree.py`, `graph_treewidth.py`, native extension, and build record. Require 36 complete workers, paired node/edge counts, exact extraction, width-q certificate, both MAP energies and direct state scores within `1e-8` of the independent oracle, matching pre/post lock, and no mutation (commit disabled). Timings are descriptive; no threshold is a pass/fail performance gate.

## Scope

This compares two synthetic, binary, pairwise graph families. It isolates a topology/ordering effect under matched N and E but does not match degree distributions, estimate natural task topology, or prove asymptotic behavior.

```sh
python3 evaluation/substrate_capability/can_edge_matched_inference_cost_v1.py --lock
python3 evaluation/substrate_capability/can_edge_matched_inference_cost_v1.py
python3 evaluation/substrate_capability/analyze_can_edge_matched_inference_cost_v1.py
```

The initial invocation stopped before MAP evaluation because the certificate used fixture ids rather than live native ids. The handle-based translation and fresh-run requirement are documented in the [v1.1 amendment](CAN_EDGE_MATCHED_INFERENCE_COST_V1_1_AMENDMENT_20260929.md); the initial lock is retained.

V1.1 showed that max bag width alone does not explain elapsed inference time. V1.2 adds full bag/separator/child profiles and source-aligned work proxies, with its pure-Python/native boundary and memory-accounting amendment recorded [here](CAN_EDGE_MATCHED_INFERENCE_COST_V1_2_AMENDMENT_20260929.md). It runs a new full replication under a new source lock.
