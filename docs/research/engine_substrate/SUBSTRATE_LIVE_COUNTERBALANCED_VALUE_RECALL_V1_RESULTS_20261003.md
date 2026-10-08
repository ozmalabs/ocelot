# Live counterbalanced value recall v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_LIVE_COUNTERBALANCED_VALUE_RECALL_V1_PREREG_20261003.md)  
Amendment: [v1.1](SUBSTRATE_LIVE_COUNTERBALANCED_VALUE_RECALL_V1_1_AMENDMENT_20261003.md)

## Result

Nine fresh workers completed (three each for prior value 14, prior value 29, and fresh control); source and worker integrity checks pass. **All 15 conversation turns across the nine workers returned `ERROR: no communicative response could be generated.`** Both counterbalanced recall arms score 0/3 on exact value selection. The fresh arm also scores 0/3 under the corrected oracle because a runtime error is not an honest abstention. V1's numeral-only control rule incorrectly gave 3/3; v1.1 corrects that mistake and preserves the original result.

| Condition | Oracle passes | Owned Goals | Direct cross-frame edges | Interaction width | Median graph nodes / edges | Median peak RSS |
|---|---:|---:|---:|---:|---:|---:|
| Prior value 14 | 0/3 | 1 | 2 | 1 | 25,068 / 11,551 | 1,721.2 MiB |
| Prior value 29 | 0/3 | 1 | 2 | 1 | 25,068 / 11,551 | 1,721.0 MiB |
| Fresh question | 0/3 | 1 | 0 | 0 | 25,040 / 11,471 | 1,721.3 MiB |

In both two-turn conditions, the sole owned Goal is `answer_topic` linked to the question Message. The earlier value-bearing Message has no owned task Goal under the strict `comprehends` relation. A post-capture interpretation audit refines the parse result: all three `14` statements have parsed subject `secret`, predicate `code`, object `14.`, but `relation_support=missing` and `grounding_status=unresolved`; all three `29` statements retain subject/predicate but have `parsed_object=null`, also with missing relation support and unresolved grounding. The identical question is parsed as `table:know` with `gap_count=0`, but never creates a `MemoryRetrievalRequest`. No communicative response is generated. Two explicit edges (`responds_to`, `follows_event`) connect the question frame to the earlier Message frame, so conversation sequence structure survives; it does not result in value recovery. The answer is invariant to the swapped values and identical to the fresh-turn failure. This is a structured output failure in the conversation path, not a Python worker exception.

The raw exact graph digest gate fails in all three conditions. Pairwise inspection finds identical graph-array order and directed typed topology; only unordered member order in `Interlocutor.attrs.believed_concepts` varies. The independent v1.1 semantic comparison sorts only that `__fset__`, retaining all raw digests, and passes. The v1 analyzer and v1 behavior-oracle results remain available.

This is a narrow live-route test. It establishes failure for plain user-stated secret-code facts in this route and source state; it does not test explicit memory APIs, external retrieval, or all substrate recall mechanisms. The graph-native [episodic memory seed](../../../seeds/episodic_working_memory_core.json) binds explicit observed `EpisodicEvent` nodes through `experienced_event`, `in_context`, and `instantiates_schema` relations; existing [episodic memory tests](../../../tests/test_episodic_working_memory_migrated.py) exercise that structured interface. Peak RSS includes full-seed runtime and should not be interpreted as memory per fact.

## Next gate

Determine whether the failure is specific to the live natural-language adapter or also present in the graph-native episodic memory API. Build a paired capability test: store a unique fact through the documented memory-write path, retrieve via the documented query path, and separately test whether `WorldAdapter.converse` calls those paths. Keep direct API recall and conversational recall as separate outcomes; require exact values plus a no-fact negative control.

Artifacts: [capture](../../../evaluation/reports/live_counterbalanced_value_recall_v1_20261003.jsonl.gz), [v1 analysis](../../../evaluation/reports/live_counterbalanced_value_recall_v1_analysis_20261003.json), [v1.1 amended analysis](../../../evaluation/reports/live_counterbalanced_value_recall_v1_1_analysis_20261003.json), [cross-capture graph audit](../../../evaluation/reports/live_structured_memory_boundary_v1_audit_20261003.json), [audit script](../../../evaluation/substrate_capability/audit_live_structured_memory_boundary_v1.py), [runner](../../../evaluation/substrate_capability/live_counterbalanced_value_recall_v1.py), [v1.1 analyzer](../../../evaluation/substrate_capability/analyze_live_counterbalanced_value_recall_v1_1.py), and [source lock](../../../evaluation/substrate_capability/live_counterbalanced_value_recall_v1_lock_20261003.json).
