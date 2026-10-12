# Finite-float clause audit v1 preregistration

## Question

Does the direct unary comparison solver classify satisfiability correctly over finite binary64 inputs, including representational boundary cases, and do its satisfying witnesses agree with native Term evaluation?

## Frozen generator

Generate 4,096 deterministic conjunctions with one or two variables and 1–8 direct `Eq`, `Lt`, `Lte`, `Gt`, or `Gte` comparisons per variable. Mix consistent intervals, contradictory bounds, repeated/equal literals, and seeded random finite binary64 constants. The value pool includes signed zeros, subnormals, adjacent representable numbers, large magnitudes, and the largest finite values. Seed: `20261004`.

## Independent reference and gates

Use an independently written interval intersection oracle: consolidate equality, lower, and upper bounds per variable, then choose the least allowed finite float above the maximum lower bound and check the minimum upper bound. Compare every solver status to the reference. For each satisfiable solver result, validate its witness against every comparison both in Python and by native Term evaluation. Lock all generated cases and sources; report status confusion counts, native agreement, solver time/CPU, case throughput, and comparison count. Zero status errors and zero native disagreement are required.

## Scope

This validates only conjunctions of unary numeric order/equality constraints over finite binary64 values. It does not cover NaN/infinity inputs, cross-variable relations, arbitrary Boolean Terms, or whether the broader query policy proposes every useful witness.
