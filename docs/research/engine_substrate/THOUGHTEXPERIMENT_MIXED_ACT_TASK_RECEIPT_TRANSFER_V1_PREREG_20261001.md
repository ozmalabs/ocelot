# Mixed-act task receipt transfer v1 preregistration

**Question.** Does the snapshot/journal/adoption path preserve an independent, connected task with multiple Goals, production-owned lifecycle events, an unsolicited assertion, and an epistemic-limit repair?

## Workload and arms

Replay the frozen ten-event `phase3_mixed_act_dialogue.v1` fixture with the registered `conversation_discourse_state` seed and current discourse rules. This is a second task family, independent of the common-ground task replay. Run eight fresh worker processes; each worker executes all arms in a counterbalanced order on fresh adapters:

- **Direct:** reproduce the ordinary materializer: record request/question/assertion/epistemic-limit events, use the production `_record_live_goal_event` helper for selection/execution/action-result events, then use the ordinary per-event `run_rules_report(100_000, False)` settlement.
- **Eager receipt:** route each task-owned event-production closure and each ordinary per-event settlement through a guarded eager branch, before-image journal, and revision-checked receipt adoption.
- **Shared snapshot receipt:** same operations through a reusable shared snapshot fork, journal, and guarded receipt adoption.

For production-helper events, branch before invoking the existing helper; its event creation and internal closure are part of that task-generated receipt. For every event, retain the existing second ordinary settlement. Do not modify the fixture, seed rules, production helper, event order, or task oracle. Compare canonical graph facts at every event; record full wire order separately.

## Gates

1. Eight distinct fresh PIDs; source/native inputs match the lock before and after each worker.
2. All arms process ten fixture events and two Goals, with identical event/Goal IDs, per-event closure progress, final Goal transitions/lifecycle state, common-ground claims, and terminal fixed point.
3. Every receipt-arm adopted primary matches its producing branch canonically before the next task event; per-event canonical graphs match Direct.
4. The production helper is called for exactly six fixture lifecycle events per arm. All helper and settlement receipts are retained, including empty receipts; any nonempty task residual must be reproducible in all three arms.
5. Report serialized graph edge-order equality separately; do not relabel canonical parity as wire equality.
6. Preserve every worker and arm. Missing inputs, stale lock, task-oracle mismatch, or semantic mismatch makes the panel inconclusive.

## Measures and limits

Report task setup, fixture materialization, branch setup, helper/settlement closure, journal readout, adoption, terminal probe, and total route-stage time separately. Separate oracle graph serialization. This tests one existing authored task family on one host; it is not a natural-task frequency estimate, concurrent-writer result, general authorization result, or serving-runtime integration.

## Development pilot disclosure

A nonconfirmatory worker replayed all three arms before locking. Event/Goal IDs, both resolved Goal paths, common-ground claims, deferred epistemic residual, per-event progress, and canonical graph facts matched. All 16 producer/settlement receipts in each branch arm matched the producing branch after adoption. Serialized wire hashes differed from Direct. The pilot's timings and outcomes are excluded from the locked capture.
