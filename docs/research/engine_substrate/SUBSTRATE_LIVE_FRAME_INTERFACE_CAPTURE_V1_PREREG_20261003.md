# Live frame-interface capture v1 preregistration

Date: 2026-10-03
Status: frozen before capture; current-source follow-up to the 2026-09-28 frame-locality contract.

## Question

Can a non-browser live task capture preserve enough graph state and runtime evidence to measure candidate task interfaces without supplying the declared frame membership to the proposal algorithm? This is a data-collection and proposal-baseline gate. It does not test partitioned execution or estimate cheap-cut prevalence.

## Workload

Run three fresh isolated workers. Each loads the full seed profile and receives, in order, `report your organisation` and `describe who you are`, matching the historical self-report task-boundary panel. Retain the first prompt's expected self-report lifecycle and the second prompt's known route shortfall as separate outcomes. Retain the existing five event/goal identity controls. Do not alter seeds, model inputs, or task schedule.

## Capture

For each conversation call, capture a bounded native graph-access trace, native scheduler/deferred work trace, dropped-event counts, and the existing per-producer scale-audit rows. Capture the full final graph, including all nodes, types, attributes and typed edges, and the native exported rule store in one worker only; require the existing semantic graph digest and the derived graph summary to repeat in all three workers. Record runtime graph-rule nodes from the full graph. These are operation/factor ownership candidates; the graph does not assert that every rule is relevant to either task.

From each inbound Message ID, propose undirected typed-graph BFS neighborhoods at radii 0–3 without reading `task_owned_nodes` or expected task targets. For every proposal, record node/edge counts, crossing incidences, distinct external nodes/types, observed attribute keys/value representations, discovery time, and dynamic-trace event/weight coverage. Keep the historical explicit task-owned cut as a separate comparison arm only. Do not use that owner set to build or tune the BFS proposals.

## Gates and failure handling

1. Three distinct worker PIDs, stable start/end/post-run source locks, a valid measuring-engine provenance check, and exact task-level graph/lifecycle behavior from the frozen baseline.
2. Full-graph semantic digest, graph type/edge/attribute summaries, and BFS proposal signatures reproduce across workers.
3. The access and work trace dropped-event counts are zero. Any positive dropped count means trace coverage is incomplete and fails the corresponding gate; retain the capture.
4. All BFS members and edge endpoints resolve in the captured graph. Recompute every typed cut from the raw graph independently of the proposal routine.
5. Retain every result, including task shortfall, trace incompleteness, or proposal mismatch. Do not repair or exclude after capture.

## Interpretation boundary

The graph-access trace is explicitly bounded and known to omit specialized graph-scanning Terms and some host-side work. Zero dropped events proves only that this recorder did not hit its cap, not that every execution dependency was observable. An attribute's observed values in one fixture are not its complete domain. BFS from an inbound Message is a generic proposal baseline, not learned ontology or a correctness-certified task frame. Candidate coverage and cut size do not prove inference factorization, closure equivalence, or speedup. No prevalence estimate follows from this authored task pair.

## Artifacts

- Runner and independent in-run checks: `scripts/substrate_live_frame_interface_capture_v1.py`
- Source lock: `evaluation/substrate_capability/live_frame_interface_capture_v1_lock_20261003.json`
- Raw workers and full graph: `evaluation/reports/substrate_live_frame_interface_capture_v1_workers_raw_20261003.json`
- Summary: `evaluation/reports/substrate_live_frame_interface_capture_v1_20261003.json`
