# Conversational Manifold Phase 0 Evaluation Contract

This is the Phase 0A/0B evaluation contract. It evaluates communication
events as cognitive events rather than comparing generated wording.

## Corpus

`tests/fixtures/conversational_manifold/phase0_events.json` uses
`communication_event_corpus.v1`. The current corpus contains 74 records,
within the planned 60–100 range. Each event independently records:

- literal form;
- communicative force;
- cognitive goal;
- grounding status;
- interaction relation;
- evidence kinds; and
- expected cognitive state.

`event_mode` distinguishes `non_turn` from `turn_compatible`. The latter is a
supported coordination mode, not a requirement of the event ontology. The
corpus spans standalone, continuation, overlap, response, and partial-event
cases, with both non-turn and turn-compatible coordination modes. Turn-compatible
is an available relation, not an ontology requirement.

## Trace contract

`tests/test_phase0_evaluation_contract.py` asserts that a live event produces a
deterministic trace with an event id, signal, reply provenance, selected graph
interpretation, interaction mode, and zero teacher/LLM calls. It also checks the
available cognition-facing dimensions: neutral evidence schema, force/goal
hypotheses, grounding/gap evidence, intent, goals, mentions, concerns, parse
evidence, and reply provenance. It deliberately does not snapshot reply wording.

Candidate/lifecycle traces are conditional and cross-reference the native
Phase 4 contract at
`seeds/conversation_deliberation_phase4a.json`. The Phase 0 validator accepts
such a trace only when the runtime has actually materialized a deliberation;
it requires an observed deliberation node and checks the observed source,
candidate count, lifecycle state, completion marker, and (for a resolved
deliberation) settle-back evidence. The fixed
74-event corpus carries no synthetic candidate records. Events that do not
generate a `ThoughtManifold`/`DiscourseState` deliberation therefore have no
candidate trace, rather than an invented `no_candidate` result. The Phase 4
manifest and its native tests remain authoritative for scoring, arbitration,
rejection, execution, and counterfactual credit.

The assertions are read-only over the existing graph trace. Runtime cognition,
topic routing, and Phase 2 files are outside this slice.

## Limits of this slice

This does not provide baseline scores or a candidate trace for every event;
those would be false for events that do not generate candidates. It closes the
Phase 0 contract gap by defining the conditional cross-reference and validating
the observed Phase 4 lifecycle shape, while the corpus remains an evaluation
substrate rather than a claim that every label is already achieved by runtime.
