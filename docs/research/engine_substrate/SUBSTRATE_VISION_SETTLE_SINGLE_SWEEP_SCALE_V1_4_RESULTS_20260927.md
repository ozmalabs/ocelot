# Vision settling single-sweep scale v1.4 results (2026-09-27)

## Result

The v1.4 capture passes all 10 driver gates and all 16 independent analyzer checks. Three fresh worker processes reproduce exact one-step outputs, native work counts, access-trace counts, graph cuts, and source fingerprints. The analyzer independently recomputes every `act_next` value. It records zero dropped access-trace events.

The trace correction makes the access-path comparison explicit. On a one-sheet graph, global and root-scoped forms visit the same number of units in their global statistic. The global arm performs two `NodesOfType(SUnit)` folds for each of N output bindings; the root-scoped arm performs two `Neighbours(root, has_sunit)` traversals for each binding. Both are quadratic in N and induce the same complete within-sheet dependency graph. The prior v1.1 report correctly warned that `Neighbours` visits were not counted; v1.4 fills that measurement gap.

## Size results

Counts below repeat exactly across all three seeds and workers. `SUnit type items` and `has_sunit edges` distinguish the two global-population access paths. Local-neighbor edges are read twice per directed graph edge in both arms: once for the numerator fold and once for the degree denominator. Timing is the median across nine worker/seed medians, where each median covers five audit-disabled calls; ranges show the min/max of those nine medians. Timings exclude graph construction, boot, commit, and fixpoint settling.

| SUnits | Variant | Candidate tests | Term evaluations | `NodesOfType` term units | SUnit type items | `has_sunit` edge visits | Local-neighbor edge visits | Cross-row dependency pairs | One-call median (range) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 9 | Global | 9 | 781 | 171 | 162 | 0 | 80 | 54 | 22.7 µs (21.0–38.3) |
| 9 | Root-scoped | 9 | 799 | 9 | 0 | 162 | 80 | 54 | 21.5 µs (21.2–31.4) |
| 64 | Global | 64 | 20,176 | 8,256 | 8,192 | 0 | 840 | 3,584 | 507.0 µs (488.1–524.1) |
| 64 | Root-scoped | 64 | 20,304 | 64 | 0 | 8,192 | 840 | 3,584 | 471.2 µs (456.1–694.5) |
| 100 | Global | 100 | 46,036 | 20,100 | 20,000 | 0 | 1,368 | 9,000 | 1.114 ms (1.095–1.150) |
| 100 | Root-scoped | 100 | 46,236 | 100 | 0 | 20,000 | 1,368 | 9,000 | 1.041 ms (1.017–1.518) |

The two `NodesOfType` folds perform `2N²` SUnit type-index reads. The per-binding `SettleParams` lookup adds N type items to the `NodesOfType` term-unit counter, giving `2N²+N` for the global arm. The root-scoped arm replaces the two global folds with `2N²` `has_sunit` edge visits; its `NodesOfType` counter then contains only the N `SettleParams` items. The trace independently verifies these counts against the runtime graph's typed-edge totals and the retained term/effect identity.

With one row per declared frame, the global activation factor induces N² directed output/input pairs; at N=100, 9,000 of these 10,000 pairs cross row frames. The exact primal treewidth is N−1. Root scoping does not remove this within-sheet global dependence.

## Interpretation and limits

This is a reproducible cross-family negative case for assuming that spatial row frames always produce cheap cuts. The row frames are protocol-defined, not learned. A root-scoped aggregate is a useful population boundary across multiple sheets, as the separate multi-world probe establishes, but on one sheet it still visits every member for every output. The observed one-call timing medians are descriptive diagnostics; ranges overlap and widen at N=64/100. They do not show a total-work reduction or an end-to-end speedup.

The measurement counts the dominant population enumeration and typed-edge visits for one rule application. It does not count every CPU instruction, memory/cache effect, boot/build cost, commit phase, iterative settling, or visual-task quality. The builder's valid anatomy caps this sweep at 100 SUnits. This does not estimate how common global factors are in natural tasks, nor does it validate learned frame locality generally.

Together with the self-report task-boundary replication, the structural evidence is now measured across two distinct workload families: one small operational projection with a nontrivial boundary, and one authored operation with dense global coupling. Cheap-cut locality remains workload-conditional and its prevalence is unknown. Next evaluate factor-aware decompositions and task-level visual outcomes, and measure beyond the small anatomy cap with a validated builder.

## Reproduction artifacts

- [v1.4 protocol](SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_4_PREREG_20260927.md)
- [v1.4 source-lock amendment](SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_4_AMENDMENT_20260927.md)
- [runner](../../../scripts/substrate_vision_settle_single_sweep_scale_v1_4.py) and [independent analyzer](../../../scripts/analyze_substrate_vision_settle_single_sweep_scale_v1_4.py)
- [source lock](../../../evaluation/substrate_capability/vision_settle_single_sweep_scale_v1_4_lock_20260927.json)
- [raw capture](../../../evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_4_20260927.json) and [analysis](../../../evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_4_analysis_20260927.json)
- Superseded gate diagnostics: [v1.2 broad-lock source drift](../../../evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_2_20260927.json), [v1.3 harness-context analyzer mismatch](../../../evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_3_analysis_20260927.json)
