# LLM transport role-separator inference v1.2 results

Three fresh workers completed all 60 cells (ten held-out transitions × learned/shuffled transport). The capture and independent analysis passed every gate. In every cell, the uninstrumented role-conditioned solver returned a valid state with energy matching monolithic junction-tree MAP and direct rescoring within 1e-8; its target-mode signs matched the JT signs exactly. The separate traced repeat returned the same state and energy. Learned-transport held-out sign accuracy was 0.800 for both solvers; shuffled accuracy was 0.413 for both.

With both solvers timed without allocation tracing, median monolithic JT time was 540.37 ms (learned) and 542.93 ms (shuffled). The conditioned solver median was 2.29 ms and 2.27 ms, respectively. Median paired JT/conditioned ratios were 236× and 241×. The conditioned solver enumerates 3⁸ target assignments and optimizes each of eight source variables over three states. Its separately measured median traced Python peak was 3.47 MiB; median process peak RSS was 67.41 MiB.

This is a large measured runtime difference for an exact decomposition of one connected K₈,₈ model-derived factor-graph family. The builder supplies source/target roles, and the conditioned implementation uses vectorized NumPy, while the baseline is the Python junction-tree implementation. The result therefore establishes that this exact decomposition is highly exploitable in the current implementation; it does not isolate structural decomposition from implementation/vectorization and is not a speedup attributable to the substrate runtime. Partition discovery, cross-family transfer, natural-task prevalence, language-task utility, and larger-graph scaling remain open.

## Reproducibility artifacts

- [Base protocol](LLM_TRANSPORT_ROLE_SEPARATOR_V1_PREREG_20261002.md), [sign-parity amendment](LLM_TRANSPORT_ROLE_SEPARATOR_V1_1_AMENDMENT_20261002.md), and [timing amendment](LLM_TRANSPORT_ROLE_SEPARATOR_V1_2_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_transport_role_separator_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_transport_role_separator_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_transport_role_separator_v1_2_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/llm_transport_role_separator_v1_2_20261002.json)
- [Analysis](../../../evaluation/reports/llm_transport_role_separator_v1_2_analysis_20261002.json)
- [Input transport census](LLM_TRANSPORT_TASK_GRAPH_EXACT_CENSUS_V1_1_RESULTS_20261002.md)
- [Monolithic timing baseline](LLM_TRANSPORT_TASK_GRAPH_COST_V1_RESULTS_20261002.md)
