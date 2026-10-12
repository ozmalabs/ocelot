# LLM transport varied-topology separator census v1.2 results

Date: 2026-10-03  
Status: confirmatory graph-structure census; all registered gates passed.

## Question

Does graph-only minimum vertex-separator search produce repeatable structural profiles across varied task graphs reconstructed from two Qwen3 model exports, and what is its cost at the tested graph sizes?

## Method and scope

The source-locked run reconstructed 960 captured rows in each of three fresh workers, representing 242 distinct `(model, fan-in, topology)` keys. Graphs have 16 vertices; the evaluator imposes fan-in 1, 2, 4, or 8 (8, 16, 32, or 64 edges). For each topology, exhaustive graph-only search enumerates vertex subsets by increasing size and retains all minimum subsets whose removal leaves at least two components. A disconnected input therefore has a valid size-zero separator. Worker node labels are independently anonymized; repeatability is checked by source topology and separator/component profiles, not by randomized labels.

The independent analyzer recomputes every separator family from the captured edges and verifies the source lock, all 960 row reconstructions, three distinct workers, and the runner gates. The v1.1 analyzer failure is retained as diagnostic; v1.2 is the confirmatory run after correcting the analyzer's node-count argument. See [preregistration](LLM_TRANSPORT_VARIED_TOPOLOGY_SEPARATOR_CENSUS_V1_PREREG_20261003.md), [v1.2 amendment](LLM_TRANSPORT_VARIED_TOPOLOGY_SEPARATOR_CENSUS_V1_2_AMENDMENT_20261003.md), [lock](../../../evaluation/substrate_capability/llm_transport_varied_topology_separator_census_v1_2_lock_20261003.json), [capture](../../../evaluation/reports/llm_transport_varied_topology_separator_census_v1_2_20261003.json), and [independent analysis](../../../evaluation/reports/llm_transport_varied_topology_separator_census_v1_2_analysis_20261003.json).

## Results

All gates pass. Each model contributes 40 distinct topologies at fan-in 1, 2, and 4, and one dense topology at fan-in 8. Among the 80 fan-in-1 topologies all graphs are disconnected and the minimum separator is empty. At fan-in 2, 73/80 graphs are disconnected; the remaining seven require a one-vertex separator. At fan-in 4, 72/80 graphs are connected; minimum separator sizes range from 1 to 3. Both fan-in-8 graphs are connected and have minimum separator size 8.

Median exhaustive-search time by model and fan-in:

| Model | Fan-in 1 | Fan-in 2 | Fan-in 4 | Fan-in 8 |
|---|---:|---:|---:|---:|
| Qwen3 0.6B | 0.013 ms | 0.012 ms | 0.160 ms | 318.6 ms |
| Qwen3 1.7B | 0.013 ms | 0.012 ms | 1.125 ms | 298.5 ms |

At fan-in 8, exhaustive search examines 39,203 subsets per graph. The measurements show a sharp cost increase as these small generated graphs become dense; model size does not explain that cost because the graph structure and search are the measured objects. Sparse and already-disconnected instances are cheap under this exact search, while the dense 16-node cases take about 0.3 seconds each on this host.

## Interpretation and limits

This supports repeatability and feasibility of exhaustive graph-only separator discovery on sparse 16-node topologies, and quantifies a dense-case cost boundary. It does **not** show that the proposed separator helps inference: no partitioned solver is run here, and separator discovery alone does not establish a beneficial decomposition. The `width` values in the capture are inherited from the upstream inference workload; they are not measured graph treewidth. The corpus is generated, the fan-in is imposed by the evaluator, only two model exports are represented, and no natural-task prevalence is estimated. Consequently, this is not evidence that natural tasks generally admit cheap cuts or that the substrate automatically discovers useful frames.

## Next gate

Feed the graph-only proposals into the generic exact solver on a varied topology set, compare exact outputs with an optimized monolithic baseline, and charge proposal, caching, and solving costs end to end. Include larger/dense graphs to test how discovery cost grows, plus task-derived structures not created by this imposed fan-in generator.
