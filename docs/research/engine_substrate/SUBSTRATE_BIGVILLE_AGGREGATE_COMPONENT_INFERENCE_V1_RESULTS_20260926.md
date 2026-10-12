# Bigville aggregate component-inference results v1

## Result

All 12 cells passed across three fresh worker processes at 10, 25, 50, and 100 residents. The residents' authored CAN models were assembled into one aggregate Microtheory with 50–500 Concepts. Connected components were found by BFS on the extracted causal graph alone; no resident IDs were used by the decomposition step. Every graph yielded exactly N components, each with five variables and five undirected coupling pairs. Aggregate factor extraction exactly matched the union of the separately extracted resident models.

Global min-fill plus junction-tree MAP and per-component exhaustive MAP agreed in independently rescored energy in all cases. Each component had width upper bound 2; the global graph also had width upper bound 2. The local exact oracle checked 243 states per component, or 24,300 total at 100 residents. All returned states were in the 3-state vocabulary.

| Residents | Variables | Components found | Aggregate extraction | Global width + JT | Discover components + local exact MAP |
|---:|---:|---:|---:|---:|---:|
| 10 | 50 | 10 | 0.64 ms | 2.07 ms | 6.02 ms |
| 25 | 125 | 25 | 1.56 ms | 9.76 ms | 14.54 ms |
| 50 | 250 | 50 | 3.14 ms | 23.58 ms | 29.06 ms |
| 100 | 500 | 100 | 6.26 ms | 85.45 ms | 59.31 ms |

Times are three-process medians on one host. Global time includes min-fill ordering plus junction-tree MAP. Component time includes BFS discovery plus exhaustive local MAP. The component method is slower at smaller sizes and faster at 100 residents in this envelope; this crossover is workload- and implementation-specific, not a general speedup claim. Aggregate extraction grows about 10× from 10 to 100 residents while the graph has 10× as many variables, consistent with the repeated authored construction.

## Interpretation and limits

This is a source-backed task-graph positive control: the decomposition is recovered from the actual assembled causal graph, and exact inference over the union agrees with independent exact inference over the recovered components. It strengthens the disconnected-component factorization evidence beyond hand-supplied module labels.

The Bigville cast is deterministic project simulation data. All components are disconnected; there is no nonzero shared separator or cross-resident factor. The experiment therefore does not demonstrate connected-frame locality, boundary-message exchange, natural-population prevalence, belief calibration, or native rule-engine scheduling. It is an exact-MAP workload result, not a task-response quality result.

## Evidence

- Preregistration: [`SUBSTRATE_BIGVILLE_AGGREGATE_COMPONENT_INFERENCE_PREREG_20260926.md`](SUBSTRATE_BIGVILLE_AGGREGATE_COMPONENT_INFERENCE_PREREG_20260926.md)
- Runner: [`substrate_bigville_aggregate_component_inference_v1.py`](../../../scripts/substrate_bigville_aggregate_component_inference_v1.py)
- Independent analyzer: [`analyze_substrate_bigville_aggregate_component_inference_v1.py`](../../../scripts/analyze_substrate_bigville_aggregate_component_inference_v1.py)
- Lock: [`bigville_aggregate_component_inference_v1_lock_20260926.json`](../../../evaluation/substrate_capability/bigville_aggregate_component_inference_v1_lock_20260926.json)
- Raw capture: [`substrate_bigville_aggregate_component_inference_v1_20260926.json`](../../../evaluation/reports/substrate_bigville_aggregate_component_inference_v1_20260926.json)
- Analysis: [`substrate_bigville_aggregate_component_inference_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_bigville_aggregate_component_inference_v1_analysis_20260926.json)

The independent analyzer passes ten checks covering provenance, fresh processes, extraction-union parity, graph-discovered component structure, exact-energy agreement, width, state domains, and exhaustive-oracle counts. Next measure a task graph with true cross-component factors and explicit boundary states; this zero-boundary positive control cannot establish the nonzero-separator proposition.
