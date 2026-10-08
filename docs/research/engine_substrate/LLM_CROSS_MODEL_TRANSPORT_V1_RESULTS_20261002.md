# Qwen3 cross-model transport v1.1 results

## Confirmatory run

The v1.1 amendment reran the graph phase after adding the cross-model orchestrator and independent analyzer to the source lock. The corpus, per-model tokenizer IDs, fitted exports, protocol, and solver methods remained fixed. Three fresh workers per model completed the full 4-hop × 10-input × 4-fan-in grid (480 cases per model; 960 total). The independent analyzer passes all registered gates: source stability, full coverage, graph accounting, live factor extraction, width certificates, junction-tree/exhaustive-oracle/direct-rescore agreement, prediction-score arithmetic, topology repeatability, and no graph mutation.

Each model's 60 training texts independently fit a 32-mode activation router and four ridge-1.0 transports over L10–L14; the ten held-out rows were not used for fitting. The source exports and tokenizations are linked below. Extraction took 143.7 s and 3.01 GiB peak RSS for Qwen3-0.6B, and 426.6 s and 7.43 GiB for Qwen3-1.7B on this CPU-only host.

| Model | Fan-in 1/2/4/8 certified widths | Median of hop-level JT medians (ms), fan-in 1/2/4/8 | Mean held-out target-sign agreement, fan-in 1/2/4/8 | Exact/BP prediction agreement |
|---|---|---|---|---|
| Qwen3-0.6B | 1 / 2 / 4–6 / 8 | 0.152 / 0.372 / 9.43 / 525.2 | 0.831 / 0.831 / 0.828 / 0.828 | 237/240 |
| Qwen3-1.7B | 1 / 2 / 4–6 / 8 | 0.156 / 0.386 / 8.79 / 542.2 | 0.800 / 0.800 / 0.784 / 0.797 | 240/240 |

The top-2 intervention reduces edge count by 75%, lowers certified width from 8 to 2, and is about 1,400× faster than fan-in 8 by the ratio of those hop-level median summaries in both models. The separate model-specific ratios are 1,412× for 0.6B and 1,405× for 1.7B. BP medians across fan-ins are about 5.6/11.8/28/77 ms. The cost response is nearly unchanged by a 2.8× model-scale increase because the substrate graphs contain the same 16 variables and differ only in fitted edge weights and retained fan-in.

Held-out sign agreement varies modestly by model/hop and does not improve monotonically as edges are removed. BP matches exact MAP in 237/240 0.6B cells and all 240 1.7B cells. This supports repeatability of the *explicit fan-in cost effect* across two model scales and separately learned bases. Fan-in pruning was specified by the evaluator, so this does not show that the substrate discovers useful cuts. The 70-item generated corpus has repeated forms; the sign-agreement metric measures internal coefficient prediction, not task utility. Natural cheap-cut prevalence, autonomous separator discovery, transfer between model-specific bases, and self-improvement remain open.

The first v1 scoring capture was treated as a pilot because its source lock omitted the outer orchestrator and independent analyzer. The confirmatory numbers here come from the amended, source-complete v1.1 rerun.

## Artifacts

- [Base preregistration](LLM_CROSS_MODEL_TRANSPORT_V1_PREREG_20261002.md)
- [Source-lock amendment](LLM_CROSS_MODEL_TRANSPORT_V1_1_AMENDMENT_20261002.md)
- [Corpus](../../../evaluation/substrate_capability/fixtures/llm_cross_model_transport_v1_corpus.json)
- [Exporter](../../../evaluation/substrate_capability/llm_cross_model_transport_v1_export.py)
- [Cross-model runner](../../../evaluation/substrate_capability/llm_cross_model_transport_v1.py)
- [Fresh graph worker adapter](../../../evaluation/substrate_capability/llm_cross_model_transport_v1_worker.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_cross_model_transport_v1.py)
- [v1.1 source lock](../../../evaluation/substrate_capability/llm_cross_model_transport_v1_1_lock_20261002.json)
- [v1.1 raw capture](../../../evaluation/reports/llm_cross_model_transport_v1_1_20261002.json)
- [v1.1 analysis](../../../evaluation/reports/llm_cross_model_transport_v1_1_analysis_20261002.json)
- Per-model exports, token IDs, and extraction provenance are in `evaluation/reports/llm_cross_model_transport_v1_qwen3_{0_6b,1_7b}.{npz,provenance.json,tokenization.json}`.
