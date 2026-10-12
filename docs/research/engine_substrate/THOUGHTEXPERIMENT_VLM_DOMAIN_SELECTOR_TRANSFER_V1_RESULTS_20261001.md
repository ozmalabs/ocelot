# Thoughtexperiment VLM domain-selector transfer v1 results

**Result:** in all three workers, derivation-only synthesis retains the `reliability_weighted_fusion__from__Kalman_filter` transfer, while normal synthesis under the all-domain implementation surface prunes it.

Each worker boots 731 seeds with 11 failures, derives exactly one order-1 gap for `vision_language_model`, and returns zero open gaps under all-domain pruning. The direct selector verdict is `already in speech codebase` with `covered_by=domains/combinatorial_recognizer.py`. Canonical graph hashes remain unchanged, worker PIDs are distinct, source/seed fingerprints are stable, and default harvested mode resolves identically across workers.

This confirms that the earlier open result depended on the narrower speech-file discovery surface. It supports the claim that reliability-weighted cue fusion is already held in this implementation. It does **not** establish a VLM, visual input path, image-text embedding, or useful task performance. The derivation is generic cue-fusion transfer from Kalman filtering; novelty must be assessed at the mechanism and task level rather than inferred from its postulate label.

See [preregistration](THOUGHTEXPERIMENT_VLM_DOMAIN_SELECTOR_TRANSFER_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_vlm_domain_selector_transfer_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_vlm_domain_selector_transfer_v1_raw_20261001.json).
