# Held-topic runtime interface trace v1.1 (2026-10-01)

## Result

Three fresh current-source workers replayed the seven held-topic turns. All 21 turns have zero dropped runtime events, mapped rule UIDs, reconciled frame/interface and trace aggregates, and repeated runtime signatures. The frozen task-quality oracle passes 18/21; all workers still ask for clarification on “Can you tell me about copper?” The trace-integrity result is therefore positive while task quality remains independently failed.

The v1.1 runner records all eight values returned by native `rule_access_sets()`, including `reads_any` and `writes_any`, and refreshes declarations after each turn. Across all three workers, the analyzer classifies 3,385,326 concrete-resource read/write observations as follows:

| Classification | Observed operations | Share of mapped operations |
|---|---:|---:|
| Explicitly declared resource | 3,231,108 | 95.45% |
| Conservatively covered by `reads_any` / `writes_any` | 153,966 | 4.55% |
| Not covered by the corresponding explicit set or wildcard | 252 | 0.007% |

Another 36 `term_index_query` observations are reported separately because they carry no concrete attribute/edge/type resource that can be reconciled against these sets. No mapped event was missing its static rule row or resource.

All 252 uncovered events are `effect_attr_compare_read` operations from `optic_flow_refuse_no_translation`: 126 reads of `assessment.status` and 126 reads of `assessment.reason`. The seed rule uses `set_attr_if_different` to write those same fields ([source](../../../seeds/optic_flow_spatial_grounding.json#L179)). That effect compares the existing value before deciding whether to write, but the derived static read set does not include those effect-time comparisons. This is a genuine static dependency-accounting gap, not an observed cross-frame access. The explicit write declarations are present; the missing declarations are reads of the same attributes.

The 4.55% wildcard-covered share is safe only as a conservative accounting classification. It is not evidence of frame locality: wildcard declarations do not name a bounded resource set. The 36 index queries likewise remain outside this concrete-resource join. Runtime hooks cover instrumented native accesses inside the captured converse calls and do not prove completeness for host work, unexecuted branches, or other task paths.

## Capability assessment

The capture shows that the substrate can expose per-rule declared sets and observed native accesses on a live workload, and the two can be joined with high coverage. It also shows that declared access metadata currently misses effect-time read dependencies created by conditional writes. Until that rule metadata is corrected or the access-set API models such implicit reads, static access declarations cannot be used as a sound dependency boundary for partitioning or parallel execution.

The small answer-lifecycle projections remain much smaller than the runtime activity described in the v1 report. This workload does not establish that the outside-cut events are required or safely removable. Cheap-cut prevalence and end-to-end partitioned execution remain unmeasured.

## Artifacts

- [Protocol amendment](SUBSTRATE_HELD_TOPIC_RUNTIME_INTERFACE_TRACE_V1_1_PREREG_20261001.md)
- [Runner](../../../scripts/substrate_held_topic_runtime_interface_trace_v1_1.py)
- [Analyzer](../../../scripts/analyze_substrate_held_topic_runtime_interface_trace_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/held_topic_runtime_interface_trace_v1_1_20261001_lock.json)
- [Compressed capture](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_1_20261001/capture.json.gz)
- [Analysis](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_1_20261001/analysis_v1_2.json)
