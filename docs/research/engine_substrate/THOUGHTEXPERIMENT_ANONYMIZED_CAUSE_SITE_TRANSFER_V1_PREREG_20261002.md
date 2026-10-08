# Thoughtexperiment anonymized cause/site transfer v1 preregistration

## Question

Does anonymized trace-guided edit-site generation and substrate-side candidate selection transfer from the recurrence ledger to the structurally different conversation reply rule, under a matched correlated-writer and no-op control?

## Design

Repeat the v1 anonymized panel on both recurrence and multi-message conversation. Both families receive a faulty task rule, a correlated shadow writer whose guard and output use a separate shadow relation, and an empty-effect no-op writer. Rule/event names are replaced by opaque aliases before candidate discovery; the native selector receives opaque proposal IDs and host-generated exact task outcome labels. The recurrence candidate pool is generated from progressed write traces. The conversation pool is generated after one training utterance has been ingested and the native observer settles its rule closure. Candidate orders and training evidence are captured first; a separate score stage evaluates every candidate on family-specific held-outs.

Four fresh workers per family, two training repetitions and two held-out repetitions per candidate. The recurrence oracle requires exactly one mint offer per due candidate and fixed point. The conversation oracle requires exactly one reply per inbound message on two training and three held-out utterances. In each family, require complete traces, a seen shadow writer, an attempted no-op that creates no candidates, a unique exact training winner, selector agreement with that winner, selected-candidate held-out success, and tie/all-wrong abstention. Report full candidate counts and stage timings; do not compare partial timing scopes as end-to-end costs.

## Interpretation boundary

This tests transfer between two authored task families, not an open distribution. Task setup, candidate scoring, labels, and oracle remain harness supplied. Typed relation structure is visible to the edit generator. The observer supplies activity evidence; the separate labeled branch evaluation supplies utility evidence. Passing both families does not prove causal necessity, open-ended concept invention, autonomous self-improvement, or general capability.

## Artifacts

- Runner: [thoughtexperiment_anonymized_cause_site_transfer_v1.py](../../../evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_transfer_v1.py)
- Lock: [thoughtexperiment_anonymized_cause_site_transfer_v1_lock_20261002.json](../../../evaluation/substrate_capability/thoughtexperiment_anonymized_cause_site_transfer_v1_lock_20261002.json)
- Orders: [thoughtexperiment_anonymized_cause_site_transfer_v1_orders_20261002.json](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_orders_20261002.json)
- Scores: [thoughtexperiment_anonymized_cause_site_transfer_v1_scores_20261002.json](../../../evaluation/reports/thoughtexperiment_anonymized_cause_site_transfer_v1_scores_20261002.json)
- Analysis: [analyze_thoughtexperiment_anonymized_cause_site_transfer_v1.py](../../../evaluation/substrate_capability/analyze_thoughtexperiment_anonymized_cause_site_transfer_v1.py)
