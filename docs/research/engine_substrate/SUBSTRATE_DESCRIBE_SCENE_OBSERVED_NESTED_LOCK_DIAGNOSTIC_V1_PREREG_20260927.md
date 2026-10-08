# Describe-scene observed plus nested lock diagnostic v1 (2026-09-27)

## Question

Does combining the v2.3 `ObservedLock(trace_enabled=False)` proxy with one extra outer lock acquisition change two simultaneous describe-scene request outcomes?

## Procedure

Use a fresh full-seed adapter and the standard three-percept scene. Replace only `_conversation_lock` with the observed-lock proxy, then wrap each `converse()` call in one additional `with adapter._conversation_lock` block. Do not add access tracing, rule-event audit, or selection barrier. Start two identical requests concurrently behind a barrier; capture source lock, replies, and per-inbound Goal/lifecycle/message readbacks.

## Limits

This isolates the lock-proxy/nested-acquisition interaction for one schedule. It does not establish arbitrary thread safety or test the other v2.3 hooks.
