# Adaptive high-degree edge index: 10M star scale v1.3 results

**Evidence grade:** source-locked 10M extension; all 8 runner gates and 11 independent analyzer checks pass. Three fresh processes completed the same attributed star and two-rule workload.

## Result

At N=10,000,000 with 19,999,998 directed typed edges, every process reached the exact fixed point: all nodes active, no pending or ready nodes, zero budget overshoot, correct sampled parent/attribute values. The median phase costs and memory were:

| Phase or measure | Median |
|---|---:|
| Node construction | 23.07 s |
| Edge construction | 19.93 s |
| Two-rule closure | 17.78 s CPU / 17.78 s wall |
| Terminal validation/readback | 0.69 s |
| Live RSS after closure | 4.14 GB |
| Process peak RSS | 7.02 GB |

Compared with the indexed 1M-star replay, node construction grows 10.25×, edge construction 12.02×, and closure 10.58× for a tenfold increase in node count. This is consistent with near-linear scaling over these two points for this particular star and fixed two-rule propagation program. The 1M indexed edge build was 275.6× faster than the original pre-index implementation; the 10M edge build takes about 22.9× less time than the original 1M star edge build.

## Interpretation and limits

This closes the measured 10M high-fanout construction/closure gap for one controlled topology after adding an adaptive target index for high-degree `(source, edge type)` buckets. The implementation keeps contiguous scans for low-degree buckets and creates a target map when the bucket reaches degree 16. The 1M replay also passes duplicate replacement, deletion, demotion, reinsertion, and sparse lookup controls.

This is not evidence for general closure complexity, natural-task locality, varied rule diversity, or arbitrary graph builders. Only one high-fanout topology and one fixed monotone rule pair were measured at 10M, on one host; the prior balanced-tree panel reaches 1M. Peak RSS includes construction and full terminal readback. Deletion semantics are checked, but high-degree deletion throughput and steady-state churn are not measured.

## Reproduction

Run `python3 scripts/substrate_interacting_tree_edge_index_scale_v1_3.py` after creating its source lock with `--lock`; run `python3 scripts/analyze_substrate_interacting_tree_edge_index_v1_3.py` for independent analysis. See the [protocol](SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_3_SCALE_PREREG_20260928.md), [runner](../../../scripts/substrate_interacting_tree_edge_index_scale_v1_3.py), [analysis](../../../evaluation/reports/substrate_interacting_tree_edge_index_v1_3_analysis_20260928.json), [raw capture](../../../evaluation/reports/substrate_interacting_tree_edge_index_v1_3_20260928.json), and [source lock](../../../evaluation/substrate_capability/interacting_tree_edge_index_v1_3_lock_20260928.json). The 1M causal replay is documented in [v1.2 results](SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_2_RESULTS_20260928.md).
