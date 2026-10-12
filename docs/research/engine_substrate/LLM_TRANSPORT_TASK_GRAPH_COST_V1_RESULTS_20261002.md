# LLM transport task-graph cost v1 results

The source-locked three-worker panel passes all gates for 60 cells: ten held-out L12→L13 inputs crossed with learned/shuffled transport in each worker. The 16-variable graphs are connected at certified width 8, factors extract exactly, paired topology signatures match, direct rescoring agrees with both exact solver passes, held-out scores reproduce, and the primary graph is not mutated. The second junction-tree call runs only under `tracemalloc` for allocation sampling; it is untimed. The independent analyzer passes all checks.

Median per-cell timings on this host are 2.35 ms graph construction, 0.579 ms factor extraction, 0.431 ms min-fill ordering, 539.6 ms uninstrumented exact JT, and 76.7 ms BP. Substrate initialization is 0.052 ms. The separate traced inference pass records 12.61 MB median Python peak allocation; median process peak RSS is 85.9 MiB. Learned exact/BP agreement is 0.800, and shuffled exact/BP agreement is 0.413, matching the prior exact-inference census. On the same workload family, the prior JT median with tracing active was 3.45 s, about 6.4× this uninstrumented median; this is an indicative same-host instrumentation comparison, not a calibrated universal factor.

This gives an isolated exact-inference cost estimate for one small width-8 model-derived graph family. Exact MAP remains about 7× slower than BP in these medians and does not improve held-out sign agreement over BP or the linear baseline. The result does not establish a general CPU cost law, task-level language utility, natural low-width prevalence, or scale to larger graphs.

## Artifacts

- [Preregistration](LLM_TRANSPORT_TASK_GRAPH_COST_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_transport_task_graph_cost_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_transport_task_graph_cost_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_transport_task_graph_cost_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/llm_transport_task_graph_cost_v1_20261002.json)
- [Analysis](../../../evaluation/reports/llm_transport_task_graph_cost_v1_analysis_20261002.json)
