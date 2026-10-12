# Edge-matched exact-inference cost v1.4 results — 2026-10-02

## Result

All 48 fresh workers pass the preregistered checks, and the independent analyzer passes 40/40. Both the min-fill and certified elimination orders match the independent factor-table MAP oracle, direct returned-state energy matches, graph extraction is exact, certified widths are q, decomposition profiles reconcile, no graph state mutates, and source/native fingerprints match before and after. This capture uses the current source-fresh native binary; the older v1.3 packet used a different binary, so the q=6 control was repeated in this same run and supplies the cost ratios below.

At N=120, exact junction-tree MAP median times increase with separator width, with topology remaining a large factor:

| Certified q | Grid min-fill / certified | Sparse q-tree min-fill / certified | Grid certified peak traced bytes | Sparse q-tree certified peak traced bytes |
|---:|---:|---:|---:|---:|
| 6 control | 204 / 276 ms | 54 / 55 ms | 1.47 MB | 0.29 MB |
| 7 | 436 / 595 ms | 71 / 90 ms | 3.00 MB | 0.34 MB |
| 8 | 1,199 / 1,228 ms | 111 / 115 ms | 6.12 MB | 0.41 MB |
| 9 | 1,684 / 2,482 ms | 158 / 210 ms | 12.06 MB | 0.53 MB |

From q=6 to q=9, certified-order time rises 9.00× on grids and 3.81× on sparse q-trees. Certified-order traced peak rises 8.20× and 1.84×, respectively. Min-fill overestimates grid width in all q=7/8/9 replicates (9, 10–12, and 12–14); it remains exact on all q-trees. Consequently a width-q heuristic gate would refuse all 18 grid cases at q=7–9 while accepting every q-tree case. These are cell medians from this implementation and host; they do not establish a universal exponent or predict which topologies natural tasks present.

## Interpretation and boundary

This extends the exact solver's measured range to certified width 9 and shows the practical cost of separator growth at fixed N on two deliberately different structures. The sparse q-tree is much cheaper than the edge-matched grid despite equal N, edge count, and certified q. The min-fill upper bound is safe but can be too pessimistic for grids, so a conservative width gate can reject exact inference even when a supplied certificate proves the desired width. Junction-tree computation remains Python after native graph extraction.

Only synthetic binary pairwise factor graphs are measured. This does not establish that natural task inference graphs have low width, that learned frames recover the sparse family, or that exact inference at these sizes dominates total cognition cost. Results should be extended to larger N at fixed q, higher q with explicit resource caps, non-binary domains, and task-derived factor graphs before extrapolating.

## Artifacts

- [Preregistration](CAN_EDGE_MATCHED_INFERENCE_COST_V1_4_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_can_edge_matched_inference_cost_v1_4.py)
- [Lock](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1_4_lock_20261002.json)
- [Capture](../../../evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002.json)
- [Analysis](../../../evaluation/reports/can_edge_matched_inference_cost_v1_4_20261002_analysis.json)
