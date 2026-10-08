# Held-topic runtime interface trace v1.5 (2026-10-01)

## Index and typed-population attribution

The 36 v1.3/v1.4 `term_index_query` events were ShapeDecode typed-population fingerprints, not `NodesWhere` attribute-index lookups. The trace now names them `term_typed_population_query` and records one candidate visit for every node whose type population contributes to the cache fingerprint. The legacy snapshot remains available; the detailed snapshot represents a type-symbol peer separately from a graph node ID.

The optimized native build and three-worker, seven-turn replay pass source stability, freshness, trace/interface reconciliation, zero dropped-event, and repeat-signature gates. The independent task-quality result remains 18/21: the copper clarification prompt fails in each worker.

| Typed population | Fingerprint queries | Candidate node visits |
|---|---:|---:|
| `ShapeSignature` | 21 | 8,589 |
| `DimensionGenerator` | 6 | 36 |
| wildcard sentinel `·?·` | 9 | 0 |
| **Total** | **36** | **8,625** |

These are three-worker totals. The wildcard sentinel is a term-level shape marker, not a node type with a populated graph set. The candidate visits are guarded by `reads_any`, so the capture identifies their volume but not a bounded interface. These scans also hash all attributes on each visited node; the visit count does not weight attribute count, value size, or CPU time.

No `NodesWhere` indexed or fallback query occurred in these seven turns. The new detailed event path can attribute its query type and attribute, but indexed internal work is still unmeasured; candidate/result counts would only measure fallback visits and returned rows. Thus this capture resolves the earlier event ambiguity and sizes ShapeDecode's typed-population scanning, but leaves attribute-index workload prevalence unknown.

Across the complete capture, the analyzer reconciles 3,748,437 concrete-resource observations: 3,585,810 explicitly declared and 162,627 conservatively wildcard-covered, with none uncovered or unmapped. Task quality and trace integrity remain separate gates.

## Next work

Audit deferred and broad effects whose execution occurs outside the `converse` trace window. Then capture a second task route and compare its access and typed-population distributions. Wildcard access remains a locality gap; partitioned-versus-monolithic execution still requires an exact semantic parity experiment.

## Artifacts

- [Preregistration](SUBSTRATE_HELD_TOPIC_RUNTIME_INTERFACE_TRACE_V1_5_PREREG_20261001.md)
- [Runner](../../../scripts/substrate_held_topic_runtime_interface_trace_v1_5.py)
- [Analyzer](../../../scripts/analyze_substrate_held_topic_runtime_interface_trace_v1_6.py)
- [Source lock](../../../evaluation/substrate_capability/held_topic_runtime_interface_trace_v1_5_20261001_lock.json)
- [Compressed capture](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_5_20261001/capture.json.gz)
- [Analysis](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_5_20261001/analysis_v1_6.json)
