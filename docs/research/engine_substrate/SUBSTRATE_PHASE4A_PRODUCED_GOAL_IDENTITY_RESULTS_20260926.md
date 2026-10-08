# Phase 4A produced Goal identity results

## Finding

The production `materialize_from_live_thought_manifold` path copies source-candidate provenance into a Deliberation linked to its Goal. The existing native `cm4a_begin_execution` rule then creates `DeliberationExecutionTrace` and writes `for_goal` from the matched Deliberation's `about_goal` link. A locked N=2/4/8, three-replicate comparison exercised that path and the native resolve settle-back rule under global and repeated frame-scoped closure.

All 18 worker PIDs were unique. Every run selected the expected task-specific candidate; each Goal had exactly one execution trace with the matching candidate ID and a resolved settlement pointing back to that same Goal. Evidence provenance was present. Full and scoped task projections matched in all nine paired cells, all reports completed without cap/deferred exits, and an independent analyzer reconstructed the gates and costs.

| N Goals | Closure | Candidate pairs (median) | Term evaluations (median) | Wall time (median) | Construction (median) | Peak RSS (median) |
|---:|---|---:|---:|---:|---:|---:|
| 2 | Full | 46 | 338 | 0.132 ms | 0.176 ms | 35.6 MiB |
| 2 | Scoped | 155 | 1,002 | 0.195 ms | 0.177 ms | 35.5 MiB |
| 4 | Full | 92 | 676 | 0.150 ms | 0.291 ms | 35.7 MiB |
| 4 | Scoped | 394 | 2,388 | 0.309 ms | 0.305 ms | 35.4 MiB |
| 8 | Full | 184 | 1,352 | 0.191 ms | 0.520 ms | 36.4 MiB |
| 8 | Scoped | 1,124 | 6,312 | 0.567 ms | 0.533 ms | 36.0 MiB |

At N=8 scoped/full medians are 6.11× in candidate pairs, 4.67× in Term evaluations, and 2.97× in wall time. The full-closure operation counts double exactly as N doubles in this small family. Scoped candidate counts grow more rapidly over these points. These are one-workload measurements, not general asymptotic bounds. Frame construction is comparable between arms and separate from the closure timer.

## Scope and discrepancy

This establishes that the existing production materializer/native writer path emits usable explicit Goal identity for the execution trace and settle-back sequence. It closes the harness-supplied identity gap for this Phase 4A producer family, but not for the discourse lifecycle rules in the separate v4.2 benchmark, nor for every producer or task.

The full-graph digests differ between scheduling policies, although all preregistered task projections match. A follow-up locked structural diagnostic captured all N=2/4/8 replicates (nine pairs): each pair has equal node descriptor multisets and exact typed-edge parity after pairing by type/attributes and resolving one ambiguous Deliberation class by ID order. The graphs are isomorphic under that mapping, while byte-for-byte identity differs because generated node insertion order/IDs change. See the [scale diagnostic results](SUBSTRATE_PHASE4A_GOAL_IDENTITY_GRAPH_ISOMORPHISM_RESULTS_20260926.md). The partition is runner-authored around independent Deliberation frames, and its evidence candidates are constructed for the probe; this does not measure natural frame locality, real task prevalence, cheap-cut quality, or memory attribution. Native runtime is small in this probe, but scoped closure is slower and performs substantially more matching work.

## Capture record and next step

The initial invalid attempt recursively launched workers because of a CLI argument-count bug; it was stopped before producing results. The dated [amendment](SUBSTRATE_PHASE4A_PRODUCED_GOAL_IDENTITY_AMENDMENT_20260926.md) records the incident. The corrected locked 18-worker capture and independent analysis pass.

Protocol: [preregistration](SUBSTRATE_PHASE4A_PRODUCED_GOAL_IDENTITY_PREREG_20260926.md). Runner and analyzer: [runner](../../../scripts/substrate_phase4a_produced_goal_identity_v1.py), [independent analyzer](../../../scripts/analyze_substrate_phase4a_produced_goal_identity_v1.py). Lock, raw and analysis: [lock](../../../evaluation/substrate_capability/phase4a_produced_goal_identity_lock_20260926.json), [raw capture](../../../evaluation/reports/substrate_phase4a_produced_goal_identity_v1_20260926.json), [analysis](../../../evaluation/reports/substrate_phase4a_produced_goal_identity_v1_analysis_20260926.json).

Next, use the graph comparison as a regression diagnostic for additional producer families and add event-driven mutations with full closure as oracle. Measure task-frame reconstruction and notification cost separately from rule closure. The initial [N=2 graph comparison](../../../evaluation/reports/phase4a_goal_identity_graph_diff_diagnostic_20260926.json) remains available with its [reproduction script](../../../scripts/diagnose_phase4a_goal_identity_graph_diff_v1.py).
