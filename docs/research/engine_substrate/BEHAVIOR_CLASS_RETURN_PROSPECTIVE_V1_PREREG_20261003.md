# Prospective behavior-class return policy v1 preregistration

Date: 2026-10-03

## Question

On fresh panels, can a substrate policy return an explicit finite prediction class instead of requesting a task-relevant hint, while preserving heldout correctness? How sensitive is that decision to zero/boundary probe coverage, and what are the measured local costs?

## Task and panel construction

Use five registered relations: additive conservation, product conservation, ordering, opposition, and inequality. Generate five fresh panels per relation with seeds `3103000 + task_index*100 + panel_index`, distinct from the earlier 903000 and 1903000 seed ranges. Draw 8 positive and 8 negative examples from integer quadruples over {-3,-2,-1,1,2,3}; the task name and heldout labels are hidden from policy functions. Candidate acquisition runs Base, Plus, Times, and Lt grammars independently on the same training rows and candidate-selection pool. A single help call may run the task-relevant extension grammar, supplied by the harness only after the policy requests help; report this as an oracle-assisted hint, not primitive discovery.

For each panel, freeze disjoint 32-row selection and 32-row challenge pools in two domains. The `nonzero` domain contains no zero coordinate. The `zero_aware` domain is drawn from integer quadruples over {-3,-2,-1,0,1,2,3} and includes zero-containing, boundary (absolute value 3), and general rows in each pool, with fixed quotas and no training overlap. Labels are revealed only when a policy chooses a row. The full 64 inputs per domain can be used without labels to partition survivor predictions; the policy records this coverage pool and its digest.

## Paired policies

1. `zero_query_help`: entropy query from the zero-aware selection pool, at most six labels, up to two random challenge labels after a singleton, then request the registered hint if unresolved.
2. `zero_query_class`: identical query order while ambiguous; after each update, if all survivors agree on the full zero-aware 64-input pool, return the whole class without help. If multiple classes remain, continue querying; after the same budgets, request help if still unresolved.
3. `nonzero_query_class`: same policy using only nonzero selection/challenge inputs to test insufficient boundary coverage.

The candidate hypotheses and label streams are paired wherever policy actions permit. A class decision uses predictions only; target labels for the 64-row unlabelled pool are never exposed to policies. Measure synthesis, selector, class partition, and help wall time separately, plus native Term evaluations and oracle-label count. Score every returned hypothesis against the fixed 6,560-row fractional holdout grid only after the decision. Count a class as heldout-safe only if every returned member is exact on that grid. Empty survivor sets, class abstentions, wrong classes, and timeout/refusal are explicit outcomes.

## Claim boundary

This evaluates fresh draws from five authored relation families on one host. Zero-aware and nonzero domains are controlled finite probes; class equality is not universal equivalence. Teacher hints are harness-supplied upper bounds. No persistent graph/rule adoption is performed.
