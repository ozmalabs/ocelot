# Natural-image rate refresh multi-image replication v1.4 preregistration (2026-09-29)

## Question

Does the post-settlement `oo_sunit_rate` refresh intervention generalize from the previously measured 180° transform to an exact 90° counter-clockwise rotation across the same eight BSDS300 test images?

## Design

- Reuse exactly the eight image paths and bytes from `natural_image_rotation_equivariance_v1_20260929`, with the same grayscale bilinear 16×16 preprocessing and exact 90° pixel rotation.
- Use the same six adapted checkpoints from the v1.3.1 panel, both global/root-scoped settlement variants, blank baseline, and post-settlement intervention procedure. Every original, rotated, and blank arm starts from its exact checkpoint and runs ordinary `WaveWorld.step` first.
- Reset only the 16 target SUnits' `rate_step`, invoke the existing non-batch `oo_sunit_rate` rule until no progress (16 progressing calls plus one termination check), and compare default and refreshed output maps.
- Full matrix: 6 checkpoints × 2 scopes × 8 images × 3 inputs = 288 cells. The image-level observation is paired within checkpoint and scope; checkpoints, not cells or SUnits, define model replication. Since these are the same six states used in the 180° panel, this is a held-transform generalization test rather than a fresh checkpoint replication.

## Amendment

This panel reuses the six exact checkpoint states and source-hash protocol locked for v1.3.1. It changes the input transform and expected spatial permutation to a 90° counter-clockwise rotation. This tests transform generalization within the same adapted states; it does not add independent checkpoint replications. Imported graph state must match the locked checkpoint within 1e-12 after native floating-point round-trip serialization.

## Gates

Require source/input stability, exact checkpoint file hash and stored graph digest, graph import equivalence within 1e-12 to accommodate native JSON floating-point round trips, exact pixel delivery, complete matrix, unchanged `act`/`theta`/`act_step`, only target `rate`/`rate_step` graph changes, full no-progress termination, and exact rate equation/update stamps. Report per-image and per-checkpoint map errors, response mass above blank, and how often the expected 90° permutation beats the identity control. No significance claim is preregistered; this remains a low-level spatial task rather than semantic image recognition.

