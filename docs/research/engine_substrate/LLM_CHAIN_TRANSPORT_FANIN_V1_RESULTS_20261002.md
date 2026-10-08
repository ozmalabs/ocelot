# LLM chain transport fan-in v1 results

Three fresh source-locked workers completed all 480 cases: four adjacent transitions (L10→11 through L13→14), ten held-out inputs per transition, and fan-in 1/2/4/8. Every case passes live factor extraction, min-fill/triangulation certificate, direct-rescore and independent exhaustive-oracle energy agreement, score recomputation, source-lock parity, and no-mutation checks. Topology signatures repeat across workers for every hop/input/fan-in condition. This independently fits a transport for each hop from that hop's 60 training examples.

| Incoming edges per target | Edges | Certified widths across hops/cases | Median JT | Median BP | Mean exact target-sign agreement | Mean pruned-linear agreement |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 8 | 1 | 0.156 ms | 5.77 ms | 0.784 | 0.784 |
| 2 | 16 | 2 | 0.397 ms | 11.96 ms | 0.781 | 0.778 |
| 4 | 32 | 4–7 | 11.08 ms | 27.70 ms | 0.806 | 0.825 |
| 8 | 64 | 8 | 535.7 ms | 76.77 ms | 0.803 | 0.850 |

At each fan-in, exact JT and BP returned identical target-state vectors in all 120 cases. The cost response replicates across four separately fitted layer transitions: top-2 fan-in uses one quarter as many edges as the dense graph, has certified width 2 rather than 8, and runs at a median JT time roughly 1,349× lower. Top-4 remains connected in these cases and its min-fill width ranges from 4 to 7; edge degree alone therefore does not identify an exact width. Accuracy varies by layer rather than moving uniformly with sparsity: fan-in 1 ranges from 0.700 to 0.863 across hops, and fan-in 8 from 0.763 to 0.825. The pooled mean is descriptive of this same-model/same-corpus sample, not a broad estimate.

This is stronger evidence that train-weight-derived sparsity can produce a repeatable cost/width change across nearby layer transitions. The model, corpus, layer-chain export, selected eight source modes, and target-sign metric are shared; edge pruning is an explicit benchmark operation. The result does not establish transfer to another model or task, spontaneous separator discovery, natural cheap-cut prevalence, or language-task utility.

## Artifacts

- [Preregistration](LLM_CHAIN_TRANSPORT_FANIN_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_chain_transport_fanin_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_chain_transport_fanin_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_chain_transport_fanin_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/llm_chain_transport_fanin_v1_20261002.json)
- [Analysis](../../../evaluation/reports/llm_chain_transport_fanin_v1_analysis_20261002.json)
