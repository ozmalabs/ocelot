# Response-priority scene-route divergence: forensic result

Date: 2026-10-06  
Status: strict graph mismatch localized to one execution-count receipt attribute.

## Finding

The source-locked two-worker scene replay confirms that the mismatch is already present before continuation. The arms have the same 25,225 nodes and 11,731 edges; type counts and edge-type counts match. The ID-independent multiset of typed node records differs in exactly one attribute: a `NativeReflectiveFacultyReceipt` for `shape_decode_loop` records `native_steps=10` under global closure and `native_steps=8` under priority. The other four reflective-faculty receipts match at five steps each. After removing only this execution-count attribute, the bounded normalized WL fingerprint matches both before and after continuation. The held reply is identical, the task's existing utility oracle still fails in both arms, and both continuations have zero residual and zero progressing steps.

The writer is [induce_concern](../../../domains/reflective_faculty.py), which records the integer returned by `native.run_rules()` as a receipt. A source search finds no rule-seed, Rust, or other Python reader for `NativeReflectiveFacultyReceipt`; the other occurrences are receipt writers in `reflective_faculty.py`. Thus the strict graph mismatch is caused by recorded scheduler work, not a changed scene interpretation or task outcome. Keep the strict full-graph parity result marked failed; separately report telemetry-normalized graph equivalence. The distinction must remain visible because `native_steps` is retained graph data even though no consumer was found.

This diagnosis explains the prior scene failure; it does not make scene description successful or prove generic scheduler equivalence. The scene route already fails its utility criterion under global closure. The response-priority result is now four task routes with strict parity, plus one known-failing route whose sole state delta is an execution-count receipt.

## Artifacts

- [Diagnostic preregistration](SUBSTRATE_RESPONSE_PRIORITY_SCENE_DIVERGENCE_V1_PREREG_20261006.md)
- [Diagnostic runner](../../../scripts/substrate_response_priority_scene_divergence_v1_20261006.py)
- [Source lock](../../../evaluation/substrate_capability/response_priority_scene_divergence_v1_20261006_lock.json)
- [Graph snapshot capture](../../../evaluation/reports/response_priority_scene_divergence_v1_20261006/capture.json.gz)
- [Forensic analysis](../../../evaluation/reports/response_priority_scene_divergence_v1_20261006/analysis.json)
- [Cross-family result](SUBSTRATE_RESPONSE_PRIORITY_CROSS_FAMILY_V1_RESULTS_20261006.md)
