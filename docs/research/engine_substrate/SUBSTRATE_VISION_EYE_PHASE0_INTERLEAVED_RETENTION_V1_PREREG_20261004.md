# Phase-0 blocked versus interleaved location retention v1

**Question.** Does phase-0 learning retain two learned locations when inputs are interleaved one step at a time, compared with blocked sequential training, given the same 4,000 exposures per location?

**Design.** For seeds 0/1/2, run fresh paired graphs under two schedules. Blocked presents location A `(5,5)` for 4,000 steps then B `(12,12)` for 4,000. Interleaved alternates A and B each step for 8,000 steps. Each location therefore occurs 4,000 times in both arms. A 16×16 retina, four WUnits, 5×5 patch, fixed 25 active cells, and unchanged `vision_waves`/`vision_eye` seed rules are used. Capture all four receptive fields after 4,000 and 8,000 total steps.

**Scoring.** Independently recompute weighted center and RMS spread from all 256 captured weights per unit. A pattern is retained when at least one unit has spread <3 cells and center distance <1 cell. At the midpoint, interleaved has 2,000 exposures per site, while blocked has only completed A; at the endpoint both modes have 4,000 exposures per site. Record closure/input costs separately, exact exposure counts, progress, and evaluator-generated Argmax occupancy.

**Predeclared gates.** All six workers pass source stability, exposure schedule, active-count, progress, and cache gates. By step 8,000, all three blocked and all three interleaved populations must localize both patterns. Midpoint scores are reported as acquisition diagnostics; no pass criterion is imposed on interleaved midpoint performance.

**Limits.** This tests two fixed spatial patterns in one authored visual subsystem with four units. It does not test a larger pattern library, noisy/rotated features, natural images, or general self-improvement. Times are descriptive on one host; construction is excluded.

**Execution.** Lock with `python3 evaluation/substrate_capability/vision_eye_phase0_interleaved_retention_v1.py --lock`, run the capture, then run `python3 evaluation/substrate_capability/analyze_vision_eye_phase0_interleaved_retention_v1.py`. Keep artifacts immutable.
