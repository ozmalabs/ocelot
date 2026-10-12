# Held-topic runtime interface trace v1.2 (2026-10-01)

## Change and result

The v1.1 trace found 252 concrete `effect_attr_compare_read` events absent from the static read set. `RewriteRule::derive_access` now treats the key written by `SetAttrIfDifferent` as both a read and a write. The optimized native extension was rebuilt from the changed Rust source, loaded from an extracted wheel package, and source-locked separately. No tests were run; this result comes from the live three-worker trace and its independent analyzer.

All 21 worker-turns pass trace, source-stability, fresh-process, event/resource aggregate, and repeated-signature integrity gates. The frozen task-quality oracle remains 18/21: “Can you tell me about copper?” still triggers clarification in all three workers.

| Classification | Observed operations | Share of concrete-resource events |
|---|---:|---:|
| Explicitly declared resource | 3,232,224 | 95.45% |
| Conservatively covered by wildcard | 153,966 | 4.55% |
| Uncovered | 0 | 0% |

The analyzer also records 36 `term_index_query` operations separately. These queries do not expose a concrete type name in the runtime event record and are not included in the explicit/wildcard/uncovered totals. Thus, for event kinds carrying concrete `attr:`, `edge:`, or `type:` keys, all observed operations are now accounted for. This is a dynamic reconciliation on this one workload, not a proof across all effect implementations or unexecuted branches.

## Interpretation and next work

The targeted static dependency defect is repaired: a conditional attribute write now declares the old-value comparison that it performs. This makes the observed static/dynamic join complete for the concrete-key events in this capture. It does not establish frame locality. Almost one in twenty concrete-key observations is still conservatively wildcard-covered, with no resource bound; the type-index query scope is also unresolved. Audit the remaining effect operations for implicit reads and improve index-query attribution before using declarations as an execution-partition contract. Then collect distinct task routes and compare partitioned versus monolithic execution under exact semantic parity.

## Artifacts

- [Preregistration](SUBSTRATE_HELD_TOPIC_RUNTIME_INTERFACE_TRACE_V1_2_PREREG_20261001.md)
- [Runner](../../../scripts/substrate_held_topic_runtime_interface_trace_v1_2.py)
- [Analyzer](../../../scripts/analyze_substrate_held_topic_runtime_interface_trace_v1_3.py)
- [Source lock](../../../evaluation/substrate_capability/held_topic_runtime_interface_trace_v1_2_20261001_lock.json)
- [Compressed capture](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_2_20261001/capture.json.gz)
- [Analysis](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_2_20261001/analysis_v1_3.json)
