# Task-graph separator discovery audit v1 results

The three-worker, source-locked graph-only search passes all gates and the independent analyzer reproduces the exact candidate sets. On K₄,₈ it tests 794 subsets through cardinality 4 and returns the unique four-mode separator; median proposal time is 5.78 ms. On K₈,₈ it tests 39,203 subsets through cardinality 8 and returns both shores as minimum separators; median proposal time is 356.57 ms. The graph family and separator candidates repeat across all weighted inputs, as expected from the fixed builder topology.

For K₈,₈, that exhaustive proposal takes about 156 role-conditioned solver calls' worth of CPU time at the 2.29 ms median. If reused across the 20 held-out/control cells in the registered transport batch, proposal adds 17.83 ms per cell; proposal plus conditioned solve is about 20.12 ms per cell versus roughly 540 ms for monolithic JT on the same host, about 26.9× faster for that batch. For a single call, proposal plus solve is about 359 ms versus 540 ms JT (about 1.5× faster). These calculations combine measured times from separate source-locked captures and are workload-specific. The proposal is exhaustive and topology-specific; its time scales combinatorially, and the follow-on solver was tested with model-role partition input rather than consuming anonymous candidates directly.

This demonstrates that exact graph-only search can recover separators on two tiny, authored bipartite model-derived families and that repeated workloads may amortize exhaustive proposal cost. It does not show that the substrate discovers useful boundaries online, that natural tasks exhibit these topologies, or that exhaustive search is suitable at larger sizes. The next gate is to pass anonymized discovered separator candidates directly into a generic exact solver, include candidate selection/validation costs, compare against optimized monolithic inference, and expand to independently sourced graphs with varied topology.

## Reproducibility artifacts

- [Protocol](TASK_GRAPH_SEPARATOR_DISCOVERY_AUDIT_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/task_graph_separator_discovery_audit_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_task_graph_separator_discovery_audit_v1.py)
- [Source lock](../../../evaluation/substrate_capability/task_graph_separator_discovery_audit_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/task_graph_separator_discovery_audit_v1_20261002.json)
- [Analysis](../../../evaluation/reports/task_graph_separator_discovery_audit_v1_analysis_20261002.json)
- Inputs: [K₄,₈ inference census](LLM_MODE_NEURON_TASK_GRAPH_INFERENCE_CENSUS_V1_RESULTS_20261002.md), [K₈,₈ transport census](LLM_TRANSPORT_TASK_GRAPH_EXACT_CENSUS_V1_1_RESULTS_20261002.md), and [K₈,₈ role-conditioned solver](LLM_TRANSPORT_ROLE_SEPARATOR_V1_2_RESULTS_20261002.md)
