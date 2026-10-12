# Live scheduler-work trace v2 preregistration

Date: 2026-09-28  
Status: confirmatory rerun after the v1 process-global/scope mismatch.

## Question

Do graph-scoped scheduler/deferred counters reconcile exactly with operation-work trace rows for the selected `WorldAdapter` substrate during a full `describe_scene` request, while legacy process-global counters remain available as a diagnostic?

## Change from v1

V1 showed that graph-scoped work rows could not be reconciled with process-global scale counters. V2 adds a scoped counter snapshot keyed by the active substrate graph and accumulated only inside `run_rules` operations. The old process-global snapshot and its behavior are preserved. No rule, match, effect, scheduling, or queue semantics are changed.

## Workload and gates

Use the same three-worker full-corpus boot and static/meter/mover `describe_scene` request as v1. Each worker records the reply, work rows, graph-scoped counters, process-global counters, and source/native fingerprints.

1. Three fresh PIDs; inputs and native binary stable before/after.
2. Expected reply in each worker; no work rows dropped; positive work units and nonzero operation IDs.
3. Work-trace totals exactly equal graph-scoped scale totals for all five scheduler metrics and all five deferred queue families' enqueue, drain-batch, and drained-item metrics, including zero counts.
4. Aggregate work rows and scoped counters reproduce across workers. Preserve per-operation totals and process-global counters for diagnosis.
5. Do not use the serialized graph hash as a parity gate; v1 showed that it is not canonical across workers.

## Claim boundary

Passing demonstrates per-graph-scope counter reconciliation on one authored dialogue route and one selected substrate instance. It does not prove all work in the request belongs to that instance, trace recall for uninstrumented operations, learned frame locality, queue prevalence, or scaling. Global-minus-scoped differences are diagnostic, not evidence of missing work until additional graph scopes are captured.
