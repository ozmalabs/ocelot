# Held-topic runtime interface trace v1.3 preregistration (2026-10-01)

## Scope

The source audit after v1.2 found three more finite effect-time dependencies on the held-topic runtime path: `SetAttr` compares its existing value, `AddNodeIfAbsent` compares configured attributes on same-type candidates, and `AddEdge`/`DelEdge` inspect the existence of the target edge. Extend `derive_access` so these keys are declared as reads as well as writes. Add native trace events at the actual comparison/probe sites, including unsuccessful edge-existence probes. Preserve existing write events and v1.2 outputs.

## Measurement

Rebuild the optimized native extension from the changed source and run the same seven turns in three fresh workers. Lock the protocol, runner, analyzer, task source, and exact loaded native binary. Capture every `rule_access_sets()` field at turn boundaries and the per-event rule UID, kind, node, resource, peer, and count.

The analyzer must reconcile concrete attribute/type/edge reads and writes against corresponding explicit declarations, retaining conservative wildcard coverage separately. Structural node deletion and edge replacement events may be covered only by the appropriate wildcard flags where their resource expansion is runtime-dependent. Keep type-index queries and any event kinds lacking concrete resource keys explicit in the unresolved category; do not silently count them as complete. Require exact per-class totals, zero dropped events, no unresolved rule UIDs, stable inputs, fresh workers, seven turns each, and repeatable trace/interface signatures. Task quality is separate and the known copper clarification failure is expected to remain.

## Limits

This checks executed native events on one task route. It does not prove static completeness for unexecuted branches, host operations, deferred work after the capture hook, or all effect variants. Wildcard flags do not provide bounded locality. No partitioned-versus-monolithic execution claim follows from access reconciliation alone.
