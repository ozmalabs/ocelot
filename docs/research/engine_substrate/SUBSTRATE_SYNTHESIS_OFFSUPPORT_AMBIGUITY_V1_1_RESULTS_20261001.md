# Synthesis off-support ambiguity v1.1 results (2026-10-01)

## Question

Does the current bounded Rung 3 synthesis route distinguish an intended square rule from another program that fits sparse examples, transfer once examples identify square, and refuse contradictory evidence? The preregistered task family uses an analytic square oracle for held-out predictions, 15 fresh workers, five repeats per task, a fixed candidate cap, and a locked randomized schedule. The v1.1 amendment adds process IDs after v1 omitted them; v1 remains diagnostic and is not pooled.

## Result

The independent analyzer passes all 10/10 v1.1 gates. All 15 workers ran in distinct processes and completed the locked schedule. On the ambiguous examples `(0,0),(1,1)`, all five workers accepted an identity-like program, the sole enumerated candidate. It fits the observations, but matches 0/20 analytic square holdout predictions. This is a measured off-support false generalization relative to the experiment's declared square target; the examples alone do not identify that target, so the result does not establish that identity selection is irrational under an unspecified prior.

When the training examples distinguish square, all five workers accept a `Times(x,x)`-like program and match all 20/20 held-out predictions. Median candidate count is 61. On contradictory examples, all five workers return a gap after reaching the 200,000-candidate cap (`enumerate_failed`). Median pump wall time is 266 ms, compared with 7.7 ms for the ambiguous task and 12.6 ms for the disambiguated task. Median captured process CPU times are 10.1, 14.1, and 263 ms respectively; CPU can exceed wall time due to native parallel work. Median peak RSS is 40.8, 40.1, and 66.1 MiB respectively.

## Interpretation and limits

The route can induce and transfer a small function in this fixed grammar when observations distinguish it. It has no measured policy for representing underdetermination or asking for a discriminating example: its Occam ordering accepts the simplest fitting identity program, which is predictively wrong against the external target. Contradiction handling is conservative but expensive because it exhausts the cap. This is evidence about one scalar grammar and one task family, not a general account of ambiguity, a calibrated refusal policy, open-ended primitive invention, or natural-task induction. The analytic holdout is an experimenter-declared target and measures prediction, not latent intention identification.

The v1 report's missing-process-provenance gate remains failed and disclosed in the [v1.1 amendment](SUBSTRATE_SYNTHESIS_OFFSUPPORT_AMBIGUITY_V1_1_AMENDMENT_20261001.md). See the [protocol](SUBSTRATE_SYNTHESIS_OFFSUPPORT_AMBIGUITY_V1_PREREG_20261001.md), [runner](../../../scripts/substrate_synthesis_offsupport_ambiguity_v1_1.py), [analyzer](../../../scripts/analyze_substrate_synthesis_offsupport_ambiguity_v1_1.py), [source lock](../../../evaluation/substrate_capability/synthesis_offsupport_ambiguity_v1_1_20261001_lock.json), [raw capture](../../../evaluation/reports/synthesis_offsupport_ambiguity_v1_1_20261001_raw.jsonl), and [analysis](../../../evaluation/reports/synthesis_offsupport_ambiguity_v1_1_20261001_analysis.json).

## Next measurement

Predefine the response to ambiguity as three separately scored behaviors: select under an explicit prior, request a query chosen to distinguish surviving candidates, or abstain with a gap. Compare these routes against default Occam ordering and broad enumeration under equal grammar and cost budgets. Include adversarial examples where the simplest fitting rule fails the analytic holdout, and separate predictive accuracy from identification of the experimenter's intended rule. Preserve contradiction-cap cost as its own measure. Do not claim that query selection exists until an end-to-end route is implemented and evaluated.
