# `NodesOfType` site-specific trace capture v2 results

Date: 2026-10-03

## Outcome

A provenance-current native engine (`f6edc8f61411`) was captured under a fresh lock. All ten gates passed across three distinct worker processes and six requests: the ordered prompts and lifecycle reproduce, the final semantic graph digest matches v1.1, semantic controls pass, and no access or work trace rows were dropped. Every direct candidate row has a matching type-read row for the same rule, node, and type.

The distinct direct-site kinds isolate `TermNode::NodesOfType` from helper typed-population accesses:

| Event source | Aggregated rows | Event count |
|---|---:|---:|
| `NodesOfType` query (36) | 114 | 948 |
| `NodesOfType` returned candidates (37) | 4,023 | 37,350 |
| Other typed-population helper query (34) | 15 | 36 |
| Other typed-population helper candidates (35) | 3,708 | 8,646 |

The direct-site trace records 18 request-scoped RuleUID/type query groups with no candidate rows, accounting for 297 query events. Each prompt’s event counts reproduce exactly across all three workers. Query markers therefore expose empty typed populations on the evaluated path, while candidate events retain the population work that returned rows.

This establishes source-specific event visibility and semantic parity for the two-prompt fixture. It does not prove complete dependency recall, estimate how often empty/population queries occur on natural tasks, or measure instrumentation cost: there is no matched access-tracing-off arm. The task-specific rule scopes remain highly connected, so the capture also does not establish frame locality or partition speedup.

## Reproduction artifacts

- Protocol: [v2 preregistration](SUBSTRATE_NODES_OF_TYPE_TRACE_CAPTURE_V2_PREREG_20261003.md)
- Runner: [v2 capture runner](../../../scripts/substrate_nodes_of_type_trace_capture_v2.py)
- Source lock: [v2 lock](../../../evaluation/substrate_capability/nodes_of_type_trace_capture_v2_lock_20261003.json)
- Compressed raw workers: [v2 raw archive](../../../evaluation/reports/nodes_of_type_trace_capture_v2_workers_raw_20261003.json.gz)
- Capture summary: [v2 summary](../../../evaluation/reports/nodes_of_type_trace_capture_v2_20261003.json)
- Independent event/hash analysis: [v2 analysis](../../../evaluation/reports/nodes_of_type_trace_capture_v2_analysis_20261003.json), [analyzer](../../../scripts/analyze_nodes_of_type_trace_capture_v2.py)
- Source inventories: [Term v1.3](../../../evaluation/reports/term_access_dependency_coverage_v1_3_20261003.json), [trace coverage v1.4](../../../evaluation/reports/substrate_runtime_access_trace_coverage_v1_4_20261003.json)

## Next gate

Measure instrumentation cost with randomized matched workers that run the same workload with access tracing disabled and enabled, preserving semantic digests and task outcomes in both arms. Then extend candidate accounting to rejected matcher candidates and derive task-specific active dependency slices before partition parity and cost experiments.
