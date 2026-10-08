# ProblemShape observation-population scale v2 results (2026-09-27)

## Integrity and state outcomes

Twelve fresh processes cover N=16/32/64 × recognition/recurrent-residual × dynamic/frozen. All workers have unique PIDs, match their locked current-source/native inputs, and pass the reused worker's exact initial/final status, mint-count, codebook-mode, and fixed-point checks. The independent raw analyzer passes all twelve cell/status checks and the separate candidate-count relation below.

## Primary operation counts

| N | Recognition dynamic: all PS candidate pairs | Recognition frozen | `ps_mint` candidate pairs / term evaluations, dynamic | Recurrent residual dynamic / frozen mints |
|---:|---:|---:|---:|---:|
| 16 | 952 | 816 | 136 / 680 | 1 / 0 |
| 32 | 3,696 | 3,168 | 528 / 2,640 | 1 / 0 |
| 64 | 14,560 | 12,480 | 2,080 / 10,400 | 1 / 0 |

For recognition-only dynamic workers, the recurrence guard independently satisfies `N(N+1)/2` candidate pairs and five term evaluations per pair at all three sizes. Frozen workers remove exactly those guard checks. Total ProblemShape candidate work still includes `ps_decode`, `ps_recognize`, `ps_residual`, and `ps_redecode`; it is not the same count as the `ps_mint` guard alone. From N=16→32→64, total recognition candidate pairs increase by 3.882× then 3.939×, near the 4× ratios expected when doubling N for this controlled workload. These three points characterize only the authored pathway, not a general complexity bound.

The recurrent-residual dynamic stream produces one mint at each N, with later observations recognized after re-decode; frozen streams produce zero mints and leave all observations residual. Both modes settle at reported fixed points. The result shows behavior remains stable through 64 observations on this repeated shape; no false-mint or alternate-shape control is included here.

## Cost and comparability

The runner enables native scale audit and per-rule counters during observations. Candidate/term counts are the primary evidence; per-observation wall/CPU fields are instrumentation-contaminated and should be treated as descriptive. Each full-seed boot also loads hundreds of manifests, so these values do not isolate learner-only startup cost.

The prior N=2/4/8 v1 report uses native extension SHA-256 `4152737c…`; this v2 extension uses `a8906948…`. They are not pooled into a single current-source scale curve. The larger-N v2 series is internally source-locked and reproducible on its own.

## Interpretation and next work

This extends one controlled rung-three pathway and confirms its quadratic recurrence-guard candidate sequence at larger populations. It does not estimate how often natural inputs become residuals, how often minting is useful, or whether learned structure improves held-out capability. The next learning evaluation should add varied schemas, singleton/false residual controls, repeated and one-off novelty, and independent held-out transfer under dynamic/frozen and memory-only controls; report acquisition cost and false mint separately. For runtime scaling, pair these operation counts with an uninstrumented twin and larger task families.

## Artifacts

- [Preregistration](SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_V2_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_problem_shape_population_scale_v2.py)
- [Independent analyzer](../../../scripts/analyze_substrate_problem_shape_population_scale_v2.py)
- [Source lock](../../../evaluation/substrate_capability/problem_shape_population_scale_v2_lock_20260927.json)
- [Raw capture](../../../evaluation/reports/problem_shape_population_scale_v2_20260927.json)
- [Analysis](../../../evaluation/reports/problem_shape_population_scale_v2_analysis_20260927.json)
- [Prior v1 results and non-comparable source](SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_RESULTS.md)
