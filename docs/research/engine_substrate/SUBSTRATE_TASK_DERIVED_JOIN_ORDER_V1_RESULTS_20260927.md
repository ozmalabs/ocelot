# Task-derived four-edge join-order replay v1 results

Date: 2026-09-27 local

## Result

The 72-worker source/native-locked replay passes **1,132/1,132 independent checks**. All 24 authored clause permutations were run in three fresh processes. Every worker passes the common-ground task and goal-identity oracle; all ten event closures reach fixed point; all 72 workers produce the same final graph. Target-rule candidate work is conserved between per-rule and per-clause native counters at every checkpoint.

The current seed-authored order (`0123`, `has_active_goal → originated_in → has_event → for_goal`) installs unchanged and incurs a median **106 target-rule candidate tests** over the ten event closures. The lowest-work order realized by the current installer is `originated_in → for_goal → has_event → has_active_goal` at 36 tests. The highest-work realized order is `has_event → has_active_goal → originated_in → for_goal` at 139 tests. Across all workers the range is 36–139, a **3.86×** spread at identical task output. The installer realizes 20 distinct orders from the 24 authored permutations; four authored pairs collapse onto existing orders. Repeats are exact within each permutation/order.

This is stronger than the synthetic chain estimate in one specific respect: the candidate work comes from a real task rule and native matcher running over the fixture's evolving graph, and each clause is attributed. It establishes order sensitivity for `discourse_goal_select` in this task fixture. The four `for_goal` edges are supplied by the frozen benchmark fixture to make the independent identity oracle identifiable; they are not produced by current conversation event ingestion. Opt-in scale audit was enabled, so closure wall/CPU measures are instrumented and are not used for a speed claim.

## Interpretation

The task confirms that global count-based reordering and author permutations can materially change native candidate work even when the complete result is unchanged. The 3.86× range motivates testing task-local cost estimators, but this panel does not show that a sample estimator would predict the best order or that changing production order is safe across other rules, mutations, or task distributions. Next capture at least one second task family with a different match topology, then build the predictor against exact per-clause work and charge planning cost before considering engine integration.

## Artifacts

- [Preregistration](SUBSTRATE_TASK_DERIVED_JOIN_ORDER_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_task_derived_join_order_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_task_derived_join_order_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/task_derived_join_order_v1_lock_20260927.json)
- [Raw workers](../../../evaluation/reports/substrate_task_derived_join_order_v1_workers_raw_20260927.json)
- [Analysis](../../../evaluation/reports/substrate_task_derived_join_order_v1_analysis_20260927.json)

Claim boundary: one frozen task fixture, one varied four-edge rule, fixture-supplied identity links, 24 authored permutations, three process repeats, and audit-on native work. No natural prevalence, general optimizer, or uninstrumented latency claim follows.
