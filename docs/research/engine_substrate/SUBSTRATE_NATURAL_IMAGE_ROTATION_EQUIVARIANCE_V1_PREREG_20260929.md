# Natural-image 180° spatial-equivariance pilot v1 preregistration (2026-09-29)

## Question and claim boundary

On natural-image patches delivered through `WaveWorld.step(frame=...)`, does the substrate's 4×4 SUnit response map transform according to the known 180° rotation of retinotopic input? This is a low-level transformation task with an exact geometric oracle. It is not object recognition or natural-image classification.

## Fixed design

- Checkpoints: the three independently adapted visual checkpoints 20260935, 20260936, and 20260937.
- Settlement: global and root-scoped variants, built with the existing paired-sheet adapter. Only the target sheet receives an image; its sibling receives a blank.
- Inputs: eight BSDS300 test photographs selected by evenly spaced indices from sorted test paths. Convert each to grayscale, resize to 16×16 with Pillow bilinear resampling, and normalize to [0,1]. The paired transform is an exact `rot90(frame, 2)` array operation. Also present a blank frame.
- Each original, rotated, and blank condition starts from an independent copy of the exact prepared checkpoint graph. Run one normal `WaveWorld.step(frame=...)` call and read the ordered 16-unit `act` and `rate` vectors.
- Matrix oracle: reshape the 16 outputs in the adapter's row-major 4×4 SUnit order. A 180° image rotation predicts a 180° rotation of this response map. Compute normalized L1 error for that permutation, and compare with the identity (no spatial transformation) mapping. Report response mass relative to the blank control to prevent a silent zero map from counting as successful transformation.
- Full matrix: 3 seeds × 2 scopes × 8 images = 48 workers; each worker has original, rotated, and blank arms.

## Integrity gates

1. Lock source, adapter, engine, checkpoint, selected image paths and bytes, preprocessing configuration, protocol, runner, and analyzer. Require source stability across two probes separated by at least 20 seconds and across the capture.
2. Verify each arm restores the exact checkpoint graph; verify exact frame-array hashes and exact pixel delivery through the production adapter.
3. Require complete worker matrix, complete 16-unit vectors, finite values, and no post-capture source drift.
4. Report both `act` and `rate` results. Summarize per image and seed/scope; do not treat 16 units within a sheet as independent samples.
5. Treat the test as exploratory. No significance claim is preregistered. A low permutation error without response mass above blank is a degenerate zero-response outcome and does not count as equivariance.

## Interpretation

The known permutation supplies an exact target for spatial equivariance on natural image inputs. Poor performance can arise from learned filter differences, global coupling, the small sheet, or adaptation mismatch; the pilot does not isolate those causes. Strong performance would establish this transformation behavior only on this eight-image sample and these three checkpoints. It would not establish semantic recognition, broad natural-image prevalence, learned frame discovery, or asymptotic tractability.

