# Accepted proposition to episode boundary v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_ACCEPTED_PROPOSITION_TO_EPISODE_BOUNDARY_V1_PREREG_20261003.md)  
Runner: [`accepted_proposition_to_episode_boundary_v1.py`](../../../evaluation/substrate_capability/accepted_proposition_to_episode_boundary_v1.py)  
Lock: [`accepted_proposition_to_episode_boundary_v1_lock_20261003.json`](../../../evaluation/substrate_capability/accepted_proposition_to_episode_boundary_v1_lock_20261003.json)  
Raw capture: [`accepted_proposition_to_episode_boundary_v1_raw_20261003.json`](../../../evaluation/reports/accepted_proposition_to_episode_boundary_v1_raw_20261003.json)

## Result

All nine rows passed integrity gates and all ten locked hashes matched before and after execution. The controlled provider supplied two counterbalanced secret-code propositions and one gate-state proposition. Native lifecycle rules accepted all 9/9 after the explicit `accept` signal, and all 9/9 propositions retained their source semantic-event link.

Across all nine graphs, the following counts were zero: `EpisodicEvent`, `MemoryContext`, `MemorySchema`, `Episode`, `MemoryRetrievalRequest`, `RecallCandidate`, and `RecallOutcome`. The episodic memory seed was loaded in each graph. Thus, accepted proposition materialization plus lifecycle uptake does not automatically enter the tested episodic-memory path. That path still requires explicit event/context/schema relations and a separate retrieval request, as shown by the [structured episodic recall benchmark](SUBSTRATE_STRUCTURED_EPISODIC_RECALL_V1_RESULTS_20261003.md).

## Capability implication

The measured system boundary is now clearer: the substrate can preserve and accept a provider-authored neutral proposition; it can bind/retrieve memory when explicit episodic graph inputs exist; the integration that turns an accepted semantic proposition and its provenance into a properly sourced memory event is absent in this route. Acceptance is not itself a sensor observation, so any future bridge must preserve the distinction between accepted communication and observed experience rather than relabel claims as observations.

This was a three-shape, nine-graph integration probe, not a general semantic-memory result. No text extraction, external provider, language model, or truth oracle was tested.

## Next gate

Specify a typed proposition-to-memory bridge contract before implementation: required source class, speaker/observer attribution, event/context/schema derivation, and whether claims from communication are eligible for episodic storage under a non-observed provenance status. Then measure safe storage and later retrieval with accepted, challenged, retracted, ambiguous, and directly observed inputs separately. Do not represent a communicated or accepted claim as a direct observation.
