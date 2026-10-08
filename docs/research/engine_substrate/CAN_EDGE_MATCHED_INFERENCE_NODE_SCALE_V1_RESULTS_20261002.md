# Edge-matched exact-inference node scaling v1 results (2026-10-02)

## Outcome

All 36 fresh workers pass capture gates: complete cell coverage, unique PIDs, exact runtime extraction, certified width, independent factor-table oracle and returned-state agreement, profile reconciliation, no mutation, and pre/post source/native lock equality. The independent analyzer passes 56/56 checks.

Certified-order junction-tree MAP medians (milliseconds) and traced Python peak (MiB) were:

| q | Family | N=126 | N=252 | N=504 | N=504 / N=126 time | N=504 / N=126 traced peak |
|---:|---|---:|---:|---:|---:|---:|
| 6 | Grid | 305 ms / 1.48 MiB | 614 ms / 3.16 MiB | 1,285 ms / 6.53 MiB | 4.21× | 4.42× |
| 6 | Sparse partial q-tree | 61 ms / 0.28 MiB | 125 ms / 0.50 MiB | 303 ms / 0.97 MiB | 5.01× | 3.48× |
| 9 | Grid | 2,726 ms / 12.50 MiB | 5,773 ms / 26.72 MiB | 11,999 ms / 55.10 MiB | 4.40× | 4.40× |
| 9 | Sparse partial q-tree | 206 ms / 0.52 MiB | 526 ms / 1.02 MiB | 1,564 ms / 1.78 MiB | 7.60× | 3.42× |

The 4× increase in node count produces roughly 4.2–7.6× certified-order time and 3.4–4.4× traced peak growth across these cells. The widest spread is the sparse q-tree q=9 timing; its min-fill ordering alone rises from 16 ms to 516 ms, so total inference cost depends on decomposition discovery as well as fixed-width message passing. At N=504, q=9 certified inference takes 12.0 s on the grid and 1.56 s on the edge-matched sparse q-tree. This topology gap is consistent with different decomposition profiles under the supplied certificates; it is not evidence about which topology natural tasks exhibit.

## Limits and next gate

This is one host, three replicates per cell, synthetic binary pairwise graphs, and widths 6 and 9 only. It does not establish natural graph-size or cheap-cut distributions, non-binary-domain scaling, engine-wide memory, or end-to-end cognitive task cost. The next inference gates are non-binary domains and factor graphs extracted from representative task traces, including a declared method for sampling task frames without selecting only favorable low-width cases.

## Reproduction artifacts

- [Preregistration](CAN_EDGE_MATCHED_INFERENCE_NODE_SCALE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/can_edge_matched_inference_node_scale_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_can_edge_matched_inference_node_scale_v1.py)
- [Source lock](../../../evaluation/substrate_capability/can_edge_matched_inference_node_scale_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/can_edge_matched_inference_node_scale_v1_20261002.json)
- [Analysis](../../../evaluation/reports/can_edge_matched_inference_node_scale_v1_20261002_analysis.json)
