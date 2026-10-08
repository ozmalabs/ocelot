# Query Index Reuse Across Thought-Experiment Branches v1

Status: preregistered bounded systems microbenchmark.

## Question

When multiple isolated hypothesis branches share the same immutable generated pool and query set, does a single cached prediction index reduce total selection compute compared with recomputing native predictions in every branch?

## Workload

Use the same three Euler anchors, fixed arithmetic grammar, candidate family, and completed max-size-5 generated pools as the Euler active-query evaluations. For each anchor and repetition, deterministically sample 20 hidden target hypotheses uniformly from the generated pool. In each branch, the hidden term supplies labels for selected candidates; the branch starts with the full pool and filters its own active-hypothesis list until one model remains. These are synthetic counterfactual label worlds, not calls to an external oracle and not a full Rust `Substrate` fork.

Measure branch batches of 1, 5, and 20, for five repetitions per anchor, using paired uncached/cached runs with arm order alternated by anchor and repetition. The cached arm builds one `QueryRankingIndex` per batch and reuses it across all branches in that batch. The uncached arm reevaluates each active hypothesis/query pair during every ranking round. Both arms use the same entropy tie breaking and absolute numeric response tolerance `1e-9`.

## Measures and gates

Record exact query-sequence and final-survivor parity by branch; unique recovery of each selected target; branch count; total and per-branch wall/CPU time; native term prediction calls; cached matrix build time; matrix heap estimate; queries to singleton; and generation cost. The cache build is charged once per batch, and memory is reported separately. The primary efficiency measure is paired total wall and CPU over a branch batch, including cache build for cached arms. Require exact branch-output parity and target recovery before reporting speed. Results are limited to serial in-process hypothesis branches; they do not establish concurrent safety, graph-level CoW, or natural-workload benefit.

## Reproduction

Create the source lock with `PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_query_index_branch_reuse_v1.py --lock`, then run the runner and analyzer. Captures use the `substrate_query_index_branch_reuse_v1_20260930` stem and are never overwritten.
