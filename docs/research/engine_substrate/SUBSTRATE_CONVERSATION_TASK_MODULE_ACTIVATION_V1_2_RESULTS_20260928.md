# Conversation task module activation v1.2 results

**Run:** 2026-09-28; current-source replay of five authored conversation conditions, two fresh profiled workers each.  
**Protocol:** [v1.2 preregistration](SUBSTRATE_CONVERSATION_TASK_MODULE_ACTIVATION_V1_2_PREREG_20260928.md).  
**Evidence:** [raw capture](../../../evaluation/reports/conversation_task_module_activation_v1_2_20260928.json), [independent analysis](../../../evaluation/reports/conversation_task_module_activation_v1_2_analysis_20260928.json), [source/input lock](../../../evaluation/substrate_capability/conversation_task_module_activation_v1_2_lock_20260928.json), [runner](../../../scripts/substrate_conversation_task_module_activation_v1_2.py), [analyzer](../../../scripts/analyze_substrate_conversation_task_module_activation_v1_2.py).

## Result

All 12 preregistered integrity/source/cache checks pass. Ten distinct workers completed with no execution errors. The task oracle again passes 8/10: scene description, held self-knowledge, self-report action, and unknown-word clarification pass 2/2 each; concern authoring fails 0/2. Module, function, and call-edge key sets are exactly equal across each condition's paired replicates.

| Condition | Oracle | Modules | Functions | Python domain calls | Instrumented task wall time |
|---|---:|---:|---:|---:|---:|
| Scene description | 2/2 | 32 | 367 | 24,472 | 10.68–11.19 s |
| Held self-knowledge answer | 2/2 | 32 | 281 | 68,346–68,348 | 468–488 ms |
| Self-report action | 2/2 | 29 | 292 | 83,088 | 502–544 ms |
| Unknown-word clarification | 2/2 | 25 | 243 | 3,240 | 248–249 ms |
| Concern authoring | 0/2 | 28 | 262 | 19,769 | 313–324 ms |

The previously drifted path, `domains/comprehend_text.py`, is included in the v1.2 source lock. Relative to v1.1, the module/function footprints and task-oracle outcomes are unchanged; Python call totals rise by 18 on four conditions and are unchanged on unknown-word clarification. This is a new source snapshot, so the difference is descriptive and is not attributed solely to that path.

## Source-link update

The reviewed adjudication assigned the 37 previously unlinked, activated modules to three new capability rows and existing synthesis, vision, and tool-I/O rows. The refreshed source census links 69/833 Python files (8.3%), up from the historical v1.1 map's 32/833. Static reachability remains 247/833 and profile-declared reachability 248/833; those values did not increase with map edits. A post-census join passes all six checks and confirms all 40 distinct Python domain modules called by v1.2 now have direct map links. This is a coverage and navigation improvement, not a substrate capability gain ([source census results](SUBSTRATE_PYTHON_SOURCE_COVERAGE_AUDIT_V1_2_RESULTS_20260928.md), [per-file census](../../../evaluation/substrate_capability/python_source_coverage_audit_v1_2_20260928.json), [activation/source crosswalk](../../../evaluation/reports/conversation_task_module_source_crosswalk_v1_2_20260928.json)).

## Interpretation and limits

This current-source replay confirms the selected task contracts and Python activation footprints on this snapshot. It does not measure native Rust work, causal necessity, natural task prevalence, profiler overhead, or capability outside these authored routes. The repeated concern-authoring failure remains a task-contract gap without causal localization. Scene description remains a roughly 11-second instrumented outlier and needs overhead-calibrated decomposition before cost conclusions.

The WordNet index remains intentionally warmed; cold construction is outside scope. Two replicates establish footprint repeatability here, not population variance. The v1.1 run remains preserved as the prior-source result; its omitted cache lock is closed in both v1.1 amendment and v1.2's repeated source/cache gates.

## Next gate

Extend the task/module activation protocol to independently specified tasks outside conversation: structured perception, relational reasoning, learning/induction, and planning/action selection. For each, use task and negative-control oracles, lock external/runtime inputs, and add native-work counters alongside Python traces. Keep family scores separate, calibrate observer overhead, and measure cold startup independently from warmed task execution.

## Later adapter-source change

After this run, `substrate/world_adapter.py` changed. The v1.3 follow-up detected that drift during capture and was censored; see the [censored result](SUBSTRATE_CONVERSATION_TASK_MODULE_ACTIVATION_V1_3_CENSORED_RESULTS_20260928.md). V1.2 remains valid for the exact locked snapshot and its 40 Python domain-module hashes remain current in the later static census, but it should not be presented as a result for the latest conversation-adapter implementation.
