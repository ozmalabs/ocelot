# Position-held-out orientation representation v1 preregistration

## Question and claim boundary

After unsupervised phase-0 learning on balanced horizontal and vertical bars, do native WUnit activation vectors carry orientation information at retinal positions excluded from learning? The stimulus classes contain the same five active cells and share an exact centroid at every location, so active count and pixel centroid cannot reveal the label. This measures transfer in a frozen substrate representation with a simple external readout. The substrate receives unlabeled retinal bursts; class labels are used only by the preregistered offline probe. This is not an in-substrate classifier or semantic vision benchmark.

## Stimuli and schedule

Use a 16×16 Retina and eight WUnits. Each stimulus is a five-pixel horizontal or vertical bar centered at one of 16 positions on a 4×4 grid with coordinates `{3,6,9,12}`. Train on the 12 non-corner locations and test on the four corners. At a given center the two orientation masks have equal active count and identical centroid; all stimuli remain in bounds. Each of the 24 training location×orientation combinations is presented 400 times, for 9,600 training steps. Shuffle the complete balanced schedule with a seed-derived Python `random.Random`; do not send the location or orientation label to graph nodes or rules. Freeze plasticity after training.

Run six independent seeds (40–45). After freezing, present each of the 32 position×orientation combinations once through the native graph scheduler, recording all WUnit activations and winners. Capture pretraining and post-training weights, exact masks, schedule and input hashes, exposure counts, work counters, and timings.

## Readouts and controls

Primary metric: fit one nearest-class-mean decoder in native activation space using the 24 training-position probes (12 per class); evaluate the 8 probes at the four held-out corners. Use Euclidean distance, with `horizontal` as the fixed tie-break. This tests whether the unsupervised substrate representation acquired orientation information useful at unseen positions; the decoder is external and its cost/role must remain explicit.

Run the identical decoder on activations reconstructed from pretraining weights as a frozen-random-projection control. Report the centroid-only and active-count-only fixed-tie baselines (both expected to score 4/8 because the classes are balanced and matched on these quantities). A translation-aware raw-mask template matcher is a positive task control and should classify all masks exactly; it establishes that the task labels are recoverable from shape while avoiding claims that this task is intrinsically hard. Report all six seeds, held-out probe outcomes, ties, and closure/input costs; do not select thresholds after seeing outcomes.

## Integrity gates

Lock protocol, runner, analyzer, native library, engine fingerprint, seeds, seed files, adapter, world, scheduler/rewrite and persistence sources before running. Require six unique workers, exact 9,600-step schedules, 400 presentations per training pair, identical label counts, exact five-pixel masks and centroids, exact corner holdout, frozen weights, successful native probes, and stable source hashes. The analyzer recomputes all geometry, exposures, baseline readouts, and prototype scores from raw captures.

## Interpretation

High post-training held-out orientation decoding that exceeds the frozen-random control would support an acquired representation invariant to the sampled position shift. Chance performance would show that the prior location-map result does not transfer to this unsupervised orientation representation. Neither result alone generalizes to natural images, broader task distributions, autonomous experiment choice, or self-improvement.

## Reproduction

Run `python3 evaluation/substrate_capability/vision_eye_position_heldout_orientation_v1.py --lock`, then run it without arguments, followed by `python3 evaluation/substrate_capability/analyze_vision_eye_position_heldout_orientation_v1.py`.
