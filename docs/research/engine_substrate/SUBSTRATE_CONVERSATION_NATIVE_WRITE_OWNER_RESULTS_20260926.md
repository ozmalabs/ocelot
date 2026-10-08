# Native Conversation Rule-Write to Frame-Owner Results (2026-09-26)

## Outcome

The locked 27-worker study adds one native trigger rule to the read-only-boundary conversation fixture. A controller Microtheory owns the trigger and a shared evidence node; consumer frames 0 and 1 also own that evidence node. When activated, the trigger rule writes `boundary_value=4` and resets itself. The existing score rule then reads the written value and updates the two consumer deliberations.

The native scoped delta report for the controller rule returns exactly `writer_controller`, `frame_0`, and `frame_1` in all 18 scoped workers. Its changed-node/edge targets are subsets of the exact full graph snapshot delta in all nine paired cases. Scheduling consumer frames from that report matches the exact full-closure projection in all nine cases and leaves zero progress for the final full-closure probe. Deliberately omitting frame 1 leaves a stale projection in every case; full catch-up performs four progress steps and restores exact parity. The independent analyzer passes all 19 provenance, schedule, native-report, target-coverage, parity, omission, and recovery checks.

This is direct evidence that the existing mutation-site observer routes a native rule's shared-node write to directly owning Microtheories on this authored conversation path. The API explicitly returns `frame_notifications_complete=false`; the caller still maps IDs to consumer scopes and drives the queue. This is not automatic native notification delivery or a general dependency-complete scheduler.

## Descriptive cost

Median microseconds over three fresh workers per size/arm. The native writer call includes scoped rule execution, graph mutation logging, direct owner mapping, and the API boundary. Consumer schedule time includes calling scoped delta reports for the returned consumer owners and queue processing. It excludes graph setup, baseline closure, and the terminal full-probe check.

| Frames | Native controller write/report | Required consumer scoped queue | Exact full snapshot-delta oracle call |
|---:|---:|---:|---:|
| 2 | 62 µs | 93 µs | 119 µs |
| 4 | 75 µs | 162 µs | 179 µs |
| 8 | 97 µs | 247 µs | 273 µs |

The exact snapshot arm includes a full O(V+E) before/after oracle and settles all rules, so its latency is not a like-for-like performance baseline for the mutation-log + caller-queue path. At eight frames, writer report plus required consumer scheduling is about 344 µs on this fixture. Three replicates are descriptive only.

## Claim limits and next work

The tested native effect is one `SetAttr` to one shared node, and ownership mapping uses direct `has_concept` links. The test does not cover other effect families, deferred writes, rule activation changes, edge/node birth or deletion, concurrent writers, ownership changes, arbitrary read/write dependencies, or natural workload frequency. The engine report deliberately does not claim notification completeness. Next test multiple native writer effects and mutation kinds, then cover deferred effects and dynamic ownership changes against exact snapshot and full-closure controls. Only after that should the effect-to-owner observer be generalized or connected to a production event queue.

## Artifacts

- [Preregistration](SUBSTRATE_CONVERSATION_NATIVE_WRITE_OWNER_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_conversation_native_write_owner_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_conversation_native_write_owner_v1.py)
- [Accepted raw capture](../../../evaluation/reports/substrate_conversation_native_write_owner_v1_20260926.json)
- [Independent analysis](../../../evaluation/reports/substrate_conversation_native_write_owner_v1_analysis_20260926.json)
- [Source lock](../../../evaluation/substrate_capability/conversation_native_write_owner_lock_20260926.json)
- [Prior mutation-observer contract/cost audit](SUBSTRATE_RULE_GRAPH_DELTA_REPORT_OVERHEAD_RESULTS.md)
