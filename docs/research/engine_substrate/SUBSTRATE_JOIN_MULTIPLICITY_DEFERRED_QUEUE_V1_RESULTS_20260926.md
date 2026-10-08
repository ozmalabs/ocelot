# Positive join multiplicity × deferred queues v1 results (2026-09-26)

## Result

The source/native-locked evaluation covered 27 fresh-process cells: `R={1,8,32}` writer/target pairs, `M={1,4,16}` two-edge join multiplicities, and three replications. The independent analyzer passed **165/165 checks**.

Every audit-on closure matched its audit-off twin's whole graph and report. All cells reached fixed point with zero budget overshoot, deleted all `R` trigger edges, opened all `R` target rules, and materialized exactly `4R` framebuffer grid cells. For both `rule_edits` and `fb_samples`, the capture recorded exactly `R×M` enqueues and drains in one batch. Per-rule producer attribution was exactly `M` enqueues for each writer and each family.

| Multiplicity per writer (`M`) | Queue items per writer, each family | Paired-workload candidate tests per writer/target |
|---:|---:|---:|
| 1 | 1 | 6 |
| 4 | 4 | 24 |
| 16 | 16 | 276 |

Both queue work and paired-workload candidate tests multiplied exactly by writer count `R`. The paired-workload count includes two candidate tests from each associated target rule, so it is not a writer-rule-only total. Candidate tests grew faster than successful match multiplicity in the `M=16` cell: the 16× increase from `M=1` corresponded to a 46× increase in paired-workload candidate tests. This is a measured signal in this exact four-literal schema and execution path. It is not sufficient to conclude asymptotic quadratic behavior; clause attribution and installed-order readback were added in the v1.1 follow-up.

Scheduler planning time stayed a separate, audit-on counter and excluded the matching/effect workload. It must not be used as total closure time or throughput.

## Interpretation and next gate

The combined capture closes an integration gap between positive join multiplicity and two deferred queues: queue accounting follows successful binding count, while observed paired-workload candidate work can be materially larger than output count. The v1.1 follow-up attributes candidates to the actual installed order and shows the engine's count-based tie behavior; the degree-skew follow-up varies relation populations at fixed output cardinality. Neither establishes a general runtime bound, memory profile, or natural-task prevalence.

## Artifacts

- [Preregistration](SUBSTRATE_JOIN_MULTIPLICITY_DEFERRED_QUEUE_V1_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_join_multiplicity_deferred_queue_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_join_multiplicity_deferred_queue_v1.py)
- [Raw workers](../../../evaluation/reports/substrate_join_multiplicity_deferred_queue_v1_workers_raw_20260926.json)
- [Run summary](../../../evaluation/reports/substrate_join_multiplicity_deferred_queue_v1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_join_multiplicity_deferred_queue_v1_analysis_20260926.json)
- [Source/native lock](../../../evaluation/substrate_capability/join_multiplicity_deferred_queue_v1_lock_20260926.json)
