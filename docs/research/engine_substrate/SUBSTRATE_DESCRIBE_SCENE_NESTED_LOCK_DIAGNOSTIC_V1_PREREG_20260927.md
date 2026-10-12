# Describe-scene nested-lock diagnostic v1 (2026-09-27)

## Question

Does one additional outer acquisition of the adapter's built-in reentrant conversation lock, around each otherwise plain `converse()` call, change two simultaneous describe-scene request outcomes?

## Procedure

Use one fresh full-seed adapter with the standard three-percept scene. Wrap only the public call in `with adapter._conversation_lock: original_converse(...)`; preserve the adapter's original lock object, do not add an observed-lock proxy, event callback, access trace, audit, or selection barrier. Start two identical requests concurrently behind a barrier. Record per-inbound parse, Goal, lifecycle, event, reply, and graph-message outcomes. Lock sources before and after.

## Limits

This isolates an extra reentrant acquisition for one schedule. It does not establish arbitrary thread safety or test the entire v2.3 hook combination.
