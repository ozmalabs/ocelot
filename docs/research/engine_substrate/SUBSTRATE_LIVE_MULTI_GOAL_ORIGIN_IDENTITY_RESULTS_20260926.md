# Live multi-Goal origin identity results

**Question.** Does the live conversation path preserve distinct origin identity across two identical instruction turns to the same recipient in one session?

**Result.** Yes, for this narrow ingress-provenance probe. Three fresh processes each booted the full seed set and submitted two `Check the pressure.` instruction turns. Each turn produced one inbound `DiscourseEvent` and one new `source=conversation` `Goal`. Each Goal comprehended its own inbound `Message` and linked through `originated_in` to its own event. Message, event, and Goal IDs were distinct across the two turns; both events had the same recipient; no cross-origin or event `for_goal` links appeared. All producer-shape and source-lock checks passed.

The capture does **not** establish downstream lifecycle identity. In every run, the discourse state contained two `instruction` events and zero `selection`, `execution`, or `action_result` events. Both Goals had no transition events. Their associated deliberations reported `no_candidate`. The internal Phase 4A `DeliberationExecutionTrace.for_goal` remains a separate trace and is not part of this live event sequence.

Median full-seed boot time was 12.27 s; median turn time was 2.08 s (4.16 s for the two-turn session). These are descriptive full-seed timings from three isolated processes, not a performance scaling result.

This resolves one part of the identity gap: live ingress can keep repeated same-recipient requests distinct at Goal creation. The next engineering/evaluation target is the missing production lifecycle producer and its Goal identity contract, followed by a multi-action check that binds selection, execution, and result events to the correct Goal without fixture-supplied identity.

## Artifacts

- Preregistration: [`SUBSTRATE_LIVE_MULTI_GOAL_ORIGIN_IDENTITY_PREREG_20260926.md`](SUBSTRATE_LIVE_MULTI_GOAL_ORIGIN_IDENTITY_PREREG_20260926.md)
- Runner: [`substrate_live_multi_goal_origin_identity_v1.py`](../../../scripts/substrate_live_multi_goal_origin_identity_v1.py)
- Independent analyzer: [`analyze_substrate_live_multi_goal_origin_identity_v1.py`](../../../scripts/analyze_substrate_live_multi_goal_origin_identity_v1.py)
- Locked inputs: [`live_multi_goal_origin_identity_lock_20260926.json`](../../../evaluation/substrate_capability/live_multi_goal_origin_identity_lock_20260926.json)
- Raw capture: [`substrate_live_multi_goal_origin_identity_v1_20260926.json`](../../../evaluation/reports/substrate_live_multi_goal_origin_identity_v1_20260926.json)
- Independent analysis: [`substrate_live_multi_goal_origin_identity_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_live_multi_goal_origin_identity_v1_analysis_20260926.json)
