# LLM transport treewidth scaling v1 results

The source-locked three-worker panel passes all gates for 180 cases: ten held-out L12→L13 transitions crossed with six mode counts. Each graph is connected; factors match the live graph construction; min-fill's reported width matches the width of its triangulation; exact JT energy equals the independent bipartite exhaustive oracle and direct rescore with zero measured error; and no graph changes during inference. Each worker reproduces the full grid, and hashes remain stable.

| Modes per side | Variables | Certified width | Median exact JT | Median BP | Exact/BP median ratio | Mean exact target-sign agreement |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 1 | 0.034 ms | 0.76 ms | 0.05× | 0.900 |
| 2 | 4 | 2 | 0.105 ms | 2.81 ms | 0.04× | 0.650 |
| 4 | 8 | 4 | 1.82 ms | 13.23 ms | 0.14× | 0.825 |
| 6 | 12 | 6 | 35.7 ms | 36.6 ms | 0.98× | 0.867 |
| 8 | 16 | 8 | 539 ms | 76.8 ms | 7.02× | 0.800 |
| 10 | 20 | 10 | 7.13 s | 158 ms | 45.0× | 0.860 |

At widths 1 through 8, JT and BP returned identical target-state vectors in all 30 cells at each width; at width 10 they were identical in 27/30. Exact inference grows sharply once the dense bipartite graph reaches width 8: increasing width by two multiplies median JT time by about 15× from 6→8 and 13× from 8→10. These are measured points, not an asymptotic theorem. The independent oracle enumerated 3^k source assignments (up to 59,049 at k=10) and minimized each target conditionally; the registered graph's target side has no internal edges, making that factorization exact.

This is a controlled scaling curve for one model, one layer transition, one dense bipartite incidence construction, and ten held-out coefficient pairs. The graph structure and selected mode counts are set by the experiment; this is not evidence that the substrate discovers low-width frames in natural task graphs. Target-sign agreement is an internal model-derived metric rather than language-task utility. Next extend the same preregistered width panel to independently selected layer transitions and a separate model/task family, then sample task-derived graph topology without fixing complete bipartite incidence.

## Artifacts

- [Preregistration](LLM_TRANSPORT_TREEWIDTH_SCALE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_transport_treewidth_scale_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_transport_treewidth_scale_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_transport_treewidth_scale_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/llm_transport_treewidth_scale_v1_20261002.json)
- [Analysis](../../../evaluation/reports/llm_transport_treewidth_scale_v1_analysis_20261002.json)
