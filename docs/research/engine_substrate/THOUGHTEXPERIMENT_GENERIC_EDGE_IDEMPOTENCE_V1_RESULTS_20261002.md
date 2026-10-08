# Generic edge-idempotence proposal generation v1 — results

## Result

All 14 independent analysis checks pass. The benchmark never calls `_default_candidates` and never injects `dedup_identity_fix`. For each of four workers, a generic scan of the faulted rule's bound `add_edge` effects emits three guard hypotheses: `agent.observed`, `candidate.has_mint_offer`, and `episode.has_mint_offer`. The ordinary graph-Term composer contributes its fixed `add_match_guard` proposal, for four candidates total. The graph evidence selector sees only opaque digests and two training labels per candidate.

In all four workers, the selector uniquely chooses the candidate guard on `candidate.has_mint_offer` with 2/2 correct training outcomes. The other three candidates each score 0/2. The selected rule passes both disjoint held-out episodes in all workers (8/8), producing exactly one offer for each due candidate and reaching fixed point. Tie and all-wrong controls abstain. Candidate/evidence nodes remain branch-local and primary rules remain unchanged.

Median candidate scoring for all four hypotheses and two training episodes is 73.84 ms; median native-Term selection is 0.452 ms; median graph-composer proposal generation is 60.56 ms. This is evidence that a generic, manually specified AST transformation plus substrate-side selection can produce a useful recurrence repair without injecting the specialized candidate. The transformation itself is benchmark-harness code, the cue and task/oracle are host supplied, and the result is one authored recurrence family. It does not establish that the production substrate invented or learned the transformation.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_GENERIC_EDGE_IDEMPOTENCE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_generic_edge_idempotence_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_generic_edge_idempotence_v1_lock_20261002.json)
- [Training orders and outcomes](../../../evaluation/reports/thoughtexperiment_generic_edge_idempotence_v1_orders_20261002.json)
- [Held-out scores](../../../evaluation/reports/thoughtexperiment_generic_edge_idempotence_v1_scores_20261002.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_generic_edge_idempotence_v1_analysis_20261002.json)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_generic_edge_idempotence_v1.py)
