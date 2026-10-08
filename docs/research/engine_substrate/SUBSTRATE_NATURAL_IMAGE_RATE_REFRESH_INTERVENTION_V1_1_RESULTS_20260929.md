# Natural-image post-settlement rate refresh v1.1 results (2026-09-29)

## Outcome

V1.1 passes all 7 integrity checks over 18 seed/scope/input cells. Each cell begins from the exact checkpoint, presents the original BSDS image, its exact 180° rotation, or blank through the ordinary `WaveWorld.step`, then resets only target `rate_step` and repeatedly invokes the existing `oo_sunit_rate` rule. The non-batch rule requires exactly 16 progressing invocations (one per target SUnit), followed by a no-progress termination call, in every cell.

The intervention's graph delta is restricted to target `rate` and `rate_step` fields; node and edge inventories remain exact. Target `act`, `theta`, and `act_step` remain unchanged. After refresh every target rate equals `max(act-theta,0)` within 1e-9, and every `rate_step` equals the Retina's current step. The default-rate arm remains the untouched post-tick state.

## Task outcome

Default rates favor the unchanged map in all three checkpoints under both global and root-scoped settlement. After refresh, root-scoped rates favor the expected 180° permutation in all three checkpoints. Median expected-permutation versus identity relative-L1 errors are 0.724 versus 0.935. Blank-subtracted response is nonzero in every root-scoped checkpoint (original L1 15.6–19.1; rotated L1 22.9–49.1).

For global settlement, refresh produces zero blank-subtracted rates in two checkpoints and a high-magnitude but non-equivariant response in the third. Its median expected-permutation error is 0 because two comparisons are degenerate zero/zero; no global equivariance is supported. This confirms that refreshing after settlement can recover the rotation map in the root-scoped condition on this one image, while global settlement still blocks useful transformed output for most checkpoints. It is a narrow schedule-intervention result, not a general scheduler recommendation.

## Protocol correction and limits

The first v1 capture called the non-batch rule once. The engine API's `apply_rule_batch` behaves like `apply_rule_once` for non-batch rules, so that run updated only a subset of target units. Its raw capture and failing analysis are preserved at the v1 paths; the analyzer rejected its equation/stamp checks. The v1.1 amendment repeats the rule to no progress and confirms complete refresh. No source, checkpoint, image, or other task factor changed.

The tested intervention runs after normal settlement and is not a production schedule change. It uses one BSDS image and three adapted checkpoints. Further work must test additional images and transforms, evaluate independent semantic labels, and assess the effect of updating per-unit thresholds. No claim about general natural-image recognition or tractability follows.

## Reproduction artifacts

- Original preregistration and correction record: [v1 protocol](SUBSTRATE_NATURAL_IMAGE_RATE_REFRESH_INTERVENTION_V1_PREREG_20260929.md), [v1.1 amendment](SUBSTRATE_NATURAL_IMAGE_RATE_REFRESH_INTERVENTION_V1_1_AMENDMENT_20260929.md)
- Capture and analysis: [v1.1 runner](../../../scripts/substrate_natural_image_rate_refresh_intervention_v1_1.py), [v1.1 analyzer](../../../scripts/analyze_substrate_natural_image_rate_refresh_intervention_v1_1.py)
- Raw capture and analysis: [18-cell data](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_1_20260929_raw.json), [analysis](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_1_20260929_analysis.json)
- Input lock: [locked v1.1 sources and data](../../../evaluation/substrate_capability/natural_image_rate_refresh_intervention_v1_1_20260929_lock.json)
- Preserved v1 failure: [raw capture](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_20260929_raw.json), [analysis](../../../evaluation/reports/natural_image_rate_refresh_intervention_v1_20260929_analysis.json)

