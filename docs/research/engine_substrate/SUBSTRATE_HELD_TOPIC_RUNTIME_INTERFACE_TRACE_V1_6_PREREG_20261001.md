# Held-topic runtime interface trace v1.6 preregistration (2026-10-01)

## Motivation

The held-topic access trace currently scopes native access events to the adapter's primary substrate. Existing all-scope operation-work tracing can expose scheduler and deferred-queue work in additional graph scopes, including drains that occur through `apply_rule_once` or `apply_rule_batch` outside the main `run_rules` loop. Add this work-only trace alongside the existing per-turn dependency trace, resetting both before each converse call and snapshotting all graph scopes after it. Do not change access tracing or conversation behavior.

## Capture and gates

Repeat the seven held-topic turns in three fresh workers with a source/native lock. For every converse call, capture operation-work rows across all scopes: scope ID, operation ID, producer UID, work kind, queue-family subject, and units. Require zero dropped rows; positive operation/scope IDs and work units; exactly one supported operation-kind marker (`run_rules`, `apply_rule_once`, or `apply_rule_batch`) per operation; stable worker sources; seven turns per worker; repeatable normalized traces across workers; and the existing access/frame invariants. Normalize raw scope pointers to per-scope work profiles for repeated-worker comparison.

Report all-scope scheduler and deferred work by kind, operation kind, queue family, scope, and turn. Keep this separate from concrete read/write access events: operation-work tracing accounts only for instrumented scheduler/deferred counters, not every host callback, matching candidate, Term read, or arbitrary graph mutation. Retain task quality as an independent gate; the known copper clarification failure is expected to remain.

## Interpretation limits

This measures native operation work performed during each converse call, including all observed substrate scopes. It does not capture work outside the call boundary or prove that scheduler/deferred units equal total computation. No frame-locality, partition-safety, overhead, or scaling claim follows without separate measurements.
