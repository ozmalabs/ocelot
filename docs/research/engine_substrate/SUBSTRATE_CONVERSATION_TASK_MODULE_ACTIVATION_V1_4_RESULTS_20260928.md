# Conversation task module activation v1.4 results

**Run:** 2026-09-28; current-source replay of five authored conversation conditions, two fresh profiled workers each.  
**Protocol:** [v1.4 preregistration](SUBSTRATE_CONVERSATION_TASK_MODULE_ACTIVATION_V1_4_PREREG_20260928.md).  
**Evidence:** [raw capture](../../../evaluation/reports/conversation_task_module_activation_v1_4_20260928.json), [independent analysis](../../../evaluation/reports/conversation_task_module_activation_v1_4_analysis_20260928.json), [source/input lock](../../../evaluation/substrate_capability/conversation_task_module_activation_v1_4_lock_20260928.json), [runner](../../../scripts/substrate_conversation_task_module_activation_v1_4.py), [analyzer](../../../scripts/analyze_substrate_conversation_task_module_activation_v1_4.py).

## Result

All 12 integrity/source/cache gates pass. Ten unique workers completed without errors, with two workers per condition. The wrapper-aware profiler recorded exactly one conversation extent and a nonempty domain trace in each worker. The independent task oracle passes 8/10: scene description, held self-knowledge, self-report action, and unknown-word clarification pass 2/2 each; concern authoring fails 0/2. Module, function, and call-edge key sets match exactly across paired workers within every condition.

| Condition | Oracle | Modules | Functions | Python domain calls | Instrumented task wall time |
|---|---:|---:|---:|---:|---:|
| Scene description | 2/2 | 32 | 367 | 24,472 | 10.51–10.58 s |
| Held self-knowledge answer | 2/2 | 32 | 281 | 68,348 | 467–487 ms |
| Self-report action | 2/2 | 29 | 292 | 83,088 | 512–530 ms |
| Unknown-word clarification | 2/2 | 25 | 243 | 3,240 | 240–271 ms |
| Concern authoring | 0/2 | 28 | 262 | 19,769 | 314–325 ms |

The source lock records the current `substrate/world_adapter.py` implementation, including its serialized public-method wrapper. The lock remained stable across all workers. The profiler correctly recognized that wrapper as the `converse` extent. The task-level times include instrumentation and remain descriptive.

## Interpretation and limits

This is a complete, current-source replay for five authored conversation contracts. It confirms those task outcomes and repeatable Python activation footprints on the locked snapshot. It does not measure Rust/native work, causal necessity, natural task prevalence, profiler overhead, or capability outside these routes. Concern-task failure is localized only to a pre-action clarification route; faculty capability remains untested. Scene description remains a roughly 10.5-second profiled outlier requiring overhead-calibrated decomposition.

### Captured failure path: concern task

Reinspection of the two stored worker records localizes the observed failure to the route before concern authoring. Both workers return `I don't know 'two' — what does it mean?`; the inbound message is classified as an instruction with `typed_unresolved_action_dependency`, has zero goals, and takes `ask_back`. Neither worker records an action result, concern object, or teacher call. Thus the 0/2 score is an end-to-end prompt failure caused at or before interpretation/grounding for this captured wording. It is not evidence that the concern-authoring faculty was invoked and failed, nor does it establish that the token `two` alone caused the interpretation: the panel has no matched wording ablation. A follow-up should compare semantically equivalent, independently scored prompt variants that vary only the numeral/relational phrasing, then separately probe the concern route with a representation the interpreter successfully grounds.

The WordNet database was prewarmed, hash-locked, and not rebuilt by any worker; cold index construction is excluded. Two workers per condition establish within-panel footprint repeatability, not population variance. Do not pool these instrumented times with older source snapshots.

## Next gate

Use this stable current-source conversation replay as the baseline, then extend module activation and task scoring to independently specified non-conversation families: structured perception, relational reasoning, learning/induction, and planning/action selection. Add independent positive and negative-control oracles, source/runtime locks, and native-work counters alongside Python traces. Keep outcomes separate by family, calibrate observer overhead, and keep cold startup separate from warmed task cost.
