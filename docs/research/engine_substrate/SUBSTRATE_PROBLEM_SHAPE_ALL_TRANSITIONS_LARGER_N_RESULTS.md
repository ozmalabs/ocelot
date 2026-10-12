# ProblemShape all-transition eventization at larger N

**Run date:** 2026-09-25  
**Status:** exploratory, preregistered fresh-process paired scaling probe.

## Result

The baseline closure and all-transition event/index candidate produced matching initial/final statuses and per-step mint transitions in all 12 pairs at N=16 and N=32. Each size had six fresh-process pairs, three in each arm order, with 24 unique worker PIDs total. The independently checked work counters were stable across pairs.

| N | ProblemShape candidate pairs, baseline → candidate | Term evaluations, baseline → candidate | Candidate/baseline wall median (paired bootstrap 95% interval) | Candidate faster |
|---:|---:|---:|---:|---:|
| 16 | 963 → 182 (−81.1%) | 6,223 → 2,492 (−60.0%) | 0.993 (0.946–1.067) | 3/6 |
| 32 | 3,707 → 606 (−83.7%) | 22,135 → 7,572 (−65.8%) | 1.043 (0.953–1.218) | 2/6 |

The operation-count reduction persists and grows in percentage terms across these two sizes. It does not produce a demonstrated wall-time gain: both bootstrap intervals include 1, the N=32 median is 4.3% slower, and only two N=32 pairs favor the candidate. Median candidate index-maintenance time was 0.77 ms at N=16 and 1.66 ms at N=32. Median peak RSS was about 1.792 GB in both arms and sizes, dominated by full runtime startup in this experiment.

## Measurement correction

The paired runner's raw baseline summaries defaulted absent `ps_mint` summary fields to zero. Those zeros are missing-field defaults, not baseline measurements. The independent analysis excludes them; aggregate ProblemShape candidate-pair and Term-evaluation totals are present and support the comparisons above. Candidate-only `ps_mint` counters are retained as diagnostics but are not used to infer a baseline delta. The raw report is preserved unchanged, and the correction is explicit in the analysis JSON.

## Scope

This tests one authored recurrent-residual sequence at two larger population sizes. It does not establish an asymptotic complexity class, a natural-task distribution, or substrate-wide scaling. Six pairs per size leave substantial timing uncertainty. It also does not answer how interleaved/varied task sequences, persistence/rebuild, rollback, concurrency, or native allocation affect the design. No default-path change follows from these results.

## Artifacts

- Preregistration: [`SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_LARGER_N_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_LARGER_N_PREREG_20260925.md)
- Runner: [`substrate_problem_shape_all_transitions_larger_n.py`](../../../scripts/substrate_problem_shape_all_transitions_larger_n.py)
- Independent analyzer: [`analyze_substrate_problem_shape_all_transitions_larger_n.py`](../../../scripts/analyze_substrate_problem_shape_all_transitions_larger_n.py)
- Input lock: [JSON](../../../evaluation/substrate_capability/problem_shape_all_transitions_larger_n_lock_20260925.json)
- Raw paired records: [JSON](../../../evaluation/reports/substrate_problem_shape_all_transitions_larger_n_20260925.json)
- Validated analysis: [JSON](../../../evaluation/reports/substrate_problem_shape_all_transitions_larger_n_analysis_20260925.json)
