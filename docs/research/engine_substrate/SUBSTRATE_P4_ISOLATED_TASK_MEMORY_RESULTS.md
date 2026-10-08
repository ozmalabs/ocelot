# Isolated per-task P4 acquisition memory results

**Outcome:** all 18 locked workers completed in distinct OS processes. This is a diagnostic repeat on the same already inspected contrast-string family.

**Execution note:** the first orchestrator invocation stopped on its first worker because the scorer did not receive the worker-local synthesis module. No task record was written. The scorer call was corrected, the runner hash in the lock was refreshed, and the full 18-worker run then completed; only that locked run is summarized below.

The result pattern reproduced the shared-process route: 11/18 tasks returned accepted IR and 5 of those passed all seven revealed/held-out rows. TermArena logical length changed by zero in every worker. Graph node count again increased by +103 to +119 (1,959 total across workers).

Per-worker process peak RSS ranged from 50,636 to 81,204 KiB (median 59,224 KiB). RSS change during route acquisition ranged from +2,160 to +31,036 KiB (median +5,158 KiB). The accepted route subset had median peak RSS 52,196 KiB and median route RSS change +2,264 KiB; gapped enumeration cases had median peak RSS 75,640 KiB and median route RSS change +26,884 KiB. The contrast localizes higher memory use to the observed gapped routes in this fixture, but does not attribute it to a specific native allocation or establish expected costs elsewhere. Since every process includes imports and seed boot, peak RSS is a whole-worker envelope rather than route-only memory.

Route-window Python `tracemalloc` current deltas were 23–28 KiB (median 26 KiB); peaks were 45–105 KiB (median 84 KiB). These values exclude Rust/native allocator use. Their small size alongside larger RSS changes, especially on gapped routes, is consistent with substantial non-Python memory activity, but RSS includes allocator retention and other process effects, so the difference is not a native-allocation measurement. Median route wall time was 172 ms overall.

This isolates process high-water memory by task and shows zero logical TermArena growth on the repeated route. It does not estimate a task population, prove arena allocation capacity is stable, or identify exact native allocations. The family and outcomes are not blind. See the [locked raw report](../../../evaluation/reports/substrate_p4_isolated_task_memory_20260925.json), [preregistration](SUBSTRATE_P4_ISOLATED_TASK_MEMORY_DIAGNOSTIC_PREREG_20260925.md), [runner](../../../scripts/substrate_p4_isolated_task_memory_diagnostic.py), and [pre-run lock](../../../evaluation/substrate_capability/p4_isolated_task_memory_lock_20260925.json).

**Next:** profile native allocations/capacity on a new independently generated task family, retaining successful retrieval, false-accept, and budget-gap cases. A valid capability estimate also requires an independent task split and paired controls; this memory diagnostic alone is not that estimate.
