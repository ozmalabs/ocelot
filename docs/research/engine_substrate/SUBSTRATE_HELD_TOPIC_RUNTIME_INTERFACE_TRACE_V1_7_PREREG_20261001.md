# Held-topic runtime interface trace v1.7 preregistration

**Question:** Do deferred queue enqueues observed across a complete worker reconcile with queue drains, while preserving the v1.6 per-turn dependency/access and task checks?

## Design

Repeat the same seven held-topic turns in three fresh workers using a source/native lock. Enable all-scope scheduler/deferred operation-work tracing once before each worker and leave it enabled through the worker. Do not reset the native trace between turns. Continue capturing concrete graph access only around each `WorldAdapter.converse`, using cumulative snapshots and per-call differences. Capture work deltas before, during, and after each conversation, plus the complete worker total. This retains producer work that occurs before a conversation, which the v1.6 per-conversation reset discarded.

The trace reports raw graph pointer scope IDs as process-local diagnostics. Repeatability gates compare normalized operation rows without scope IDs, because allocator reuse can change pointer grouping without changing operation work. Queue family subject codes are preserved. A queue-accounting claim requires enqueue and drained-item units to reconcile by family over the whole worker; drain-batch counts are reported separately and are not compared to item counts.

## Integrity gates

- Three fresh worker processes, seven turns each, unchanged locked inputs, and current runner/analyzer/protocol/native hashes.
- Zero dropped access or operation-work records; valid operation markers and positive row units.
- Existing task-frame partition, schema, access attribution, and repeat-signature invariants remain in force.
- Whole-worker rows equal the sum of pre-turn, during-turn, and post-worker segments.
- Normalized whole-worker operation work is identical across the three workers.
- Deferred queue enqueue-item and drained-item counts reconcile by family; any mismatch is reported as an unresolved accounting gap, not hidden by a passing turn-level trace.
- Frozen task quality is reported separately from trace integrity.

## Scope limits

This is explicit scheduler/deferred-work instrumentation on one authored route. It does not measure all CPU work, all graph mutations, host callbacks, all matcher candidates, or queue behavior on other tasks. A passing result is not a complete execution trace or a general tractability result.
