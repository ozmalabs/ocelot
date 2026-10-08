# ProblemShape rule-order preservation V1.4 results

Date: 2026-09-25  
Status: locked exploratory comparison; all validity gates passed

## Result

The V1.4 candidate installs the five eventized ProblemShape rules in their original seed slots. Both arms loaded from immutable snapshots made from the same locked 831-file seed corpus. All 12 paired comparisons (six per workload) passed semantic parity, seed-load order and failure parity, exact active-rule-name order through pre-observation, and unique-process checks. The complete baseline snapshot matches every seed hash in the corpus lock. The candidate snapshot matches every locked seed byte except its intentionally transformed `problem_shape_growth.json`.

| Workload, N=32 | Whole-seed candidate tests, baseline → eventized | Whole-seed Term evaluations, baseline → eventized | Rule enumerations | Median wall ratio (range) | Median CPU ratio |
|---|---:|---:|---:|---:|---:|
| Recognition | 324,976 → 321,872 (−0.96%) | 3,048,748 → 3,034,252 (−0.48%) | 96,160 → 96,160 | 1.009 (0.935–1.128) | 0.996 |
| Recurrent residual | 323,692 → 320,591 (−0.96%) | 3,050,449 → 3,035,886 (−0.48%) | 96,993 → 96,993 | 1.003 (0.964–1.043) | 1.000 |

For both workload mixes, all audited counters for every non-ProblemShape rule were identical in every pair. The whole-seed reductions come entirely from `ps_decode`, `ps_recognize`, `ps_residual`, and `ps_mint`. `ps_redecode`, which remains a global invalidation scan, did not change. Candidate graph writes approximately doubled (129→258/259), so the smaller closure workload does not translate into a measured latency improvement. The timing intervals are broad and cross parity.

The eventized-rule Term-evaluation deltas were identical across the six pairs within each mix:

- Recognition: decode −4,096; recognize −5,120; residual −2,640; mint −2,640.
- Recurrent residual: decode −4,096; recognize −5,120; residual −2,645; mint −2,702.

## Interpretation limits and next gate

This establishes that eventization can reduce its own matching work without collateral per-rule counter changes when its rules retain their seed positions, on these two authored N=32 workloads. It does **not** prove that the gains seen in six other rules in the earlier append-order experiment were caused by rule placement: that earlier run did not use the same immutable corpus snapshot, so the cross-run contrast is not a controlled causal comparison. The next targeted experiment should compare baseline, appended rules, and original-slot rules from one shared immutable seed corpus, randomize arm order, and retain the same semantic, per-rule, and timing gates.

Timing remains inconclusive. This is not evidence for natural-task frame locality, substrate-wide tractability, learning capability, or scaling beyond N=32.

The live seed corpus changed after the locked snapshot was made. This did not alter V1.4's worker inputs: snapshot verification confirms byte-for-byte identity with the lock. The post-run live corpus digest is recorded separately in the machine-readable analysis, and later runs must take a new corpus lock.

## Artifacts

- Protocol amendment: [`V1.4 amendment`](SUBSTRATE_PROBLEM_SHAPE_RULE_ORDER_PRESERVATION_V1_4_AMENDMENT_20260925.md)
- Runner: [`V1.4 runner`](../../../scripts/substrate_problem_shape_rule_order_preservation_v1_4.py)
- Immutable snapshot builder: [`V1.4 seed transformer`](../../../scripts/substrate_problem_shape_rule_order_seed_transform_v1_4.py)
- Corpus lock: [`V1.4 corpus lock`](../../../evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_4_20260925.json)
- Worker lock: [`V1.4 lock`](../../../evaluation/substrate_capability/problem_shape_rule_order_preservation_v1_4_lock_20260925.json)
- Raw data: [`V1.4 report`](../../../evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_4_20260925.json)
- Analyzer: [`V1.4 analyzer`](../../../scripts/analyze_substrate_problem_shape_rule_order_preservation_v1_4.py)
- Analysis: [`V1.4 analysis`](../../../evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_4_analysis_20260925.json)
- Failed predecessor retained for audit: [`V1.3 diagnostic`](SUBSTRATE_PROBLEM_SHAPE_RULE_ORDER_PRESERVATION_V1_3_DIAGNOSTIC.md)
