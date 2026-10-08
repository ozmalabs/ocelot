# Vision-eye corruption replay — post-hoc protocol v1.2

This correction follows the [v1.2 amendment](SUBSTRATE_VISION_EYE_CORRUPTION_REPLAY_POSTHOC_V1_2_AMENDMENT_20261005.md). The v1 analyzer used a tie tolerance; v1.1 used exact max scores but misread WUnit indices as site indices. Both failed clean reconciliation and are preserved without capability claims.

Use the v2.1 source-locked capture and the same fixed perturbations and scorers defined in the [v1 protocol](SUBSTRATE_VISION_EYE_CORRUPTION_REPLAY_POSTHOC_V1_PROTOCOL_20261005.md). Select WUnit winners as units whose captured weight-sum equals the exact floating-point maximum. Convert each winning unit to predicted training-site region(s) using the captured unit's learned receptive-field center and nearest trained-site mapping. Score region success only after this mapping. Centroid and Hamming controls receive exactly the same corrupted pixel set.

Require clean learned scores to reconcile to 288/288 square and 210/288 cross before reporting corrupted scores. Preserve deterministic corruption, 288 probes per morphology/condition, scorer-input mask identity, and source/analysis hashes. Scope remains frozen-weight analytical replay on synthetic binary retinotopy masks; the scheduler is not rerun.
