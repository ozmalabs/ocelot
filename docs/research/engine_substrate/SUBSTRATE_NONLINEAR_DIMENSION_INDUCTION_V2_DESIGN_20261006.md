# Bounded quadratic-map induction v2: design gate

## Status

This is an implementation design, not a substrate capability result. The
existing v1.5 production route searches 2×2 integer matrices and rejects the
registered coupled-quadratic map because no such matrix passes residual
validation. This design adds one explicitly bounded, opt-in hypothesis family
without widening that matrix enumeration.

## Candidate family

For two integer coordinate dimensions, normalize each input axis to its
frame's minimum and represent each output coordinate as an exact integer
combination of the five non-constant total-degree-2 monomials
`[x, y, x², xy, y²]`. The resulting 2×5 coefficient matrix is the
`quadratic2` generator payload. Translation remains the existing residual
stage; no intercept is fitted. Initially require integer coefficients with
absolute value at most 8, exact integer arithmetic with checked overflow, and
exact agreement on every identity-aligned training relation. Refuse if the
training design is rank-deficient, identity matching is ambiguous, a
coefficient is non-integral/out of bound, or any training residual remains.

Recover coefficients by exact elimination from stable predicate+`id` pairs,
then validate the single recovered operator across all training relations.
Do not enumerate coefficient tuples. For fixed five monomials, solving is
`O(N·5² + 5³)` arithmetic per candidate base and validation is `O(N·5)`;
report actual row/operation counts and checked-arithmetic refusals. Keep the
existing linear candidate as the preferred simpler hypothesis when both fit.

## Fixture identifiability preflight

The prior coupled-quadratic fixture used x coordinates only in `{0,1}`. There
`x²=x`, so its training feature design has rank 4 instead of 5 and cannot
identify the `x²` coefficient. The v2 basis coordinates are
`(1,0),(2,0),(0,1),(0,2),(1,1)`; their exact feature determinant is 4 and
rank is 5. Solve on differences from a reference relation so an output
translation remains a rung-1 residual. Add `(3,1)` and `(4,1)` as
overdetermining training-validation points and require the same exact residual
translation on every row before minting; this rejects the registered cubic
out-of-family control instead of allowing a five-point interpolant. For
`F(x,y)=(x+xy,y+x²)`, exact rational elimination recovers
coefficient rows `[1,0,0,1,0]` and `[0,1,1,0,0]`. Six disjoint held-out
coordinates transfer exactly. An independent exhaustive check finds no
affine integer 2×2 map with entries in `[-8,8]` that fits the training pairs.
The reproducible preflight is [here](../../../evaluation/substrate_capability/nonlinear_quadratic_basis_preflight_v1.py)
and its [machine-readable result](../../../evaluation/reports/nonlinear_quadratic_basis_preflight_v1_20261006.json).

## Required engine changes

The current `Generator` carries a data-defined matrix only for `kind="linear"`;
`GenAttempt` and the `GenInfer` output expose a matrix; and the graph seed rule
hardcodes the minted kind as `linear`. A real learned quadratic operator
therefore requires a new kind and coefficient payload through the complete
path: native operator application, candidate fitting and ranking, Term output,
seed mint rule, `DimensionGenerator` loading, `DimInfer` reuse, persistence, and
scale-audit attribution. Use an explicit coefficient attribute rather than
mislabeling a polynomial as a matrix. Put acquisition behind a Cargo feature
and a runtime opt-in so feature-off behavior remains byte-for-byte unchanged.

## Evaluation before enabling by default

The confirmatory evaluation should compare feature-off and feature-on arms on
fresh substrates and preserve the existing linear positive control. Include:

- full-rank coupled-quadratic training and identity-disjoint held-out transfer;
- a second quadratic map and the corresponding linear map, to distinguish
  family coverage from a single hardcoded target;
- rank-deficient geometry, duplicate/missing IDs, ambiguous predicates,
  corrupted training rows, and nonlinear out-of-family controls;
- exact training fit, held-out prediction, generator receipt, mint count,
  pre/post codebook, and refusal parity;
- solver row operations, candidates per eligible base, validation work,
  closure time, allocation/RSS, and matched audit-on/off overhead.

Freeze candidate grammar, coefficient bound, identity semantics, source/native
inputs, generated fixtures, schedule, and analyzer before execution. Keep the
feature opt-in unless held-out transfer and all false-mint controls pass; report
this as one bounded 2-D polynomial family, not general nonlinear induction.
