# Live action event identity producer audit

## Runtime result

Three locked fresh-process runs loaded the full seed set and executed the same production call, `WorldAdapter.converse("Check the pressure.", speech_act="instruction", speaker="alice")`. All three produced exactly one new `DiscourseEvent`, kind `instruction`, with no `for_goal` edge. The live action bridge created a conversation Goal linked to the inbound Message and its originating DiscourseEvent. Its associated Phase 4A Deliberations followed the empty discourse-state route (`no_candidate`); the Goal had no lifecycle transition.

The state contained zero `selection`, `execution`, and `action_result` DiscourseEvents in all three runs. This live instruction path therefore produces source-Goal provenance, but not the later event stream expected by the discourse lifecycle seed. Three distinct worker PIDs and all independent gates passed.

Full-seed boot median was 12.17 seconds; the measured `converse` call median was 3.37 seconds. These timings are descriptive for this full-seed live path, not a clean engine-only latency measure. Setup, rule closure, adapters, and readout are mixed into the call interval.

## Source path and distinction between the two trace types

- `domains.discourse_state.record_event` has no Goal parameter. It writes the event into a DiscourseState, links `follows_event`, optional speaker/addressee edges, and common-ground contribution; it does not emit `for_goal`.
- The production world adapter calls this recorder for inbound/semantic events. `_bind_live_goals_and_deliberation` binds a current inbound event to a Goal whose `comprehends` edge points to that Message, then to a Deliberation via `about_goal`.
- `domains.conversation_action._mint_goal` records the inbound Message relation and turn ID. This is the path exercised by the instruction bridge.
- The Phase 4A native `cm4a_begin_execution` rule does emit a `DeliberationExecutionTrace.for_goal` edge from the Deliberation's Goal. This is a separate internal deliberation trace. It does not produce a `DiscourseEvent` with kind `execution`, nor does it emit discourse lifecycle `selection` or `action_result` events.
- The three `conversation_discourse_state` rules consume later DiscourseEvents by temporal order and addressee, so the live `converse` path observed here does not provide the event sequence those rules expect.

The result is bounded to one live instruction path. It does not prove that no other application producer writes these event kinds, and it does not estimate the frequency of multi-goal identity failures. Together with the separate common-ground fixture replication, it shows a specific implementation gap between tested harness events and the current live producer.

## Reproducibility and next action

Protocol: [preregistration](SUBSTRATE_LIVE_ACTION_EVENT_IDENTITY_PREREG_20260926.md). Runner and independent analysis: [runner](../../../scripts/substrate_live_action_event_identity_probe_v1.py), [analyzer](../../../scripts/analyze_substrate_live_action_event_identity_probe_v1.py). Lock and captures: [lock](../../../evaluation/substrate_capability/live_action_event_identity_lock_20260926.json), [raw report](../../../evaluation/reports/substrate_live_action_event_identity_v1_20260926.json), [analysis](../../../evaluation/reports/substrate_live_action_event_identity_v1_analysis_20260926.json).

Next, specify one owner for creating operation lifecycle events and their Goal association. Preserve the Phase 4A execution trace as distinct evidence unless an explicit mapping is defined. Then add a producer-integrated multi-goal evaluation whose task oracle is derived from separate inbound turns, and require the production event writer—not the harness—to associate each generated event with its originating Goal. Do not claim a runtime correction until that path passes held-out conversation fixtures.
