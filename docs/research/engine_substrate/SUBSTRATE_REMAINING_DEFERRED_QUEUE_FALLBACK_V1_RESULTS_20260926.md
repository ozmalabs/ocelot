# Scoped pending and global fallback for remaining queue families v1 results (2026-09-26)

## Result

The locked evaluation covers 12 fresh processes: `N={1,2,4,8}` writer/target pairs with three replications, each running full, scoped-only, and scoped-then-global-fallback arms. Source/native inputs stayed stable. Independent analysis passed **207/207 checks**.

For all sizes, full closure and scoped-plus-global-fallback reached identical whole-graph state. Both produced all `N` target edges and `4N` framebuffer grid cells. Scoped-only and the first scoped phase in fallback arms reported pending deferred effects and remained intentionally incomplete: they produced neither target edges nor grid cells. Each scoped phase enqueued exactly `N` records per family and drained none; each subsequent global fallback enqueued none and drained all `N` `rule_edits` and `fb_samples` in one batch. Full closure enqueued and drained `N` items in one batch. Per-writer enqueue attribution matched exactly.

Combined with v2's equivalent evidence for `rule_patches`, `track_identity`, and `net_collapses`, this closes the measured scoped-pending/global-fallback counter and parity matrix for all five instrumented queue families on their authored fixtures.

## Limits

This establishes behavior for one owner-linked synthetic workload, not general correctness for every queue composition or dynamic frame boundary. It does not estimate natural queue frequency, concurrent framebuffer writes, queue throughput, or frame-locality prevalence. Drain timings are audit-on and fixture-specific. Broader closure costs, multi-edge matcher scaling, and naturally derived execution boundaries remain open.

## Artifacts

- [Preregistration](SUBSTRATE_REMAINING_DEFERRED_QUEUE_FALLBACK_V1_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_remaining_deferred_queue_fallback_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_remaining_deferred_queue_fallback_v1.py)
- [Raw workers](../../../evaluation/reports/substrate_remaining_deferred_queue_fallback_v1_workers_raw_20260926.json)
- [Run summary](../../../evaluation/reports/substrate_remaining_deferred_queue_fallback_v1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_remaining_deferred_queue_fallback_v1_analysis_20260926.json)
- [Source/native lock](../../../evaluation/substrate_capability/remaining_deferred_queue_fallback_v1_lock_20260926.json)
