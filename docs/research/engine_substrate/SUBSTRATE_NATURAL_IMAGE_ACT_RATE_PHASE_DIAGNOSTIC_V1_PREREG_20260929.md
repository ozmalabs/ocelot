# Natural-image `act`/`rate` phase diagnostic v1 preregistration (2026-09-29)

## Question

At which native rule phase does the 180° spatial response seen in root-scoped `act` arise, and does `oo_sunit_rate` carry that transformed response into the reported `rate` map?

## Design

- Reuse the three frozen visual checkpoints, global/root-scoped settlement variants, and the first locked BSDS300 image (`101085.jpg`) from the natural-image equivariance pilot.
- For each seed/scope, restore the exact checkpoint independently for original, 180°-rotated, and blank inputs. Run each input once through default `WaveWorld.step`, and once through the parity-validated opt-in native rule observer. This gives 18 input conditions and 36 adapter calls.
- The observer watches `oo_sunit_rate` and the selected settlement rule, recording `act`, `theta`, `rate`, `act_step`, `rate_step`, and `aff` for both sheets after every successful whole-rule invocation. Preserve event order, pass index, progress index, and final state.
- Require exact final graph parity between default and traced calls per seed/scope/input. Require complete, nontruncated snapshots for each target-sheet SUnit.
- Compare blank-subtracted target maps at the last `oo_sunit_rate` event, the last settlement event, and final tick state. For `act` and `rate`, score expected 180° permutation against identity mapping using relative L1 error. Report update stamps and rule-event order; do not infer per-binding causality from whole-rule snapshots.

## Interpretation

This is a mechanism-localization diagnostic on one image and three checkpoints. It can locate divergence to a rule-invocation phase, but it cannot prove per-binding write order, semantic recognition, natural-image prevalence, or scaling. Results remain descriptive at checkpoint level.

