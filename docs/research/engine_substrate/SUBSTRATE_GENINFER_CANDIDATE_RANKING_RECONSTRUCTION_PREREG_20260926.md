# GenInfer candidate-ranking reconstruction preregistration (2026-09-26)

## Purpose

Reconstruct, from source-documented operations, the finite candidate set and Occam ranking for the captured repeated-predicate identity-ablation cases. This is a diagnostic model, not an instrumented native candidate trace.

## Method

Read every condition from the locked identity-ablation capture. For each source signature, derive B from the same max normalized coordinate extent, enumerate every non-identity 2×2 integer matrix in `[-B,B]^4`, apply origin-normalized `M·(v−min)`, sort transformed held and observed tuples by the substrate's canonical value order (all fixture slots are strings or integers), and zip them positionally. Reproduce the numeric `build_candidate` checks: globally uniform slot deltas merge; otherwise each predicate group must have an internally uniform delta; zero groups are omitted; accept only when transform-entry count equals differing-slot count and is ≤ `max_dims`. Rank eligible candidates by `(residual entry count, sum(abs(matrix entries)), lexicographic matrix)`.

## Gates and interpretation

For every layout × identity mode × corruption magnitude (18 cells; five native repeats per cell), the reconstructed checked count and winner fields (`explained`, `matrix`, `residual_dims`, `transforms`, `dims`) must match the native capture exactly. Report the winning score, number of eligible candidates, first ten candidates in score order, and whether the generating matrix is eligible and its score. A mismatch means the reconstruction is incomplete and must not be used to explain the native decision. Agreement validates this reconstruction only over the small, numeric fixture family; it is not a proof of all source semantics or a substitute for instrumenting the native loop.

## Reproduction

```sh
python3 scripts/reconstruct_geninfer_candidate_ranking_v1.py
python3 scripts/analyze_geninfer_candidate_ranking_v1.py
```
