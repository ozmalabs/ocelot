# Vision-eye corruption replay v1.1 amendment

The first post-hoc analyzer grouped model activations within an absolute tolerance of `1e-12`. This incorrectly treated distinct, very small scores as tied and failed the clean-score reconciliation gate. The failed output remains preserved at [`vision_eye_corruption_replay_posthoc_v1_20261005.json`](../../../evaluation/reports/vision_eye_corruption_replay_posthoc_v1_20261005.json) and is not evidence about corruption robustness.

The v1.1 analyzer defines model winners as the exact floating-point maximum of the captured weight-sum scores, matching the engine's `Argmax` readout and the captured clean winner reconstruction. It changes no masks, corruption seeds, or baseline rules. The corrected protocol and output are separate; the failed v1 analysis is not overwritten.
