# Thoughtexperiment anonymized cause/site discovery v1 results — 2026-10-02

## Result

All 52 independent analysis checks pass across four fresh workers. The trace contains 25 firing records per worker, with no dropped events. Three opaque productive writer identities appear: the faulty offer writer, a correlated shadow writer using the same bindings, and another productive recurrence writer. The explicit empty-effect no-op appears in the attempt trace but contributes no write site. Discovery generates six edge-identity candidates, three from the faulty offer rule and three from the shadow writer; its inputs contain opaque aliases rather than original rule names, and the native selector receives opaque proposal IDs plus task-outcome evidence.

Training produces one unique all-correct candidate in every worker. Native graph-Term selection chooses it in all four workers. The selected edit comes from the faulty offer writer and passes both disjoint held-out episodes in all four workers; all six candidates are scored on held-outs. Tie and all-wrong controls abstain in every worker. Median training scoring over the six candidates and two episodes is 5.934 ms; median selector time is 0.833 ms. These timings exclude task/fixture setup, trace capture, candidate discovery, held-out scoring, and the external cost of producing labels, and must not be read as end-to-end cost.

## Interpretation

This advances beyond the v1 site-discovery pilot: semantic rule identifiers no longer enter discovery, a correlated productive writer expands the candidate pool, and a no-op writer is rejected by the progress/write gate. It demonstrates evidence-guided repair selection from a six-candidate set on one authored recurrence family. It does not establish causal necessity from trace data alone: the graph-Term selector uses externally generated exact task labels, and the harness constructs the task, confounder, candidate scoring and held-out oracle. Relation labels and rule structure remain visible to the edit generator, so this is not semantic cue blindness. No broad task distribution, open-ended grammar induction, autonomous task selection, or self-improvement is shown.

## Artifacts

- [Protocol](THOUGHTEXPERIMENT_ANONYMIZED_CAUSE_SITE_DISCOVERY_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_discovery_v1.py)
- [Lock](../../../evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_discovery_v1_lock_20261002.json)
- [Orders](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_orders_20261002.json)
- [Scores](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_scores_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_discovery_v1_analysis_20261002.json)
