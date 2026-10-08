# Accepted proposition to episode boundary v1 preregistration

Date: 2026-10-03  
Runner: [`accepted_proposition_to_episode_boundary_v1.py`](../../../evaluation/substrate_capability/accepted_proposition_to_episode_boundary_v1.py)  
Lock: [`accepted_proposition_to_episode_boundary_v1_lock_20261003.json`](../../../evaluation/substrate_capability/accepted_proposition_to_episode_boundary_v1_lock_20261003.json)

## Question

When a neutral proposition is explicitly supplied and native uptake accepts it, do the existing rules automatically create the observed-event, context, schema, episode, or retrieval structures needed by episodic memory?

## Design

Run three fresh graphs for each of three accepted propositions: two counterbalanced `has_secret_code` values (14 and 29) and a `state_open(user, gate)` proposition. Each graph loads the episodic memory seed and proposition commitment lifecycle rules. The semantic adapter explicitly supplies an affirmed proposition with `commitment_status=proposed` and `uptake_signal=accept`; the normal `ingest_semantic_event` path performs graph materialization and native rules. After another native rule pass, record proposition status, event provenance, and counts of `EpisodicEvent`, `MemoryContext`, `MemorySchema`, `Episode`, `MemoryRetrievalRequest`, `RecallCandidate`, and `RecallOutcome`.

The runner writes no episodic-memory input node, context, schema, or request. The positive control is successful proposition acceptance plus its event provenance. The separate structured-recall benchmark is the control showing that explicit memory graph inputs activate memory rules.

## Gates and interpretation

All nine propositions must materialize, transition to accepted through the explicit native `accept` signal, and retain their originating semantic event. Report the memory node counts without treating expected absence as a measurement crash. A zero `EpisodicEvent` count means this selected semantic-ingress/lifecycle route did not activate episodic binding; it does not show that memory rules fail when their required graph facts are supplied.

## Limits

This is a bounded integration test over three authored proposition shapes. Provider output is explicit and trusted only for this controlled input; the assay does not assess language extraction, provider authentication, or factual truth. It tests an event-to-memory transition, not retrieval or response generation.
