# Thoughtexperiment generic structural proposal on recurrence v1.1 — results

## Result

The corrected, source/native-locked panel captured four outcome-blind proposal orders and then four separate held-out scores. All ten analyzer checks pass. In every worker the graph-Term composer selected `mrl_offer_due_once` and `add_match_guard`, producing the same generic site, `where += Eq(Attr('agent', 'adopted_variant_probe'), True)`. The proposal preserved its receipt and the primary graph, but emitted zero offers for both held-out candidates in all four workers and therefore failed the task oracle 0/4 times. The held-out `dedup_identity_fix` reference emitted one offer for each candidate and reached zero work at fixed point in all four workers.

Median composer time was 56.85 ms. Per-worker branch creation was 0.075–0.146 ms; generic proposal patching was 0.184–3.331 ms; scoring was 0.189–0.385 ms. The outlying patch cost is retained as observed and is not treated as stable. This is a negative transfer result for the current generic operator/site vocabulary: correctly selecting the rule and broad operator family does not specify the recurrence identity or idempotent mint semantics needed by this task. The cue explicitly names the target and guard concept, and the known-positive candidate is a post-order control. Nothing here measures autonomous fault diagnosis, invention of a recurrence-specific operator, or general recurrence prevalence.

V1 produced no worker data because a command-dispatch typo stopped capture before worker 0; that failure and the corrected v1.1 are documented in the [amendment](THOUGHTEXPERIMENT_RECURRENCE_GENERAL_STRUCTURAL_PROPOSAL_V1_1_AMENDMENT_20261002.md). The original lock is preserved but is not used for outcome claims.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_GENERAL_STRUCTURAL_PROPOSAL_V1_PREREG_20261002.md)
- [V1.1 amendment](THOUGHTEXPERIMENT_RECURRENCE_GENERAL_STRUCTURAL_PROPOSAL_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_general_structural_proposal_v1.py)
- [V1.1 lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_general_structural_proposal_v1_1_lock_20261002.json)
- [Order capture](../../../evaluation/reports/thoughtexperiment_recurrence_general_structural_proposal_v1_1_orders_20261002.json)
- [Held-out score capture](../../../evaluation/reports/thoughtexperiment_recurrence_general_structural_proposal_v1_1_scores_20261002.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_recurrence_general_structural_proposal_v1_1_analysis_20261002.json)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_general_structural_proposal_v1.py)
