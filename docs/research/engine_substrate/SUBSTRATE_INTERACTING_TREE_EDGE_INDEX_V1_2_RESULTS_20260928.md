# Adaptive high-degree edge index v1.2 results

**Evidence grade:** source-locked current-source replay; all runner gates pass and the independent analyzer passes 29/29 checks. The failed v1/v1.1 captures are retained and disclosed in their amendments; v1.2 is the confirmatory replay.

## Semantics and scale

The targeted semantic probe passed index creation at degree 16, lookup at degree 17, duplicate insertion without edge-count growth, duplicate attribute replacement, deletion while indexed, index demotion below threshold, lookup after demotion, reinsertion and index recreation, and a low-degree lookup. All 12 scale workers reached the exact expected graph counts and terminal fixed point with sampled parents and attributes correct.

The three-replicate phase medians, compared with the original locked implementation, are:

| N | Topology | Edge build before → after | Speedup | Closure before → after | Peak RSS before → after |
|---:|---|---:|---:|---:|---:|
| 100k | Balanced | 151.8 → 150.4 ms | 1.01× | 489.5 → 508.0 ms | 91.7 → 92.2 MiB |
| 100k | Star | 2.799 s → 139.5 ms | 20.1× | 132.7 → 123.9 ms | 90.1 → 93.5 MiB |
| 1M | Balanced | 1.674 → 1.706 s | 0.98× | 6.112 → 6.200 s | 612.6 → 613.6 MiB |
| 1M | Star | 456.86 → 1.657 s | 275.6× | 1.677 → 1.681 s | 794.1 → 808.0 MiB |

The target index removes the measured high-fanout construction bottleneck on this fixture. Balanced-tree construction and closure remain effectively unchanged at these three-replicate medians. The 1M star spends roughly as long building edges as reaching closure after the change. The measured incremental peak for the indexed star is about 13.9 MiB at 1M; timing and memory are descriptive, and allocator noise is not quantified.

## Interpretation and limits

This is a causal implementation replay on one star and one balanced-tree generator: the current engine differs by the adaptive high-degree target index, and output/semantic gates pass. It strongly supports the duplicate-check scan as the bottleneck on this high-fanout insertion path. It does not establish asymptotic guarantees, high-degree deletion throughput, performance on every hub-heavy graph, or general substrate tractability.

## Reproduction

Run `python3 scripts/substrate_interacting_tree_edge_index_v1.py` after creating the frozen v1.2 source lock with `--lock`; run `python3 scripts/analyze_substrate_interacting_tree_edge_index_v1.py` for independent analysis. See the [preregistration](SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_PREREG_20260928.md), [v1.1 amendment](SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_1_AMENDMENT_20260928.md), [v1.2 amendment](SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_2_AMENDMENT_20260928.md), [runner](../../../scripts/substrate_interacting_tree_edge_index_v1.py), [analysis](../../../evaluation/reports/substrate_interacting_tree_edge_index_v1_2_analysis_20260928.json), [raw capture](../../../evaluation/reports/substrate_interacting_tree_edge_index_v1_2_20260928.json), and [source lock](../../../evaluation/substrate_capability/interacting_tree_edge_index_v1_2_lock_20260928.json). The prior implementation's original raw data is linked in the [construction-cost report](SUBSTRATE_INTERACTING_TREE_CONSTRUCTION_COST_V1_RESULTS_20260928.md).
