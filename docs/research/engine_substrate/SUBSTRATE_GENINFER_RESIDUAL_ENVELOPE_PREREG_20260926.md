# GenInfer residual envelope preregistration (2026-09-26)

## Question

Which residual kinds and dimensionality budgets does `GenInfer` accept alongside a recovered 2-D linear generator, and does a symbolic mapping conflict refuse?

## Design

Use the four locked matrices, four points, and unique predicates from the transform-family protocol. For each map, test five conditions: `positive`; `global_shift_r` adds +1 to target coordinate slot 1 for every relation; `two_slot_shifts_max2` adds +1 to slot 1 and +2 to slot 2 for every relation with `max_dims=2`; `two_slot_shifts_max1` applies the same target with `max_dims=1`; and `global_substitution` changes every target value from red to blue. Five repetitions per cell. Read `explained`, `matrix`, `residual_dims`, `transforms`, `dims`, and `checked`, without timing.

Add two five-repeat conditions on a repeated-predicate signature using the asymmetric scale/shear map and points `(0,0),(1,0),(2,0),(0,2)` with predicates `p0,p0,p1,p1`: `repeated_predicate_nonuniform_numeric` increments target slot 1 by +1 on relation 0 and +2 on relation 1; `repeated_predicate_symbolic_conflict` changes the first two target values to blue and green respectively, leaving the other two red. These exact inputs follow an exploratory run. The numeric case's alternate recovered matrix/residual decomposition is a characterization target, not a prediction of matrix-only fit.

## Expected outputs and gates

Each positive returns the exact matrix with no residual. Each global shift returns the same matrix plus the corresponding single `shift`; two shifts are accepted with `max_dims=2` as two ordered transforms and refused with `max_dims=1`; global substitution returns the same matrix plus a `subst` mapping red to blue. The repeated-predicate numeric case is expected to return matrix `[-2,-2,0,2]` with two predicate-local shifts on dim 1: p0 +3 then p1 +6. The repeated-predicate symbolic conflict is expected to refuse with an empty matrix and no transforms. All successful calls check 6,560 candidates. Verify all 110 observations, source construction, outputs, balanced repetitions, and source/native hashes.

## Claim boundary

This is an evaluator decomposition envelope for small 2-D integer-linear fixtures. It does not establish precision/recall for natural residuals, search cost beyond this bound, or full-seed mint/reuse behavior.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_residual_envelope_probe_v1.py
python3 scripts/analyze_substrate_geninfer_residual_envelope_probe_v1.py
```
