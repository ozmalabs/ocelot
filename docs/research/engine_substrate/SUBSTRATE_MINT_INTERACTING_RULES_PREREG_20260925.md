# Interacting mint rules: native closure and finite-bound probe

**Status:** preregistered synthetic confirmatory probe for the finite-key insertion fragment.

## Question

For small fixed rule sets with multiple keyed mint signatures and rules that enable later rules (including one feedback cycle), does the native runner reach an exact independently computed closure within the static progress bound?

## Frozen workloads

Both cases start with three `Seed` nodes and `seed_link(0,1)`, `seed_link(1,2)` and use only positive edge-triple matches, scalar-constant `add_node_if_absent`, and empty-attribute `add_edge`.

1. **Cascade:** seed links mint/share one `Witness`; derived links enable a second rule that mints/shares one `Marker`; marker links enable a third rule that adds a self-loop.
2. **Feedback:** seed links mint/share one `Witness`; derived links enable a second rule that creates a `seed_link` back from the witness to its source. This re-enables the first rule and tests quiescence when newly enabled matches produce only duplicate facts.

## Procedure and acceptance

Load each rule through PyO3 `add_rule`, record native `rule_access_sets`, and run `run_rules_report(max_steps=1000, detect_cycles=false)`. An independent Python set-based bottom-up evaluator computes the least positive closure from the frozen rule JSON. Compare every edge triple over every extant node ID and declared edge type, plus node count and minted type counts. Require native `fixed_point`, exact graph parity, classifier acceptance, and progress steps no greater than its bound. One run per case in a fresh substrate instance; this is a mechanism test, not a timing study.

## Interpretation limits

Passing supports only these two finite cases. It does not prove arbitrary scheduler completeness, imported/rewritten rule parity, or production termination for all rules in the fragment. A mismatch fails the gate and must be preserved for diagnosis; do not alter the oracle or bound after seeing outcomes.
