# Phase-0 morphology transfer v2.1 amendment

The first v2 capture attempt failed before any training update. Its proposed training grid included coordinate 1 while using masks with radius 2, producing negative retina indices; all 12 workers exited at the first mask write. The failed capture is preserved at [`vision_eye_phase0_dense_map_morphology_transfer_v2_20261005.json`](../../../evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_20261005.json). It contains no valid worker outcomes and is excluded from capability analysis.

The corrected v2.1 grid is `(2,7,13) × (2,7,13)`, which keeps the 5×5 masks within the 16×16 retina while shifting the site arrangement from v1. The held-out grid and all other registered factors remain unchanged. The corrected run uses a new runner, source lock, capture, and analysis; the failed v2 artifacts remain immutable.
