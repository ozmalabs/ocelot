# Two-edge join degree-skew v1 results (2026-09-26)

## Result

The source/native-locked evaluation covered **126 fresh-process cells**: `M={4,16,64}` complete two-edge paths, decoy ratios `D/M={0,4,16}`, one-sided decoy splits, two authored orders, and three replications. The independent analyzer passed **1,013/1,013 checks**. Each nonzero-ratio split has the same `M` successful bindings and total `D` decoy edges; audit-on/off whole-graph and report parity, fixed-point completion, queue conservation, clause/per-rule candidate-count conservation, and installed-order readback pass. Both authored orders produce equal final graphs for each identical fixture.

At `M=64`, ratio 16 (`D=1,024`), each arm still emits 64 outputs and queues 64 items per deferred family. The writer-rule candidate counts and median uninstrumented closure-call times were:

| Decoy placement | Authored order → installed order | Writer candidate tests by installed edge | Writer tests | Plain wall time |
|---|---|---:|---:|---:|
| Left-only | trigger,left,right,game → trigger,game,right,left | game 1, right 64, left 69,632 | 69,698 | 909 µs |
| Left-only | trigger,right,left,game → trigger,game,right,left | game 1, right 64, left 69,632 | 69,698 | 906 µs |
| Balanced | trigger,left,right,game → trigger,game,right,left | game 1, right 576, left 331,776 | 332,354 | 2,257 µs |
| Balanced | trigger,right,left,game → trigger,game,left,right | game 1, left 576, right 64 | 642 | 557 µs |
| Right-only | trigger,left,right,game → trigger,game,left,right | game 1, left 64, right 64 | 130 | 546 µs |
| Right-only | trigger,right,left,game → trigger,game,left,right | game 1, left 64, right 64 | 130 | 528 µs |

The substrate already reorders match edges at installation using global edge-type cardinalities. In the unbalanced splits, that heuristic picks the lower-population path edge first and both authored orders install identically. In the balanced split, equal cardinalities leave a deterministic tie that depends on authored order. That tie changes the installed final path edge and yields about **518×** difference in writer candidate tests. The median plain closure call in that balanced comparison is about 4.05× longer for the higher-work order. Timing is based on three fresh-process replications and the sub-millisecond baseline is noisy. The instrumented arm is slower in high-work cells, so audit-on timing is not a substitute for plain timing.

The earlier v1.1 order sweep reported *paired workload* tests (writer plus its target rule), which include two fixed target-rule candidate tests per writer. This report's clause table gives writer-rule tests only; the two measures differ by those two fixed tests and are not contradictory.

## Interpretation and limits

The counter evidence shows that the existing count-based install-time reorder handles unequal relation populations consistently but has a costly tie case when global cardinalities match and join selectivity differs by order. An optimizer based on estimated intermediate join cardinality is a concrete next target. The plain timing moves in the same direction in the largest balanced comparison, but three repetitions and these small fixtures do not establish a stable speedup or general relation between candidate counts and runtime. The capture does not estimate natural-task frequency, memory use, or behavior beyond this isolated two-edge schema.

The matcher source explains the measured asymmetry: a bound source enumerates outgoing `(node, edge type)` neighbors; a bound target enumerates incoming neighbors; with both endpoints bound, the current branch still enumerates the source's outgoing neighbors before rejecting nonmatching targets. A follow-up order policy should therefore estimate candidate expansion from endpoint-specific degrees and expected bound-variable populations, not global edge-type counts alone. First evaluate an exact small-fixture cost oracle and charge its planning work; then test a bounded/sample-based estimator against the current count heuristic. Hold graphs, rule effects, output cardinality, process count, and measurement boundaries fixed. Report authored and installed order, writer-only and whole-paired candidate totals distinctly; gather repeated uninstrumented closure CPU/wall time, peak RSS, exact semantic parity, and instrumentation overhead. After the synthetic gate, replay frozen representative task-derived subgraphs before making claims about the cheap-cut hypothesis.

## Artifacts

- [Preregistration](SUBSTRATE_JOIN_DEGREE_SKEW_V1_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_join_degree_skew_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_join_degree_skew_v1.py)
- [Raw workers](../../../evaluation/reports/substrate_join_degree_skew_v1_workers_raw_20260926.json)
- [Run summary](../../../evaluation/reports/substrate_join_degree_skew_v1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_join_degree_skew_v1_analysis_20260926.json)
- [Source/native lock](../../../evaluation/substrate_capability/join_degree_skew_v1_lock_20260926.json)
