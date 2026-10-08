# GenInfer held-out relation evaluation preregistration

**Lock date:** 2026-09-26, before capture. **Question:** do the matrix and predicate-local residuals selected from training relations predict withheld relations from the same underlying 2-D generator?

Use known matrix `[1,1,0,2]` and eight points `(0,0),(1,0),(0,1),(1,1),(2,0),(0,2),(2,1),(1,2)`. Cross three predicate assignments—`adjacent_01: p0={0,1,4,6}`, `opposite_03: p0={0,3,4,7}`, and `adjacent_12: p0={1,2,5,6}`; all remaining rows are p1—with three training conditions: clean, +1 in coordinate slot 1 on every training p0 relation, and inconsistent +1/+2 on the first two training p0 relations. Each assignment holds out one p0 and one p1 row (respectively indices `{6,7}`, `{7,6}`, `{6,7}`).

For each training condition, score two held-out targets: clean generator output, and output with the same +1 p0 shift as the uniform training condition. The inconsistent training condition uses clean and +1 held-out targets as well; it does not extrapolate a guessed +2 pattern. The inferred matrix and returned residual transforms are applied mechanically to each withheld base row. Primary measures: exact matrix recovery, training decomposition acceptance, exact held-out relation accuracy and per-predicate accuracy. Five repeats per cell. No perturbation case is required to pass; the clean training/clean holdout cells must recover the known matrix and predict all holdouts exactly.

Only the six training relations enter the codebook signature and GenInfer goal. The two held-out relations are stored separately and are never passed to the evaluator. Record all fields, applied predictions, outcomes, candidate counts, and source/native provenance. The analyzer reconstructs both partitions and predictions independently.

This is a controlled, small 2-D generalization diagnostic, not an estimate of natural-task accuracy or end-to-end learning cost. Reproduction: `PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_heldout_relation_probe_v1.py` and `python3 scripts/analyze_geninfer_heldout_relation_probe_v1.py`.
