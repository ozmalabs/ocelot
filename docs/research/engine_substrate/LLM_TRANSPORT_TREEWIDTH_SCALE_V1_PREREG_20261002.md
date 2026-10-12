# LLM transport treewidth scaling v1 preregistration

## Question and workload

How do exact-inference cost and held-out mode-sign agreement change as the real-export L12→L13 transport graph grows in selected modes? Use the frozen `transport_L12_13.npz` export, fit transport at ridge 1.0 from all 60 training coefficient pairs, then evaluate every one of the ten held-out transitions for mode counts k={1,2,4,6,8,10}. For each k, choose the k largest-magnitude L12 source coefficients and first k L13 targets; build a fresh 3-state graph with source unary fields, zero target fields, and bidirectional learned transport edges. Run three fresh processes over the complete 60-cell grid.

## Exactness and measurements

Measure substrate initialization, graph construction, live factor extraction, min-fill order, exact junction-tree MAP, and BP in separate uninstrumented intervals. Build a second exact oracle by enumerating all 3^k assignments to the source side and, conditioned on each assignment, independently minimizing each target variable. This computes the global minimum exactly because the registered graph has no target-target or source-source factors. Compare exact and oracle energies, direct-rescore the returned state, verify every extracted factor against the learned T and held-out source coefficients, certify elimination width from the generated triangulation, and record per-cell held-out target-sign agreement. Require stable source/export hashes, full input coverage, no graph mutation, and valid connectedness/topology records. Timing is per one-host workload, not a universal law.

## Claim boundary

This is a width-scaling experiment for one learned Qwen3-0.6B L12→L13 transition and ten held-out coefficient pairs. Its dense bipartite incidence is fixed by the factor-graph construction; it measures the engine's cost on that graph family, not naturally discovered separators or general language capability. The k=10 maximum is a bounded extension, not asymptotic proof.

## Artifacts

- Runner: [llm_transport_treewidth_scale_v1.py](../../../evaluation/substrate_capability/llm_transport_treewidth_scale_v1.py)
- Analyzer: [analyze_llm_transport_treewidth_scale_v1.py](../../../evaluation/substrate_capability/analyze_llm_transport_treewidth_scale_v1.py)
- Lock: [llm_transport_treewidth_scale_v1_lock_20261002.json](../../../evaluation/substrate_capability/llm_transport_treewidth_scale_v1_lock_20261002.json)
- Capture: [llm_transport_treewidth_scale_v1_20261002.json](../../../evaluation/reports/llm_transport_treewidth_scale_v1_20261002.json)
- Analysis: [llm_transport_treewidth_scale_v1_analysis_20261002.json](../../../evaluation/reports/llm_transport_treewidth_scale_v1_analysis_20261002.json)
