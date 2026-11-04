# Additive target learning and transfer contract

**Status:** P24 design contract; frozen before P24.02 implementation. **Historical P20:** unchanged, primary transfer AUC difference −0.3333 (`FAIL`). **New policy:** disabled by default; no P24 efficacy or held-out result is claimed.

## Causal question and common learner

For each target domain pair, does verified compatible source structure improve a learner that receives the same target evidence through the same ordinary native transition-learning path? The target receipt is the evidence unit. Optional source mapping may add a candidate prior; it cannot replace, delay, suppress, or duplicate ordinary receipt assimilation.

The two directions remain `heat_to_thermal` and `lever_to_latch`, using the existing independently coded finite worlds. Every arm starts with an empty target learner, the same target affordances, action/model access, initial epochs, native ordinary-learning rules and target work limits. Only the registered source-information and map-work interventions vary.

## Receipt identity and single delivery

One target action yields one immutable `WorldReceipt` keyed by:

`(owner_id, episode_id, event_id, source_epoch, model_epoch, frame_epoch)`

The record also retains object, action, feature, before/after, authorization, status and world epoch. The event enters ordinary learning exactly once as a `TransitionObservation` joined to exactly one action receipt and one outcome receipt. A map-pair view references that same target event ID; it is not another target observation, action or support unit.

The adapter must therefore fan out one validated receipt to:

1. ordinary `observe_world_receipt` in every arm; and
2. optionally, native map-pair induction in arms assigned map work.

The ordinary path owns target action and observation counts. Pairing owns only map-work, source-information and verification counters. A control arm may spend the same map-construction work on same-target evidence, but its map is not imported as a source prior. Replay of an event ID is idempotent and cannot create a second transition/support record. Conflicting receipts, stale epochs, missing outcome, wrong owner, unauthorized action and reused pair IDs are retained as explicit rejects.

## Arm interventions

| Arm | Source acquisition | Map work | Ordinary target evidence | Prior use |
|---|---|---|---|---|
| `fresh` | None | None | Every target receipt, once | None |
| `compatible_source` | Acquire the compatible source examples; count their actions and information separately | Build, verify and retain the source→target map | Same target receipts, once | Candidate prior only after map and target-effect verification |
| `wrong_source` | Acquire the registered inconsistent source examples; charge them | Attempt the same map path and retain rejection/counterexample | Same target receipts, once and immediately | None; rejected source cannot block ordinary learning |
| `same_target_map_work` | No external source | Spend the registered map-work allowance on same-target evidence | Same target receipts, once | No imported prior; cost-control arm only |

The same-target control may not count its paired view as extra support, target action, or an additional target interaction. All four arms receive the same target receipt IDs, order, visible opportunities, target affordances and target action cap. Source actions, source observations, map construction, map verification and native inference work are separate cost fields; no source cost is hidden inside target interaction count.

## Causal contrasts and registered outcomes

- Primary: compatible-source minus the stronger source-free comparator, where the comparator is `max(fresh, same_target_map_work)` on normalized learning-curve AUC across the common target-interaction horizon.
- Negative-transfer contrast: `wrong_source − fresh`; retain every conflict, abstention and target-learning outcome.
- Map-work contrast: `same_target_map_work − fresh`; this prices optional map induction without source information.
- Report compatible-source versus fresh as a secondary total package contrast.

All curves use the same checkpoints at target interactions 0, 1 and 2, include every allocated stream, and divide trapezoidal AUC by the same horizon. Do not extend the compatible arm's target horizon to acquire a prior. Report final target accuracy and all statuses alongside AUC. The planned efficacy gate remains normalized AUC gain ≥0.10 over the stronger source-free arm, no final accuracy loss greater than 0.02, and zero receipt loss or double credit. A failed gate remains a valid negative result.

The later frozen evaluation uses 200 paired streams per direction and 100 duplicate/stale/mismatch structural controls. Source and target allocations are disjoint; no target solution, held-out label, or evaluator-only effect enters learner input. Exact allocations, task order, ceilings and loaded artifact hashes are frozen in P24.E2 after all arm adapters and self-checks work.

## Accounting and fail-closed rules

Per stream and cumulatively report: target action count, target receipt/event count, ordinary support by event ID, source action count, source-information units, map-pair count, map verification queries, native rule/model work, shared-budget debits, elapsed time, graph nodes/bytes and outcome status. Equal target action counts are required across arms; source costs may differ and must remain visible. One event ID contributes at most one ordinary support item regardless of map fan-out.

Ordinary target learning proceeds if the map is absent, pending, stale, incompatible, wrong, or rejected. A source prior remains a candidate until verified by exact source provenance, map evidence and independent target receipts. The host may transport typed receipt fields and read the terminal native record, but it may not pick a prediction, choose the winning map, synthesize a target outcome, or switch target-learning paths by arm.

## Frozen acceptance intent for P24.01/P24.02

- `test_all_arms_assimilate_each_target_receipt`: each registered target event reaches the same ordinary learner path once in every arm.
- `test_pairing_does_not_duplicate_observation_credit`: map fan-out does not add an observation/action/support count for the same event.
- `test_missing_map_cannot_block_fresh_learning`: absent or pending mapping leaves ordinary prediction and counterexample learning operational.
- `test_source_exposure_cost_visible`: source acquisition, source information, mapping, verification, and target action costs are reported separately.

P24.02 implements the single-event ingress and ordinary graph projection. P24.03 adds opt-in native map-pair validation/funding and a source-proposal import rule: typed authorized source receipts create funded pair views; native target-learning induces a map candidate; only verified map and exact target-effect receipt records become `TargetProcessPrior` candidates. The existing native target-learning rule still requires a matching ordinary target transition before creating a source-confirmed hypothesis. When that exact target hypothesis already exists, the source prior is retained with `portfolio_candidate` status and does not create a duplicate prediction. Missing/rejected records remain visible and ordinary learning continues. Map and source costs are separate from target action/support counts. The P24.E1 cognition profile integration and P24.E2/E3 causal evaluation are still outstanding. P20's existing runner and result remain immutable.
