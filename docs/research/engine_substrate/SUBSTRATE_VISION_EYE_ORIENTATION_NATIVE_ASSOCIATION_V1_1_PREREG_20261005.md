# Native orientation association v1.1 preregistration

## Question and boundary

Can graph rules learn supervised links from current WUnit activations to orientation labels and use those links to classify centered horizontal/vertical bars at positions excluded from training? This follows the weak unsupervised-representation result with a small, explicit responsibility transfer: the experiment author supplies the association and prediction rules, and the substrate receives teacher labels during training; native graph closure stores associations and predicts test labels. This measures one authored graph-resident classifier, not autonomous rule invention or self-improvement.

## Amendment after v1 admission failure

The first source-locked v1 attempt stopped before training because its five evaluation-only relations were not in the graph grammar vocabulary (`Type-2` rejection). That failed capture is retained. V1.1 explicitly adds typed grammar productions for Eye→OrientationClass, OrientationClass→OrientationAssociation, OrientationAssociation→WUnit, Eye→OrientationQuery, and OrientationQuery→OrientationClass before installing graph facts. No seed, learner, schedule, classifier formula, outcome threshold, or sample changes. The v1.1 lock includes `grammar.rs` and `checker.rs` to cover this gate.

## Fixed panel

Reuse the position-held-out v1 task exactly: six paired seeds (40–45), eight WUnits, 16×16 Retina, 12 training positions and four held-out corners, two centered five-pixel orientations, 9,600 training steps and 400 presentations per training-position/orientation. Preserve v1's deterministic shuffled schedule and 32 post-freeze probes. The class labels are supplied only during the supervised reader-training stage as graph facts; the visual learner itself receives the same unlabeled bursting masks and settings as v1.

Install two evaluation-only graph rules. The first accumulates each current WUnit activation into that unit's association with the active class, at most once per step. The second predicts a class by `Argmax` over the two graph-resident classes, scoring each class with the sum over units of `current act × learned association count`. The rule definitions are fixed before capture, source-locked, and shared across workers. Save associations and one graph-predicted class per query. No host-side model chooses the output class.

## Comparators and scoring

Primary outcome is native graph-prediction accuracy on the eight held-out position/orientation probes per seed (48 total), reported by seed and class. Compare with the paired v1 external nearest-class-mean readout, the v1 frozen random projection, centroid and count baselines (24/48 expected), and the translation-aware pixel template (48/48 positive control). Keep post-training changes in receptive fields separate from readout changes. Include cue/rule work, closure time, and prediction abstentions/errors.

## Gates

Require stable source/native lock, six unique workers, exact paired schedule hashes against v1, exact exposures and masks, balanced supervised labels, at most one association update per unit/class/step, frozen visual weights at probes, no association increments during probes, one graph prediction per query, and independent recomputation of all baseline comparisons and aggregate metrics. Preserve a failed capture or rule error as diagnostic evidence; do not infer capability from runtime gates alone.

## Interpretation

A successful result establishes this hand-authored supervised association/readout mechanism for this task only. Since labels and rules are authored externally, it demonstrates substrate-side execution and stateful learning under guidance; it does not show independent hypothesis formation, task discovery, or self-improvement. Generalization remains bounded to the specified held-out positions, two orientations, and six seeds.

## Reproduction

Run `python3 evaluation/substrate_capability/vision_eye_orientation_native_association_v1_1.py --lock`, then run it without arguments, followed by `python3 evaluation/substrate_capability/analyze_vision_eye_orientation_native_association_v1_1.py`.
