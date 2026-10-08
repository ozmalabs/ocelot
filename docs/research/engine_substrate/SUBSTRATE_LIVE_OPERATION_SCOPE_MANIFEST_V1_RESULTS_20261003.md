# Live operation-scope manifest v1 results

Date: 2026-10-03

## Result

The current-source, request-time capture supports a syntactic read/write manifest for the 401 distinct runtime-touched rule definitions and all 67 Term variants present in those definitions. The analyzer conserves 1,650,456 weighted access events and classifies all observed effect kinds; no effect form remains unrecognized. Ninety-three rule definitions contain population-query Terms, 56 have broad or dynamic reads, and three have broad or unresolved writes. These classes overlap.

The finite declared-resource overlap graph has 1,236 resources, 42,742 rule-pair incidences and seven components. Its largest component contains 381 of 401 rules. Adding conservative edges for broad or dynamic accesses makes a single component containing all 401 rules. Frequently shared keys include `attr:status`, `attr:kind`, and `edge:holds_interpretation`.

This is evidence that the exported seed-wide rule set is not decomposed into small independent scopes by literal resource keys alone. It does not show that the active rules for an individual task lack useful frames: the graph joins every rule touched by the two captured prompts, syntactically includes Terms that may not execute, and treats potentially global population queries conservatively. It is neither an inference factor graph nor a measured treewidth. Current traces also miss `NodesOfType` population scans and empty scans, rejected matcher candidates, selected callback/adapter work, and unchanged conditional-write reads.

## Reproduction artifacts

- Protocol: [frame-locality measurement contract](SUBSTRATE_FRAME_LOCALITY_MEASUREMENT_CONTRACT_V1_20260928.md)
- Analyzer: [analyze_live_operation_scope_manifest_v1.py](../../../scripts/analyze_live_operation_scope_manifest_v1.py)
- Lock: [source lock](../../../evaluation/substrate_capability/live_operation_scope_manifest_v1_lock_20261003.json)
- Machine-readable output: [manifest analysis](../../../evaluation/reports/live_operation_scope_manifest_v1_20261003.json)
- Inputs include the retained request-time rule exports, trace-scope join, Term inventory, and their source hashes, listed in the lock.

## Next measurement

Derive a task-specific operational slice from rule activations and candidate-level access/scan instrumentation. Then compare ownership-free candidate partitions with monolithic closure under shared-state and cross-partition mutation controls. Record exact semantic parity, partition discovery and maintenance, interface traffic, scheduler overhead, and total runtime. Do not infer cheap-cut prevalence from this two-prompt capture.

## Retrospective prompt-induced slices

A follow-up analyzer induced per-prompt graphs from the manifest's cross-worker prompt labels. The “describe who you are” slice contains 397 of 401 observed rules; its finite-resource graph has a 377-rule largest component (95.0%), and its conservative broad-scope graph connects all 397. The “report your organisation” slice contains all 401 rules; its largest finite component is 381 (95.0%), and its broad-scope graph connects all 401. This confirms that these two prompt-tagged rule sets remain nearly as connected as the pooled graph. Membership is the union of access-emitting rules across three workers, so it is not a request-time activation trace or a representative task sample.

Reproduce with [analyze_live_task_rule_slices_v1.py](../../../scripts/analyze_live_task_rule_slices_v1.py); the hash-linked output is [live_task_rule_slices_v1_20261003.json](../../../evaluation/reports/live_task_rule_slices_v1_20261003.json).

## Instrumentation follow-up

After the retrospective slice analysis, `TermNode::NodesOfType` was updated to emit the existing typed-population query event once per invocation (including empty results) and the typed-population candidate event once per returned node. This fills the specific query-marker gap in that evaluator path and exposes candidate cardinality on cache-independent evaluation. The earlier source inventory and captures predate this edit, so they do not measure its coverage or overhead. Required next step: rebuild the source inventory and run a new locked capture before using these event kinds in tractability claims.

The post-edit source inventory confirms all 237 Term variants remain mapped and the trace vocabulary still contains 34 event kinds, including `term_typed_population_query` and `term_typed_population_candidate`. These are source-level checks only; the inventory does not establish that the rebuilt runtime emits them. See the refreshed [Term inventory v1.2](../../../evaluation/reports/term_access_dependency_coverage_v1_2_20261003.json) and [trace coverage inventory v1.3](../../../evaluation/reports/substrate_runtime_access_trace_coverage_v1_3_20261003.json).
