# CEGIS query order sensitivity v2 preregistration

## Question

Does the v1 family-order sensitivity persist when every synthesis call uses the same literal set, independent of which output labels have already been revealed?

## Task and arms

Reuse the existing grounded triangular-number task and CEGIS implementation with the same known row (`n=1`), candidate inputs (`n=2..12`), heldout inputs (`17,23,50,99,100,250`), operators, size limit, timeout, and round limit. Compare five fresh-process paired runs of ascending family order and seeded permutations. The only treatment difference is family order.

Patch the CEGIS module's `synthesize` reference inside each isolated worker so every call delegates to native `domains.generator.synthesize` with the fixed literal set `{-1,0,1,2,3,6,10,15,21,28,36,45,55,66,78}`. This set contains the normal base literals and every possible triangular output on the complete candidate family, regardless of which examples are currently in the spec. Log every synthesis call, candidate count, oracle call, query, result, and cost. No persistent source module is modified by the worker patch.

## Protocol and measures

The worker and schedule are source-locked before the confirmatory run. Run ten fresh worker processes (five paired replicates) in a seeded randomized schedule. The analyzer reconstructs the arm orders, known/candidate/heldout labels, query order, synthesis-call counts, and per-worker exact heldout score; it checks worker uniqueness, source/native lock, complete schedule, no failures, and output consistency.

Report selected query sequences, convergence, exact heldout accuracy, queried-label count, oracle calls, aggregate native candidates explored, native synthesis elapsed time, and end-to-end CEGIS wall/CPU time. Interpret differences descriptively; five pairs on one function are not a policy superiority estimate.

## Claim boundary

This holds the enumerator literal vocabulary fixed, removing v1's label-dependent literal-set effect. The candidate family and target remain authored, the callable oracle still labels each candidate the current first-disagreement scan reaches, and only one function is tested. This is not a comparison with information gain, version-space selection, or a label-sealed choice among candidate queries.
