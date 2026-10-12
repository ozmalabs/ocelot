# Thoughtexperiment predecessor fanout instrumentation overhead v1 — results

Date: 2026-10-04

## Result

All twelve source-locked workers completed with no failures. The independent
v1.1 analyzer confirms exact pairwise semantic outcome parity for all six
instrumented/uninstrumented pairs, as well as graph/oracle parity, primary
isolation, rule preservation, stale-return rejection, and quiescent candidate
closure in each arm.

Paired lifecycle timing is noisy at this sample size. For full-copy, the
instrumented-minus-control deltas range from −182 to +222 ms, with median
−0.5 ms and median on/off ratio 1.000. For shared pages, deltas range from −69
to +208 ms, with median −45.8 ms and median ratio 0.986. The paired data do not
show a consistent slowdown, but three pairs per backend cannot establish
negligible instrumentation overhead. The instrumented arms reproduce median
graph-export/digest times of 2.53/0.79 s (full-copy) and 2.52/0.74 s (shared
pages), broadly consistent with the preceding cost decomposition.

## Analyzer correction

The first post-capture analyzer checked that each arm independently passed the
monolithic oracle but compared only the boolean oracle-parity flag across
paired arms. It did not compare the candidate outcome records themselves. The
v1.1 analyzer adds an exact projection comparison over candidate identity,
grounding status/evidence, grounded-frame counts, closure work, and residual
counts. All six pairs pass. The raw capture and pre-run lock are unchanged; use
the v1.1 analysis for paired semantic parity.

## Claim boundary

This estimates the combined effect of clock calls and Python wrapper dispatch
for one authored 100k-node workload on one host. The timing ranges overlap
zero, but the sample is too small for a general overhead factor. It does not
establish general engine cost or graph-size scaling.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_INSTRUMENTATION_OVERHEAD_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1.py)
- [Initial analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1.py)
- [Amended analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1.py)
- [Lock](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_20261004.json)
- [Amended analysis](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1_analysis_20261004.json)
