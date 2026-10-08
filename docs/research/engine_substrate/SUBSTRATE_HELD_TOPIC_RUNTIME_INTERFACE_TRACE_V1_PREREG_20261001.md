# Held-topic runtime interface and dependency trace v1

## Question

For a current-source live held-topic task family, what dynamic native graph accesses occur during each request, and what typed edges and attribute fields cross the protocol-declared operational task cut?

## Workload and instrumentation

Reuse the seven frozen turns in `substrate_live_held_topic_evidence_v1_6.py`: three known-topic meta answers, the table route, honest-capability route, unknown-topic control, and injected local-source hit. Run three fresh workers under the full current source closure, native extension, seed closure, and base task protocol lock. Wrap each `WorldAdapter.converse` call with reset/enable/disable/snapshot of the native runtime-access trace. Do not alter prompts, teaching data, route logic, or frame membership. For every turn, capture the exact graph cut from the base protocol, full node attributes for owned and external boundary nodes, and dynamic accesses grouped by rule UID, access kind, node, resource, and peer. Join UIDs to rule names and retain static read/write declarations for observed rules.

## Gates and measurements

Require source-lock stability at worker start/end and after the run; all seven turns present in each of three fresh PIDs; exact current task-route/quality gates copied from the base result; zero dropped runtime events; stable runtime graph/cut signatures across workers; and independent recomputation of boundary incidence and external node sets from the captured graph metadata. Report, separately, static declared reads/writes, actually observed dynamic access classes/resources, nodes inside the owned cut, nodes on its direct boundary, and accesses outside both sets. Report attribute names, value types, and observed distinct-value counts for owned and boundary nodes. These are observed interface schemas, not complete semantic domains.

## Limits

Task ownership remains operationally declared by the prior protocol. Runtime traces cover executed paths only and must not prune static dependencies. This is a current-source rerun of a known authored task family, not a fresh independent task sample, natural-task prevalence estimate, complete host/scheduler dependency graph, or factorization/speed claim. If dynamic tracing reports dropped events or the semantic task gates fail, retain the capture as failed/incomplete evidence.

## Reproduction

Create the source lock with the runner's `--lock` command, run it, then run `scripts/analyze_substrate_held_topic_runtime_interface_trace_v1.py`.
