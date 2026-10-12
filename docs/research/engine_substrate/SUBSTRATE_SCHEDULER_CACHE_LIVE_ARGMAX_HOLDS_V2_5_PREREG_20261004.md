# Live Argmax/Holds scheduler-cache replay v2.5 preregistration

## Question

Do evaluator-generated Argmax and two-node Holds entries survive checkpoint restore across multiple outer bindings, and does a dependency mutation prevent stale Holds results from affecting the next rule pass?

## Method

Load the source-locked CAN engine seed, replace its rules with one fixture rule, and create two Microtheory owners with three Concept candidates each. The rule uses neighbour traversal, Argmax over each owner's candidates, and a defined Holds concept depending on candidate (`x`) and owner (`y`) attributes. Run to fixpoint, force the rule dirty without a semantic graph change, capture the populated checkpoint, and restore two stores. Compare exact checkpoint restoration, global/per-rule work, graph, and scheduler. Then change the `group` attribute read by the Holds definition and reset the selected candidate's effect marker to zero. Run the closure and observe the result.

## Acceptance

Require at least two Argmax keys, two two-node Holds keys, and two neighbour keys before checkpoint; exact restored checkpoint equality and matching work/output across the two restored executions; a pending mutation before the post-mutation closure; at least two Holds evaluations after mutation; zero selected marker after the pass; and an empty Holds cache after the pass boundary.

## Limits

This is an authored two-owner synthetic workload. It measures one term/rule shape and pass-boundary cache invalidation, not natural cache prevalence, general tractability, or scale. Reachable and SD-operation cache entries remain unsupported.
