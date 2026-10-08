# Thoughtexperiment edit-operator node-identity hypotheses v1.1 results

## Result

The preregistered gate passes all ten independent analysis checks. Four fresh
workers regenerate eight unique hypotheses from the faulted
`mint_actor_goal_recipient` rule, including one edge-existence guard and seven
node-attribute signatures. Each worker freezes its candidate permutation,
scores every candidate on the training episode, and gives only opaque IDs and
training outcomes to the native graph-Term selector. The selector chooses the
generated `actor+verb` guard in all four workers; all-wrong and tied controls
abstain.

All four held-out episodes pass for the selected repair and for the unmodified
source-rule positive control. Every one of the other seven candidates fails
the held-out sequence. That includes actor-only, verb-only, object-based,
broader multi-key, and any-edge scopes. All eight candidates are scored in
each worker, so this is not a selected-only estimate. Candidate generation
costs 0.78 ms median; training scoring 22.19 ms; native selection 0.65 ms; and
held-out scoring all eight candidates 77.17 ms.

## Fixture correction and limits

V1 is retained as a failed diagnostic. It added a new `RecipientVerb` node for
each action, which created cross-product matches and multiple outputs within a
single closure; none of its proposals fit the malformed fixture. V1.1 reuses
one recipient node per verb, a correction specified before the v1.1 lock and
capture. V1 results are excluded from capability estimates.

V1.1 measures generic site enumeration, candidate construction, and
evidence-based selection on one authored actor/verb rule. Rules, fault,
training/held-out examples, and expected outcomes remain supplied by the
harness. Each candidate is evaluated in a fresh task context; this gate does
not yet combine candidate generation with the CoW branch, residual merge-back,
or autonomous raw-residual diagnosis. It is a bounded candidate-acquisition
result, not general self-improvement.

## Artifacts

- [Protocol](THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_V1_1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_editops_node_identity_v1.py) and [analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_editops_node_identity_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_editops_node_identity_v1_1_lock_20261003.json)
- [Frozen training orders](../../../evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_orders_20261003.json), [held-out scores](../../../evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_scores_20261003.json), and [analysis](../../../evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_analysis_20261003.json)
- V1 diagnostic artifacts: [lock](../../../evaluation/substrate_capability/thoughtexperiment_editops_node_identity_v1_lock_20261003.json), [orders](../../../evaluation/reports/thoughtexperiment_editops_node_identity_v1_orders_20261003.json), and [scores](../../../evaluation/reports/thoughtexperiment_editops_node_identity_v1_scores_20261003.json)

## Next gate

Wire these generated node-identity proposals into the thoughtexperiment
candidate lifecycle: keep the primary rule untouched, apply each candidate in
a CoW branch, capture branch-local outcome residuals, select from substrate
evidence, and revision-check the chosen residual's return. Pair the actor
identity family with recurrence and conversation controls, including
intentional repeatable effects, and measure complete lifecycle cost and
false-proposal rates.
