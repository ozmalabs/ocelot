# Phase-0 sequential location acquisition and retention v1

**Question.** Can the native phase-0 visual-learning rules acquire a second stable burst location while retaining a first location in the same four-unit population, and does the result depend on training order?

**Design.** Six fresh workers cross three deterministic initialization seeds (0/1/2) with the two orders `(5,5)→(12,12)` and `(12,12)→(5,5)`. Each stage presents one fixed 5×5 active patch for 4,000 Eye-clock steps. The activity count is exactly 25 at every step. Use the unchanged `vision_waves` and `vision_eye` seeds, a 16×16 retinal sheet, four WUnits, and `ph0_eta=5e-4`. At each stage boundary, capture every WUnit's 256 synaptic weights.

**Measures.** An independent analyzer recomputes each receptive-field center and weighted RMS spread from captured weights. A location is localized when at least one unit has spread below 3 cells and center distance below 1 cell. Record localization of the first location after stage 1, then both the first and second locations after stage 2, plus closure/input times, input writes, rule progress, and Argmax cache occupancy.

**Predeclared gates.** Stage 1 localizes the first trained location for all six workers; stage 2 localizes the second location and retains the first for all six workers; both training orders must meet all gates. The runner also requires exact 25-cell activity, full 4,000-step progress in each stage, nonempty Argmax state, and stable source hashes. Failed cases remain in the capture and are not repaired post hoc.

**Limits.** This tests two fixed locations in one authored visual rule family with four units. It does not establish natural-image recognition, capacity beyond two patterns, generalization across visual feature classes, cross-domain transfer, or general self-improvement. Timing is descriptive on one host; graph construction is excluded.

**Execution.** Lock with `python3 evaluation/substrate_capability/vision_eye_phase0_sequential_location_transfer_v1.py --lock`, execute the runner, then execute `python3 evaluation/substrate_capability/analyze_vision_eye_phase0_sequential_location_transfer_v1.py`. Keep the lock, capture, and analysis immutable.
