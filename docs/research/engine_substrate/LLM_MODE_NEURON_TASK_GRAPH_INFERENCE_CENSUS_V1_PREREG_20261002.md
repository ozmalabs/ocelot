# LLM mode-neuron task-graph inference census v1 preregistration (2026-10-02)

## Question

Can the current exact 3-state CAN solver infer over the connected mode-neuron factor graph built from a real trained-model representation and each available held-out input, with MAP energies independently verified?

## Sampling frame and design

Use all held-out rows (n=10) in `/applications/data/model_graph_work/mode_export_L12b.npz`; do not truncate or select by outcome, graph width, or timing. This is the existing Qwen3-0.6B layer-12 mode export used by the native-graph aperture studies. The export contains learned modes, an input-to-mode map, a 24-neuron ordering, and ten held-out input vectors. For each held-out row, compute mode coefficients with `llm_native_graph.coarse_mode_state`, select the same eight top-loading neurons and four dominant modes used in the existing block-322 measurement, and call `build_mode_neuron_factor_graph` with raw incidence, zero mode self-field, and the supported 3-state vocabulary. Extract every factor from the live graph with `can_network_from_mt`.

Run three fresh processes; each rebuilds all ten held-out graphs. Measure topology/connectivity, nodes/edges, min-fill ordering and its valid elimination-width certificate, certified-order JT, independent factor-table variable elimination in natural extraction order, direct returned-state energy, held-out dominant-mode sign agreement, and Python traced peak. Require exact equality of unary/pair factors with independently constructed inputs, all ten graphs connected, valid states, JT/oracle/direct-energy agreement within 1e-8, no model mutation, same canonical topology across queries/repeats, complete all-row coverage, and source/native/export hashes stable before/after.

## Claim boundary

This is a census of ten held-out inputs for one model export, layer, and fixed 8-neuron/4-mode graph construction. The learned weights and held-out vectors are real export data, but the incidence architecture is explicitly authored. It measures exact inference integration and one held-out mode-sign agreement outcome; it does not establish broad language capability, natural frame prevalence, learned cut discovery, other layers/models, or scaling beyond this small connected graph.

## Artifacts

- Runner: [llm_mode_neuron_task_graph_inference_census_v1.py](../../../evaluation/substrate_capability/llm_mode_neuron_task_graph_inference_census_v1.py)
- Analyzer: [analyze_llm_mode_neuron_task_graph_inference_census_v1.py](../../../evaluation/substrate_capability/analyze_llm_mode_neuron_task_graph_inference_census_v1.py)
- Lock: [llm_mode_neuron_task_graph_inference_census_v1_lock_20261002.json](../../../evaluation/substrate_capability/llm_mode_neuron_task_graph_inference_census_v1_lock_20261002.json)
- Capture: [llm_mode_neuron_task_graph_inference_census_v1_20261002.json](../../../evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_20261002.json)
- Analysis: [llm_mode_neuron_task_graph_inference_census_v1_20261002_analysis.json](../../../evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_20261002_analysis.json)
