# Live describe-scene concurrent full-boundary audit v1 (2026-09-26)

## Result

Three fresh source-locked workers pass all **8 top-level gates**. The original two-thread schedule still joins without errors, B remains serialized behind A, event identity/order and both Goal lifecycles remain correct, both exact baseline replies are preserved, and the complete task-boundary signatures reproduce. The final graph contains 25,147 nodes and 11,798 edges in each worker.

| Request | Owned nodes | Internal edges | Complete boundary incidences | Unique external nodes | Induced-width upper bound |
|---|---:|---:|---:|---:|---:|
| A | 7 | 12 | 35 | 20 | 2 |
| B | 6 | 11 | 32 | 18 | 2 |

The declared owned node set includes each inbound message, its same-event Goal, Goal-linked transition events and reply candidates, matching production receipts, and outbound replies. Full graph serialization and cut calculation occur after the threaded schedule and are excluded from the existing elapsed-turn and producer-helper work measurements.

## Direct interaction and shared boundary

The two owned task sets have one direct typed crossing: `B inbound Message -responds_to-> A inbound Message`. Their boundaries also share six external nodes: Agent, Channel, Concept, DiscourseEvent, DiscourseState, and Interlocutor. This structure is replicated in all three workers. It means the paired schedule has both a direct task-to-task relation and shared graph context. The capture records that graph structure; it does not decide whether the relation is semantically appropriate or an error.

## Limits

The min-fill width is an upper bound on the undirected subgraph induced by the declared owned nodes. It omits rule/factor dependencies and does not include paths through external shared nodes. This is a repeated live `describe_scene` concurrency schedule, not a natural-conversation sample, learned frame, complete engine dependency graph, or inference/execution factorization result. The source lock also includes the full domain/substrate/seed Python closure and native extension/build identity.

## Artifacts

- [Amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_BOUNDARY_V1_AMENDMENT_20260926.md)
- [Runner](../../../scripts/substrate_live_describe_scene_boundary_v1.py)
- [Source lock](../../../evaluation/substrate_capability/live_describe_scene_boundary_v1_lock_20260926.json)
- [Raw workers](../../../evaluation/reports/substrate_live_describe_scene_boundary_v1_workers_raw_20260926.json)
- [Analysis and gates](../../../evaluation/reports/substrate_live_describe_scene_boundary_v1_20260926.json)
- [Cross-family boundary comparison](SUBSTRATE_RUNTIME_TASK_BOUNDARY_COMPARISON_V1_RESULTS_20260926.md)
