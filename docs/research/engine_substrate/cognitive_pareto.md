# Cognitive Pareto: “is my goal wrong?”

Pareto comparison is a general metacognitive faculty, not a motor-control
feature. A goal is falsified relative to its declared objective basis when a
known alternative is no worse on every objective and strictly better on at
least one. Incomparability is not failure and is not resolved by inventing a
weighted score.

The `cognitive_pareto` seed therefore owns two graph decisions:

1. Relate complete, verified candidates by strict Pareto dominance.
2. When a profile audits a `Goal` and its incumbent candidate is dominated,
   mint a `GoalRevisionRequest` linked to the goal and the concrete dominating
   alternative.

The faculty does not silently replace the goal. A counterexample justifies
revision; choosing a new goal remains a separate contextual decision. Nor does
absence of a counterexample prove the goal globally correct—it only says that
the currently represented alternatives did not dominate it.

New profiles use `ParetoProfile`, `ParetoDimension`, `ParetoCandidate`, and
`ParetoValue`. Cognitive measurements are integer quanta. The mechanical
publication API rejects floating-point measurements.

`embodied_pareto_profile` is now a compatibility vocabulary. Its rules are
generated from the same general dominance-rule builder and bridge legacy motor
relations onto the general relations. It contains no independent decision
algorithm.
