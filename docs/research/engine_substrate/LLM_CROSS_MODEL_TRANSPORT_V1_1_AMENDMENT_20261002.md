# Cross-model Qwen3 transport v1.1 lock-coverage amendment

Before any repeated graph scoring, inspection found that v1's source lock included the shared corpus, extraction code, reused graph worker/analyzer, substrate sources, native binary, and both model exports, but omitted the cross-model orchestration script and independent cross-model analyzer. The v1 capture therefore remains a pilot and is not the confirmatory result.

The v1.1 rerun keeps the corpus, tokenization, fitted coefficient exports, transport fitting, graph grid, model set, thresholds, and interpretation boundary unchanged. It adds the cross-model runner itself and the independent analyzer to the source lock, records a fresh lock, and reruns three fresh workers per model over the complete 480-case grids. The v1.1 capture is confirmatory only if all registered gates pass and the source lock is unchanged before and after scoring. No model export or corpus is refit for this amendment.

## Artifacts

- Parent preregistration: [LLM_CROSS_MODEL_TRANSPORT_V1_PREREG_20261002.md](LLM_CROSS_MODEL_TRANSPORT_V1_PREREG_20261002.md)
- Corpus: [llm_cross_model_transport_v1_corpus.json](../../../evaluation/substrate_capability/fixtures/llm_cross_model_transport_v1_corpus.json)
