# ProblemShape all-transition eventization on recognition-only streams at larger N

**Run date:** 2026-09-25  
**Status:** preregistered exploratory fresh-process paired scaling probe.

## Result

The ordinary closure and all-transition event/index candidate matched every expected recognition status and fixed point in all 12 paired workers at N=16 and N=32. There were six pairs at each size, three in each execution order, with unique worker processes and stable aggregate counters.

| N | ProblemShape candidate pairs, baseline → candidate | Term evaluations, baseline → candidate | Candidate/baseline wall median (paired bootstrap 95% interval) | Candidate faster |
|---:|---:|---:|---:|---:|
| 16 | 952 → 168 (−82.4%) | 5,816 → 2,152 (−63.0%) | 1.024 (0.976–1.063) | 1/6 |
| 32 | 3,696 → 592 (−84.0%) | 21,616 → 7,120 (−67.1%) | 0.995 (0.934–1.046) | 3/6 |

This recognition-only workload has no mint recurrence. The treatment still substantially reduces measured candidate pairs and Term evaluations, showing the reductions are not limited to the recurrent-mint stream. Wall and CPU time do not show a reliable gain: the median CPU ratios are 1.025 and 1.033, and the wall bootstrap intervals at both sizes include parity. Median event/index maintenance is 0.82 ms at N=16 and 1.55 ms at N=32. Median process RSS remains about 1.79 GB in both arms, dominated by full-runtime startup.

## Measurement correction

The baseline worker summary omitted `ps_mint` aggregate fields, so its zero defaults are not measurements. Independent analysis excludes baseline `ps_mint` values. Candidate-side `ps_mint` counters are zero, consistent with the recognition-only arm, but are not used as a between-arm comparison. The raw report is retained unchanged and this correction is recorded in the analysis JSON.

## Scope

This is one authored recognition-only workload at two sizes with six pairs per size. It complements the recurrent-residual larger-N probe but does not establish natural-task prevalence, an asymptotic law, or substrate-wide performance. The two workloads both show operation-count reductions without a reliable wall-time improvement. Sequence variation, other task mixtures, persistence/rebuild, rollback, concurrency, and native allocation attribution remain open. No default-path change follows.

## Artifacts

- Preregistration: [`SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_RECOGNITION_LARGER_N_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_RECOGNITION_LARGER_N_PREREG_20260925.md)
- Runner: [`substrate_problem_shape_all_transitions_recognition_larger_n.py`](../../../scripts/substrate_problem_shape_all_transitions_recognition_larger_n.py)
- Independent analyzer: [`analyze_substrate_problem_shape_all_transitions_recognition_larger_n.py`](../../../scripts/analyze_substrate_problem_shape_all_transitions_recognition_larger_n.py)
- Input lock: [JSON](../../../evaluation/substrate_capability/problem_shape_all_transitions_recognition_larger_n_lock_20260925.json)
- Raw paired records: [JSON](../../../evaluation/reports/substrate_problem_shape_all_transitions_recognition_larger_n_20260925.json)
- Validated analysis: [JSON](../../../evaluation/reports/substrate_problem_shape_all_transitions_recognition_larger_n_analysis_20260925.json)
