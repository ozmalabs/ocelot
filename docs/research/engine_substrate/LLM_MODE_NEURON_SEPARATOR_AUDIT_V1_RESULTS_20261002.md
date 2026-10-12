# LLM mode-neuron separator audit v1 results

The exhaustive audit passed all eight gates. All 30 rows in the prior capture share one connected complete bipartite K₄,₈ topology. Of all 4,096 variable subsets, the unique minimum vertex separator is the four mode variables; removing them leaves eight isolated neuron variables. Thus this graph has a genuine four-variable separator, but it is one third of the variables and was made visible by the authored mode/neuron roles.

For three-state variables, the preregistered table-assignment proxy is 2,064 for width-optimal monolithic elimination and 1,944 when conditioning on the four modes and solving the eight neurons independently, a 1.06× ratio. The separator therefore gives only a small reduction in this proxy; it does not make the already width-4 graph dramatically cheaper. The calculation excludes factor-combination work, separator search, storage, scheduling, and runtime, so no speedup is claimed. Parallel execution of the eight conditioned neuron subproblems remains a possible benefit, but was not measured.

This is one real model export/layer and a fixed, authored incidence structure repeated across ten inputs and three workers. It establishes neither natural-task separator prevalence nor autonomous cut discovery. A stronger next gate needs varied independently sourced task graphs and must compare the cost of proposing partitions, exact inference with semantic parity, and end-to-end runtime/memory against monolithic execution.

## Reproducibility artifacts

- [Protocol](LLM_MODE_NEURON_SEPARATOR_AUDIT_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_mode_neuron_separator_audit_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_mode_neuron_separator_audit_v1_lock_20261002.json)
- [Machine-readable result](../../../evaluation/reports/llm_mode_neuron_separator_audit_v1_20261002.json)
- [Input census result](LLM_MODE_NEURON_TASK_GRAPH_INFERENCE_CENSUS_V1_RESULTS_20261002.md)
