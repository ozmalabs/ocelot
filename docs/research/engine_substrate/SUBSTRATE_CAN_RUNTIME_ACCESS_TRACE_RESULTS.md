# CAN runtime access trace

**Run date:** 2026-09-25  
**Evidence grade:** selected workload trace with paired semantic control  
**Status:** 16 traced/untraced pairs match graph, progress, settlement, and an independent local fixed-point oracle. No observed resource key falls outside the corresponding native static access set.

## Protocol and workload

The runner [`substrate_can_runtime_access_trace_v1.py`](../../../scripts/substrate_can_runtime_access_trace_v1.py) reuses the project’s authored native CAN rules and fixture builder. It covers N=8/16, path/complete coupling, two-state/three-state updates, and two seeded replicates per cell. Each cell runs the same generated input once with the concrete trace disabled and once enabled. Both arms must produce equal final states and progress, settle on a zero-progress terminal probe, and pass the separately computed local update residual. The traced arm also enables per-rule scale counters. The [independent analyzer](../../../scripts/analyze_substrate_can_runtime_access_trace_v1.py) compares concrete identity overlaps with the native static `rule_access_sets()` keys among rules that emitted trace events, then reconciles each implemented event site against the corresponding per-rule operation counter.

## Results

All six runner checks pass across 16 paired cells. The refreshed trace build records 152,576 event occurrences in total, with no event-cap overflow. The increase from the initial 106,188-event capture reflects added concrete TypeOf and adjacency events; it is not a workload-growth change. Final graph/state and progress match in every pair; all terminal probes return zero; every independent residual is zero; and every observed resource key is present in the corresponding rule’s static read/write projection or covered by its wildcard flag. For every observed CAN rule, per-rule trace counts exactly reconcile with scale-audit counts for interpreted Attr evaluations, accepted binding leaves × pattern-edge arity, SetAttr attempts, and AddEdge attempts. This validates accounting at the instrumented sites for this workload while leaving omitted term/effect families unvalidated.

In every cell, five rules emit trace events. Intersecting their global static keys yields 24 possible writer→reader rule pairs after wildcard completion. Intersecting concrete `Attr(node,key)` and edge `(src,type,tgt)` identities in the observed trace yields 4 pairs; the other 20 static pairs have no concrete overlap in these finite traces. The static-to-observed overlap ratio is therefore 6:1 in this particular workload slice.

Raw capture: [`substrate_can_runtime_access_trace_v1_20260925.json`](../../../evaluation/reports/substrate_can_runtime_access_trace_v1_20260925.json). Independent analysis: [`substrate_can_runtime_access_trace_v1_analysis_20260925.json`](../../../evaluation/reports/substrate_can_runtime_access_trace_v1_analysis_20260925.json). The initial one-replicate capture is preserved separately as [`one-replicate raw`](../../../evaluation/reports/substrate_can_runtime_access_trace_v1_one_replicate_20260925.json) and is superseded by the two-replicate runner output.

## Interpretation and limits

This is direct evidence that node identity can reduce apparent static coupling for this small authored CAN workload. It is not evidence that the 20 unobserved pairs are impossible, that the 4 observed overlaps are all scheduler dependencies, or that any of the resulting cuts preserve semantics. The trace covers accepted pattern edges, interpreted `Attr`/`TypeOf` reads, and selected native effect events only; it misses JIT predicate reads, most aggregate/traversal Term footprints, external host mutation, and some effect families. The analysis has two replicates per cell and no trace-overhead arm; the wall cost of tracing is unknown. Counts are not a treewidth estimate and do not support a general cheap-cut claim.

Next: measure trace coverage against scale-audit invocation counts, measure enabled/disabled cost on these same cells, and repeat on an authored conversation workload. Only then use observed concrete dependencies to propose frame cuts and test them against monolithic closure plus omitted-boundary negative controls.

Reproduce with:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_can_runtime_access_trace_v1.py
python3 scripts/analyze_substrate_can_runtime_access_trace_v1.py
```
