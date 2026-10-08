# Cross-model Qwen3 transport v1 preregistration

## Question

Do the already-measured low-width cost effects of learned mode transport, and the associated internal held-out mode-sign agreement, appear in a second Qwen3 model when the entire fitting procedure is repeated independently? This is a model-family generalization check. It is not a language task-utility test and does not ask whether a transport learned in one model transfers to another model's basis.

## Locked data and split

Use `evaluation/substrate_capability/fixtures/llm_cross_model_transport_v1_corpus.json` (SHA-256 `68ac2e8e8a150055f2dbb7c4bb5474c65822c22001a7572d701684c1b417503c`): 70 fixed English text inputs with the train/held-out assignment recorded per row in the checked-in fixture. The corpus has repeated lexical and syntactic components by design, so held-out means a disjoint input row, not an out-of-vocabulary or out-of-template test. Preserve exact text and encode separately with each checkpoint's local tokenizer using `add_special_tokens=True`.

## Models and fitting

Use local `Qwen3-0.6B` and `Qwen3-1.7B` checkpoints in `/applications/data/model_graph_work`. The 0.6B model is the reference scale; the 1.7B model is the held-out model scale. For each model independently, fit a 32-mode activation router with `fit_mode_router`, ridge 1.0 and `all_positions=False`, using only the 60 training inputs. Export coefficient vectors at layers 10–14 for all 60 training and ten held-out inputs. Fit four independent ridge-1.0 transport maps (L10→11 through L13→14) from that model's training coefficients.

For each hop and held-out input, take the eight largest-absolute source coefficients and first eight target modes. Construct fresh three-state CAN factor graphs at incoming fan-in 1/2/4/8 by retaining the strongest absolute fitted incoming transport weights per target, with stable source-column tie-breaking. Run exact junction-tree MAP, min-fill triangulation/certificate, direct energy rescore, exhaustive `3^8` source-assignment oracle, native BP, and pruned linear prediction. Three fresh workers per model repeat the full 4-hop × 10-input × 4-fan-in grid. Report model-specific results; do not pool the two models into a universal estimate.

## Gates and measurements

Lock corpus, tokenizer/config files, every model-weight shard, exporter/runner/analyzer, substrate inference sources, native binary/build manifest, and seed before scoring. Record model tokenization IDs, model/revision metadata, configuration, software versions, CPU, wall times, peak RSS, and the separate graph construction, extraction, ordering, exact JT, and BP durations. Require full worker coverage, stable source hashes before/after, exact live factor extraction, node/edge accounting, valid width certificates, JT/oracle/direct-rescore equality, score recomputation, exact/BP output comparison, repeatable topology signatures, and no graph mutation. Any failed gate remains a reported failure; no post-hoc corpus or fitting changes.

## Interpretation boundary

A pass would support repeatability of this synthetic-text, model-family transport experiment at two model scales. It would not establish natural cheap-cut prevalence, autonomous frame discovery, cross-model basis transfer, broad text generalization, task benefit, or self-improvement. A failure is informative and must be reported by model and hop. The source corpus is generated rather than sampled from a natural-task distribution, and the 60/10 split is only input-disjoint.
