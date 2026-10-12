# Edge-matched exact-inference cost v1.4 preregistration: higher widths

## Question

How do exact binary pairwise junction-tree MAP costs, intermediate storage, and min-fill refusal behavior change as certified separator width rises from q=4–6 to q=7–9, with node count and edge-matched topology families held fixed?

## Design

The historical v1.3 packet used a native binary/build manifest that no longer matches the currently installed engine, although its Python junction-tree and treewidth sources remain byte-identical. Reuse the v1.3 worker and independent factor-table variable-elimination oracle unchanged with the currently installed, provenance-fresh native extension. Include a contemporaneous q=6 baseline with six replicates per family, then measure certified width q∈{7,8,9} at N=120 on grids and sparse partial q-trees, again with six deterministic replicates per family/width. Keep node relabeling, potentials, extraction, min-fill ordering, and certified ordering unchanged. Report extraction, ordering, oracle and junction-tree timings; bag/separator profiles and 2^k work proxies; traced Python peaks and process high-water RSS. All 48 workers must match both exact MAP energies and returned states against the independent factor-table oracle within 1e-8, report the certified width, preserve graph state, and match the full current source lock before and after capture. Compare widths to the q=6 control from this same binary; do not use the historical v1.3 timing as the paired baseline.

This is a fresh continuation capture rather than an edit of v1.3. The v1.3 code and result remain immutable historical inputs. No algorithm, topology, solver, domain, or task is changed besides the width range and corresponding deterministic seeds.

## Gates and claim boundary

Any timeouts, memory failures, mismatches, refusals, or source drift are recorded as failures; no cells are silently omitted. Summaries report medians and ranges by cell, plus ratios against matching v1.3 q=4/5/6 cells, explicitly describing host/runtime dependence. The panel measures exact inference on two synthetic binary pairwise families only. It does not estimate natural-task width, frame-boundary prevalence, general scaling laws, or total cognitive-system cost.

## Artifacts

- Runner: [can_edge_matched_inference_cost_v1_4.py](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4.py)
- Analyzer: [analyze_can_edge_matched_inference_cost_v1_4.py](../../../evaluation/substrate_capability/analyze_can_edge_matched_inference_cost_v1_4.py)
- Lock: [can_edge_matched_inference_cost_v1_4_lock_20261002.json](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4_lock_20261002.json)
- Capture: [can_edge_matched_inference_cost_v1_4_20261002.json](../../../evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002.json)
- Analysis: [can_edge_matched_inference_cost_v1_4_20261002_analysis.json](../../../evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002_analysis.json)
