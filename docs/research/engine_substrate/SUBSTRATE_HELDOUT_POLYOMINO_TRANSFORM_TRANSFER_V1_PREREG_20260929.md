# Held-out polyomino transform-transfer panel v1 preregistration

**Question.** Does the substrate's graph-native transform recognizer identify known rotations, reflections, and recolouring when the supplied base shape belongs to a shape orbit absent from the existing six-symbol LS20 corpus?

## Task set

Use 12 manually fixed, connected monochrome polyomino shapes of sizes 5, 6, and 7, each with a trivial dihedral stabilizer and a dihedral orbit disjoint from all six shapes in `worlds.arc_ls20_scenario.CORPUS`. The exact coordinate sets are locked in the runner. For every held-out shape, evaluate all six required operators: rotate 90/180/270 degrees, reflect across row/column axes, and recolour palette value 9 to 8. The asymmetry condition ensures the five geometric operators produce distinct target shapes; recolouring also changes the exact signature.

Add one negative control per shape by appending one adjacent cell to the base. Its relation count differs from the base; the six registered transforms and translation preserve cell/relation count. A non-refusal on this control is a false acceptance. The negative-control claim is deliberately narrow and does not represent arbitrary non-transform rejection.

For each positive operator case and each negative control, capture one clean recognition and four independent noisy recognitions at pixel-noise sigma 8 and 12. Gaussian noise is generated from NumPy PCG64 with a locked seed derived from shape, case, sigma, and replicate; it is added independently to symbol and target renders before the production pixel-grid recovery and graph-native recognizer. Total: 84 shape/case groups and 756 recognizer observations (72 positive groups, 12 negative groups; 72 clean positive + 12 clean negative; 336 noisy positive + 48 noisy negative per sigma).

## Measures and interpretation

Preserve expected transform key, recognized key or refusal, exact seen cells, deterministic seed, per-call wall/CPU time, and all task coordinates. Report exact-key rate, refusal rate, wrong-key rate, and negative-control false-accept rate overall, by operator, and by held-out shape size; give Wilson intervals and per-shape results. Timing is descriptive. Do not treat repeated noisy observations of one shape/operator as independent shape families or use them to claim broad task prevalence. This is zero-shot transform transfer to new base-shape inputs, not learning new transforms or acquiring shape concepts.

Integrity gates: exactly 12 held-out shapes and 84 complete groups; all 12 shapes connected, sizes correct, asymmetric under all seven nonidentity/equivalent D4 transformations, and orbit-disjoint from the six current LS20 shapes; all six operators present exactly once per shape; every positive target recomputes exactly and is geometrically distinct; every negative control has exactly one extra adjacent relation; all 756 output rows have their required seeds and clean/noisy observation records; source/build/input lock is stable pre/post/live and native extension is fresh. Recognition accuracy is a measured outcome, not an integrity gate. Preserve refusals and wrong keys; do not tune or exclude.

## Reproducibility

Hash this protocol, runner, independent analyzer, the imported scenario/vision/runtime closure, Rust source/manifests, Python facade/extension/build manifest, recursively loaded core and shape-decoder seed closure, and direct environment script. Checkpoint each complete shape/operator (or negative-control) group. Resume only on exact lock equality. The independent analyzer recomputes shape orbits, transformations, relation counts, clean/noisy observations' cell-to-signature correspondence, and all metrics without calling the recognition or benchmark scoring functions.
