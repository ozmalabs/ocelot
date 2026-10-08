# Rule graph-delta observer results

## Mutation-target parity

The mutation-site observer passed its target-coverage comparison against the exact graph snapshot oracle in all eight direct-effect fixtures:

| Effect family | Result |
|---|---|
| AddEdge | Exact edge and both endpoints covered |
| DelEdge | Deleted edge and both endpoints covered |
| AddNode | New node covered |
| DelNode with incident edge | Deleted node, surviving endpoint, and removed edge covered |
| SetAttr | Written node covered |
| ReplaceValue | Rewired edge keys and endpoints covered |
| AddNodeIfAbsent | Minted node covered |
| SetAttrIfDifferent | Written node covered |

All eight observer/oracle pairs agreed on fixed-point status, progress count, and final node count. Oracle-changed node and edge sets were subsets of the observer targets in all cases. The observer is intentionally conservative: mutable accessors can report writes whose final value equals the prior value.

The replay runner and per-case record are [`substrate_graph_delta_observer_parity.py`](../../../scripts/substrate_graph_delta_observer_parity.py) and [`substrate_graph_delta_observer_parity_20260925.json`](../../../evaluation/reports/substrate_graph_delta_observer_parity_20260925.json). The run used native SHA-256 `664602673132ad5ef822c786897e20b5c336e9ada0d0d9009f8146d83442df40` and Rust-source fingerprint `7a9759403ebeced72ca8525ff15de21f8d7e54924473f77ca302feea0ced61cc`.

Ownership routing then passed four additional fixtures: changes on concepts owned by two Microtheories returned both IDs; a newly owned concept and a deleted owned concept returned their owner; deleting the Microtheory root still returned its now-deleted ID using pre-mutation type data. A deferred `TrackIdentity` effect also reached a fixed point and matched the exact graph oracle for changed nodes, identity assignments, and both owning Microtheories. The scoped-report API notified both owners for a cross-owner causal edge. A scoped `TrackIdentity` queue control returned `deferred_effects_pending=true`, reported the step-cap exit, and returned no unsupported owner IDs because the queued write had not yet run.

## Empty-closure cost probe

Nine paired calls per graph size compared ordinary closure, mutation-log reporting, and exact snapshot reporting on an already settled graph with no rules and no edges:

| Live nodes | Ordinary call | Mutation-log report | Snapshot report |
|---:|---:|---:|---:|
| 1,000 | 0.60 µs | 5.29 µs | 78.91 µs |
| 10,000 | 0.70 µs | 5.91 µs | 724.10 µs |
| 50,000 | 3.05 µs | 13.60 µs | 4,313.45 µs |

Absolute ordinary timings are sub-microsecond to low-microsecond and ratios are sensitive to timer and FFI floors. Mutation-log reporting adds roughly 5–14 µs in this probe; snapshot cost grows with graph size.

An active sparse add-edge closure was also measured with five paired fresh-substrate replicates per size. Each input edge matched once and produced one derived edge; observer target sets covered the exact snapshot targets on every pair.

| Matched input edges | Ordinary closure | Mutation-log report | Snapshot report | Observer / ordinary |
|---:|---:|---:|---:|---:|
| 64 | 48.36 µs | 114.86 µs | 109.79 µs | 2.38× |
| 512 | 150.43 µs | 436.24 µs | 743.87 µs | 2.90× |
| 2,048 | 732.38 µs | 1,952.05 µs | 3,590.62 µs | 2.67× |

The caller-visible observer is 2.4–2.9× the ordinary call on this fixture. This includes mutation-log insertion, deduplication, owner mapping, conversion of returned IDs, and the API boundary. It is a meaningful cost for affected-frame work to overcome. The probe does not isolate the graph-level disabled-logger branch from the ordinary path because all arms use the same instrumented build.

Reproduce with [`substrate_rule_graph_delta_report_overhead.py`](../../../scripts/substrate_rule_graph_delta_report_overhead.py); raw pairs and build fingerprints are in [`substrate_rule_graph_delta_report_overhead_20260925.json`](../../../evaluation/reports/substrate_rule_graph_delta_report_overhead_20260925.json). The active arm is a sparse generated closure, not a natural workload; neither arm includes frames or deferred effects.

## Remaining coverage gaps

The latest cost run used native SHA-256 `664602673132ad5ef822c786897e20b5c336e9ada0d0d9009f8146d83442df40`; the Rust-source fingerprint is `7a9759403ebeced72ca8525ff15de21f8d7e54924473f77ca302feea0ced61cc`.

The observer report maps touched graph nodes to directly owning Microtheories, not to dependency-connected component frames. `TrackIdentity` is the only deferred rule effect exercised. Framebuffer sampling, net collapse, rule patch/edit drains, imported/rewritten rules, shared evidence propagation, dynamic ownership changes, and end-to-end event-scheduler parity remain open. Scoped settlement exposes pending deferred queues and step-cap exits but does not drain those queues. These results do not establish complete frame notification or natural-task performance.

## Shared conversation evidence write follow-up (2026-09-26)

A new locked 27-worker integration probe closes one narrow gap above. A native conversation rule writes a shared `BoundaryEvidence.boundary_value`; the scoped mutation observer returns the controller Microtheory plus both consumer-frame owners, exactly matching the full snapshot-delta owner oracle in all nine size/replicate pairs. The caller schedules those consumer frames and matches full closure; an omitted owner leaves a stale projection and full catch-up restores parity. This covers the `SetAttr` shared-evidence path on one authored rule family only. `frame_notifications_complete` remains false and the runner still performs caller-side queue delivery. See [`SUBSTRATE_CONVERSATION_NATIVE_WRITE_OWNER_RESULTS_20260926.md`](SUBSTRATE_CONVERSATION_NATIVE_WRITE_OWNER_RESULTS_20260926.md), [protocol](SUBSTRATE_CONVERSATION_NATIVE_WRITE_OWNER_PREREG_20260926.md), [analysis](../../../evaluation/reports/substrate_conversation_native_write_owner_v1_analysis_20260926.json), and [raw capture](../../../evaluation/reports/substrate_conversation_native_write_owner_v1_20260926.json). Deferred effects, edge/node lifecycle changes, dynamic ownership, other rule families, and automatic event delivery remain open.
