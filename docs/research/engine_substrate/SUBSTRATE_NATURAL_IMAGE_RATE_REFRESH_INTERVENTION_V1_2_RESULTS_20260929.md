# Natural-image rate refresh multi-image replication v1.2 results (2026-09-29)

## Integrity

The 144-cell matrix completed across eight locked BSDS300 test images, three adapted checkpoints, two settlement scopes, and original/180°-rotated/blank inputs. All 7 independent gates pass: complete matrix; source lock and stability; image, transform, and checkpoint identity; exact pixel delivery; unchanged activation state; intervention writes restricted to target `rate`/`rate_step`; and the full rule equation/stamp oracle. Every cell used 16 progressing rate-rule calls followed by a no-progress termination call. Maximum refreshed-rate equation residual is exactly 0.

## Spatial task result

After post-settlement refresh, the root-scoped rate map favors the expected 180° spatial permutation over an unchanged-map control in 22/24 image/checkpoint pairs. The result repeats in each checkpoint: 7/8, 8/8, and 7/8 images. Seven of eight images show the expected permutation in all three checkpoints; image `376043.jpg` is the exception, with one of three checkpoint cells favoring the permutation. All 24 root-scoped cells have nonzero response relative to blank.

Under global settlement, the refresh produces nonzero response on only eight of 24 image/checkpoint pairs, all from checkpoint 20260936. That checkpoint favors the unchanged map on all eight images. The other two checkpoints produce zero refreshed response across the image set. The default pre-refresh rates favor the unchanged map in all 24 cells under both scopes.

This replicates the v1.1 one-image root-scoped outcome across a small natural-image set and shows it is not tied to that single photograph. It also shows the effect depends on root-scoped settlement and the supplied adapted checkpoints. Three checkpoints are the replication units; the 24 paired image/checkpoint cells are not independent model replications.

## Interpretation limits and next work

The measured behavior is low-level spatial equivariance under one exact 180° transform after an explicit diagnostic rate refresh. BSDS image identities supply no semantic class labels here. The experiment establishes neither object/scene recognition, general visual competence, a production scheduling policy, nor CPU complexity. The result supports carrying the scope/readout interaction into further evaluation. Next test additional rotations and reflections, expand checkpoint replication, add independently labeled visual tasks, and vary threshold adaptation in a separately controlled arm.

## Reproduction artifacts

- Protocol: [v1.2 preregistration](SUBSTRATE_NATURAL_IMAGE_RATE_REFRESH_INTERVENTION_V1_2_PREREG_20260929.md)
- Runner: [capture program](../../../scripts/substrate_natural_image_rate_refresh_intervention_v1_2.py)
- Analyzer: [independent analysis](../../../scripts/analyze_substrate_natural_image_rate_refresh_intervention_v1_2.py)
- Raw capture: [144-cell data](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_2_20260929_raw.json)
- Analysis: [checks and per-image/per-checkpoint outcomes](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_2_20260929_analysis.json)
- Input lock: [sources, images, and checkpoints](../../../evaluation/substrate_capability/natural_image_rate_refresh_intervention_v1_2_20260929_lock.json)
- Earlier one-image result: [v1.1 results](SUBSTRATE_NATURAL_IMAGE_RATE_REFRESH_INTERVENTION_V1_1_RESULTS_20260929.md)

