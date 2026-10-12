# Multi-route static dependency reconciliation v1 results

Date: 2026-10-06  
Status: observed-key concordance passed; dependency precision and complete interface remain open.

## Result

The ten access-trace workers all resolve against five separately source-locked post-route rule tables. Every observed UID has the same rule name in both captures. For all five routes and both trace replicates, the existing conservative reconciliation reports **zero static resource-key mismatches**, zero undeclared implicit attribute reads, and zero concrete read/write rule pairs outside the static projection. Weighted trace classification by route is:

| Route | Declared static key match | Declared `reads_any` wildcard | Implicit read declared/covered | Uncheckable event kinds | Concrete dynamic pairs | Static possible pairs among observed rules |
|---|---:|---:|---:|---:|---:|---:|
| Scene description | 1,473,965 | 253,058 | 2,262 | 42,428 | 222 | 77,001 |
| Held self-knowledge answer | 244,642 | 50,084 | 114,506 | 9,012 | 210 | 59,227 |
| Self-report action | 303,694 | 50,460 | 114,602 | 12,441 | 237 | 61,076 |
| Unknown-word clarification | 249,851 | 50,090 | 114,519 | 10,710 | 195 | 60,171 |
| Concern authoring | 269,024 | 51,130 | 114,529 | 9,968 | 213 | 59,227 |

Replicates match exactly on these summaries. The static possible-pair projection is very conservative: it contains roughly 250–350 times as many rule pairs as the concrete pairs witnessed in this finite trace. Thus the result establishes concordance for observed keys and events, not that declared dependencies are complete or precise enough to use as a practical frame interface. About 2–10% of weighted events by route have no static resource key in the current event vocabulary and remain uncheckable here.

## Where the outside-cut work comes from

The dominant observed paths line up with the prior source-level hotspot audit:

- `slang_variant_bind_denotes` performs a `Concept` candidate scan and compares `name` while its `AddNodeIfAbsent` effect seeks an existing concept. Its definition is in [slang_lexicon.json](../../../seeds/slang_lexicon.json:314). In ordinary non-scene routes, the trace records about 107,000 candidate-type reads and the same number of name comparisons per worker. This is a broad vocabulary population dependency, even when only one word is being resolved.
- `curiosity_targets_ambivalent_nodes` reads `state` and `is_ambivalent` across the resident Concept population; its pattern and predicate are in [causal_attitude_networks.json](../../../seeds/causal_attitude_networks.json:721). The trace records about 95,000–158,000 outside-cut attribute reads per worker, depending on route.
- Scene description dynamically adds recognition rules in [`build_describe_faculty`](../../../scripts/arc_self_report.py:37). Those rules test concept names and `Holds` against each request's percepts. Each of the three recognition rules produces about 322,000 outside-cut accesses in the captured scene route, dominated by `term_attr_read(name)`. The low frame width therefore says little about this rule's vocabulary and concept interface.
- `sd_decode`, `sd_infer_dimension`, `sd_transform_decode`, and `gr_condition_lapse` add other recurring or initial population work. Their declarations are source-visible in [shape_decode_loop.json](../../../seeds/shape_decode_loop.json:127) and [goal_residuals.json](../../../seeds/goal_residuals.json:787); the prior [hotspot audit](SUBSTRATE_PREOUTCOME_TASK_FRAME_HOTSPOT_AUDIT_V1_RESULTS_20261005.md) characterizes their observed contributions on the held-topic workload.

These scans may be semantically required under the current rules: the engine must find existing lexicon entries, classify resident Concepts, and compare percepts with held concepts. The evidence does not distinguish required population lookup from avoidable full scans. They are therefore concrete candidates for index/cache experiments with negative and invalidation controls, not demonstrated optimization opportunities.

## Consequence and next gate

The current state indicates a layered dependency structure rather than a request-only separator: ingress syntax frame, task/world boundary, and resident shared vocabulary/model populations. A tractability argument must account for the size and access cost of those shared population interfaces; calling them “outside” does not make them irrelevant or unnecessary.

Next, run an exact-parity candidate-generation experiment on the dominant scans. First measure the current candidate populations and work as relevant population sizes grow; then compare existing behavior with keyed/indexed candidate retrieval for lexicon lookup, and cached/incremental state classification for curiosity and ShapeDecode where mutation invalidation can be made explicit. Preserve outputs, receipts, graph structure, and rule firing semantics; include add/change/delete and duplicate-name or equal-state controls. Do not move to frame-partitioned closure until these shared interfaces are either explicitly represented or proven irrelevant to each task's semantics.

## Artifacts

- [Metadata supplement protocol](SUBSTRATE_MULTIROUTE_STATIC_DEPENDENCY_METADATA_V1_PREREG_20261006.md)
- [Metadata capture runner](../../../scripts/substrate_multiroute_static_dependency_metadata_v1_20261006.py)
- [Reconciliation analyzer](../../../scripts/analyze_substrate_multiroute_static_dependency_metadata_v1_20261006.py)
- [Metadata lock](../../../evaluation/substrate_capability/multiroute_static_dependency_metadata_v1_20261006_lock.json)
- [Static rule metadata](../../../evaluation/reports/multiroute_frame_access_v1_20261006/static_rule_metadata.json)
- [Dependency reconciliation](../../../evaluation/reports/multiroute_frame_access_v1_20261006/dependency_reconciliation.json)
