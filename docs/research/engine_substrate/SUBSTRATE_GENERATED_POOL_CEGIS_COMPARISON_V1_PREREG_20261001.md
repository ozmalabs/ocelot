# Generated-pool active query versus iterative resynthesis v1

Status: preregistered bounded confirmatory comparison.

## Question

Does entropy query selection over a complete, bounded generated hypothesis pool improve end-to-end learner cost or held-out correctness against the substrate's existing iterative MDL resynthesis loop, when both see the same labeled anchors and candidate queries?

## Task families

Use three target functions with independent input adapters and labels: triangular numbers, scalar squares, and Euler characteristic on two-dimensional simplicial complexes. Triangular and Euler oracles are grounded from held primitives by the existing task modules; the square oracle is a direct integer multiplication independent of the candidate DSL evaluation. Each task has a fixed small training set, a deterministic unlabeled query family, and disjoint held-out inputs. The query adapter exposes only input descriptors; the selection code receives no labels until it commits a query. The evaluator retains the oracle and held-out labels.

All arms use `Plus`, `Times`, `Minus`, and `Div`, literals `(0, 1, 2, -1)`, maximum expression size 5, and `include_output_constants=False`. Generated-pool mode has a 30-second complete-pool cap, a 10,000-solution cap, and no saturation stop. A pool is eligible for selector comparison only when `halt_reason == "max_size"` and the true target behavior is represented on all held-out inputs. A cap or incomplete pool is reported as a failure outcome, not excluded.

## Arms and accounting

- **Iterative MDL resynthesis:** synthesize the smallest fitting term, query the first disagreement in the locked candidate order, add its oracle label, and resynthesize. Count every candidate whose oracle is consulted, including candidates before the selected counterexample.
- **Generated-pool entropy:** enumerate the bounded pool once from the same training rows, then iteratively choose the remaining query with maximum predictive entropy and filter survivors by the returned label.
- **Generated-pool fixed-first:** use the same pool and filtering, choosing the first remaining query.
- **Generated-pool seeded-random:** use the same pool and filtering with `random.Random(20261001 + task_index)` and sample without replacement.

The generated pool is a different search strategy from single-survivor resynthesis. Therefore report both total learner work and conditional query efficiency; do not interpret fewer queries alone as an overall win. Charge synthesis/pool construction, entropy-index construction, ranking/filtering, oracle calls, and held-out evaluation separately. Record wall and CPU time, candidates/terms explored, solution count and stop reason, approximate retained index heap, query order, final survivors/recipe, and exact held-out correctness. Run each arm in a fresh child process with source-current engine provenance. Keep all attempts, including errors and timeouts, in the capture.

## Gates and claim limits

1. Source hashes, native build provenance, task identity, candidate/held-out disjointness, and fixed grammars match the lock.
2. Every active-policy query is in the declared candidate family, is queried at most once, and is labeled only after selection.
3. The complete-pool gate and held-out target-support gate are reported per task; partial pools do not count as selector successes.
4. On complete eligible pools, fixed/entropy/random policies preserve the target behavior whenever it is present and return the same correct/incorrect held-out verdict when their survivor sets are behaviorally equivalent.
5. The resynthesis arm records exact label queries, stop status, final fit, and held-out behavior. No timeout is recoded as convergence.

Three small authored functions cannot establish general task-distribution performance, natural residual frequency, or autonomous hypothesis invention. Query ranking over a complete precomputed pool does not prove that pool generation is tractable in general. This study does not alter the production CEGIS default or authorize persistent adoption of learned structure.

## Reproduction

Create the lock with `PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_generated_pool_cegis_comparison_v1.py --lock`, save it to `evaluation/substrate_capability/substrate_generated_pool_cegis_comparison_v1_20261001_lock.json`, then run the runner and `python3 scripts/analyze_substrate_generated_pool_cegis_comparison_v1.py`. The runner refuses stale locks or an existing raw capture.
