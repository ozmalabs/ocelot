# LLM transport topology fan-in v1 preregistration

## Question and sample

At fixed 16-variable graph size and eight source/target modes, how does sparsifying the learned transport topology change separator width, exact-inference cost, and held-out target-sign agreement? Use `transport_L12_13.npz`, fit the 32×32 map at ridge 1.0 on the 60 training pairs, and score all ten held-out L12→L13 coefficient pairs in three fresh workers.

For each input select the eight largest-magnitude L12 coefficients and the first eight L13 target modes. For each target, retain its r strongest absolute transport weights among those selected source modes, with r={1,2,4,8}. Ties use stable source-column order. Pruning depends only on the train-fitted T and the current input's selected source basis; held-out destination values are read only for final scoring. Construct a fresh 3-state graph per input/r using source unary fields, zero destination unary fields, and bidirectional retained couplings. The r=8 dense condition is the within-run control.

## Gates and measurements

Measure graph size, retained edges, connected components, min-fill and triangulation width, graph construction, live factor extraction, exact JT, BP, and sparse linear transport. Independently verify MAP using an exhaustive oracle over all 3^8 source assignments with conditional target minimization; compare both exact solver energies and direct rescore. Verify expected pruned factors, stable source/export hashes, full paired coverage, no graph mutation, and recompute target-sign accuracy from stored predictions. Report cost and accuracy by fan-in; do not assume more sparsity improves utility.

## Claim boundary

This compares four train-weight-derived sparsity levels on one Qwen3-0.6B L12→L13 transition and ten held-out coefficient pairs. It measures topology sensitivity for a fixed bipartite family, not spontaneous frame discovery, natural task graph distributions, language-task utility, or broad model transfer. Results at each r, including any disconnected graph or accuracy loss, are reported as observed.

## Artifacts

- Runner: [llm_transport_topology_fanin_v1.py](../../../evaluation/substrate_capability/llm_transport_topology_fanin_v1.py)
- Analyzer: [analyze_llm_transport_topology_fanin_v1.py](../../../evaluation/substrate_capability/analyze_llm_transport_topology_fanin_v1.py)
- Lock: [llm_transport_topology_fanin_v1_lock_20261002.json](../../../evaluation/substrate_capability/llm_transport_topology_fanin_v1_lock_20261002.json)
- Capture: [llm_transport_topology_fanin_v1_20261002.json](../../../evaluation/reports/llm_transport_topology_fanin_v1_20261002.json)
- Analysis: [llm_transport_topology_fanin_v1_analysis_20261002.json](../../../evaluation/reports/llm_transport_topology_fanin_v1_analysis_20261002.json)
