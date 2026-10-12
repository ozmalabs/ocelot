# Live describe-scene access trace v2.5 preregistration

## Question

Does a current-source, production `describe_scene` route expose request-local graph/access cuts when two Goal-identified requests run under the existing serialized schedule? This is a held-out operation family relative to the assistant-authored anaphora boundary study. It tests one route and one shared Scene/Percept fixture; it cannot estimate natural-task prevalence.

## Frozen design

Reuse the v2.4 worker protocol and frozen task text, seed/profile, concurrent A/B schedule, reply oracle, lifecycle checks, and explicit `WorldAdapter` request wrappers. Run three paired traced/untraced replicates in six fresh processes. Request ownership is derived from the Goal linked to each exact inbound message through `comprehends`, then the source-authored lifecycle/event/message descendants (`scene_task_nodes`); this mapping does not use node allocation order. The shared Scene and its Percepts remain a separately labeled input interface. Do not assign shared Concepts or Agent state to either request.

The trace interval remains the serialized `converse` operation captured by the v2.4 wrapper. Report this scope precisely: trace kinds identify native rule accesses only. Host work, Python callbacks, receive-time mutations, queue draining, and non-rule native work are not presumed covered. Compare traced and untraced replies, lifecycle, schedule, semantic whole-graph digest, and graph boundary projections exactly.

## Measurements and gates

Freeze all source closure hashes, protocol/amendment hashes, native binary/build manifest hashes, and current trace source. Require three paired replicates/six PIDs, stable worker input hashes and post-run hashes, all threads joined, task/lifecycle/reply gates, zero trace drops, complete nonempty request intervals, trace-total reconciliation, and exact semantic projection and whole-graph digest parity within each pair.

For each request and replicate, report: request-owned node count/type distribution; internal typed edges; boundary incidence and distinct external nodes/types; direct A↔B edges; exact owned-node IDs; pairwise trace crossings to the other request or external/global nodes; unary node accesses to owned/external nodes; index queries and host dispatches; event-kind and rule distributions; and trace event totals. Keep graph-boundary counts distinct from dynamic access counts. Do not treat traced events as exhaustive dependencies or assert safe scoped execution.

## Decision rule

If the source lock is stale, any worker drifts, or a parity/oracle gate fails, retain raw output and label the run censored; do not pool partial metrics. If all gates pass, treat the result as current-source replication on this one production route. A follow-up needs a held-out family plus explicit coverage for receive-time, host, scheduler, and non-rule native work before any frame locality claim.

## Reproduction

Use `PYTHONPATH=runners/dsl/python:.`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. Create the lock with `scripts/substrate_live_describe_scene_access_trace_v2_5.py --lock`, inspect and preserve it, then run that script with the same environment. The runner refuses to replace existing lock/raw/summary artifacts.
