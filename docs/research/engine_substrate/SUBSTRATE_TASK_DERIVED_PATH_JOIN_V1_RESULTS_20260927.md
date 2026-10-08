# Task-authored three-edge path join replay v1 results

Date: 2026-09-27 local

## Result

The 108-worker locked panel passes **987/987 independent checks**. It crosses three positive-path multiplicities, two decoy ratios, all six authored edge permutations, and three fresh-process repeats. The native matcher realizes four installed orders per graph setting. Plain and audit-on normalized graphs and closure reports agree within each worker; across permutations, all positive and negative controls produce identical normalized terminal state. The three clause counters conserve to each target-rule candidate-test total.

The real `sc_canary_requests_commit` policy rule reaches fixed point and produces exactly M commits and commit edges at each size. All positive canaries become `passed`, their patches become `transaction_queued`, and the parent reaches `commit_ready`; disconnected decoy patches and canaries remain unchanged.

| Positive paths M | Decoy ratio D/M | Relation population | Candidate tests, min–max | Current authored order `selected_patch → has_canary → has_canary_evidence` |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 4–5 | 5 |
| 1 | 4 | 5 | 12–13 | 13 |
| 8 | 0 | 8 | 32–40 | 40 |
| 8 | 4 | 40 | 96–104 | 104 |
| 32 | 0 | 32 | 128–160 | 160 |
| 32 | 4 | 160 | 384–416 | 416 |

For every setting, the minimum is the installed order `has_canary_evidence → has_canary → selected_patch`; the maximum is the seed-authored order. At M=32, the current order uses 25% more candidate tests than the minimum with no decoys and 8.3% more at D/M=4. The improvement in relative work shrinks as disconnected decoys grow because all relations have equal global counts and each order pays to traverse larger candidate populations. At M=1, two orders tie on the same minimum; at larger M four distinct orders are realized and the best is consistently the reverse path.

## Interpretation and limits

This extends order sensitivity to a task-authored three-edge path with real policy effects and an independent output oracle. It differs structurally from the four-edge cyclic discourse rule, but uses generated controlled graphs rather than a captured production self-change state. The sweep demonstrates semantic invariance and modest-to-material candidate-work differences on this rule only. The audit is enabled for attributed counters; timings are not used. This is not evidence for an automatic estimator, general task prevalence, or broad optimizer gains.

The next high-value gate is to capture a runtime-derived multi-edge rule and graph from a task execution, then compare its measured candidate work and any proposed partition/order prediction against the exact native trace. In parallel, the two task-authored fixtures now provide distinct path and cyclic topologies for predictor design and held-out evaluation.

## Artifacts

- [Preregistration](SUBSTRATE_TASK_DERIVED_PATH_JOIN_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_task_derived_path_join_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_task_derived_path_join_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/task_derived_path_join_v1_lock_20260927.json)
- [Raw workers](../../../evaluation/reports/substrate_task_derived_path_join_v1_workers_raw_20260927.json)
- [Analysis](../../../evaluation/reports/substrate_task_derived_path_join_v1_analysis_20260927.json)

Claim boundary: one authored self-change rule over generated positive/decoy graphs, six match permutations, three sizes, two decoy ratios, and three repeats. No live production-state or general tractability claim follows.
