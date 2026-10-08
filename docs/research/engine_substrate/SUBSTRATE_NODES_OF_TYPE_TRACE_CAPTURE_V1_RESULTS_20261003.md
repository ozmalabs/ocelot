# `NodesOfType` trace capture v1 results

Date: 2026-10-03

## Outcome

The source-built native extension passed provenance checks. Three fresh workers completed the two-prompt fixture (six requests total); all nine preregistered gates passed. The final semantic graph digest matches the accepted v1.1 capture, the task lifecycle and controls reproduce, and access/work trace drop counters are zero.

Across the six requests, the capture contains 129 aggregated typed-population query rows (984 event count) and 7,731 candidate rows (45,996 event count). Twenty-one request-scoped query rows have no corresponding candidate rows, representing 306 query events. These include five distinct RuleUID/type groups: four whose exported rule definitions contain `NodesOfType` syntax and one without it. The latter is direct evidence that event kinds 34/35 are shared with other typed-population helper paths. The syntax join is correlational: a rule containing a `NodesOfType` term does not prove a particular event came from that term evaluation.

The code change in `TermNode::NodesOfType` now emits the population-query marker even for an empty result and one candidate marker per returned node. Candidate rows cross-check against matching type-read rows in all observed cases. The capture therefore establishes that typed-population events are live, empty-result groups are visible, and candidate cardinality is retained on this fixture. It does not yet isolate the edited evaluator path from helper emitters, prove complete dependencies, estimate instrumentation overhead against a matched off condition, or establish frame locality.

## Reproduction artifacts

- Protocol: [capture preregistration](SUBSTRATE_NODES_OF_TYPE_TRACE_CAPTURE_V1_PREREG_20261003.md)
- Runner: [capture runner](../../../scripts/substrate_nodes_of_type_trace_capture_v1.py)
- Source lock: [capture lock](../../../evaluation/substrate_capability/nodes_of_type_trace_capture_v1_lock_20261003.json)
- Compressed worker output: [raw archive](../../../evaluation/reports/nodes_of_type_trace_capture_v1_workers_raw_20261003.json.gz)
- Capture summary: [machine-readable summary](../../../evaluation/reports/nodes_of_type_trace_capture_v1_20261003.json)
- Independent archive and rule-syntax join: [analysis](../../../evaluation/reports/nodes_of_type_trace_capture_v1_analysis_20261003.json), [analyzer](../../../scripts/analyze_nodes_of_type_trace_capture_v1.py)
- Current source inventory: [Term inventory v1.2](../../../evaluation/reports/term_access_dependency_coverage_v1_2_20261003.json), [trace coverage inventory v1.3](../../../evaluation/reports/substrate_runtime_access_trace_coverage_v1_3_20261003.json)

## Next gate

Use distinct source-site event kinds (or an equivalent emitter identity) to separate direct `NodesOfType` evaluation from helper scans, then run a matched instrumentation-off/on replay to estimate trace overhead. In parallel, instrument rejected matcher candidates and derive task-specific active scopes. Only then evaluate candidate partitions against monolithic closure with cross-boundary mutation controls and full discovery/interface/scheduler costs.
