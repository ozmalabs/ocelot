# ProblemShape rule-order preservation V1.7 results

Date: 2026-09-25  
Status: locked three-arm comparison; all gates passed

## Design and validity

V1.7 compares three arms on one immutable 833-file seed corpus: baseline; eventized rules tombstoned and appended; and the same eventized rules installed in their original seed slots. There are six randomized triads per workload mix, with each of the six arm permutations used once. The runner explicitly clears and warms both seed-index caches before any arm runs, checks cache bytes and immutable corpus bytes around every worker, and locks the boot loader, adapter, seed loader, and domain sources.

All 12 triads pass semantic parity, identical seed-load order and failures, exact baseline/original-slot pre-observation rule order, and the expected appended-rule block check. The baseline snapshot matches the corpus lock byte for byte; the candidate snapshot differs only in the transformed ProblemShape seed. All 36 worker PIDs are unique.

## Work counts

Values below are medians over six triads per mix. Candidate and Term counts are summed across the full observation stream; rule enumerations are unchanged in all arms.

| Workload, N=32 | Candidate pairs: baseline / append / original slots | Term evaluations: baseline / append / original slots | Rule enumerations | Graph writes: baseline / both event arms |
|---|---:|---:|---:|---:|
| Recognition | 324,976 / 322,192 / 321,872 | 3,048,748 / 3,035,788 / 3,034,252 | 96,224 | 129 / 259 |
| Recurrent residual | 323,692 / 321,035 / 320,591 | 3,050,449 / 3,037,980 / 3,035,886 | 97,057 | 129 / 258 |

The original-slot arm saves an additional 1,536 Term evaluations over append on recognition and 2,094 on recurrent residual. Candidate-pair savings over append are 320 and 444 respectively. The five eventized ProblemShape rules do the same work in both event arms. `ps_redecode` remains a global scan and is unchanged.

The append arm exactly reproduces the six non-ProblemShape Term-evaluation increases identified in the earlier attribution run:

| Rule | Recognition increase | Recurrent-residual increase |
|---|---:|---:|
| `ca_mark_cut` | 320 | 320 |
| `ca_step_mag` | 320 | 320 |
| `ca_step_res` | 320 | 320 |
| `retire_duplicate_residual_concern` | 320 | 630 |
| `resolve_reply_fix_gap` | 128 | 252 |
| `resolve_self_account_gap` | 128 | 252 |

Each value is identical in every triad. The original-slot arm has zero counter changes in every non-ProblemShape rule. Since the only intended treatment difference between the event arms is where those five rules enter the ordered native rule vector, this is direct evidence that rule placement/order caused the collateral work on these two workloads.

## Timing and limits

Median wall ratios against baseline were 1.000 (range 0.946–1.431) for append and 0.992 (0.756–1.319) for original slots on recognition; recurrent-residual medians were 1.026 (0.743–2.098) and 1.131 (0.905–2.101). CPU ratios were similarly variable. The counter reduction did not produce a resolved CPU-time improvement. Eventization also doubled graph writes.

This is a causal work-attribution result for two authored N=32 workloads. It is not evidence that natural workloads have cheap separators, that whole-engine execution is substantially faster, or that rung 3/4 induction is tractable. The independent cold/warm seed-cache result also showed that the loader can change rule order unless cache state is controlled; V1.7 held that state fixed. A follow-up source repair now preserves cold-build order through the warm cache and passes a focused cold/warm probe ([cache repair results](SUBSTRATE_SEED_INDEX_CACHE_ORDER_FIX_V2_RESULTS.md)).

## Artifacts

- Protocol amendment: [`V1.7 amendment`](SUBSTRATE_PROBLEM_SHAPE_RULE_ORDER_PRESERVATION_V1_7_AMENDMENT_20260925.md)
- Runner: [`V1.7 runner`](../../../scripts/substrate_problem_shape_rule_order_preservation_v1_7.py)
- Corpus transformer: [`immutable snapshot builder`](../../../scripts/substrate_problem_shape_rule_order_seed_transform_v1_4.py)
- Corpus lock: [`V1.7 corpus lock`](../../../evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json)
- Source lock: [`V1.7 lock`](../../../evaluation/substrate_capability/problem_shape_rule_order_preservation_v1_7_lock_20260925.json)
- Raw data: [`V1.7 report`](../../../evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_7_20260925.json)
- Analyzer: [`V1.7 analyzer`](../../../scripts/analyze_substrate_problem_shape_rule_order_preservation_v1_7.py)
- Analysis: [`V1.7 analysis`](../../../evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_7_analysis_20260925.json)
- Cold/warm probe: [`cache-order runner`](../../../scripts/substrate_seed_index_cache_order_probe.py), [`probe report`](../../../evaluation/reports/substrate_seed_index_cache_order_probe_20260925.json)
- Cache repair verification: [`V2 probe runner`](../../../scripts/substrate_seed_index_cache_order_probe_v2.py), [`V2 probe report`](../../../evaluation/reports/substrate_seed_index_cache_order_probe_v2_20260925.json)
- Earlier gate checkpoints: [`V1.5 cold/warm order diagnostic`](SUBSTRATE_PROBLEM_SHAPE_RULE_ORDER_PRESERVATION_V1_5_DIAGNOSTIC.md), [`V1.6 append-block gate checkpoint`](../../../evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_6_partial_20260925.json)
