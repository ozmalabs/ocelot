# Native candidate-adequacy gate v2 results

## Outcome

The source-locked capture completed all 40 fresh panels (10 each for additive conservation, product conservation, componentwise opposition, and inequality). All five capture gates passed, and the independent analyzer passed all ten replay and integrity checks. Each panel used exactly 16 positive and 16 negative validation examples, with zero-containing and boundary-containing examples in each class. The held-out set contained 2,369 integer rows (the complement in the 7^4 grid) and all 1,296 fractional rows, for 3,665 rows per panel. Candidate predictions were captured before held-out labels were revealed.

Native balanced accuracy correctly selected the additive and product candidates on all 20 in-menu panels. It selected a candidate on all 10 opposition panels, which is a 100% false-accept rate for that challenge: the product candidate averaged 0.9719 balanced accuracy and achieved 31.1/32 mean raw validation agreement, yet was not the target relation. Its selected transfer accuracy averaged 91.18% across the held-out grids, showing that high aggregate accuracy still masks a wrong relation. On all 10 inequality panels the best balanced accuracy stayed below 0.75, so the graph requested help in every panel. There were no ties or false-help outcomes on positive controls.

| Task | Native decision across panels | Balanced accuracy, mean (additive / product) | Interpretation |
|---|---:|---:|---|
| Additive | Select additive 10/10 | 1.0000 / 0.6125 | Positive control succeeds |
| Product | Select product 10/10 | 0.5938 / 1.0000 | Positive control succeeds |
| Opposition | Select product 10/10 | 0.5094 / 0.9719 | False acceptance in every panel |
| Inequality | Request help 10/10 | 0.4688 / 0.4031 | Mismatch detected in every panel |

Balanced sampling fixes the v1 failure caused by class imbalance and improves detection for inequality. It does not make a fixed threshold a reliable model-adequacy test: opposition remains close to product equality on the balanced validation distribution. The native engine faithfully computes scores and decisions; the remaining gap is selecting informative probes or richer adequacy criteria that separate near-neighbor relations. No help response, new primitive, or autonomous grammar widening is tested here.

## Reproduction and evidence

Run `python3 evaluation/substrate_capability/native_candidate_adequacy_v2.py --lock`, then `--run`, then `python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_v2.py`. The checked-in source lock preserves all generated validation rows and binds the runner, analyzer, preregistration, native engine, and measured source files.

- [Preregistration](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_V2_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/native_candidate_adequacy_v2.py)
- [Source lock](../../../evaluation/substrate_capability/native_candidate_adequacy_v2_lock_20261005.json)
- [Capture](../../../evaluation/reports/native_candidate_adequacy_v2_20261005.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_native_candidate_adequacy_v2.py)
- [Analysis](../../../evaluation/reports/native_candidate_adequacy_v2_analysis_20261005.json)

The result is finite evidence for native scoring, selection, and help signaling over one supplied two-candidate menu. It does not show autonomous candidate invention or general self-improvement.
