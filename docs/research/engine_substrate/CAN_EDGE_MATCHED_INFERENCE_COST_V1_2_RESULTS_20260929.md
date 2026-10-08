# Edge-matched exact-inference cost v1.2 profile results (2026-09-29)

## Outcome

The 36-worker source-locked replication passes ten gates, including the v1.1 extraction, width-certificate, oracle, state, and lock checks plus reconciliation of each profile's maximum bag size with the executed junction-tree result. Both orders match the independent factor-table variable-elimination oracle in all 36 graphs.

The implementation explains what the memory and timing fields mean: `junction_tree_map` and treewidth/order construction are pure Python; native-backed substrate state is used to build and extract the model, after which the MAP algorithm runs on Python collections. `tracemalloc` therefore reports Python allocations attributed to one JT call. `ru_maxrss` is a whole-worker high-water mark after graph construction, extraction, oracle work, and both JT calls; it is not per-call or native-allocator usage.

## Full elimination profiles

The source-aligned loop proxies count message-table assignments, bag assignments, JT inner-loop iterations (separator assignments × states × one plus child count), and local-energy scope visits. These explain the counterintuitive max-bag result more directly than a single width value.

| q | Family | Order | Max bag | Message entries | Bag assignments | Inner-loop proxy | Local-energy visits | Median JT (ms) |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 4 | Grid | min-fill | 5 | 1,607 | 3,214 | 6,820 | 15,522 | 56.1 |
| 4 | Grid | certified | 5 | 1,851 | 3,702 | 7,396 | 18,426 | 61.8 |
| 4 | Sparse partial q-tree | min-fill | 5 | 550 | 1,100 | 3,447 | 3,782 | 27.2 |
| 4 | Sparse partial q-tree | certified | 5 | 554 | 1,108 | 3,334 | 3,826 | 26.7 |
| 5 | Grid | min-fill | 7 | 2,755 | 5,510 | 12,732 | 31,778 | 109.0 |
| 5 | Grid | certified | 6 | 3,643 | 7,286 | 14,564 | 43,514 | 136.3 |
| 5 | Sparse partial q-tree | min-fill | 6 | 641 | 1,282 | 4,914 | 4,930 | 36.9 |
| 5 | Sparse partial q-tree | certified | 6 | 647 | 1,294 | 4,548 | 4,998 | 35.4 |
| 6 | Grid | min-fill | 8 | 4,391 | 8,782 | 22,284 | 59,170 | 208.2 |
| 6 | Grid | certified | 7 | 7,163 | 14,326 | 28,644 | 99,834 | 273.2 |
| 6 | Sparse partial q-tree | min-fill | 7 | 745 | 1,490 | 6,780 | 6,526 | 50.5 |
| 6 | Sparse partial q-tree | certified | 7 | 761 | 1,522 | 7,646 | 6,734 | 57.4 |

On the q=5/6 grids, the certified order's maximum bag is smaller, but its full profiles contain more message entries and local-energy visits than min-fill's. The profile then correctly points in the direction of the measured JT latency: 136 versus 109 ms at q=5, and 273 versus 208 ms at q=6. The sparse partial q-tree profiles are much smaller under both orders at matched N/E/q. This is fixture-specific explanatory evidence, not a fitted universal cost law.

Per-call traced Python peaks remain lower on sparse partial q-trees: q=4 approximately 0.21–0.23 MB, q=5 0.25 MB, and q=6 0.29–0.30 MB, compared with grid peaks of 0.37 MB, 0.70 MB, and 1.23–1.47 MB respectively. Whole-worker peak RSS medians are 29,376 KiB for all q=4/5 cells and both q=6 sparse q-tree calls, versus 31,168 KiB for q=6 grids; because this high-water value includes the complete worker, it is only a coarse process-level envelope.

## Limits

These proxies inspect elimination structure and align with this source's loops, but are not machine-independent operation counts and do not model allocator reuse/cache behavior. Only two synthetic binary factor families are evaluated. The study does not establish natural graph distributions, a general big-O runtime, or exact inference behavior for other vocabularies/factor types.

## Reproducibility

- Protocol and amendment trail: [`CAN_EDGE_MATCHED_INFERENCE_COST_V1_PREREG_20260929.md`](CAN_EDGE_MATCHED_INFERENCE_COST_V1_PREREG_20260929.md), [`v1.1 harness`](CAN_EDGE_MATCHED_INFERENCE_COST_V1_1_AMENDMENT_20260929.md), [`v1.2 profiles`](CAN_EDGE_MATCHED_INFERENCE_COST_V1_2_AMENDMENT_20260929.md)
- Runner/analyzer: [`can_edge_matched_inference_cost_v1.py`](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1.py), [`analyzer`](../../../evaluation/substrate_capability/analyze_can_edge_matched_inference_cost_v1.py)
- Lock/raw/analysis: [`lock`](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1_2_lock_20260929.json), [`capture`](../../../evaluation/reports/can_edge_matched_inference_cost_v1_2_20260929.json), [`analysis`](../../../evaluation/reports/can_edge_matched_inference_cost_v1_2_20260929_analysis.json)

