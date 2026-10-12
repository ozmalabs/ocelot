# Seed manifest corpus footprint v1 results (2026-09-27)

The 837 JSON seed manifests occupy **288.15 MB** on disk. Their top-level payloads contain 12,900 direct nodes plus 2,501 nodes in one legacy nested graph, 9,278 edges, 3,994 rules, 6,360 concepts, and 1,799 productions. This is a static corpus inventory, not resident-memory accounting or proof that each payload is retained at runtime.

The corpus is highly skewed by serialized file size: the largest manifest, `grounded_lexicon.json`, is 110.73 MB (38.4% of all manifest bytes); the three largest account for 73.7%, five for 82.3%, and ten for 89.4%. The largest files include a mix of lexical payloads and embodied/rule manifests, so byte share alone does not identify runtime cost. The selected/full profile comparison should first test whether selective conversation boot retains the expected describe-scene lifecycle, then compare its current/peak RSS to the full-seed profile.

This establishes a tractable next experiment: test content-heavy and rule-heavy seed families separately and compare manifest bytes, graph/rule counts, and incremental RSS. It does not yet attribute the 1.295 GiB anonymous RSS increase during full seed boot to particular manifests or prove that omitted seeds are unnecessary for general capability.

## Artifacts

- [analysis runner](../../../scripts/analyze_substrate_seed_manifest_footprint_v1.py)
- [full per-manifest inventory and source hashes](../../../evaluation/reports/substrate_seed_manifest_footprint_v1_20260927.json)
- [memory phase profile](SUBSTRATE_DESCRIBE_SCENE_BOOT_MEMORY_PROFILE_V1_RESULTS_20260927.md)

A same-source selective-profile follow-up confirms that serialized size is not enough to choose a reduced runtime: the four- and eight-seed conversation profiles cut peak RSS to about 0.129 GiB but fail the full-profile scene-description capability. See the [profile comparison](SUBSTRATE_DESCRIBE_SCENE_SELECTIVE_SEED_PROFILE_RESULTS_20260927.md).
