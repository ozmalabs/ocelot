# Ternary exact-inference higher-width envelope v1 preregistration (2026-10-02)

## Question

How far does exact junction-tree MAP extend in the substrate's supported 3-state CAN domain as certified width rises beyond q=6, and how does that cost compare with binary inference on identical graph/potential fixtures?

## Design

Run source-locked 3-state workers at N=120, q={6,7,8}, topologies={grid,sparse_partial_qtree}, and three deterministic replicates per cell (18 fresh workers). The q=6 ternary cell is a contemporaneous control. Reuse the domain-cost v1 worker and its generic independent factor-table oracle. The binary comparison comes from the existing current-native v1.4 width capture at the exact same q/family/replicate indices; require native binary hash, solver source hashes, fixture seeds, graph counts, and the deterministic potential generator to match before forming ratios. No comparison is made when a parity gate fails.

At each cell record certified/min-fill JT, independent oracle, extraction, ordering, decomposition profile, and traced Python peak. All 3-state results must match the oracle and direct returned-state rescore within 1e-8, return only {-1,0,+1}, preserve model state, certify q, and pass exact extraction/profile checks. Require full 3-replicate coverage and stable pre/post source locks. Report wall-time ranges as well as medians; timeouts and memory failures are retained as failures. No performance threshold is a pass criterion.

## Claim boundary

This measures exact 3-state binary-pairwise MAP on synthetic grids and sparse q-trees through q=8 at N=120, on one host. Binary ratios are valid only after the registered same-fixture/native/source gates. It does not estimate natural topology prevalence, task-derived frame width, widths above q=8, or whole-system cost.

## Artifacts

- Runner: [can_ternary_high_width_inference_v1.py](../../../evaluation/substrate_capability/can_ternary_high_width_inference_v1.py)
- Analyzer: [analyze_can_ternary_high_width_inference_v1.py](../../../evaluation/substrate_capability/analyze_can_ternary_high_width_inference_v1.py)
- Lock: [can_ternary_high_width_inference_v1_lock_20261002.json](../../../evaluation/substrate_capability/can_ternary_high_width_inference_v1_lock_20261002.json)
- Capture: [can_ternary_high_width_inference_v1_20261002.json](../../../evaluation/reports/can_ternary_high_width_inference_v1_20261002.json)
- Analysis: [can_ternary_high_width_inference_v1_20261002_analysis.json](../../../evaluation/reports/can_ternary_high_width_inference_v1_20261002_analysis.json)
