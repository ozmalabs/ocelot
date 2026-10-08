# Deferred queue operation-work trace v2 preregistration

**Question:** Do native per-operation work rows expose the same deferred-item enqueue and drain counts reported by the independent family counters, across full closure, scoped-only pending work, and global fallback?

## Fixture and arms

Reuse the authored mixed deferred workload from the v2 audit. It emits one `RulePatch`, one `TrackIdentity`, and one `NetCollapse` per writer. Measure writer counts 1, 2, and 4; two replications; and three arms: full closure, scoped-only, and scoped plus global fallback. This yields 18 fresh worker processes. Earlier locked studies cover `rule_edits` and `fb_samples`; this trace does not claim to cover those families.

For each closure phase, enable all-scope runtime operation-work tracing immediately before the phase, then disable and snapshot it immediately afterward. The scoped-delta API now enters the same operation-work guard as full closure, so work inside scoped matching/effects has an operation identity. Independently retain scale-audit family totals and per-rule producer attribution. Do not change graph semantics or queue ordering. Each trace row records graph scope pointer, operation ID, producer RuleUID, work kind, optional queue-family code, and units.

## Gates

- The current runner, analyzer, protocol, native extension, and queue/work instrumentation sources match the source lock before and after capture.
- Eighteen fresh worker processes cover exactly the declared size × replicate × arm matrix.
- Existing semantic gates hold: pending state is explicit after scoped-only, full and fallback final state match exactly, and runs reach fixed point.
- Every phase has zero trace drops, valid positive operation/scope IDs and units, and exactly one supported operation marker per captured operation.
- For each family and phase, runtime-work enqueue, drained-item, and drain-batch units equal the corresponding scale-audit family counters.
- Queue conservation is evaluated only for phases with nonempty enqueue items; scoped-only intentionally has pending items and zero drains.
- Enqueue producer RuleIdx attribution remains independently checked by the existing scale-audit counters. Runtime rows use RuleUID and drain records do not retain producer identity.

## Claim limits

This is a synthetic fixture and an explicit instrumented-work trace, not full CPU accounting. It covers three queue families and one operation path; it does not establish natural queue prevalence, workload throughput, all matcher work, host callback cost, safe frame partitioning, or asymptotic complexity. The existing separate queue-family studies are needed for the other two instrumented families.
