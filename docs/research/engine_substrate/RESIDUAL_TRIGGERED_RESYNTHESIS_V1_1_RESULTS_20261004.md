# Residual-triggered resynthesis v1.1 — results

The first v1 capture is retained as diagnostic only: a post-lock analyzer
correction caused its current-source gate to fail. This v1.1 capture binds the
corrected runner/analyzer and passes all six independent gates, including
source/upstream provenance, triggered cohort, first-mismatch residual replay,
acquired-example fit, candidate/selector replay, and post-decision holdout
rescoring.

The task-blind Term-conditioned audit generated an observable mismatch in 6 of
20 panels. On those six, four-branch native synthesis ran in paired arms with
0.5 seconds per branch. The no-residual control and residual arm each ended
with one holdout-correct acceptance, four false acceptances, and one help
request. Both arms produced a holdout-exact candidate in only one of six
candidate pools (the same absolute-value panel), and neither arm selected an
exact candidate in any other panel. The residual arm reduced the candidate
pool in three panels (7→7, 5→1, 7→7, 1→1, 8→4, 3→2 by panel order) and used a
median one selector label versus two for the control. These intermediate
changes did not improve final heldout correctness. Median synthesis wall time
is about 2.00 seconds per arm; the configured maximum is 2 seconds across four
branches, with truncation/partial candidate pools retained.

This assay does not show useful repair from one counterexample under the
registered small grammar and budget. It does show the residual reaches native
synthesis and changes its candidate set in some panels, while the paired
control demonstrates that this is not enough to improve adoption quality.
No proposal is installed or persisted. The next gate should diagnose search
expressivity versus selector failure, then compare cumulative budget growth
and multiple independently selected residuals against an equal-cost no-residual
control. Do not treat candidate-pool shrinkage or fewer labels as improvement
without heldout quality gains.

Artifacts: [original preregistration](RESIDUAL_TRIGGERED_RESYNTHESIS_V1_PREREG_20261004.md), [v1.1 amendment](RESIDUAL_TRIGGERED_RESYNTHESIS_V1_1_AMENDMENT_20261004.md), [runner](../../../evaluation/substrate_capability/residual_triggered_resynthesis_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_residual_triggered_resynthesis_v1.py), [v1.1 source lock](../../../evaluation/substrate_capability/residual_triggered_resynthesis_v1_1_lock_20261004.json), [v1.1 capture](../../../evaluation/reports/residual_triggered_resynthesis_v1_1_20261004.json), and [analysis](../../../evaluation/reports/residual_triggered_resynthesis_v1_1_analysis_20261004.json). The failed v1 capture and lock remain as diagnostic records and are not used by the v1.1 analysis.
