# Describe-scene lifecycle identity v1.2 results

Three fresh, source-stable full-seed workers pass the repeated attached-scene request gates with the native owner-uniqueness guard loaded. Each worker issues two requests against one attached scene; each gets a distinct parent Goal, exact Message and origin-event ownership, three utterance children, and one Goal-bound selection/execution/result sequence. Both parent Goals resolve, close, and leave the active set. Replies are nonempty and byte-identical to the original baseline. The independent analyzer confirms current lock equality, worker and post-run stability, and normalized graph-shape replication.

Median full-seed boot was 12.07 s and median turn time was 7.12 s. These end-to-end timings include lazy faculty construction and request-scene copying; they do not isolate guard cost or establish scaling.

This is sequential route evidence only. Native event-level interleaving is measured separately in [interleaving v1.1 results](SUBSTRATE_NATIVE_GOAL_LIFECYCLE_INTERLEAVING_V1_1_RESULTS_20260926.md); actual concurrent calls, request-level missing/ambiguous-owner controls, complete graph-projection parity, other routes, and scaling remain open.

## Evidence

- Preregistration: [`SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_PREREG_20260926.md`](SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_PREREG_20260926.md)
- Amendment: [`SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_IDENTITY_V1_2_AMENDMENT_20260926.md`](SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_IDENTITY_V1_2_AMENDMENT_20260926.md)
- Runner: [`substrate_describe_scene_lifecycle_identity_v1_2.py`](../../../scripts/substrate_describe_scene_lifecycle_identity_v1_2.py)
- Independent analyzer: [`analyze_substrate_describe_scene_lifecycle_identity_v1_2.py`](../../../scripts/analyze_substrate_describe_scene_lifecycle_identity_v1_2.py)
- Lock: [`describe_scene_lifecycle_identity_v1_2_lock_20260926.json`](../../../evaluation/substrate_capability/describe_scene_lifecycle_identity_v1_2_lock_20260926.json)
- Raw capture: [`substrate_describe_scene_lifecycle_identity_v1_2_20260926.json`](../../../evaluation/reports/substrate_describe_scene_lifecycle_identity_v1_2_20260926.json)
- Independent analysis: [`substrate_describe_scene_lifecycle_identity_v1_2_analysis_20260926.json`](../../../evaluation/reports/substrate_describe_scene_lifecycle_identity_v1_2_analysis_20260926.json)
