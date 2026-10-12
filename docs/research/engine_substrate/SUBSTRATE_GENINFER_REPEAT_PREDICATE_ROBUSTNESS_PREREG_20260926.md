# GenInfer repeated-predicate recovery robustness preregistration (2026-09-26)

## Question

How do repeated-predicate geometry and within-predicate numeric corruption magnitude affect recovery of the generating matrix, residual decomposition acceptance, and inferred residual complexity?

## Locked design

Use matrix `[1,1,0,2]`, predicates `[p0,p0,p1,p1]`, and three point layouts in relation order: `original=[(0,0),(1,0),(2,0),(0,2)]`, `orthogonal_pairs=[(0,0),(0,1),(1,0),(1,1)]`, `paired_square=[(0,0),(1,0),(0,1),(1,1)]`. Conditions per layout are exact `positive` and `corrupt_p0_r_1/2/3`, where only relation 0's target row-coordinate is incremented by the suffix magnitude. Use five repetitions per layout/condition, fresh substrate per cell, `max_dims=2`, and read `explained`, `matrix`, `residual_dims`, `transforms`, `dims`, and `checked`. No timings are collected.

## Metrics and gates

Independently reconstruct every source/target signature. Positive cases must return the generating matrix with no residual. All five repeated calls within each cell must return identical fields. Record, without a pass threshold, corruption acceptance rate, exact-generating-matrix recovery rate, alternative-matrix rate, candidate count, and residual forms by layout and magnitude. Check complete 60-observation factorial, finite/valid output types, and current source/native hashes.

## Claim boundary

Three small 2-D layouts, one generating matrix, one repeated-predicate pair receiving a row-coordinate perturbation, and three magnitudes. This is a robustness surface for one inducer and does not estimate natural-task error rates or establish general identifiability.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_repeat_predicate_robustness_probe_v1.py
python3 scripts/analyze_substrate_geninfer_repeat_predicate_robustness_probe_v1.py
```
