# Continuous singleton audit v1 — results

The locked post-search comparison reuses all 20 candidates and outcomes from
the amended adaptive factored-search capture. Independent analysis passed
upstream provenance, balanced-example generation, disjointness, every native
prediction and oracle label, policy stopping, and holdout rescoring.

The captured integer audit accepts 19 candidates after two matching reserve
labels: 12 are exact on the sealed fractional holdout and seven are false
acceptances. The continuous audit presents up to four task-conditioned
continuous examples, balanced between valid positives and near-miss negatives.
It asks 62 labels across the 20 panels (median four when a candidate exists),
rejects all seven false candidates to help, accepts the 12 holdout-correct
candidates, and makes zero false acceptances. The panel without a candidate
also requests help. Immediate help makes no false acceptance but declines all
20 panels; continuous confirmation preserves 12 useful accepted results.

This directly supports the diagnosis that the previous integer reserve points
were inadequate for the observed fractional generalization failures. It does
not establish an autonomous adequacy detector: the continuous examples are
generated using task-conditioned positive and near-miss templates, so the
generator has access to task structure. The study audits fixed post-search
candidates and does not feed mismatches back into branch search or repair.
Four examples still cannot certify equivalence over the real domain.

Next measure how to obtain these kinds of distinguishing examples without a
task-informed generator: compare generic domain sampling, Term-directed
proposals, and abstention on held task families, then integrate successful
residuals into resynthesis and measure net cost and adoption quality.

Artifacts: [preregistration](CONTINUOUS_SINGLETON_AUDIT_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/continuous_singleton_audit_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_continuous_singleton_audit_v1.py), [source lock](../../../evaluation/substrate_capability/continuous_singleton_audit_v1_lock_20261004.json), [capture](../../../evaluation/reports/continuous_singleton_audit_v1_20261004.json), and [analysis](../../../evaluation/reports/continuous_singleton_audit_v1_analysis_20261004.json).
