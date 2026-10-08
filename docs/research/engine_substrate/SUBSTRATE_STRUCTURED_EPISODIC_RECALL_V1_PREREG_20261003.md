# Structured episodic recall v1 preregistration

Date: 2026-10-03  
Status: preregistered before runner implementation and capture.

## Question

When the episodic-memory rule's documented graph inputs are supplied directly, does it bind an observed fact, retrieve that fact from an exact cue, and reject an unknown cue? This isolates structured memory capability from the natural-language bridge evaluated in [counterbalanced live value recall](SUBSTRATE_LIVE_COUNTERBALANCED_VALUE_RECALL_V1_RESULTS_20261003.md).

## Conditions

Run nine fresh processes, three each for:

* `known_14`: create a `MemoryContext`, `MemorySchema`, and `EpisodicEvent` with `event_key=code-14`, `cue_key=secret-code`, `state_summary=secret code is 14`, `observation_status=observed`, and `provenance_kind=perceived`; connect the agent to the event using `experienced_event`, event to context with `in_context`, event to schema with `instantiates_schema`; tick the graph rule engine, issue `MemoryRetrievalRequest(cue_key=secret-code)`, tick again.
* `known_29`: identical structure and cue with `event_key=code-29`, `state_summary=secret code is 29`.
* `unknown_cue`: bind the same `code-14` episode, then request `cue_key=never-seen`.

Use only the `episodic_working_memory_core` seed, matching the existing structured-memory fixture. No Python memory lookup is permitted: storage, retrieval, and outcome must arise from `agent.tick()` executing graph rules. The fixture construction is mechanical input translation, as in the existing migrated memory tests.

## Exact gates

Positive arms pass only if exactly one Episode binds the supplied event/context/schema, retrieval yields exactly one RecallCandidate reconstructing that Episode/Event with the exact expected state summary, candidate `provenance_kind=recalled`, `observation_status=not_observed`, and no RecallOutcome reports insufficient information. Negative control passes only if no RecallCandidate is minted and exactly one RecallOutcome has `status=insufficient_information`, uncertainty 1.0, and `observation_status=not_observed`. Retain all raw graphs and source/worker metrics.

Require nine distinct worker PIDs, three workers per arm, source-lock stability, complete records, and exact graph digest equality within each arm. If the exact digest gate fails due to representation order, preserve that failure and use a separately documented semantic amendment. This structured fixture tests memory-rule capability, not natural-language learning or discourse integration. The existing fixture source is [test_episodic_working_memory_migrated.py](../../../tests/test_episodic_working_memory_migrated.py); production graph rule source is [episodic_working_memory_core.json](../../../seeds/episodic_working_memory_core.json).
