# Live Argmax/Holds scheduler-cache replay v2.1 preregistration

## Question

Do evaluator-generated Argmax and two-node Holds entries survive checkpoint restore across multiple outer bindings, and does a dependency mutation invalidate then rebuild those entries?

## Method

Load the source-locked CAN engine seed, replace its rules with one deterministic fixture rule, and create two Microtheory owners with three Concept candidates each. The rule uses neighbour traversal, Argmax over each owner's candidates, and a defined Holds concept depending on both candidate (`x`) and owner (`y`) attributes. Run to fixpoint, force the rule dirty without changing graph semantics, capture, and restore two stores. Compare full checkpoint restoration, global/per-rule work, graph, and scheduler. Then mutate the `group` attribute read by the Holds concept and check that all cached entries clear before a further closure rebuilds Argmax/Holds results.

## Acceptance

Require at least two Argmax keys, two Holds keys, and two neighbour keys before checkpoint; exact restored state and replay outputs; zero cache occupancy immediately after dependency mutation; and nonempty Argmax/Holds entries after the mutated closure. Lock sources before execution.

## Limits

This remains an authored two-owner synthetic workload. It does not estimate natural cache prevalence or scale, and it leaves reachable/SD-operation entries outside checkpoint support.


V2.1 checks deferred invalidation at the next rule-pass boundary: mutation sets `any_mutation`; `run_rules` clears graph-dependent cache entries before selecting dirty rules. It also resets the selected candidate marker before replay so stale Holds data would be observable as an incorrect refire.
