# Edge-matched exact-inference domain cost v1 preregistration (2026-10-02)

## Question

At fixed graph size, width, topology, and potentials, how much does exact junction-tree MAP cost change between the substrate's supported binary and ternary CAN domains?

## Design

Run paired binary (`2state`, {-1,+1}) and ternary (`3state`, {-1,0,+1}) workers over the same deterministic graph and potential fixtures: N=120; certified q={4,5,6}; families={grid,sparse_partial_qtree}; three replicates per cell (36 fresh processes). The q-tree has the same edge count as its grid partner. Node relabeling and potentials remain identical across modes within each (q,family,replicate). The graph is extracted from the live native Microtheory separately for each domain. Reuse the existing exact MAP implementation and decomposition routines; use an independent generic factor-table variable-elimination oracle over the declared vocabulary.

Record construction, extraction, min-fill, oracle, min-fill-order JT, certified-order JT, decomposition profiles, traced Python peak, and process high-water RSS. Require exact extraction, certified width q, profile reconciliation, independent oracle and returned-state agreement within 1e-8 for both modes, valid returned domain values, unchanged state, complete paired coverage, distinct fresh PIDs, and stable source/native lock. Report medians/ranges and paired ternary/binary ratios. Performance has no pass threshold.

## Claim boundary

This is a synthetic binary/ternary pairwise model comparison at N=120, q≤6, on one host. It measures exact inference cost for the two supported vocabularies; it does not estimate natural graph/domain prevalence, higher-width ternary performance beyond q=6, learned frame discovery, or total system cost.

## Artifacts

- Runner: [can_edge_matched_domain_cost_v1.py](../../../evaluation/substrate_capability/can_edge_matched_domain_cost_v1.py)
- Analyzer: [analyze_can_edge_matched_domain_cost_v1.py](../../../evaluation/substrate_capability/analyze_can_edge_matched_domain_cost_v1.py)
- Lock: [can_edge_matched_domain_cost_v1_lock_20261002.json](../../../evaluation/substrate_capability/can_edge_matched_domain_cost_v1_lock_20261002.json)
- Capture: [can_edge_matched_domain_cost_v1_20261002.json](../../../evaluation/reports/can_edge_matched_domain_cost_v1_20261002.json)
- Analysis: [can_edge_matched_domain_cost_v1_20261002_analysis.json](../../../evaluation/reports/can_edge_matched_domain_cost_v1_20261002_analysis.json)
