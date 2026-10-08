# Describe-scene observed-lock diagnostic v1 preregistration (2026-09-27)

## Question

Does replacing the adapter's built-in reentrant lock with the v2.3 `ObservedLock` proxy, by itself and with native access tracing disabled, change the result of two simultaneous describe-scene requests?

## Procedure

Use one fresh full-seed adapter, attach the standard three-percept scene, replace only `_conversation_lock` with the same observed-lock proxy implementation used by the paired access-trace runner (`trace_enabled=False`), then launch two simultaneous identical requests behind a start barrier. Do not wrap `_record_live_goal_event`, add a selection barrier, or enable any native trace/audit. Capture both returned surfaces and per-inbound parse, Goal, lifecycle, and outbound-message evidence. Lock current source before and after.

## Limits

This isolates the lock proxy from the access-trace and event-audit hooks for one schedule. It does not identify effects from combinations of hooks or establish arbitrary concurrency safety.
