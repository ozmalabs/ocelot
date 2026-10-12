# DimInfer nonlinear geometry-distribution evaluation v2 preregistration

## Question

Across a preregistered distribution of small integer point sets, how often does the full-seed DimInfer path select each intended held primitive/composition, and how often do other seeded generators plus predicate-local residual shifts explain the same target? Exact D4 identities are expected to remain unidentifiable from endpoints and are reported separately from geometry-dependent residual aliases.

## Geometry sampling

Generate 24 distinct unordered six-point sets uniformly by rejection from the 4×4 integer lattice `{0,1,2,3}²`, using seed `20260927`. Require both row endpoints 0 and 3, at least three distinct values on each axis, and at least one non-collinear triple. Canonically sort each accepted set and name it `geom_00`…`geom_23`. Preserve the generated list in the lock and raw report; the analyzer independently reproduces it. This is a controlled finite lattice distribution, not a natural-data sample.

Cross the same eight codebook families as v1.3 (five primitives and three two-step compositions), intact versus expected-generator ablation, and three fresh-process replicates. There are 24×8×3 = 576 worker processes, each constructing independent paired intact/ablated full-seed states and setting GenInfer off in both.

## Outcomes and gates

Require exact sample reproduction, balanced 576 cells, unique worker PIDs, stable source/native lock, complete records, exact requested generator removals, and GenInfer-off controls. Reconstruct each transformation and score: intended residual-free route; alternate residual-free route; alternate route with residual transforms; no transform; status; quantum delta; and closure time. Compare geometry-level incidence, not just pooled worker counts, because the three repeats share one geometry.

## Claim boundary

The study estimates alias and route frequencies under this explicitly sampled 4×4 point-set distribution only. It does not estimate natural-task frequencies or nonlinear induction capability. Algebraically identical generator sequences cannot be disambiguated from endpoints by adding geometries; report those as equivalence classes. Residual-bearing alternatives may vary with geometry and are the empirical focus.
