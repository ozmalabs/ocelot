# Describe-scene lifecycle identity v1.1 results — prior seed state

V1.1 passed against its locked pre-uniqueness-guard seed. Current source confirmation after the guard is in [v1.2 results](SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_IDENTITY_V1_2_RESULTS_20260926.md).

## Confirmatory result

The request-scoped producer fix passes all locked gates in three fresh, source-stable full-seed processes. Each worker attached one three-percept scene and issued two identical sequential instructions. Both replies were nonempty and byte-identical to the original single-request baseline text.

For each request, the authored rule minted a distinct `describe_scene` parent Goal linked to exactly that inbound Message. Each parent links to exactly that turn's origin event and owns three per-percept `produce_utterance` subgoals in a distinct request-scoped Scene view. The view points back to the shared attached source Scene. The parent alone receives the ordered `selection`, `execution`, `action_result` lifecycle; each event has exactly that Goal as owner. Both Goals resolve, enter `has_closed_goal`, and are absent from `has_active_goal`. Independent analysis verifies current lock/hash equality, worker and post-run source stability, three distinct processes, one-to-one identity, lifecycle ownership/terminal state, and normalized graph-shape replication.

The parent Goal is the request-level lifecycle owner. Its utterance children are internal decomposition tasks and receive no discourse lifecycle events. This ownership policy is now explicit in both the implementation and protocol.

Median full-seed boot was 11.94 s and median turn time was 7.00 s. Turn time includes lazy faculty construction, request-scene copying, native closure, and production; it is descriptive only and not an isolated overhead estimate.

## Implementation boundary

`arc_self_report.world_receive` now accepts the actual inbound Message and attaches it to a request-local Scene view. The view copies source percept attributes and has a `source_scene` edge. The authored comprehension rule links its new Goal to the matched Message. Host wiring selects the unique newly minted Goal by that explicit comprehension edge and fails closed if the rule yields zero or multiple matching new parent Goals. It no longer selects the last global `describe_scene` Goal. `self_report` is limited to the selected parent Goal. The action boundary records lifecycle events against that Goal.

This fixes sequential repeated-request identity on the measured route. It does not establish thread/concurrent safety, other action routes, external-effect authorization, natural workload prevalence, or scaling. The probe does not compare every node/edge against an independent full-closure oracle; it checks the route's request/Goal/event ownership projection, three-child production structure, terminal state, and reply equality with the prior baseline.

## Evidence

- Baseline audit: [`SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_PRODUCER_SOURCE_AUDIT_20260926.md`](SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_PRODUCER_SOURCE_AUDIT_20260926.md)
- Initial failure preregistration: [`SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_PREREG_20260926.md`](SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_PREREG_20260926.md)
- Initial failure result: [`SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_RESULTS_20260926.md`](SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_RESULTS_20260926.md)
- v1.1 amendment: [`SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_IDENTITY_V1_1_AMENDMENT_20260926.md`](SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_IDENTITY_V1_1_AMENDMENT_20260926.md)
- Runner: [`substrate_describe_scene_repeated_request_identity_v1.py`](../../../scripts/substrate_describe_scene_repeated_request_identity_v1.py)
- Independent analyzer: [`analyze_substrate_describe_scene_lifecycle_identity_v1_1.py`](../../../scripts/analyze_substrate_describe_scene_lifecycle_identity_v1_1.py)
- Lock: [`describe_scene_lifecycle_identity_v1_1_lock_20260926.json`](../../../evaluation/substrate_capability/describe_scene_lifecycle_identity_v1_1_lock_20260926.json)
- Raw capture: [`substrate_describe_scene_lifecycle_identity_v1_1_20260926.json`](../../../evaluation/reports/substrate_describe_scene_lifecycle_identity_v1_1_20260926.json)
- Independent analysis: [`substrate_describe_scene_lifecycle_identity_v1_1_analysis_20260926.json`](../../../evaluation/reports/substrate_describe_scene_lifecycle_identity_v1_1_analysis_20260926.json)
