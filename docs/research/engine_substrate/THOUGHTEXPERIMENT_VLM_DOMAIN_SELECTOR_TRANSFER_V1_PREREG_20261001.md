# Thoughtexperiment VLM transfer under all-domain selector v1 preregistration

## Question

For the previously discovered reliability-weighted fusion derivation on `vision_language_model`, does the actual synthesis operator still derive the implication with openness pruning off, while pruning it under an all-domain implementation scan?

## Procedure

- Run three fresh full-seed workers.
- Load the exact default harvested shape library and frozen coverage set once per fixed graph.
- Set the measurement-only `_SPEECH_GLOBS_OVERRIDE` to every top-level `domains/*.py` file.
- Call `synthesize_gaps` for `vision_language_model` with order 1, `record=False`, identical explicit shapes and cached coverage in both arms: first `prune=False`, then `prune=True`.
- Record all outputs and determine whether the known `reliability_weighted_fusion__from__Kalman_filter` derivation is present in each arm. Also record the direct selector verdict and source path for its complete `capability_keys` list.
- Compare canonical graph hashes before and after and lock all domain source, relevant engine/boot/native files, and top-level seeds.

## Interpretation gates

The expected mechanism signature is: the derivation-only arm contains the fusion transfer, the all-domain selector identifies `domains/combinatorial_recognizer.py`, and the same transfer is absent from the normal-pruned arm. Direct/receipt equivalence, utility, novelty of the full VLM, and presence of visual input are outside this panel. A pruned fusion operation does not imply the complete VLM capability is implemented.

See the [results](THOUGHTEXPERIMENT_VLM_DOMAIN_SELECTOR_TRANSFER_V1_RESULTS_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_vlm_domain_selector_transfer_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_vlm_domain_selector_transfer_v1_raw_20261001.json).
