# Vision-eye corruption replay — post-hoc protocol v1.1

This corrected analysis follows the [v1.1 amendment](SUBSTRATE_VISION_EYE_CORRUPTION_REPLAY_POSTHOC_V1_1_AMENDMENT_20261005.md). The initial analyzer incorrectly grouped learned activations within a tolerance and failed clean parity; that output is preserved and excluded.

Use the same source-locked v2.1 phase-0 capture and conditions defined in the [v1 protocol](SUBSTRATE_VISION_EYE_CORRUPTION_REPLAY_POSTHOC_V1_PROTOCOL_20261005.md): random removal of 25%, 50%, and 75% of active mask pixels, and random addition of background pixels at 25% and 50% of original mask area. Deterministic SHA-256-derived per-probe/per-condition seeds select pixels. Feed each exact same perturbed mask to the captured-weight, pixel-centroid, and training-mask Hamming scorers.

For the captured-weight readout, sum the stored weights over active pixels and select every unit whose floating-point score is exactly equal to the maximum score. Do not use an epsilon for ties: all weights are nonnegative and the source engine's winner is the maximum of these same sums. Report region accuracy, tie/ambiguity rates, centroid coordinate error, and counts by dose and morphology.

Required gates: the capture and independent v2.1 analysis pass; the clean learned predictions reconcile exactly with the published 288/288 square and 210/288 cross scores; all 12 workers and 48 held-out probes per worker are represented; all conditions have 288 probes per morphology; corruption is deterministic; the same mask digest is shared across the three scorers; and every output group denominator reconciles.

Claim boundary remains frozen-weight analytical forward replay on synthetic binary retinotopy masks. It does not rerun the Rust scheduler, test online adaptation, or establish semantic/natural-image vision.
