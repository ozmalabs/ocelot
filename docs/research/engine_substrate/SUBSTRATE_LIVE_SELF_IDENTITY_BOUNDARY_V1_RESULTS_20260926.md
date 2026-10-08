# Live self-identity full-boundary audit v1 (2026-09-26)

## Result

Three fresh full-source-locked workers pass all **22 gates**, including the existing v3.1 route, Goal ownership, receipt, failure-suppression, and external-object controls. Complete typed-edge structural signatures match across workers for the two successful self-report actions and the injected reflective-faculty failure.

| Self-report case | Owned nodes | Internal edges | Complete boundary incidences | Unique external nodes | Induced-width upper bound |
|---|---:|---:|---:|---:|---:|
| `describe yourself` | 7 | 15 | 29 | 15 | 3 |
| `tell me about yourself` | 7 | 15 | 31 | 17 | 3 |
| Injected faculty failure | 7 | 13 | 29 | 15 | 2 |

The owned set is operationally defined as the inbound message, its same-event Goal, Goal-linked lifecycle events, Goal-linked reply candidates, matching production receipts, and outbound messages that respond to the inbound. The induced-width number uses a deterministic min-fill elimination on the underlying undirected owned-node graph. The complete cut counts every typed edge with exactly one endpoint in the owned set.

## Cross-family comparison and interpretation

The held-topic v1.6 panel had 11 owned nodes and 41–46 crossing incidences for positive answers, with induced-width upper bound 2. This independent self-report action family has 7 nodes, 29–31 crossings, and upper bound 3. Both are sparse small operational projections, but the exact cut and induced width vary by task family. In both, the external side contains shared Agent, Channel, Interlocutor, GoalFrame, and discourse structures; repeated edges to these hubs are incidence counts, not independent boundary dimensions.

The result supports measuring complete graph cuts on named live tasks instead of relying on an edge-type allowlist. It does not establish that either manually declared owned set is a learned frame, that the full rule dependency graph has the same width, or that inference factorizes across these boundaries. Wider coverage needs additional task/evidence families, shared-hyperedge treatment, and direct cost/parity tests for any proposed partitioned execution.

## Artifacts

- [Audit amendment](SUBSTRATE_LIVE_SELF_IDENTITY_BOUNDARY_V1_AMENDMENT_20260926.md)
- [Source-locked runner](../../../scripts/substrate_live_self_identity_boundary_v1.py)
- [Full source lock](../../../evaluation/substrate_capability/live_self_identity_boundary_v1_lock_20260926.json)
- [Raw workers and incident edges](../../../evaluation/reports/substrate_live_self_identity_boundary_v1_workers_raw_20260926.json)
- [Analysis and gates](../../../evaluation/reports/substrate_live_self_identity_boundary_v1_20260926.json)
- [Held-topic comparison](SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_6_RESULTS_20260926.md)
