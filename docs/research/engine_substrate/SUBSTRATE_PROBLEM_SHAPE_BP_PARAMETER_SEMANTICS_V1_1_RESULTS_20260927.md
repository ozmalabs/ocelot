# ProblemShape BP parameter semantics v1.1 results (2026-09-27)

## Outcome

All six fresh workers (two per resident index 0, 25, and 50) pass source-lock, Goal-resolution, output-finiteness, and no-commit computational-state parity gates. Every `max_product` and `sum_product` pair has the same ProblemShape key, as designed, but all six pairs return different final belief maps. The maximum per-variable absolute difference is 2.0 in every pair. `sum_product` converges in all six runs; `max_product` reports nonconvergence in four. Two resident indices show the same result in both replicates.

This confirms that the current ProblemShape key identifies a common structural Goal schema while omitting a parameter that changes solver behavior on these fixtures. Recognition/reuse by that key must not be read as solver-output equivalence. It does not by itself make the design incorrect: the codebook claims structural shape, and the `combine` value remains on each Goal for its solver.

## Limits and interpretation

Only three selected resident networks and two combine settings were compared. The panel does not establish which combination is more accurate or useful, whether one is preferable on other networks, or the prevalence of either setting in natural tasks. Nonconvergence and belief differences are observable outputs, not quality judgments. The protocol checks unchanged concept computational fields (`state`, `external_field`, `identity_field`) across the `commit=False` calls; it does not inspect all native graph state or all edge metadata.

The v1 exploratory capture is retained separately. Its full-attribute no-commit check failed because ordinary rule closure added `is_ambivalent` metadata; v1.1's preregistered computational-field check isolates the solver-state parity claim. This failure does not erase the separately visible v1 belief contrasts, but only v1.1 is used for the integrity-passed result above.

## Artifacts

- Confirmatory preregistration: [SUBSTRATE_PROBLEM_SHAPE_BP_PARAMETER_SEMANTICS_V1_1_PREREG_20260927.md](SUBSTRATE_PROBLEM_SHAPE_BP_PARAMETER_SEMANTICS_V1_1_PREREG_20260927.md)
- Runner: [substrate_problem_shape_bp_parameter_semantics_v1_1.py](../../../scripts/substrate_problem_shape_bp_parameter_semantics_v1_1.py)
- Input lock: [problem_shape_bp_parameter_semantics_v1_1_lock_20260927.json](../../../evaluation/substrate_capability/problem_shape_bp_parameter_semantics_v1_1_lock_20260927.json)
- Raw workers: [problem_shape_bp_parameter_semantics_v1_1_20260927.json](../../../evaluation/reports/problem_shape_bp_parameter_semantics_v1_1_20260927.json)
- Independent analyzer: [analyze_substrate_problem_shape_bp_parameter_semantics_v1_1.py](../../../scripts/analyze_substrate_problem_shape_bp_parameter_semantics_v1_1.py)
- Independent analysis: [problem_shape_bp_parameter_semantics_v1_1_analysis_20260927.json](../../../evaluation/reports/problem_shape_bp_parameter_semantics_v1_1_analysis_20260927.json)
- Excluded v1 gate-failed capture: [problem_shape_bp_parameter_semantics_v1_20260927.json](../../../evaluation/reports/problem_shape_bp_parameter_semantics_v1_20260927.json)
