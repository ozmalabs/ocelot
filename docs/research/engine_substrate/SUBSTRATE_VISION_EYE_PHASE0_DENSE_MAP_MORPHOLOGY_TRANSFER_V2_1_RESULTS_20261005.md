# Vision-eye phase-0 dense-map morphology transfer v2.1 results

## Result

All capture gates and all independent scoring gates pass. The six paired seeds ran on the shifted `(2,7,13) × (2,7,13)` training grid with a larger 5×5 patch span. Both morphologies cover all nine trained sites and classify the trained locations correctly on 162/162 probes. On the 288 held-out probes, the 5×5 square scores 288/288 nearest-region correct and the 9-cell axial cross scores 210/288 (72.9%). Square is higher in every paired seed, by 6–18 probes out of 48. Both conditions have zero exact held-out coordinate localizations.

The direction of the v1 morphology effect transfers to a shifted grid and larger span, while the cross condition improves substantially from v1's 33/288 to 210/288. The comparison across panels is descriptive: both the grid and mask scale changed, and the square has 25 active cells while the cross has 9. This experiment cannot identify which change explains the different gap. The within-v2 square/cross contrast also combines morphology with active-cell count.

## Cost and integrity

All 12 workers have distinct PIDs and stable source identities. The capture verifies 36,000 training steps, 4,000 exposures per site, 75 probes per worker, exact mask sizes, unique winners, positive runtime progress, and unchanged learned weights during frozen probing. The independent analyzer reconstructs all 900 activation vectors and winners from the captured weights and masks.

Median per-worker training closure time is 393.2 s for squares and 393.6 s for crosses. Median total closure time for the 75 frozen probes is 348 ms and 364 ms respectively (about 4.64 and 4.86 ms per probe). These are one-host measurements for this fixed graph and schedule. They do not isolate mask-specific engine cost because most rule closure work is shared across each run.

The initial v2 attempt used a grid that put radius-2 masks outside the retina and failed before training; it is preserved and excluded in the [amendment](SUBSTRATE_VISION_EYE_PHASE0_DENSE_MAP_MORPHOLOGY_TRANSFER_V2_1_AMENDMENT_20261005.md).

## Coordinate baseline and next gate

A post-hoc control on both phase-0 captures shows that active-pixel centroids recover all held-out coordinates exactly and classify the nearest trained region on 288/288 probes per morphology. The mask-based nearest-neighbor control also covers the true region in all cases, but has ties on 288/288 v1-cross and 126/288 v2.1 cases. This means absolute position is available directly in the stimulus; these results measure retinotopic map formation, not position-invariant visual learning. See the [post-hoc baseline results](SUBSTRATE_VISION_EYE_COORDINATE_BASELINES_POSTHOC_V1_RESULTS_20261005.md) and [machine report](../../../evaluation/reports/vision_eye_phase0_coordinate_baselines_posthoc_v1_20261005.json).

The post-hoc [v1.2 corruption replay](SUBSTRATE_VISION_EYE_CORRUPTION_REPLAY_POSTHOC_V1_2_RESULTS_20261005.md) now covers active-pixel dropout and background additions against centroid and Hamming controls. It is frozen-weight analytical scoring, not a scheduler replay. Next validate selected corruption doses through live substrate rule execution against the captured-weight prediction and exact mutation/readback parity. Then run a dose-controlled design separating morphology from active-cell count. Keep held-out region classification, abstention, wrong-region errors, and exact coordinate error distinct; object recognition needs a separate label/task that absolute position cannot resolve.

## Artifacts

- [Preregistration](SUBSTRATE_VISION_EYE_PHASE0_DENSE_MAP_MORPHOLOGY_TRANSFER_V2_1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v2_1.py)
- [Source lock](../../../evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v2_1_lock_20261005.json)
- [Capture](../../../evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_20261005.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_vision_eye_phase0_dense_map_morphology_transfer_v2_1.py)
- [Analysis](../../../evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_analysis_20261005.json)
