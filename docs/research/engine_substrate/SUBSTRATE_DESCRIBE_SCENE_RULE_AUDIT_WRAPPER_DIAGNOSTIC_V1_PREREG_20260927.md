# Describe-scene rule event audit wrapper diagnostic v1 (2026-09-27)

## Question

Does wrapping `domains.conversation_action._record_live_goal_event` with the v2.3 scale-audit reset/enable/snapshot sequence, by itself, change the outcome of two simultaneous describe-scene requests?

## Procedure

Use one fresh full-seed adapter with the standard three-percept scene. Keep its built-in conversation lock unchanged, leave native runtime access tracing disabled, and launch two identical utterances concurrently behind a start barrier. Wrap only `_record_live_goal_event` with the same counter-reset, enable, snapshot, and disable calls used by the paired capture. Do not add a selection pause or replace the conversation lock. Capture returned replies and inbound parse, Goal, lifecycle, and outbound-message evidence. Lock current sources before and after.

## Limits

This isolates the scale-audit callback wrapper for one schedule. It does not establish general concurrency safety or effects from combining this wrapper with the lock proxy and access trace.
