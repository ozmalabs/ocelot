# Vision-eye phase-0 dense-map morphology transfer v2.1 preregistration

This is the corrected in-bounds execution of the v2 protocol. The initial v2 attempt failed before training because the grid coordinate 1 placed a radius-2 mask outside the retina; see the [amendment](SUBSTRATE_VISION_EYE_PHASE0_DENSE_MAP_MORPHOLOGY_TRANSFER_V2_1_AMENDMENT_20261005.md). No failed-v2 observations are included.

**Question.** Does the square-versus-cross difference from the first phase-0 map panel persist on a shifted nine-site grid when both patterns span a 5×5 bounding box?

**Design.** Reuse six paired seeds (30–35), nine WUnits, a 16×16 retina, 4,000 contiguous presentations per site, three frozen probes per trained/held-out location, and the v1 readout. Shift the training grid from `(3,8,13) × (3,8,13)` to `(2,7,13) × (2,7,13)` and the held-out probe grid from `{5,6,10,11}²` to `{4,5,9,10}²`. Compare a filled 5×5 square (25 active cells) with a 5×5 axial cross (9 active cells: center and offsets ±1, ±2 on each axis). Hold site order, exposures, probe locations, and all other runner parameters fixed within each seed. The manipulation changes both spatial morphology and active-cell count; this panel tests transfer of the joint contrast and cannot isolate those effects.

**Scoring.** Independently reconstruct all probe activations, winners, nearest trained-site regions, exact coordinate localization, field coverage, training work, and inference work from captured weights and input masks. Report square/cross results separately, paired seed differences, and comparison with v1 as a descriptive reference. The v1 seeds are not pooled with v2.1 as independent replicates.

**Gates and limits.** Lock the v2.1 runner, analyzer, protocol, v1 capture/analysis hashes, engine/native identity, seeds, and source dependencies before running. Require 12 fresh worker processes, six complete seed pairs, exact schedule and masks, unique native winners, positive runtime progress, frozen weights, source stability, and independent activation/argmax reconstruction. This remains one authored phase-0 learner and does not establish semantic vision, natural-task capability, or general learning.

**Reproduction.** Run `python3 evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v2_1.py --lock`, then run the same script without arguments, followed by `python3 evaluation/substrate_capability/analyze_vision_eye_phase0_dense_map_morphology_transfer_v2_1.py`.
