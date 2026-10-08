# Thoughtexperiment attribute-site cue ablation v1 — preregistration

## Question

Does the current structural composer select an ordered attribute-swap site from the residual when the cue omits the direction, or does it abstain on the resulting tie? This isolates the boundary between cue-conditioned selection and site discovery.

## Fixture and cue conditions

Use the same synthetic `classify_meter_delta` fault fixture as attribute-site active-query v1, which has two ordered swap candidates (`bad_score -> good_score` and its reverse). Each cue is run on a fresh substrate in four workers. Compare: (A) answer-bearing `classify meter delta swap attribute bad_score to good_score`; (B) direction-omitted `classify meter delta swap attribute`; (C) source-only `classify meter delta swap attribute bad_score`; (D) destination-only `classify meter delta swap attribute good_score`. The composer receives no oracle labels, candidate outcomes, or held-out cases. Capture whether it builds or abstains, selected rule/operator/site where present, elapsed composition time, and whether the primary rule remains unchanged. Independently enumerate generic host candidates only to confirm both ordered swap candidates are available; this is a fixture-validity check, not substrate selection.

## Predictions and interpretation

The site-selection hypothesis predicts A selects `bad_score -> good_score`, while B–D abstain because the graph Term sees a tie between opposite ordered sites. Site discovery would require a cue without orientation to select the semantically useful candidate using other evidence; this experiment supplies no such evidence and cannot support that stronger claim. The test passes as a boundary characterization if all workers reproduce A's selection and B–D abstention, both ordered candidates exist, and the primary rule is unchanged in every condition. Any other outcome is reported without changing thresholds.

## Scope and reproduction

This is a small source-locked diagnostic, not a capability improvement or performance benchmark. It tests ordinary composer behavior and does not let an oracle select among candidate proposals. Record exact source and native-binary hashes, per-worker outcomes, and an independent analyzer. Execute the preregistered runner's `--lock`, then `--capture`, then its analyzer. The next capability gate should expose candidate alternatives to isolated prediction and active query selection without encoding the correct direction in the cue.
