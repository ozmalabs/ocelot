# Phase-0 spatial pattern learning transfer v1

**Question.** Does native phase-0 learning localize a receptive field to a stable burst patch at more than one retinal position, and does localization depend on stable spatial correlation when the active-cell count is held constant?

**Design.** Cross two patch centers, `(5,5)` and `(12,12)`, three deterministic initialization seeds (0/1/2), and two input conditions (fixed patch; temporally shuffled 25-of-256 active cells), yielding 12 fresh graphs. Each graph has a 16×16 retina, four all-to-all WUnits, and 4,000 Eye-clock steps. The fixed arm repeats the same 5×5 patch. The shuffled arm samples exactly 25 active cells without replacement at each step. Both use the unchanged `vision_waves` and `vision_eye` rule manifests and `ph0_eta=5e-4`.

**Execution and measures.** Present activity directly as RetinaCell `bursting` graph facts, advance the Eye clock, and run native `run_rules` to a fixed point each step. Record per-unit synapse weights, independently re-derived RF center/spread, closure time, input-update time, write count, progress, cache occupancy, source rule set, and input-sequence digest. Lock engine/source/seed/protocol/runner hashes before and after. An independent analyzer recomputes RF center/spread from captured weights.

**Predeclared gates.** All 12 cases keep exactly 25 active cells at every step, load `ph0_wunit_winner`, progress through the 4,000-step horizon, and retain a nonempty evaluator-generated Argmax entry. All six fixed-patch cases must have at least one unit with RF spread below 3 cells and center within 1 cell of the patch center. No shuffled case may meet that localization criterion. Any failed gate is retained as a measured result; do not change thresholds after capture.

**Limits.** This is a small authored visual-learning workload, not a natural-image benchmark or a general induction result. The stable-versus-shuffled contrast tests spatial correlation at matched activity count; it does not isolate every temporal or biological variable. Timing is descriptive on one host; graph construction is excluded. The direct graph-fact/native-closure path isolates the rule mechanism and is not a full production sensory-ingress measurement.

**Execution.** Lock with `python3 evaluation/substrate_capability/vision_eye_phase0_pattern_learning_v1.py --lock`, run without arguments, then run `python3 evaluation/substrate_capability/analyze_vision_eye_phase0_pattern_learning_v1.py`. Preserve all captures and analysis, including failures.
