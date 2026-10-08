# Remaining deferred-queue family audit v1 results (2026-09-26)

## Result

Twelve fresh-process workers covered 1, 2, 4, and 8 writer/target pairs with three replications per size. Each writer queued one legacy rule-clause edit and one framebuffer sample; a real `/dev/shm` BGRA frame was sampled into a 2×2 grid. Inputs stayed locked before and after each worker. The independent analyzer passed **75/75 checks**.

In every cell, audit-on and audit-off runs reached the same fixed point and produced identical full graph state and reports. All `N` target rules opened and produced their expected `seen_i` edge; each game received four grid cells. For both `rule_edits` and `fb_samples`, counters recorded exactly `N` enqueues, `N` drained items, one drain batch, and nonnegative drain time. Per-rule attribution assigned exactly one enqueue from each writer rule to each queue family.

## Cumulative queue coverage

Together with deferred-queue audit v2, all five instrumented families now have direct dynamic enqueue/drain evidence: `rule_edits`, `rule_patches`, `fb_samples`, `track_identity`, and `net_collapses`. The earlier v2 experiment covered scoped-only pending behavior and global fallback drain for `rule_patches`, `track_identity`, and `net_collapses`. This v1 experiment covers full-closure conservation and audit parity for `rule_edits` and `fb_samples`; it does **not** measure scoped-only pending or fallback behavior for those two families. Queue timing is audit-on and fixture-specific.

## Limits and next gate

This validates queue instrumentation and semantic parity on one authored workload. It does not estimate natural queue frequency, concurrent external framebuffer changes, real image segmentation quality, queue throughput, or production prevalence. Next test scoped-only pending plus global fallback for `rule_edits` and `fb_samples`, then combine complete queue-family capture with positive multi-edge joins and mutation requeues before making a whole-scheduler cost claim.

## Artifacts

- [Preregistration](SUBSTRATE_REMAINING_DEFERRED_QUEUE_FAMILIES_V1_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_remaining_deferred_queue_families_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_remaining_deferred_queue_families_v1.py)
- [Raw workers](../../../evaluation/reports/substrate_remaining_deferred_queue_families_v1_workers_raw_20260926.json)
- [Run summary](../../../evaluation/reports/substrate_remaining_deferred_queue_families_v1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_remaining_deferred_queue_families_v1_analysis_20260926.json)
- [Source/native lock](../../../evaluation/substrate_capability/remaining_deferred_queue_families_v1_lock_20260926.json)
