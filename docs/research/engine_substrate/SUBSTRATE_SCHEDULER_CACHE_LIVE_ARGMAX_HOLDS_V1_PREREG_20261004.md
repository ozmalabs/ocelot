# Live Argmax/Holds scheduler-cache replay v1 preregistration

## Question

Can an evaluator-generated nonempty `Argmax` and `Holds` cache be restored at a scheduler boundary and produce the same subsequent rule work and state?

## Method

Load the source-locked CAN engine seed to establish the graph vocabulary, remove its authored rules, and construct a tiny three-candidate graph with one deterministic rule. The rule uses a neighbour traversal, `Argmax` over a candidate attribute, and a defined concept evaluated through `Holds`; its effect marks the unique selected candidate. Run to fixpoint to naturally populate cache entries. Force the rule dirty without changing the graph, capture the populated checkpoint, normalize the diagnostic `any_mutation` bit to false, restore two independent stores, and replay the same closure from both.

## Acceptance

Require source-lock stability, initial progress, nonempty neighbour/argmax/holds occupancy, full checkpoint equality after restore, and exact global/per-rule work, graph, and scheduler parity between the two restored executions.

## Limits

This is a small synthetic fixture. It proves evaluator-generated keys can be serialized and reused for this term/rule shape, not that these cache families are common in natural workloads or that replay scales. Filter and remaining cache families are outside this fixture.
