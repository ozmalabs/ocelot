# Native orientation association v1.2 preregistration

## Follow-up question

The v1.1 supervised graph-native readout predicted horizontal on 20/24 held-out horizontal probes and vertical on 10/24 held-out vertical probes. Does replacing the raw activation×association dot product with Euclidean distance to each class's mean activation prototype reduce this bias and improve position-held-out accuracy?

This is a post-result, hypothesis-driven follow-up. It is not confirmatory evidence for a pre-existing claim. Reuse the exact six seeds, training masks, 9,600-step schedule, supervised cue stream, phase-0 learner, association-update rule, and 32 probes per worker. Hold the 12-train/four-heldout location split and labels fixed. The only intervention is the native prediction rule.

## Locked readout

Association count `a.count` stores accumulated activation for one WUnit/class pair over the 4,800 training presentations of that class. Define each class prototype coordinate as `a.count / 4800`. At a query, score a class by the sum over its eight associations of `(current WUnit act − prototype coordinate)^2`; select the class with minimum score using native `Argmin` and its first-encountered tie behavior. No host code selects a class. Keep v1.1's raw dot-product predictions and v1's external nearest-mean / initial-projection outcomes as paired controls.

## Gates and reporting

Require the v1.1 gates plus exact schedule, learned-weight, and association-count parity with v1.1. Require one native prediction per query and no association updates during probes. Report class-stratified accuracy, per-seed paired changes against v1.1, distance ties, external controls, and closure cost. The principal question is whether the bias decreases without sacrificing total held-out accuracy; no success threshold is claimed. Since this readout follows observed v1.1 bias, report the result as exploratory.

## Interpretation

A gain would support calibrated graph-native readout for this guided task only. It would not show that the substrate invented the readout, chose the experiment, or improved its own task specification. Failure would leave the current associative representation/readout inadequate for the tested transfer panel.

## Reproduction

Use `python3 evaluation/substrate_capability/vision_eye_orientation_native_association_v1_2.py --lock`, run it without arguments, then run `python3 evaluation/substrate_capability/analyze_vision_eye_orientation_native_association_v1_2.py`.
