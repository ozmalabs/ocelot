# Edge-matched exact-inference cost v1.3 preregistration

This replay renews the exact-inference cost evidence against the current native engine. The v1.2 36-worker packet remains a historical, source-locked 2026-09-29 result; live validation found that only its native binary and build-manifest fingerprints have since changed, while `can_junction_tree.py` and `graph_treewidth.py` remain byte-identical. The current native build reports no source/build staleness.

V1.3 repeats the same frozen binary factor families (120 nodes; q=4/5/6; grid and sparse partial q-tree; six replicates per cell), extracts the model through the native-backed substrate, computes min-fill and supplied certified width-q orders, and measures exact junction-tree MAP against an independent factor-table variable-elimination oracle. It captures full separator/bag/child profiles, loop-work proxies, phase timings, traced Python peaks, process high-water RSS, and no-mutation state. All 36 workers must match both orders and direct returned states to the oracle within `1e-8`, and the exact source lock must match before and after.

- Runner: [can_edge_matched_inference_cost_v1_3.py](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1_3.py)
- Analyzer: [analyze_can_edge_matched_inference_cost_v1_3.py](../../../evaluation/substrate_capability/analyze_can_edge_matched_inference_cost_v1_3.py)
- Lock: [can_edge_matched_inference_cost_v1_3_lock_20261002.json](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1_3_lock_20261002.json)
- Capture: [can_edge_matched_inference_cost_v1_3_20261002.json](../../../evaluation/reports/can_edge_matched_inference_cost_v1_3_20261002.json)
- Analysis: [can_edge_matched_inference_cost_v1_3_20261002_analysis.json](../../../evaluation/reports/can_edge_matched_inference_cost_v1_3_20261002_analysis.json)

The claim boundary remains two synthetic binary pairwise graph families only. This does not estimate natural task topology or general inference complexity.
