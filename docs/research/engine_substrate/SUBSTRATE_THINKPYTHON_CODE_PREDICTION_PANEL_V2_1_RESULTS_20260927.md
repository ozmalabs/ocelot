# Think Python code-prediction panel v2.1 results

Date: 2026-09-27  
Status: source-stable corrected two-worker panel passed all 12 independent checks.

## Results

The corrected panel covers 18 outcome-blind selected textbook functions under a static safe-AST grammar and 36 fixed inputs. The independent interpreter successfully classified every input within its limits. Two fresh workers had distinct PIDs, stable full-runtime locks, identical schedules, and identical typed predictions.

Each worker returned **10/36 exact typed outputs**, abstained on **26/36** with `EmitError`, and made **zero incorrect returned predictions**. Thus coverage is 27.8%, exact accuracy over all scheduled cases is 27.8%, and accuracy among the ten returned predictions is 100%. Successful outputs came from five examples: a constant-return function, two divisibility implementations, a loop-based sum, and the complete absolute-value implementation. The other 13 function examples, including the absolute-value version without an `else` branch, yielded abstentions on both inputs. Call-expression functions (`min_max`, `different_words`) and several branch/loop/string/sequence forms consistently abstain. This is a coverage result for this route and grammar, not a broad code accuracy estimate.

Each worker records five concern receipts across the 36 calls; two are Observation-linked minted axes. Minting did not guarantee an emittable Term or a returned answer. Median call wall time is 4.03–4.12 ms; nearest-rank p95 is 33.3–33.9 ms. Boot takes 12.56–12.60 s, loads 731 of 742 manifests, and reports the same 11 failures; peak RSS is 1.951–1.954 GB.

## Censoring and run history

The first v2 analyzer run is preserved as censored because its two `shift` inputs caused oracle `TypeError`s; see [censored record](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_CENSORED_20260927.md). The first corrected v2.1 attempt crossed edits to `domains/fetch_dispatch.py` and `domains/wiktionary_reference.py` and failed source-stability gates. Its raw output was overwritten by the subsequent stable rerun before archival, so it is not used as evidence. The successful report below contains the refreshed lock and source-stable rerun only.

## Interpretation

The broader frame provides stronger evidence than the nine-case v1 probe about an operating boundary: the system returns exact values on the measured arithmetic/comparison/sum subset and abstains widely across other statically interpretable source shapes. There is no evidence of a wrong returned value in these 20 worker-level predictions, but the sample remains only 18 examples from one textbook and the successful subset is concentrated in a few structures. The result supports explicit coverage accounting; it does not support general code competence, learned-structure transfer, or a complexity bound.

## Reproduction artifacts

- Parent protocol: [v2 preregistration](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_PREREG_20260927.md)
- Correction: [v2.1 amendment](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_1_AMENDMENT_20260927.md)
- Frozen rerun protocol: [v2.1 preregistration](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_1_PREREG_20260927.md)
- Selector: [v2.1 selector](../../../scripts/audit_thinkpython_code_prediction_frame_v2_1.py)
- Frame: [v2.1 frame](../../../evaluation/reports/thinkpython_code_prediction_frame_v2_1_20260927.json)
- Runner: [v2.1 runner](../../../scripts/substrate_thinkpython_code_prediction_panel_v2_1.py)
- Independent interpreter/analyzer: [v2.1 analyzer](../../../scripts/analyze_substrate_thinkpython_code_prediction_panel_v2_1.py)
- Source lock: [v2.1 lock](../../../evaluation/substrate_capability/thinkpython_code_prediction_panel_v2_1_lock_20260927.json)
- Raw capture: [v2.1 raw](../../../evaluation/reports/thinkpython_code_prediction_panel_v2_1_20260927.json)
- Analysis: [v2.1 analysis](../../../evaluation/reports/thinkpython_code_prediction_panel_v2_1_analysis_20260927.json)

## Next gate

Expand beyond this textbook and these 18 signature strata. Select code from an independent source corpus, include more functions per construction family, freeze diverse inputs based on declared parameter contracts, and retain a bounded independent interpreter. Next measure acquisition and transfer explicitly: acquire a structure from earlier examples, then evaluate unseen functions with the same shape and adversarial near-neighbor controls. Keep coverage, correctness, abstention, and mint incidence separate.
