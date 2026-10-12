# LLM mode-neuron task-graph inference census v1 results

The source-locked three-process census passed all runner checks and the independent analyzer. Each fresh worker rebuilt all ten held-out inputs from the Qwen3-0.6B layer-12 mode export. Thus 30/30 input graphs had exact live-graph factor extraction, a connected 12-variable/32-edge mode-neuron topology, and matching min-fill and triangulation width certificates of 4. The exact 3-state junction-tree MAP energy matched both natural-order factor-table variable elimination and direct returned-state rescoring in all 30 rows; maximum absolute energy difference was zero. Graph state and factors were unchanged by inference, source/native/export hashes remained stable, and the canonical topology was identical across all held-out rows and workers.

Mean dominant-mode sign agreement was 0.75 over the four selected modes per input. Median graph construction was 2.15 ms and median junction-tree MAP was 30.17 ms in the measured Python process. These are per-run observations on one host, not stable cross-host latency estimates. The result establishes real-export exact-inference integration for a small fixed connected graph; it does not establish language-task performance, learned graph construction or cut discovery, prevalence of low-width natural graphs, other models/layers, or scaling beyond 12 variables.

## Artifacts

- [Preregistration](LLM_MODE_NEURON_TASK_GRAPH_INFERENCE_CENSUS_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_mode_neuron_task_graph_inference_census_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_mode_neuron_task_graph_inference_census_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_mode_neuron_task_graph_inference_census_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_20261002.json)
- [Analysis](../../../evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_analysis_20261002.json)
