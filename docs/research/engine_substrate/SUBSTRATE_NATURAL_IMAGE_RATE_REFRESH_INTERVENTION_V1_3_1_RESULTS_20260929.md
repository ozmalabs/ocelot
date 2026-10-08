# Natural-image rate-refresh multi-image replication v1.3.1 results (2026-09-29)

## Integrity

The confirmatory 288-cell matrix covers eight BSDS300 test images, six independently adapted checkpoints (seeds 20260935–20260940), global and root-scoped settlement, and original/180°-rotated/blank inputs. All seven independent integrity gates pass: complete matrix; lock agreement and source stability; checkpoint, image, and transform identity; exact pixel delivery; unchanged `act`; intervention writes restricted to target `rate`/`rate_step`; and the full no-progress/rate-equation/stamp oracle. Each intervention makes 16 progressing rule calls and confirms no progress on the next call. The maximum rate-equation residual is 0.

The first v1.3 attempt completed 144 cells and stopped at seed 20260938 because strict graph re-serialization digest equality rejected harmless double-precision round-trip differences. The checkpoint file hash and saved graph digest were intact. That partial capture and its lock are preserved as exploratory artifacts and excluded from this analysis. V1.3.1 verifies the exact source checkpoint hashes and stored graph digests, then checks imported graph equivalence within 1e-12. Its source lock remained stable through all 288 cells.

## Spatial result

After refresh, root-scoped rates favor the expected 180° permutation over identity in 45/48 image/checkpoint pairs. Each checkpoint succeeds on 7/8 or 8/8 images: seeds 20260935, 20260937, and 20260940 each score 7/8; seeds 20260936, 20260938, and 20260939 each score 8/8. All 48 cells have nonzero response relative to blank. This reproduces the v1.2 effect across the three newly adapted checkpoints and strengthens the result from three to six checkpoint replication units.

Global refresh favors the expected permutation in 0/48 pairs. It produces nonzero response in 24/48 cells: all eight images for seeds 20260936, 20260938, and 20260940, and no response for the other three checkpoints. On every nonzero global cell, identity error is zero and the expected-permutation error is positive. Before refresh, both scopes favor identity in 44/48 nondegenerate cells; four cells favor the expected transform, two each under seeds 20260938 and 20260939. Seed 20260939 has only two nondegenerate default-rate cells.

This is evidence for a scope- and phase-dependent low-level spatial transform response under an explicit post-settlement rate-rule refresh. It is not semantic vision, object/scene recognition, production scheduler behavior, a complexity bound, or a measure of learned cheap-cut prevalence. Image/checkpoint pairs are repeated observations within only six adapted states; they must not be treated as 48 independent model replications. The transform is one exact 180° rotation and the images carry no task labels.

## Cost observations

Across the 288 isolated cells, median intervention-worker wall time is 623 ms (range 459–2,406 ms; 95th percentile 1,296 ms), and median process CPU time is 623 ms. Peak process RSS reaches about 199 MB. The timed section includes `WaveWorld.step`, graph snapshots, input-delivery checks, and the diagnostic refresh; these are fixture-specific costs, not per-token or engine-only costs. Most wall time tracks CPU time in this local run, but this does not establish scaling behavior or commodity-hardware performance generally.

## Next work

Test additional rotations and reflections with independent checkpoint replication, then add independently labeled object/scene and compositional visual tasks with held-out identities and explicit chance/identity controls. Keep production adapter behavior separate from diagnostic rate refresh. In parallel, measure frame discovery and separator/boundary width on task-derived graphs, and relate those widths to exact inference or scoped-closure cost. This visual panel does not close the substrate's rung-three/four induction gap or establish tractability of the general architecture.

## Reproduction artifacts

- Protocol and amendment: [v1.3.1 preregistration](SUBSTRATE_NATURAL_IMAGE_RATE_REFRESH_INTERVENTION_V1_3_1_PREREG_20260929.md)
- Runner: [capture program](../../../scripts/substrate_natural_image_rate_refresh_intervention_v1_3_1.py)
- Analyzer: [independent analysis](../../../scripts/analyze_substrate_natural_image_rate_refresh_intervention_v1_3_1.py)
- Raw capture: [288-cell data](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_3_1_20260929_raw.json)
- Analysis: [checks and per-image/per-checkpoint outcomes](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_3_1_20260929_analysis.json)
- Input lock: [sources, images, and checkpoints](../../../evaluation/substrate_capability/natural_image_rate_refresh_intervention_v1_3_1_20260929_lock.json)
- Exploratory v1.3 partial capture and lock: [partial data](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_3_20260929_exploratory_partial.json), [lock](../../../evaluation/substrate_capability/natural_image_rate_refresh_intervention_v1_3_20260929_exploratory_lock.json)
- Prior three-checkpoint replication: [v1.2 results](SUBSTRATE_NATURAL_IMAGE_RATE_REFRESH_INTERVENTION_V1_2_RESULTS_20260929.md)
