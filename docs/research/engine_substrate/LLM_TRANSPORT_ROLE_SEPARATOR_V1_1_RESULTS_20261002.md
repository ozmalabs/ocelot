# LLM transport role-separator inference v1.1 results

Three fresh workers completed all 60 cells (ten held-out transitions × learned/shuffled transport). The capture and independent analysis passed all gates. In every cell, the role-conditioned solver returned a valid state with energy matching monolithic junction-tree MAP and direct rescoring within 1e-8; its eight target-mode signs exactly matched the JT signs. Learned-transport held-out sign accuracy was 0.800 for both solvers; shuffled accuracy was 0.413 for both.

Median monolithic JT time was 542.39 ms (learned) and 543.45 ms (shuffled). The conditioned solver median was 2.41 ms and 2.39 ms, respectively, yielding paired median JT/conditioned ratios of 222× and 226×. The conditioned solver enumerates 3⁸ target assignments and optimizes each of eight source variables over three states; its median traced Python peak was 3.47 MiB and process peak RSS was 67.23 MiB.

This is a large measured speed difference for an exact decomposition of one connected K₈,₈ model-derived factor graph family. The model builder supplies the source/target partition, and the conditioned implementation uses a vectorized NumPy calculation while the baseline is the Python junction-tree implementation. The result therefore demonstrates that exact structure-aware inference can be implemented much faster on this fixed workload; it does not isolate the contribution of partition structure from implementation/vectorization, and it is not a speedup attributable to the substrate runtime itself. Partition discovery, cross-family transfer, natural-task prevalence, language-task utility, and larger-graph scaling remain unmeasured.

## Reproducibility artifacts

- [Base protocol](LLM_TRANSPORT_ROLE_SEPARATOR_V1_PREREG_20261002.md) and [v1.1 amendment](LLM_TRANSPORT_ROLE_SEPARATOR_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_transport_role_separator_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_transport_role_separator_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_transport_role_separator_v1_1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/llm_transport_role_separator_v1_1_20261002.json)
- [Analysis](../../../evaluation/reports/llm_transport_role_separator_v1_1_analysis_20261002.json)
- [Input transport census](LLM_TRANSPORT_TASK_GRAPH_EXACT_CENSUS_V1_1_RESULTS_20261002.md)
- [Uninstrumented monolithic timing baseline](LLM_TRANSPORT_TASK_GRAPH_COST_V1_RESULTS_20261002.md)
