# Held-topic runtime interface trace v1.3 (2026-10-01)

## Effect dependency audit and result

The source audit extended the v1.2 repair to effects that inspect existing graph state. `SetAttr` declares the target key as read and write because it compares old and new values; `AddNodeIfAbsent` declares each candidate attribute key as read; `AddEdge` and `DelEdge` declare their edge key as read and write because they probe whether that edge exists. Native tracing now records those old-value, candidate-attribute, and edge-existence reads, including absent-edge probes.

The optimized extension was rebuilt from the changed source and loaded from an isolated extracted wheel. Three fresh workers completed all seven turns. Source stability, trace/interface aggregates, rule UID mapping, zero dropped events, and repeated runtime signatures pass. The independent task-quality oracle remains 18/21; all workers still ask for clarification on “Can you tell me about copper?”

| Classification | Observed operations | Share of mapped concrete-resource events |
|---|---:|---:|
| Explicit declarations | 3,585,810 | 95.88% |
| Conservative wildcard declarations | 153,966 | 4.12% |
| Uncovered | 0 | 0% |

The analyzer accounts for 3,739,776 concrete-resource events exactly. Thirty-six additional `term_index_query` events have no concrete type identity in the captured event and remain separately unclassified. The newly instrumented events include 346,233 attribute comparison reads and 2,718 edge-existence reads; both are explicitly declared. There are no unexplained concrete-key events in this workload.

## Limits and next action

This confirms the finite effect dependencies exercised by this task path. It does not prove completeness for other effect implementations, deferred effects outside the converse trace window, or unexecuted branches. The 153,966 wildcard-covered events still expose no bounded resource set, and the 36 type-index queries still lack type-name and population attribution. Before treating access declarations as a partition contract, audit broad and deferred effects, add type/scope data to index-query instrumentation, and run a second task route. Then compare partitioned and monolithic execution under exact semantic parity.

## Artifacts

- [Preregistration](SUBSTRATE_HELD_TOPIC_RUNTIME_INTERFACE_TRACE_V1_3_PREREG_20261001.md)
- [Runner](../../../scripts/substrate_held_topic_runtime_interface_trace_v1_3.py)
- [Analyzer](../../../scripts/analyze_substrate_held_topic_runtime_interface_trace_v1_4.py)
- [Source lock](../../../evaluation/substrate_capability/held_topic_runtime_interface_trace_v1_3_20261001_lock.json)
- [Compressed capture](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_3_20261001/capture.json.gz)
- [Analysis](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_3_20261001/analysis_v1_4.json)
