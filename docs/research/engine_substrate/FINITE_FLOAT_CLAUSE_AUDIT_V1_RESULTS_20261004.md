# Finite-float clause audit v1 results (2026-10-04)

## Result

The locked 4,096-case audit passes all six independent checks. The clause
solver and an independently implemented bound-intersection reference agree
on every status: 690 conjunctions are satisfiable and 3,406 are unsatisfiable
over finite binary64 values. Across 20,160 generated comparisons, there are
zero status confusions. All 690 satisfying witnesses satisfy every
constraint in Python and return true through native Term evaluation; there
are zero invalid witnesses or native disagreements.

The seeded corpus mixes one- and two-variable conjunctions, 1–8 comparisons,
compatible and contradictory bounds, repeated equalities, signed zero,
subnormal values, adjacent floats, large magnitudes, and the largest finite
values. The capture processed about 72,396 cases/s (56.6 ms total wall time)
on this run. This is an implementation-specific microbenchmark, not an engine
scaling estimate.

## Interpretation and limits

This strengthens the direct unary comparison proof fragment with broad
differential evidence and native witness parity. The independent oracle uses
bound intersection, while the solver uses literal endpoints and adjacent
representable candidates. The sample does not constitute a formal proof of
the implementation, and it does not cover NaN or infinity inputs,
cross-variable constraints, arbitrary Boolean Terms, or query proposal
completeness. The next gate is proof-oracle verification over larger
adversarial boundary combinations plus generated variable-alias formulas;
keep the scope explicitly restricted to finite binary64 unary comparisons.

## Reproduction

- [Protocol](FINITE_FLOAT_CLAUSE_AUDIT_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/finite_float_clause_audit_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_finite_float_clause_audit_v1.py)
- [Lock](../../../evaluation/substrate_capability/finite_float_clause_audit_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/finite_float_clause_audit_v1_20261004.json)
- [Analysis](../../../evaluation/reports/finite_float_clause_audit_v1_analysis_20261004.json)
