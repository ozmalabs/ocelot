# Describe-scene observed lock plus rule-audit diagnostic v1 (2026-09-27)

## Question

Does combining the `ObservedLock(trace_enabled=False)` proxy with the scale-audit wrapper around `_record_live_goal_event` change two simultaneous describe-scene request outcomes, without the extra outer conversation lock or native access tracing?

## Procedure

Use a fresh full-seed adapter with the standard three-percept scene. Replace the adapter lock with the same context-manager proxy used by the v2.3 trace runner and wrap only `_record_live_goal_event` with its counter reset/enable/snapshot/disable calls. Leave native access tracing disabled, do not add the selection pause or outer lock, and start two identical calls concurrently behind a barrier. Capture source hashes, replies, and per-inbound Goal/lifecycle/message evidence.

## Limits

This tests one pairwise hook combination and one schedule. It does not identify higher-order interactions or establish general concurrency safety.
