# Semantic ingress contract v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_SEMANTIC_INGRESS_CONTRACT_V1_PREREG_20261003.md)  
Runner: [`semantic_ingress_contract_v1.py`](../../../evaluation/substrate_capability/semantic_ingress_contract_v1.py)  
Raw capture: [`semantic_ingress_contract_v1_raw_20261003.json`](../../../evaluation/reports/semantic_ingress_contract_v1_raw_20261003.json)

## Result

All nine rows passed the locked checks: three replicates each for a valid structured proposition, a proposition containing a forbidden text field, and a raw string supplied as the semantic frame. All ten locked hashes covering the runner, Python ingress, graph/seed wrappers, native extension, lifecycle seed, and supporting modules matched after execution.

| Condition | Gate result | Observed behavior |
|---|---:|---|
| Valid structured proposition | 3/3 | One proposition materialized per graph; `proposed` status retained; evidence and originating-event links present; no `accepted_claim` edge |
| Text-bearing proposition | 3/3 | Bridge returned unsupported; zero propositions materialized |
| Raw text frame | 3/3 | `TypeError`; graph node counts unchanged |

This is direct evidence that the substrate can execute the explicit neutral-event/proposition contract and preserve the proposed-versus-accepted distinction. The adapter supplied predicate, argument, polarity, provider, and evidence ID. Therefore the result says nothing about natural-language extraction, provider authentication, external truth, episodic retrieval, or self-directed improvement. The nine graph instances ran sequentially in one process; this is a contract check, not a throughput or independent-process reliability estimate.

The existing full-seed `proposition_event_commitment_measurement.py` was also attempted from the current worktree. Direct launch first failed because the repository was not on `PYTHONPATH`; after correcting import paths it did not complete while booting all seeds per case and was stopped. That attempt is not a substrate failure and is not used in these results. The focused assay loads only the lifecycle manifest needed to test this seam.

## Next gate

Pair this explicit-ingress baseline with a raw-text extraction panel using identical proposition targets. Score extraction separately, then measure integrated episodic write, follow-up query handoff, retrieval, and response. Include counterbalanced values, paraphrase, negation, ambiguity, unsupported facts, and wrong-context controls. Keep adapter/provider outputs attributable so that upstream extraction success is not counted as substrate learning.
