# Edge-matched exact-inference cost v1.1 results (2026-09-29)

## Result

The corrected source-locked run completed 36 fresh workers (q=4/5/6 × two graph families × six replicates). All nine gates pass: exact runtime factor extraction, paired node/edge sizes, width-q certificates, direct scoring and both junction-tree MAP routes agreeing with the independent variable-elimination oracle, no graph mutation, and matching pre/post locks. Thus min-fill JT returns the exact optimum even where its width estimate would cause the production gate at bound q to refuse the graph.

Median timings below are milliseconds. Junction-tree timings include `tracemalloc` instrumentation; they are not uninstrumented production latency.

| q | Family | Min-fill width | Min-fill order | JT: min-fill order | JT: certified q order | Independent oracle |
|---:|---|---:|---:|---:|---:|---:|
| 4 | Grid | 4 | 8.72 | 56.59 | 63.78 | 12.95 |
| 4 | Sparse partial q-tree | 4 | 11.64 | 28.13 | 27.32 | 7.73 |
| 5 | Grid | 6 | 9.55 | 107.51 | 134.55 | 22.42 |
| 5 | Sparse partial q-tree | 5 | 12.59 | 38.27 | 35.98 | 8.95 |
| 6 | Grid | 7 (4/6), 8 (2/6) | 11.24 | 192.22 | 276.34 | 41.00 |
| 6 | Sparse partial q-tree | 6 | 12.66 | 51.83 | 56.43 | 10.71 |

At equal N and E, grid MAP is about 2.0×/2.8×/3.7× the sparse partial q-tree at q=4/5/6 when each uses min-fill order. Traced Python peak for min-fill inference is about 0.38/0.70/1.23 MB on grids versus 0.23/0.26/0.30 MB on partial q-trees. In this synthetic pair, graph topology changes execution time and traced allocation despite matching node/edge count and true treewidth.

The maximum bag-width statistic alone does not predict this implementation's observed JT time: on q=5/6 grids the min-fill order has a larger maximum bag than the certified order, yet its measured JT call is faster. The distribution of bag sizes, separator overlaps, and child counts matters as well. The run did not capture full per-order bag profiles, so it does not identify which structural feature accounts for this timing difference. This limits reducing inference cost to a single scalar k without further profiling.

## Limits and gate history

V1's first locked invocation stopped before MAP evaluation because its certificate used fixture IDs rather than live graph IDs; that no-capture attempt is retained and corrected in v1.1 ([amendment](CAN_EDGE_MATCHED_INFERENCE_COST_V1_1_AMENDMENT_20260929.md)).

Only two synthetic binary pairwise families are compared. Degree distribution and separator placement remain unmatched. The independent oracle uses generic factor-table variable elimination, algorithmically distinct from the engine's elimination-tree message pass but sharing the certified graph ordering. Native memory is not included in Python traced allocation. No natural-task or scaling-generalization claim follows.

## Reproducibility

- Protocol/amendment: [`CAN_EDGE_MATCHED_INFERENCE_COST_V1_PREREG_20260929.md`](CAN_EDGE_MATCHED_INFERENCE_COST_V1_PREREG_20260929.md), [`v1.1 amendment`](CAN_EDGE_MATCHED_INFERENCE_COST_V1_1_AMENDMENT_20260929.md)
- Runner/analyzer: [`can_edge_matched_inference_cost_v1.py`](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1.py), [`analyzer`](../../../evaluation/substrate_capability/analyze_can_edge_matched_inference_cost_v1.py)
- Lock/raw/analysis: [`lock`](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1_1_lock_20260929.json), [`capture`](../../../evaluation/reports/can_edge_matched_inference_cost_v1_1_20260929.json), [`analysis`](../../../evaluation/reports/can_edge_matched_inference_cost_v1_1_20260929_analysis.json)

