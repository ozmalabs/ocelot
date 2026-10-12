# Interacting balanced-tree closure at 10M v1.4.1 results

**Evidence grade:** source-locked three-worker balanced-tree extension; all 8 runner gates and 9 independent analysis checks pass. V1.4's three workers passed task oracles but failed the worker-source projection gate because one reused analyzer path was missing from the lock. That capture is preserved and disclosed; v1.4.1 adds the dependency and is confirmatory.

## Result

At N=10,000,000 and 19,999,998 directed typed edges, every worker reaches exact fixed point with all nodes active, no pending/ready nodes, zero budget overshoot, and correct sampled attributes and parents. Median measures:

| Phase or measure | Median |
|---|---:|
| Node construction | 23.17 s |
| Edge construction | 20.92 s |
| Two-rule closure | 77.89 s CPU / 77.89 s wall |
| Terminal validation/readback | 0.67 s |
| Live RSS after closure | 5.10 GB |
| Process peak RSS | 6.33 GB |

Against the v1.2 1M balanced-tree replay, node, edge, and closure time grow 10.11×, 12.26×, and 12.56×. At the same N, the 10M balanced tree and star have similar construction medians (node 23.17/23.07 s; edges 20.92/19.93 s) but balanced closure is 77.89 s versus 17.78 s for the star (4.38×). Balanced live post-closure RSS is 5.10 GB versus 4.14 GB for the star, while validation-inclusive peak RSS is lower (6.33 GB versus 7.02 GB). These timings come from separate sequential runs on one host, not a randomized same-session topology comparison.

## Interpretation and limits

This confirms that after indexing high-degree duplicate checks, both hub-heavy and bounded-degree tree fixtures can be built and closed at 10M nodes. Similar build times with different closure times point to propagation/matcher work rather than edge construction as the dominant topology contrast in this rule pair. This does not establish broad closure complexity, rule-family generality, natural frame locality, or capability on learned workloads. Auditing remains off at 10M; exact per-rule candidate counts at that scale are therefore not available. The balanced worker's closure time is materially higher than the star's and grows 12.56× from 1M, so “near-linear through 10M” is not supported uniformly across these topologies.

## Reproduction

Run `python3 scripts/substrate_interacting_tree_edge_index_scale_v1_4_balanced.py` after freezing its lock with `--lock`, then `python3 scripts/analyze_substrate_interacting_tree_edge_index_v1_4_balanced.py`. See the [protocol](SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_4_BALANCED_SCALE_PREREG_20260928.md), [v1.4.1 amendment](SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_4_1_AMENDMENT_20260928.md), [runner](../../../scripts/substrate_interacting_tree_edge_index_scale_v1_4_balanced.py), [analysis](../../../evaluation/reports/substrate_interacting_tree_edge_index_v1_4_1_balanced_analysis_20260928.json), [raw capture](../../../evaluation/reports/substrate_interacting_tree_edge_index_v1_4_1_balanced_20260928.json), and [source lock](../../../evaluation/substrate_capability/interacting_tree_edge_index_v1_4_1_balanced_lock_20260928.json). The matched 10M star result is documented in [v1.3](SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_3_SCALE_RESULTS_20260928.md).
