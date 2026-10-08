# Native candidate-adequacy gate v1 results

## Integrity

All 15 source-locked workers complete, and the independent analyzer passes all 13 checks. It reconstructs candidate predictions, validation scores, threshold states, and selector outcomes; verifies task identity is absent from the graph; and confirms evaluation labels are revealed only after predictions or refusals are captured.

## Threshold outcome

The preregistered threshold is 24/32 validation agreements. It accepts all ten in-menu panels and correctly selects the target family in all ten: additive 5/5 and product 5/5. It also falsely accepts all five componentwise-opposition panels as adequate. Their best candidate scores are 25–31/32, even though neither candidate is exact on the 1,296-row evaluation grid in any opposition panel. The opposition validation labels are highly imbalanced: four panels contain 31 negatives and one positive, while the fifth contains 29 negatives and three positives. A near-constant false predictor can therefore clear the raw-accuracy threshold. The selected false-family candidate happens to be correct on 5,974/6,480 opposition-grid rows (92.2%), demonstrating why aggregate accuracy alone can obscure a missing relation family.

Thus false mismatch on the positive controls is 0/10, but false acceptance on the out-of-menu challenge is 5/5 and mismatch detection is 0/5. A fixed 75% raw-agreement threshold does not diagnose candidate-space failure on these imbalanced panels. The protocol gate was executed faithfully; the adequacy policy failed its stated purpose.

Median validation closure is 0.340 ms, score closure 0.151 ms, diagnosis closure 0.065 ms, and selection commit closure 0.105 ms. Median worker CPU is 112.7 ms and peak RSS is 44,832 KiB. These are small-fixture measurements.

## Interpretation and next gate

Native graph rules can apply a supplied score threshold and suppress no outputs only when the score is below that threshold. This proves execution of the policy, not that the policy measures adequacy. The opposition panels expose a distribution-shift and model-adequacy gap: the validation pool rewards candidate behavior that is common in the pool, while the finite evaluation grid exposes systematic misses.

Do not tune the threshold against these outcomes and present it as confirmatory. The next prospective gate should use newly generated, task-identity-blind challenge pools with balanced positive/negative labels and coverage-directed boundary/zero cases; include multiple out-of-menu relation families and matched in-menu controls. Compare raw accuracy with balanced accuracy or class-stratified adequacy criteria, and include an explicit abstain/help action. Keep the final evaluation domain sealed and report false acceptance, false mismatch, family coverage, and risk/coverage curves separately.

## Reproduction artifacts

- [Protocol](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/native_candidate_adequacy_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_native_candidate_adequacy_v1.py)
- [Source lock](../../../evaluation/substrate_capability/native_candidate_adequacy_v1_lock_20261005.json)
- [Raw capture](../../../evaluation/reports/native_candidate_adequacy_v1_20261005.json)
- [Analysis](../../../evaluation/reports/native_candidate_adequacy_v1_analysis_20261005.json)
