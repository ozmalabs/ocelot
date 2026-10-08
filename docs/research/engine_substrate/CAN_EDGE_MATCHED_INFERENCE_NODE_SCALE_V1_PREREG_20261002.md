# Edge-matched exact-inference node scaling v1 preregistration (2026-10-02)

## Question

At fixed certified separator widths q=6 and q=9, how do exact binary pairwise junction-tree MAP runtime and traced Python memory grow with node count on two edge-matched graph families?

## Design

Reuse the v1.4 exact worker and its independent factor-table variable-elimination oracle without changing solver or factor semantics. Measure N={126,252,504}, q={6,9}, families={grid,sparse_partial_qtree}, and three deterministic replicates per cell (36 fresh workers). Each N is divisible by both widths so the grid contains exactly N nodes. Within each N and q, sparse partial q-trees match the grid's edge count. Relabel nodes and edges, randomize deterministic potentials, and provide a certified elimination order as in v1.4. The N=126 row is the within-experiment baseline; do not ratio against the v1.4 N=120 timing.

Record graph construction, extraction, min-fill ordering, oracle, both junction-tree orders, bag/separator profiles, traced Python peaks, and process high-water RSS. Every worker must extract the fixture exactly, certify its requested width, match min-fill and certified MAP energy plus returned-state rescoring against the independent oracle within 1e-8, preserve model state, and start/end under the same source/native lock. The analysis reports medians, ranges, and N=126-normalized costs by matched family/width. Performance has no pass threshold.

## Integrity and scope

Record all failures and timeouts; do not omit cells. Require fresh worker PIDs and complete 3-replicate coverage. The panel varies N at only two widths, on one host, for synthetic binary pairwise graphs. It does not estimate natural-task graph sizes, width prevalence, multi-state cost, or total cognitive-system cost. High-water RSS is a process-level measure; traced peaks cover Python allocations only.

## Artifacts

- Runner: [can_edge_matched_inference_node_scale_v1.py](../../../evaluation/substrate_capability/can_edge_matched_inference_node_scale_v1.py)
- Analyzer: [analyze_can_edge_matched_inference_node_scale_v1.py](../../../evaluation/substrate_capability/analyze_can_edge_matched_inference_node_scale_v1.py)
- Lock: [can_edge_matched_inference_node_scale_v1_lock_20261002.json](../../../evaluation/substrate_capability/can_edge_matched_inference_node_scale_v1_lock_20261002.json)
- Capture: [can_edge_matched_inference_node_scale_v1_20261002.json](../../../evaluation/reports/can_edge_matched_inference_node_scale_v1_20261002.json)
- Analysis: [can_edge_matched_inference_node_scale_v1_20261002_analysis.json](../../../evaluation/reports/can_edge_matched_inference_node_scale_v1_20261002_analysis.json)
