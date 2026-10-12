# Natural-image rate refresh multi-image replication v1.2 preregistration (2026-09-29)

## Question

Does the post-settlement `oo_sunit_rate` refresh intervention measured in v1.1 generalize across the eight BSDS300 test images in the prior locked natural-image pilot?

## Design

- Reuse exactly the eight image paths and bytes from `natural_image_rotation_equivariance_v1_20260929`, with the same grayscale bilinear 16×16 preprocessing and exact 180° pixel rotation.
- Use the same three independently adapted checkpoints, global/root-scoped settlement variants, blank baseline, and intervention procedure from v1.1. Every original, rotated, and blank arm starts from its exact checkpoint and runs ordinary `WaveWorld.step` first.
- Reset only the 16 target SUnits' `rate_step`, invoke the existing non-batch `oo_sunit_rate` rule until no progress (16 progressing calls plus one termination check), and compare default and refreshed output maps.
- Full matrix: 3 checkpoints × 2 scopes × 8 images × 3 inputs = 144 cells. The image-level observation is paired within checkpoint and scope; checkpoints, not cells or SUnits, define model replication.

## Gates

Require source/input stability, exact checkpoint identity and pixel delivery, complete matrix, unchanged `act`/`theta`/`act_step`, only target `rate`/`rate_step` graph changes, full no-progress termination, and exact rate equation/update stamps. Report per-image and per-checkpoint map errors, response mass above blank, and how often the expected 180° permutation beats the identity control. No significance claim is preregistered; this remains a low-level spatial task rather than semantic image recognition.

