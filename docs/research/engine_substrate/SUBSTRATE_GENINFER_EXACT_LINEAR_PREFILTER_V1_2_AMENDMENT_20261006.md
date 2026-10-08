# Exact-linear GenInfer prefilter v1.2 amendment (2026-10-06)

## Trigger

The expanded oracle refusal panel exposed that `Value::as_i64()` truncates
`Float` values. The prefilter initially used that coercion in its coordinate
read, contrary to v1's explicit integer-lattice requirement. The failing
noninteger-affine control provided direct evidence of the gap.

## Correction and verification

The prefilter now extracts coordinates only from `Value::Int`. Any float,
rational, or other runtime value returns to historical enumeration. No
coefficient, bound, alignment, candidate, or mint rule changes. Add/retain
controls for noninteger coordinates, missing identity keys, duplicate
identity keys, rank deficiency, and multiple typed identity slots.

The source-locked finite oracle is expanded to run all five feature-gated
prefilter tests, including four full-rank point sets crossed with every one of
the 625 integer 2x2 matrices in `[-2,2]` and comparison against historical
candidate enumeration. The latest run passes all five tests and freezes the
2,500-case oracle digest before any v1 native main-panel capture. This amendment
does not change the remaining three-build panel or its admission criteria.
