# Vision-eye corruption replay v1.2 amendment

The v1.1 analyzer fixed activation tie handling but still treated winning WUnit indices as training-site indices. Those identities are not equivalent: a learned unit's site region is determined by its captured receptive-field center. The v1.1 clean gate correctly rejected this scoring mismatch; preserve its output at [`vision_eye_corruption_replay_posthoc_v1_1_20261005.json`](../../../evaluation/reports/vision_eye_corruption_replay_posthoc_v1_1_20261005.json) and exclude it.

The v1.2 analyzer maps each exact-max WUnit winner through that unit's independently analyzed `nearest_site_regions`, using the same map as the published clean metric. Corruption conditions and deterministic masks remain unchanged. The corrected analysis must pass clean-score reconciliation before corrupted results are interpreted.
