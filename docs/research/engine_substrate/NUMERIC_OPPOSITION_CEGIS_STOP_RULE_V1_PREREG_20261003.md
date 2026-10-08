# CEGIS consecutive-agreement stopping replay v1 preregistration

Date: 2026-10-03

## Question

Can a simple consecutive-agreement rule stop counterexample-guided resynthesis earlier while preserving held-out correctness on the frozen XOR panels?

## Frozen replay

Replay the five v1.2 grammar-expansion traces without changing learner behavior. Evaluate thresholds k ∈ {1,2,3,4,5,6}: after the expanded candidate agrees with k consecutive reserve-oracle labels since its last counterexample, stop and return that candidate. A disagreement resets the streak and the recorded trace already contains the resulting resynthesis candidate at the next query. If a threshold is never met, use the recorded budget-exhausted final state. Score only after choosing the stopping point on the recorded trace, using the existing 1,296-case fractional holdout. Report each threshold, worker-level exactness, false-singleton count, oracle labels consumed, and savings relative to the 12-label policy. Treat the five workers as paired panels, not broad task samples.

This is retrospective policy evaluation on one synthetic task, not a prospective system capability or a valid stopping guarantee. The holdout does not influence the threshold rule and remains evaluator-only.
