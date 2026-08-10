# Hidden-damage navigation v1 results

The preregistered primary claim **did not pass**.

The protocol hash was
`c95fdb3ee6e5b161578fa0ce6fb09e11080228845bc5db64483255933089da92`.
All 54 runs completed, every paired calibration trajectory matched exactly,
adaptive graphs updated after the change, and frozen graphs did not. Adaptive
navigation beat frozen navigation in 11 of 18 pairs. Its pooled median paired
advantage was `0.031387`, below the preregistered `0.05` gate.

Median adaptive progress was positive for each morphology. Median paired
advantages were `0.022480` for R2-D2, `0.272427` for Husky, and `-0.052086`
for Racecar. The result therefore supports neither a general cross-body damage
resilience claim nor a claim that plasticity was harmless.

## Sequencing defect exposed by the trial

The trace showed 432 `change_recalibration` actions across the 18 adaptive
damaged runs, despite a declared maximum of one nine-action cycle per run.
Inspection found an effect-order bug: the same graph production first opened
`recalibration_remaining`, then evaluated the cycle-counter expression. The
second expression saw the newly opened window, so its "open now" predicate
became false and the counter never latched.

The result remains the v1 result; it was not reclassified. The correction
writes an explicit `opened_recalibration` event to the receipt, then derives
both the window and counter from that stable event. An already-seen development
case confirmed exactly one event and nine probe actions. A new protocol with
unseen cases is required to test the corrected implementation.

Machine-readable result:
`results/embodied_damage_navigation_v1.json`.
