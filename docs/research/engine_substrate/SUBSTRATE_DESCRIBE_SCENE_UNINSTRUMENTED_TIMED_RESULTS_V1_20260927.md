# Uninstrumented describe-scene timing v1 (2026-09-27)

## Result

The existing plain-concurrency diagnostic was rerun on the exact same source closure and native extension locked by v2.4. The source remained stable. Two simultaneous identical `converse()` calls both joined without errors, returned the expected scene description, and each had one request-bound Goal. Neither trace collection, per-rule scale auditing, nor graph reply readback was enabled in this runner.

The single run recorded 10.746 s and 11.021 s wall time for the A/B caller threads; seed boot took 12.013 s. These are simultaneous-call wall intervals from one two-request shared-adapter schedule, not isolated service-time medians. This diagnostic did not record per-thread CPU, process peak memory, or a repeated timing distribution; do not infer a stable commodity-CPU cost from one sample.

The request summaries confirm the previously noted output-channel gap: both public replies are the expected scene description, while neither inbound has a matching unsuppressed graph outbound Message. The runner's event-kind projection aggregates the shared discourse-state history, so its per-inbound event list is not suitable for lifecycle attribution; request-bound Goal counts are separately recovered.

## Same-source comparison

The v2.4 traced access run and this uninstrumented run have identical hashes for `source_sha256`, `source_closure_sha256`, native extension, and native build manifest. The trace-only comparison is therefore controlled for source generation. V2.4's lifecycle, parity, and access data can be analyzed alongside this capture, but its callback audit and readback timings must remain excluded from baseline latency.

## Artifacts and next measurement

- [plain concurrency protocol](SUBSTRATE_DESCRIBE_SCENE_PLAIN_CONCURRENCY_DIAGNOSTIC_V1_PREREG_20260927.md)
- [plain concurrency runner](../../../scripts/substrate_describe_scene_plain_concurrency_diagnostic_v1.py)
- [source lock](../../../evaluation/substrate_capability/describe_scene_plain_concurrency_diagnostic_v1_lock_20260927.json)
- [raw timing and request report](../../../evaluation/reports/describe_scene_plain_concurrency_diagnostic_v1_20260927.json)
- [v2.4 traced access result](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_4_RESULTS_20260927.md)

Next collect at least five fresh uninstrumented replicates on this exact fixture, measuring per-thread CPU, wall time, and process peak RSS, and separate boot from request execution. Then repeat on independent task families and larger graph sizes before making general tractability claims.
