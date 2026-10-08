# Discourse lifecycle producer source audit

**Scope:** static audit of discourse-event production and Goal lifecycle consumption after the repeated live-origin probe. This is source evidence, not a claim that every action route was dynamically exercised.

## Findings

1. `domains/discourse_state.py::record_event` creates a `DiscourseEvent`, links it to the state, predecessor, speaker/addressee, and optionally CommonGround. Its signature accepts no Goal or task identity and it does not emit a `for_goal` edge.
2. The production `substrate/world_adapter.py` call sites are the text-turn ingress (`_record_live_discourse_state`) and `ingest_semantic_event`. The former emits the interpreted communicative kind (including `instruction`); the latter emits `semantic_event`. The inspected production call sites do not emit `selection`, `execution`, or `action_result` kinds.
3. `seeds/conversation_discourse_state.json` contains native transition rules for those three lifecycle kinds. They match a state event occurring after the Goal's origin event index, then transition the Goal. They do not require an event-to-Goal identity edge, so event order alone is not a safe association rule for concurrent or repeated Goals.
4. Existing synthetic identity probes explicitly attach `event --for_goal--> goal`; some also add that relation to the lifecycle rule match. This demonstrates the relation can be represented and tested in the graph, but it is harness-supplied and is not a production producer integration.
5. Live instruction handling in `domains/conversation_action.py::act_on_instruction` mints and binds Goals to inbound Messages, routes held faculties or reports an honest goal-only limit, and returns a conversational result. The separate `domains/operational_planning.py::run_plan` executor dispatches configured capabilities. The audited production files do not bridge these outcomes into lifecycle DiscourseEvents.

## Conclusion and next implementation/evaluation gate

The missing seam is not Goal creation: repeated live ingress now has distinct Goal-to-origin links. The missing seam is an authoritative owner that spans live action selection, execution, and outcome reporting while retaining the associated Goal ID. A correct producer should create each lifecycle event with an explicit `for_goal` identity edge (or an equally strict identity key resolved unambiguously), and the native discourse transition rules should require that same identity. Event index and recipient alone are insufficient when one recipient has multiple open Goals.

Before adding lifecycle production to a path, select one executable action route and define its authority, event payload, failure/partial-result semantics, and Goal transition contract. Then run a preregistered two-Goal same-recipient sequence with one-to-one identity, deliberate event omission, swapped identity, duplicate result, and execution-failure controls. Require exact expected lifecycle projections and demonstrate that temporal-only matching fails the negative/cross-assignment controls. Do not treat synthetic fixture events or Phase 4A `DeliberationExecutionTrace.for_goal` as production lifecycle events.

## Source anchors

- [`discourse_state.py`](../../../domains/discourse_state.py): `record_event`, `open_goal`, `transition_goal`
- [`world_adapter.py`](../../../substrate/world_adapter.py): `_record_live_discourse_state`, `ingest_semantic_event`, `_bind_live_goals_and_deliberation`
- [`conversation_action.py`](../../../domains/conversation_action.py): `_mint_goal`, `act_on_instruction`
- [`operational_planning.py`](../../../domains/operational_planning.py): `run_plan` and capability registry
- [`conversation_discourse_state.json`](../../../seeds/conversation_discourse_state.json): lifecycle transition rules
- [`SUBSTRATE_DISCOURSE_GOAL_IDENTITY_REPLICATED_SCALE_V4_2_RESULTS_20260926.md`](SUBSTRATE_DISCOURSE_GOAL_IDENTITY_REPLICATED_SCALE_V4_2_RESULTS_20260926.md): synthetic explicit-identity controls
- [`SUBSTRATE_LIVE_MULTI_GOAL_ORIGIN_IDENTITY_RESULTS_20260926.md`](SUBSTRATE_LIVE_MULTI_GOAL_ORIGIN_IDENTITY_RESULTS_20260926.md): repeated live ingress evidence
