# LLM transport task-graph cost v1 preregistration

## Question

What are the separately measured costs of constructing, extracting, ordering, and solving the learned L12→L13 transport graph when JT is timed without Python allocation tracing? The preceding exact-inference census passes correctness gates but times JT with `tracemalloc` active and combines graph construction with an initial extraction inside its construction interval.

## Fixed workload

Use `/applications/data/model_graph_work/transport_L12_13.npz`, fit the 32×32 transport at ridge 1.0 on all 60 training coefficient pairs, and process all ten held-out transitions. For each input, evaluate both learned transport and the deterministic flattened-value shuffle from seed 0. Each condition builds a fresh 3-state graph with eight largest-absolute L12 source coefficients, the first eight L13 targets, source unary fields, zero target unary fields, and bidirectional transport edges. Run three fresh workers over all 60 condition cells.

## Measurements

Record disjoint intervals: `Substrate()` allocation; `build_transport_factor_graph` including seed load but excluding network extraction; one `can_network_from_mt` extraction; min-fill order; exact JT without `tracemalloc`; substrate BP; and a separate second JT pass with `tracemalloc` used only to sample peak Python allocation. Verify expected topology/factor sizes, width certificates, exact state energy by direct rescore, prediction vectors, no graph mutation, source/export stability, and per-cell target agreement. Do not interpret one-host timing as a universal scaling law.

## Claim boundary

This is a timing and allocation profile of one model-derived 16-variable width-8 transport graph family, across ten held-out transitions and one value-shuffle control. It does not establish general speedup, language-task utility, natural graph prevalence, or scale beyond this topology. Results must report the large allocation tracing timing delta separately from the uninstrumented JT estimate.

## Artifacts

- Runner: [llm_transport_task_graph_cost_v1.py](../../../evaluation/substrate_capability/llm_transport_task_graph_cost_v1.py)
- Analyzer: [analyze_llm_transport_task_graph_cost_v1.py](../../../evaluation/substrate_capability/analyze_llm_transport_task_graph_cost_v1.py)
- Lock: [llm_transport_task_graph_cost_v1_lock_20261002.json](../../../evaluation/substrate_capability/llm_transport_task_graph_cost_v1_lock_20261002.json)
- Capture: [llm_transport_task_graph_cost_v1_20261002.json](../../../evaluation/reports/llm_transport_task_graph_cost_v1_20261002.json)
- Analysis: [llm_transport_task_graph_cost_v1_analysis_20261002.json](../../../evaluation/reports/llm_transport_task_graph_cost_v1_analysis_20261002.json)
