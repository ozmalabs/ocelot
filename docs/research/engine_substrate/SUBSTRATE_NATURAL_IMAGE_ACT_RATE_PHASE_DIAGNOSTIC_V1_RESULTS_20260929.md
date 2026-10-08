# Natural-image `act`/`rate` phase diagnostic v1 results (2026-09-29)

## Integrity and parity

The 18 input conditions (three checkpoints × two settlement scopes × original/rotated/blank) were each run through both default and traced adapters. All nine independent integrity checks pass, including exact default/traced final graph parity on 18/18 calls, no event truncation, exact checkpoint graph identity, complete snapshots, and observations of both the rate and settlement rules for every input.

## Where the maps diverge

After the last `oo_sunit_rate` event, blank-subtracted `act` favors the correct 180° permutation in all three checkpoints, under both global and root-scoped rule variants. The `rate` map favors the unchanged spatial map in all three checkpoints under both variants. At that post-rule snapshot, `rate = max(act-theta, 0)` has zero maximum residual across the 16 target SUnits in every input; all 16 activation/rate update stamps match. Thus the `rate` result is consistent with the declared rule equation at the point where it fires.

The event order accounts for a second mismatch: in all 18 calls, the last observed `oo_sunit_rate` event precedes the last settlement-rule event. The rate rule stamps the current step once, while settling continues to update `act` later in that same tick. Final root-scoped `act` retains the rotation map; global final `act` collapses toward the identity map. The final `rate` still reflects the earlier rate-rule phase.

As an explicitly post-hoc calculation, the analysis recomputed `max(final_act-final_theta, 0)` offline, without mutating any graph. In root-scoped mode the recomputed blank-subtracted rate map favors the rotation permutation in 3/3 checkpoints, though response magnitudes are modest (original-vs-blank L1 15.6–19.1, rotated-vs-blank 22.9–49.1). In global mode the recomputed map is zero for two of three checkpoints; the third is equivariant but the three-checkpoint result still favors neither robust generalization nor a broad capability claim. The per-unit `theta` map remains fixed across the paired frames and itself has no transformed response, so thresholding can independently reduce equivariance.

## Interpretation

This localizes the discrepancy to two concrete mechanisms: the rate rule runs before settlement finishes, and its per-unit fixed thresholds do not transform with the image. It does not establish that moving the rate phase would fix the system: the counterfactual is equation evaluation, not an executed schedule intervention. Next test a schedule intervention with exact default-path controls, then expand across additional transforms and independently labeled visual tasks. The pilot remains limited to one BSDS image and three adapted checkpoints.

## Reproduction artifacts

- Protocol: [preregistration](SUBSTRATE_NATURAL_IMAGE_ACT_RATE_PHASE_DIAGNOSTIC_V1_PREREG_20260929.md)
- Capture: [runner](../../../scripts/substrate_natural_image_act_rate_phase_diagnostic_v1.py)
- Primary analysis: [phase and parity analyzer](../../../scripts/analyze_substrate_natural_image_act_rate_phase_diagnostic_v1.py)
- Supplemental post-hoc analysis: [v1.1 analyzer](../../../scripts/analyze_substrate_natural_image_act_rate_phase_diagnostic_v1_1.py)
- Raw data: [18 traced/default pairs](../../../evaluation/reports/natural_image_act_rate_phase_diagnostic_v1_20260929_raw.json)
- Primary analysis data: [integrity and phase results](../../../evaluation/reports/natural_image_act_rate_phase_diagnostic_v1_20260929_analysis.json)
- Supplemental analysis data: [ordering and recomputation results](../../../evaluation/reports/natural_image_act_rate_phase_diagnostic_v1_1_analysis_20260929.json)
- Source lock: [locked inputs](../../../evaluation/substrate_capability/natural_image_act_rate_phase_diagnostic_v1_20260929_lock.json)

