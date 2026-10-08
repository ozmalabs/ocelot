# Bigville runtime-partition dynamic-link results

## Runtime-derived partitions and semantic outcome

The locked 27-worker replay used 100 authored Bigville residents. Before benchmark links were injected, the v3.1 builder derived 100 runtime dependency components from live `causal_influence` adjacency and mapped them through live `has_concept` ownership; every component contained five Concepts. Ring, star, or seeded random connected cross-resident links were then inserted between `world_safe` Concepts without changing those discovered frames.

Across all three link topologies and three fresh-process replicates, event and full arms had zero independently recomputed full-graph residual at all seven checkpoints, and exact state projections matched 3/3 per topology. The omitted-evidence-notification arm had positive residual in every replicate at the authored evidence-update checkpoint (ring 6/6/6; star 6/6/6; random 6/8/8). The independent analyzer recomputed all residuals from stored states, fields, directed weights, and the source threshold.

## Costs

Values below are medians of the accumulated seven settlement checkpoints across three process replicates.

| Cross-frame topology | Full candidates | Event candidates | Full Term evaluations | Event Term evaluations | Full settle time | Event settle time |
|---|---:|---:|---:|---:|---:|---:|
| Ring (100 pairs) | 6,075 | 2,360 | 281,361 | 109,535 | 28.791 ms | 14.893 ms |
| Star (99 pairs) | 5,565 | 1,805 | 256,737 | 86,533 | 22.267 ms | 12.014 ms |
| Random connected (100 pairs) | 6,135 | 2,195 | 284,773 | 104,289 | 23.816 ms | 14.483 ms |

The event queue reduced candidate work by 61–68%, Term evaluations by 61–66%, and accumulated settlement time by 36–48% on these three injected link structures. These values show that event-driven visitation can help on this authored workload even when all residents are connected. They are not natural topology prevalence estimates or a general CPU scaling law.

## Native notification remains open

The event arm uses the v3.1 Python dependency queue. The runner explicitly supplies dirty frames after link insertion, deletion, and reweighting, and after scenario evidence changes; it rebuilds dependencies from the current graph. Source inspection confirms the [Python binding](../../../runners/dsl/src/py.rs) accepts a caller-selected `scope_mt` and returns only a progress count; the [Rust Substrate API](../../../runners/dsl/src/substrate.rs) likewise accepts an optional caller-selected Microtheory and returns `usize`. It does not return affected frame IDs from rule effects. Therefore this result measures runtime-derived partitions and caller-provided notification correctness/cost; it does **not** measure native effect-to-frame notification or automatic membership maintenance.

The omitted-notification control establishes sensitivity for the evidence update. Dynamic-link arms also seed their endpoint residents, but no native observer emits those seeds. Building such an observer requires a separate semantic contract for effect write targets, Microtheory ownership, effects that touch nodes outside a frame, node birth/deletion, and topology changes.

Artifacts: [preregistration](SUBSTRATE_BIGVILLE_RUNTIME_PARTITION_DYNAMIC_LINKS_PREREG_20260925.md), [runner](../../../scripts/substrate_bigville_runtime_partition_dynamic_links.py), [independent analyzer](../../../scripts/analyze_substrate_bigville_runtime_partition_dynamic_links.py), [raw report](../../../evaluation/reports/substrate_bigville_runtime_partition_dynamic_links_20260925.json), [independent analysis](../../../evaluation/reports/substrate_bigville_runtime_partition_dynamic_links_analysis_20260925.json), and [lock](../../../evaluation/substrate_capability/bigville_runtime_partition_dynamic_links_lock_20260925.json).
