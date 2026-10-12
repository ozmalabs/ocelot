# Thoughtexperiment predecessor fanout instrumentation overhead v1.1 — results

Date: 2026-10-04

## Result

The higher-replication source-locked panel completed 32/32 workers without
failure. All 16 instrumented/uninstrumented pairs pass the exact candidate
outcome projection; every arm also passes candidate selection, direct-oracle
graph parity, primary isolation, rule preservation, stale-revision rejection,
and scoped-closure quiescence. The source lock is stable before and after the
capture.

The paired mean lifecycle delta (instrumented minus control) is −154 ms for
full-copy, with a 95% paired t interval of −470 to +163 ms, and +127 ms for
shared pages, with an interval of −85 to +340 ms. Both intervals include zero
and remain wide. Median paired deltas are −61 ms and +113 ms respectively;
observed ranges are −998 to +273 ms and −207 to +469 ms. These data do not
identify a precise wrapper-overhead correction. At this sample size they are
consistent with no effect and with moderate effects in either direction.

The on-arm median graph export/digest measurements are 2.34/0.69 s for
full-copy and 2.43/0.72 s for shared pages. These remain descriptive timer
shares; the instrumentation effect is not calibrated tightly enough to treat
them as precise estimates. The median lifecycle remains about 3.2–3.3 s.

## Claim boundary

Eight pairs per backend reduce uncertainty relative to v1, but this is still
one host and one authored graph/task shape. A paired t interval is descriptive
at n=8 and assumes a roughly symmetric paired-difference distribution. No
natural workload prevalence or graph-size scaling is established.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_INSTRUMENTATION_OVERHEAD_V1_1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1_20261004.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_2_analysis_20261004.json)
