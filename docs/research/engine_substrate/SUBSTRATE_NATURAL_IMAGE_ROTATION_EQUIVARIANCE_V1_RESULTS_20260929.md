# Natural-image spatial-equivariance pilot v1 results (2026-09-29)

## Capture and integrity

The 48-worker panel completed on eight locked BSDS300 test images, three independently adapted checkpoints, and global/root-scoped settlement. Each worker used independently restored original, 180°-rotated, and blank arms through `WaveWorld.step(frame=...)`. The corrected analysis passes 10/10 integrity checks: complete matrix, locked source and image identity, exact checkpoint graph restoration, exact pixel delivery, exact transform hashes, finite 16-unit maps, and completed steps.

The first analyzer is preserved at [analysis v1](../../../evaluation/reports/natural_image_rotation_equivariance_v1_20260929_analysis.json). It compared the runner's prepared-graph digest to the lock's checkpoint file hash and initially rejected that join. It also compared raw activity magnitude, which included the checkpoint's blank-state activity. The [corrected analyzer](../../../scripts/analyze_substrate_natural_image_rotation_equivariance_v1_corrected.py) compares graph digests with graph digests and evaluates each image response after subtracting its independent blank-arm map. The [corrected analysis](../../../evaluation/reports/natural_image_rotation_equivariance_v1_20260929_corrected_analysis.json) records both checks and the correction provenance.

## Task-level outcome

The exact expected map for a 180° image rotation is the 180° permutation of the 4×4 retinotopic unit map. For blank-subtracted `act`, root-scoped settlement favors that expected permutation over the unchanged-map control in all 24 image/checkpoint combinations (8/8 in each checkpoint). Median relative L1 error is 0.187 for the expected permutation and 1.729 for the unchanged-map control. Under global settlement, the unchanged map wins all 24; median errors are 0.852 expected-permutation versus 0.0011 unchanged-map. This is consistent with global settling suppressing the target sheet's spatially transformed response on this fixture, while root-scoped `act` preserves a map that tracks the input rotation.

The `rate` readout does not show the same behavior: the unchanged-map control wins all 24 combinations in both scopes. Median expected-permutation error is 0.787, versus 0.183 for the unchanged map. Every image changes the `act` and `rate` maps relative to its blank arm, so these comparisons are not zero-response artifacts.

These counts are descriptive; images share only three checkpoint states, so 24 combinations are not 24 independent model replications. This demonstrates low-level spatial transformation behavior for one transform, eight natural image patches, three adapted states, and two settlement scopes. It does not establish object/scene recognition, broad natural-image prevalence, learned frame discovery, or scaling. The mismatch between `act` and `rate` is an open state/readout question for the next gate.

## Reproduction artifacts

- Protocol: [preregistration](SUBSTRATE_NATURAL_IMAGE_ROTATION_EQUIVARIANCE_V1_PREREG_20260929.md)
- Capture: [runner](../../../scripts/substrate_natural_image_rotation_equivariance_v1.py)
- Original analyzer: [initial analyzer](../../../scripts/analyze_substrate_natural_image_rotation_equivariance_v1.py)
- Corrected analyzer: [blank-subtracted independent analysis](../../../scripts/analyze_substrate_natural_image_rotation_equivariance_v1_corrected.py)
- Raw data: [48-worker capture](../../../evaluation/reports/natural_image_rotation_equivariance_v1_20260929_raw.json)
- Corrected analysis: [machine-readable result](../../../evaluation/reports/natural_image_rotation_equivariance_v1_20260929_corrected_analysis.json)
- Source and data lock: [locked inputs](../../../evaluation/substrate_capability/natural_image_rotation_equivariance_v1_20260929_lock.json)

