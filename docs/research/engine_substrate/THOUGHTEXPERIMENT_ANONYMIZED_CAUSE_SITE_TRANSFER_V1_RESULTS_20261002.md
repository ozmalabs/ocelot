# Thoughtexperiment anonymized cause/site transfer v1 results — 2026-10-02

## Result

The independent analyzer passes all 105 checks across four fresh workers in each of two task families. Every discovery replay matches its order-stage record and every source/native fingerprint matches the lock. In recurrence, 25 trace events per worker (zero drops) expose three productive opaque writer identities and produce six candidates. In conversation, 398 events (zero drops) expose seven productive writers and produce 18 candidates. Both include the correlated shadow writer; the empty-effect no-op is observed as a non-progressing attempt and yields no candidate.

Within each family and worker, two labeled training cases produce one unique candidate that is correct on every case. Native graph-Term selection chooses that candidate in all eight worker-family cells. Each selected candidate passes all two recurrence or three conversation held-out episodes in both repetitions (16/16 selected held-out episodes total). Every candidate is evaluated on held-outs; exactly one candidate per worker-family cell passes all held-outs. Tie and all-wrong controls abstain in all eight cells.

Median candidate scoring time is 5.826 ms for recurrence's six candidates and two episodes, and 601.746 ms for conversation's 18 candidates and two two-utterance episodes. Selector medians are 0.865 ms and 0.866 ms, respectively. These scopes include fresh task-context creation and candidate scoring but exclude trace discovery; conversation has more candidates and a more expensive fixture, so the raw family times are not a controlled per-candidate comparison. They exclude held-out validation and external label acquisition and do not establish total search cost.

## Interpretation and boundary

This is a successful transfer of the same anonymized trace-to-site generation and native evidence-selection path across two authored families with different graph/task structure. It shows that the substrate can rank a small, host-generated candidate set from externally supplied exact task outcomes, including under one correlated irrelevant writer and one no-op control. It does not show that write attribution alone establishes causal necessity: labels, task construction, proposal scoring, and held-out oracles are provided by the harness. The edit generator sees typed relation structure. Two families and four workers per family do not estimate natural-task success rates, open-ended induction, autonomous task discovery, self-improvement, or an overall tractability boundary.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_ANONYMIZED_CAUSE_SITE_TRANSFER_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_transfer_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_anonymized_cause_site_transfer_v1.py)
- [Lock](../../../evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_transfer_v1_lock_20261002.json)
- [Orders](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_orders_20261002.json)
- [Scores](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_scores_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_analysis_20261002.json)
