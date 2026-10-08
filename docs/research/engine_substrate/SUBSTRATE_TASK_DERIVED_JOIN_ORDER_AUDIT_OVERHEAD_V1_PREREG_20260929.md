# Task-derived join-order audit-overhead replay v1 preregistration

Date: 2026-09-29, before confirmatory capture.

## Question and design

Estimate the timing effect of native global, per-rule, and per-clause scale
counters on the frozen ten-event common-ground task. Run paired fresh-process
workers at 0, 8, and 32 disconnected decoy components, always requesting the
seed-authored `discourse_goal_select` order `0123`. The current native rule
installer remains enabled. Cross each context with ten paired repeats and
counter mode `off` or `on` (60 workers total); randomize the complete schedule
with a fixed seed. Each pair uses the same context/order/repeat inputs and
differs only in whether the counter APIs enable instrumentation.

The task, fixture-supplied identity links, rule set, and context construction
are the v1 context-scale replay. Record all ten event-closure wall and process
CPU times, task/common-ground outcomes, installed-order readback, complete
graph digest, and audit counters. Off-mode counters must remain zero; on-mode
candidate counts must reconcile against the v1 capture for matching context
and installed order. Compare the complete semantic graph within every pair.

## Gates and claim boundary

- Exactly 30 pairs / 60 workers, all in unique fresh processes, with stable
  source/native fingerprints.
- Every worker preserves the two-goal task oracle, common-ground oracle,
  ten fixed points, and expected decoy inertness.
- Paired graph digests and task paths agree exactly; both modes read back the
  same installed clause order for each context.
- Counter-off per-rule/global/clause totals are zero; counter-on counts
  reconcile with native target-rule attribution.
- Report paired wall and CPU ratios with medians, ranges, and all pair values.
  The sample is one small task and does not establish general instrumentation
  overhead, uninstrumented production latency, throughput, or scaling.

No thresholds are tuned from timing outcomes. Source, native binary, task
inputs, base runner, this protocol, runner, and analyzer are locked before the
capture.

## Harness smoke disclosure

Before the lock was written, one excluded D=8 pair checked the counter toggle.
Both arms passed task/common-ground oracles and fixed points and produced the
same full graph digest. The off arm recorded zero audit counters; the on arm
recorded 6,423 total counter increments. This smoke only confirms the two
modes execute as intended; its timings and work counts are excluded from the
30-pair confirmatory analysis.
