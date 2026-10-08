# Natural-image rate-refresh 90° generalization v1.4 results (2026-09-29)

## Integrity

The 288-cell matrix covers eight BSDS300 test images, six adapted checkpoint states, global/root-scoped settlement, and original/90° counter-clockwise/blank inputs. All seven independent gates pass: complete matrix, lock agreement and source stability, checkpoint/image/transform identity, exact pixel delivery, unchanged `act`, writes limited to target `rate`/`rate_step`, and the full termination/equation/stamp oracle. Each cell completes 16 progressing rate-rule calls and one no-progress check. The maximum rate-equation residual is 0.

The runner verifies exact checkpoint file hashes and stored graph digests, then checks graph import equivalence within 1e-12 for native floating-point serialization. These are the same six states used in the v1.3.1 180° panel; this is a held-transform generalization test, not a new checkpoint replication.

## Transform result

After post-settlement refresh, root-scoped rates favor the expected 90° spatial permutation over identity in 47/48 image/checkpoint pairs. Five of six checkpoints score 8/8; seed 20260937 scores 7/8. Every root-scoped cell has nonzero response relative to blank.

Global refresh favors the expected permutation in 0/48 pairs. It produces nonzero responses on 24/48 cells, across all eight images for seeds 20260936, 20260938, and 20260940, and none for the other three checkpoints. Identity error is zero on every nonzero global cell. Default rates favor identity in 47/48 nondegenerate cells; seed 20260939 has no default-rate response.

The 90° result (47/48 root-scoped) closely matches the 180° panel (45/48) and extends the measured spatial behavior to a second exact transform on the same adapted states. This supports held-transform generalization for one low-level rate-map task. The two panels share checkpoint states, images, preprocessing, scope variants, and diagnostic schedule intervention. They do not establish semantic object or scene recognition, performance on new checkpoints, a production scheduler policy, learned frame discovery, or general visual competence.

## Cost observations

Across 288 workers, median wall and process CPU time are about 0.62 s per cell, with peak process RSS around 199 MB. The timed region includes normal image ingestion/settling, graph capture, delivery checks, and the diagnostic rate refresh. These are local fixture costs and do not establish an asymptotic bound or broad commodity-hardware profile.

## Next work

Add independently labeled visual tasks with held-out object/scene identities and explicit chance/identity baselines. Then replicate the transform matrix with newly adapted checkpoints and separately compare production scheduling against the diagnostic post-settlement intervention. Measure frame discovery and boundary width independently from runtime cost. These task-level and structural results are still needed for general capability and cheap-cut claims.

## Reproduction artifacts

- Protocol: [v1.4 preregistration](SUBSTRATE_NATURAL_IMAGE_RATE_REFRESH_INTERVENTION_V1_4_PREREG_20260929.md)
- Runner: [capture program](../../../scripts/substrate_natural_image_rate_refresh_intervention_v1_4.py)
- Analyzer: [independent analysis](../../../scripts/analyze_substrate_natural_image_rate_refresh_intervention_v1_4.py)
- Raw capture: [288-cell data](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_4_20260929_raw.json)
- Analysis: [integrity checks and per-image/per-checkpoint outcomes](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_4_20260929_analysis.json)
- Input lock: [sources, images, and checkpoints](../../../evaluation/substrate_capability/natural_image_rate_refresh_intervention_v1_4_20260929_lock.json)
- 180° comparison: [v1.3.1 results](SUBSTRATE_NATURAL_IMAGE_RATE_REFRESH_INTERVENTION_V1_3_1_RESULTS_20260929.md)
