# Describe-scene access-trace isolation v1 (2026-09-27)

## Question

On one unchanged source snapshot, does enabling native access tracing around the serialized request lock by itself prevent the current describe-scene lifecycle from completing?

## Design

Run two fresh adapters sequentially in one process, one trace-off and one trace-on, each with the same scene and two simultaneous identical requests. Keep the observed reentrant lock proxy in both arms; it enables/resets the native trace only after outermost lock acquisition and disables/snapshots before outermost release. Do not install the rule-audit wrapper, nested public lock, or selection pause. Compare source closure hashes before and after, worker completion, public replies, request-bound Goals and lifecycle events. Preserve the trace event count as instrumentation evidence only if both arms pass lifecycle gates.

This isolates only native trace toggling on the current immutable snapshot and schedule. It does not estimate natural workload cost or complete access locality. If source hashes change or either lifecycle gate fails, classify the comparison as inconclusive/censored.

## Gates

- Both arms recover exactly two inbound requests and join both workers without error.
- Both replies equal the expected scene description; each request has one resolved Goal and selection/execution/action-result events.
- The source lock is identical before and after the paired run.
- Trace-off has zero recorded access events; trace-on records trace events without drops.

Runner and output: [isolation runner](../../../scripts/substrate_describe_scene_access_trace_isolation_v1.py), [report](../../../evaluation/reports/describe_scene_access_trace_isolation_v1_20260927.json).
