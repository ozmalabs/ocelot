# LLM transport task-graph exact-inference census v1.1 results

All three fresh source-locked workers processed ten held-out L12→L13 transitions under learned and shuffled transport conditions; all runner gates and the registered analyzer passed. The 60 condition cells had connected 16-variable graphs with 64 pair factors and certified width 8. Exact 3-state junction-tree energies matched natural-order factor-table variable elimination and direct rescoring with zero maximum energy difference. Factors matched the expected live graph, no graph mutated, and all source/native/export hashes remained stable. A separate post-capture audit recomputed all six reported agreement means directly from saved predictions and targets and passed.

Across the 30 learned-transport cells, exact MAP and substrate BP each reached mean held-out target-sign agreement 0.800; the linear transport baseline reached 0.863. On the 30 shuffled-transport cells, exact MAP reached 0.413, BP 0.413, and the linear baseline 0.375. Thus the learned transition carries held-out signal well above the shuffle control, while exact inference does not improve on BP's measured predictions here and remains below the direct linear baseline. Median exact JT time was 3.45 s per condition, versus 78 ms for BP and 791 ms for the independent oracle. JT timing was measured with `tracemalloc` active to capture Python peak allocations, so it is instrumented timing rather than an uninstrumented deployment estimate; traced peak median was 12.6 MB and process peak RSS was about 86 MiB. The recorded graph-construction interval includes an initial factor extraction performed inside the graph helper; the separate extraction interval measures a repeated extraction. Do not interpret those two fields as isolated construction and extraction costs.

The first v1 attempt is retained as a diagnostic: all three workers stopped before producing results because its state-snapshot code passed integer IDs where the native API required `NodeID` handles. V1.1 fixed that adapter defect and is the valid result. This census covers one Qwen3-0.6B L12→L13 learned transport, eight selected modes at each layer, and ten held-out transitions. It is not a language task benchmark, a learned separator result, or evidence of natural task prevalence or transfer across models/layers.

## Artifacts

- [V1.1 preregistration](LLM_TRANSPORT_TASK_GRAPH_EXACT_CENSUS_V1_1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1_1.py)
- [Registered analyzer](../../../evaluation/substrate_capability/analyze_llm_transport_task_graph_exact_census_v1_1.py)
- [Post-capture arithmetic audit](../../../evaluation/substrate_capability/audit_llm_transport_task_graph_exact_census_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1_1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/llm_transport_task_graph_exact_census_v1_1_20261002.json)
- [Registered analysis](../../../evaluation/reports/llm_transport_task_graph_exact_census_v1_1_analysis_20261002.json)
- [Post-capture audit output](../../../evaluation/reports/llm_transport_task_graph_exact_census_v1_1_posthoc_audit_20261002.json)
- [Separated uninstrumented timing follow-up](LLM_TRANSPORT_TASK_GRAPH_COST_V1_RESULTS_20261002.md)
- [V1 failed diagnostic capture](../../../evaluation/reports/llm_transport_task_graph_exact_census_v1_20261002.json)
- [V1 failed diagnostic lock](../../../evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1_lock_20261002.json)
