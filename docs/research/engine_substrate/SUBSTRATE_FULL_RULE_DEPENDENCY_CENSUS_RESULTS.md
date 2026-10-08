# Full loaded rule dependency census

Date: 2026-09-25  
Status: exploratory full-library native access census; two-worker state and access parity pass

## Workload and method

The census boots the frozen full corpus of 833 physical manifests and 737 indexed IDs, then reads the access sets directly from the loaded native rule store. Both independent workers load 2,289 active rules in 2,289 slots. Their full state and ordered access rows match each other and the frozen full-corpus baseline. The rule slots map to 324 source seeds across 43 attributed area labels; source attribution covers 99.78% of active rules. Six rule names are duplicated, so attribution uses manifest sequence plus RuleIdx order rather than name uniqueness.

For each writer→reader pair, the explicit projection adds an edge when native write resources intersect native read or term-edge-read resources. A second projection conservatively completes every `writes_any` writer to all readers and every `reads_any` reader from all writers. The census also compares contiguous RuleIdx blocks of 16/32/64/128 rules with five fixed-seed shuffled orders. These are grouping baselines, not optimized separators.

## Results

| Projection | Directed dependencies | Weak components | Largest component | Largest SCC | Width-32 crossing dependencies | Width-32 boundary rules |
|---|---:|---:|---:|---:|---:|---:|
| Explicit resource intersections | 613,049 | 31 | 2,231 / 2,289 rules | 1,820 | 96.6% | 95.0% |
| Native wildcard completion | 761,285 | 1 | 2,289 / 2,289 rules | 2,289 | 97.1% | 100% |

The explicit graph has a strong global-key concentration. `attr:status` alone connects 737 writers to 706 readers, producing 520,322 unique directed pairs—about 85% of all explicit dependency edges. Other large pair loads include `attr:kind` (39,780), `attr:name` (13,596), and `attr:epoch` (8,772). The native readback exposes only global `Attr` keys, not which graph node each rule reads or writes, so these are conservative possible dependencies and can greatly overstate real interactions.

Contiguous RuleIdx blocks are slightly better than shuffles but still have very broad boundaries. At width 32, 592,489 explicit edges (96.6%) cross blocks, compared with a shuffled median of 602,795 (98.3%); 2,175 rules (95.0%) touch a cross-block edge, compared with 2,269 rules (99.1%) under shuffled order. At width 128, 91.4% of edges still cross and 93.6% of rules remain boundary endpoints. The wildcard-completed graph has one strongly connected component and every rule touches a boundary.

## Interpretation and limits

This is counterevidence to using the current global-key native access graph or RuleIdx order as proof of small frames: under this projection, the full rule library is densely coupled. It is **not** evidence that natural task state lacks cheap cuts. Most edges arise from generic attribute names, especially `status`, without bound-node identity; a rule library loaded together is also broader than the active rules in any one task. No treewidth was computed for this large graph, and no partitioned execution, dynamic access trace, task-conditioned rule subset, or semantic cut validation was measured.

The runner's before/after lock checks passed during capture. Since then, `substrate/world_adapter.py` has changed in the shared worktree; the independent analysis records this post-measurement source drift. The raw source/build lock remains the provenance for the captured state and should not be read as a current-checkout run.

The actionable gap is access precision. A stronger next census should retain matched graph-node identity or a validated variable-role abstraction for actual firings, compare that trace against the static readback for false negatives, and repeat on at least two task families. Until then, dependency width here is an upper-bound-like static warning, not a tractability verdict.

## Artifacts

- Protocol: [`preregistration`](SUBSTRATE_FULL_RULE_DEPENDENCY_CENSUS_PREREG_20260925.md)
- Native capture runner and independent analyzer: [`runner`](../../../scripts/substrate_full_rule_dependency_census_v1.py), [`analyzer`](../../../scripts/analyze_substrate_full_rule_dependency_census_v1.py)
- Source/corpus lock, raw records, and analysis: [`lock`](../../../evaluation/substrate_capability/full_rule_dependency_census_lock_20260925.json), [`raw`](../../../evaluation/reports/substrate_full_rule_dependency_census_v1_20260925.json), [`analysis`](../../../evaluation/reports/substrate_full_rule_dependency_census_v1_analysis_20260925.json)
- Excluded unstable-source attempt: [`raw attempt`](../../../evaluation/reports/substrate_full_rule_dependency_census_v1_harness_attempt1_20260925.json), [`lock`](../../../evaluation/substrate_capability/full_rule_dependency_census_lock_harness_attempt1_20260925.json)
- Related seed-family dependency analysis: [`two-family census`](SUBSTRATE_RULE_DEPENDENCY_CENSUS_RESULTS.md)
