# Live scheduler-work trace overhead v1 results

Date: 2026-09-28  
Status: all preregistered semantic and counter gates pass; timing evidence is descriptive.

## Result

Nine fresh processes completed the three-arm, three-replicate `describe what you see` panel. Every arm returned the expected reply, and all nine normalized graph signatures, node counts (25,181), and edge counts (11,695) match. Source/native fingerprints were stable before and after every worker and across the capture.

The independent analyzer passes all 12 checks. Baseline produced no scale counters or work rows. Counter and counters-plus-work-trace arms produced identical count-valued scale-audit vectors in every pair. All three traced workers recorded 193 aggregated all-scope work rows with zero drops; per-scope work reconciles exactly with scoped counters, and scoped totals reconcile with process-global scheduler/deferred counters.

| Replicate | Counters / baseline | Counters + work trace / counters | Trace / baseline |
|---:|---:|---:|---:|
| 0 | 1.0463× | 1.0065× | 1.0531× |
| 1 | 1.0704× | 1.0021× | 1.0727× |
| 2 | 1.0540× | 0.9975× | 1.0513× |
| Median | 1.0540× | 1.0021× | 1.0531× |

Conversation-call times ranged from 10.447 to 11.206 seconds. The counters-enabled path was about 5.4% slower than baseline at the median. Adding work tracing on top of counters changed median time by about +0.2%; the three pairs include one slight speedup, so the marginal trace cost is unresolved at this sample size. The trace contained only 193 aggregated rows, while the counter-only path included per-rule accounting; results do not estimate cost for larger traces or high-cardinality workloads.

## Interpretation and limits

For this one full-seed route, work tracing preserves output and adds little measurable cost beyond the enabled scale audit. The scale audit itself has measurable overhead on this route. The design cannot separate host drift from small marginal trace overhead with only three pairs, and it does not estimate the overhead of enabling the concrete graph-access trace. It covers scheduler and five deferred-queue families only where current hooks exist; callback internals, arbitrary adapter work, and omitted native event classes remain outside the measurement.

This result does not establish a general instrumentation overhead factor, runtime frame interface, low treewidth, or natural-task locality. The next gate is a matcher/Term counter calibration with independently known synthetic candidate and predicate work, plus a distinct live route for operation-work scope coverage.

## Reproduction

- Protocol: [preregistration](SUBSTRATE_LIVE_SCHEDULER_TRACE_OVERHEAD_V1_PREREG_20260928.md)
- Runner: [`substrate_live_scheduler_trace_overhead_v1.py`](../../../scripts/substrate_live_scheduler_trace_overhead_v1.py)
- Independent analyzer: [`analyze_substrate_live_scheduler_trace_overhead_v1.py`](../../../scripts/analyze_substrate_live_scheduler_trace_overhead_v1.py)
- Source/native lock: [lock JSON](../../../evaluation/substrate_capability/live_scheduler_trace_overhead_v1_lock_20260928.json)
- Raw capture: [worker records](../../../evaluation/reports/live_scheduler_trace_overhead_v1_20260928.json)
- Analysis: [independent checks and paired ratios](../../../evaluation/reports/live_scheduler_trace_overhead_v1_analysis_20260928.json)

The runner requires `SUBSTRATE_NATIVE_PACKAGE` pointing at the package directory containing the locked extension. It accepts `--lock` to capture a new pre-run lock, then runs without arguments for the nine workers. Run the analyzer after capture.
