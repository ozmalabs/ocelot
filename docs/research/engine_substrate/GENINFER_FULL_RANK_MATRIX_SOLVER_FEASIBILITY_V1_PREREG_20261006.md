# GenInfer full-rank matrix solver feasibility v1

## Question

Can exact elimination recover a unique integer linear map from identity-aligned, full-rank examples in dimensions one through three, validate it on additional training relations, transfer it to held-out relations, and abstain when the source examples are rank deficient? This is an algorithm feasibility probe for a possible path beyond current GenInfer's explicit `n == 2` gate.

## Fixed method

- Use fixed authored integer matrices for dimensions 1, 2, and 3. Build training points from the origin, each unit vector, and two additional points; build a separate held-out point set.
- Recover a matrix with rational Gaussian elimination from a greedily selected independent set of identity-aligned displacement vectors. Accept only integral coefficients and verify every training relation exactly.
- Apply the recovered matrix to held-out points and require exact equality. A separate repeated-origin data set is rank deficient and must return no candidate.
- Record solver elapsed time and the current exhaustive candidate count `(2B+1)^(d²)-1` for the maximum coordinate bound in each training fixture. This count is an analytical comparison, not an executed enumeration.
- Preserve runner, analyzer, and protocol hashes in the output. Refuse to overwrite a prior result.

## Scope limits and decision gate

This probe does not call the Rust evaluator or establish native GenInfer behavior, feature integration, graph semantics, candidate ranking parity, or production performance. A successful result only shows that a full-rank exact-solve route is feasible on authored fixtures. The next gate must compare the solver with exhaustive enumeration on small bounded cases, then integrate an opt-in native path and capture current-kernel refusal, exact semantics, held-out transfer, rank-deficient abstention, false acquisition, operation counts, timing, and memory. Rank-deficient inputs require a separate bounded search or honest refusal; this probe makes no claim about them beyond abstention.

## Reproduction

```sh
python3 evaluation/substrate_capability/geninfer_full_rank_matrix_solver_feasibility_v1.py
python3 evaluation/substrate_capability/analyze_geninfer_full_rank_matrix_solver_feasibility_v1.py
```
