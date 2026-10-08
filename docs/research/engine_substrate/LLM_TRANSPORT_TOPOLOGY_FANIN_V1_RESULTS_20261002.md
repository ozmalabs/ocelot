# LLM transport topology fan-in v1 results

All three fresh source-locked workers completed the full 120-case panel: ten held-out L12→L13 inputs crossed with fan-in 1, 2, 4, and 8. All extracted factors match the train-fitted, deterministically pruned transport. Every exact JT energy matches the exhaustive 3^8 source-assignment oracle and direct state rescore; all width certificates reconcile, primary graphs remain unchanged, and topology signatures match across fresh-worker replicas. The independent analyzer passes and recomputes each prediction accuracy from the stored vectors and targets.

| Retained incoming edges per target | Edges | Median components | Certified widths | Median exact JT | Median BP | Mean exact/BP sign agreement | Mean sparse-linear agreement |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 8 | 8 | 1 | 0.153 ms | 5.72 ms | 0.863 | 0.863 |
| 2 | 16 | 2 | 2 | 0.399 ms | 11.94 ms | 0.863 | 0.800 |
| 4 | 32 | 1 | 5–6 | 10.07 ms | 27.56 ms | 0.813 | 0.850 |
| 8 | 64 | 1 | 8 | 541.5 ms | 76.85 ms | 0.800 | 0.863 |

JT and BP returned identical target-state vectors in all 30 cases at every fan-in. The one-edge condition's mean exact agreement equals the dense graph's linear baseline (0.863) and exceeds the dense exact graph's result (0.800) on this held-out sample; the two-edge condition has the same exact agreement while its own sparse-linear baseline is 0.800. The two-edge graph cuts edge count by 75%, lowers the certified width from 8 to 2, and has about 1,356× lower median JT time. Fan-in one is about 3,534× faster than fan-in eight. These are substantial measured savings for this selected transport and sample, not a guarantee that pruning preserves behavior or helps other tasks. Four incoming edges give connected graphs but widths 5–6, demonstrating that degree alone does not determine the width certificate.

The result demonstrates that topology induced by train-only learned-weight pruning materially changes exact-inference cost and held-out internal mode-sign agreement at fixed node count. It does not establish that the substrate autonomously discovers such a cut, that low fan-in is common in natural task graphs, or that coefficient-sign agreement transfers to language behavior. Edge selection is an explicit registered operation over the learned transport matrix.

## Artifacts

- [Preregistration](LLM_TRANSPORT_TOPOLOGY_FANIN_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_transport_topology_fanin_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_transport_topology_fanin_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_transport_topology_fanin_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/llm_transport_topology_fanin_v1_20261002.json)
- [Analysis](../../../evaluation/reports/llm_transport_topology_fanin_v1_analysis_20261002.json)
