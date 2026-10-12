# Label-blind query ranking v1 preregistration

## Question

Can a substrate-side finite-pool selector choose an input that best separates an explicit current hypothesis set, without consulting the answer oracle, across scalar, list-statistic, and topology task families?

## Implementation validation disclosure

The initial harness launch failed in three workers before recording measurements because the Python `Times` constructor requires a list argument. The run was interrupted, its stale pre-correction lock and error are preserved as `substrate_label_blind_query_ranking_v1_20260930_initial_failed_lock.json` and `substrate_label_blind_query_ranking_v1_20260930_initial_failure.json`. After correcting the constructor calls, one entropy-selector smoke worker per task family may be run to check setup/evaluation; those three workers are pilots and are excluded from the 120-worker locked panel. The confirmatory lock is refreshed after the corrected runner and analyzer are complete.

## Selector and tasks

The new `domains.query_selection.rank_queries_by_disagreement` evaluates every supplied hypothesis on every candidate and ranks candidates by predictive entropy under equal hypothesis weights. Ties prefer more distinct predictions, then original candidate order. The function accepts no oracle or labels.

Use three source-defined task fixtures and four policies:

- Triangular number: hypotheses `n`, `1`, `n²`, and `n(n+1)/2`; known `n=1`; candidate family `n=2..12`.
- Population variance: hypotheses `1`, `sum/n - 2`, `n-1`, and `((sum_sq - sum²/n)/n)`; known list `[2,4]`; candidate lists L0–L11 from the CEGIS variance fixture.
- Euler characteristic: hypotheses `1`, `ncells`, `V-E+F`, and `V-E+F+(V-1)(V-2)(V-3)`; known point/edge/triangle; the fixed Euler family from the existing CEGIS fixture. All four hypotheses fit the three known rows; the polynomial null term vanishes at the known simplex vertex counts and diverges on selected non-simplex candidates.

Policies are fixed-first, seeded-random, entropy-ranked (the new selector), and oracle-best upper bound. Run ten deterministic replicates per task-policy (120 fresh processes) in one source-locked randomized schedule. For non-oracle policies, reveal only the selected candidate's answer and charge one oracle call. The oracle-best arm evaluates all candidates, selects the point that leaves the fewest hypotheses consistent with its actual answer, and is explicitly charged one call per candidate. All policies use the same hypothesis set and candidate pool within a task.

## Measures and integrity gates

Record ranked candidate scores and predictions, selected input, oracle query/answer pairs, surviving hypothesis IDs, whether the true hypothesis survives alone, selector evaluation count, oracle-call count, and wall/CPU time. Independently reconstruct task labels: triangular formula, Python population variance, and Euler characteristic from simplicial closure. Require source/native/task lock match, exact schedule/cell count, unique PIDs, each hypothesis fits the disclosed known examples, selected query belongs to the candidate pool, answer/call accounting, entropy ranking correctness, random schedule reconstruction, oracle-best optimality, survivor-set reconstruction, and no omitted worker failures.

## Claim boundary

This evaluates a real label-blind ranking utility over caller-supplied hypotheses and authored finite pools. It does not generate the hypotheses, assign prior weights, integrate the ranker into `cegis_synthesize`, establish natural-task prevalence, or demonstrate general active learning. Results should show where the selector is useful, where no single query identifies the true rule, and its scoring cost relative to one oracle call.
