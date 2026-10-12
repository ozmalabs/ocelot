# Semantic ingress source audit

Date: 2026-10-03  
Scope: source contract for the semantic-event ingress, as a follow-up to the live/structured episodic-memory boundary audit. This is a source audit, not a new runtime measurement.

## Finding

`WorldAdapter.ingest_semantic_event(frame, provider=...)` is a supported callable boundary for already-adapted semantic evidence. It validates a mapping, converts neutral communicative evidence, creates a `SemanticEventFrame`, `CommunicationInterpretation`, and discourse event, runs native rules, and returns their graph handles. It deliberately rejects a raw string as its frame and does not create a `Message`, call `converse`/`comprehend_text`, derive meaning from surface language, select a reply, or produce one (`reply` is `None`). See [`WorldAdapter.ingest_semantic_event`](../../../substrate/world_adapter.py) and [`from_semantic_frame`](../../../domains/communication_evidence.py).

When the caller also supplies `frame["proposition"]`, the ingress passes that payload to `bridge_proposition_evidence`. The bridge requires a neutral schema, predicate, role arguments, polarity, provider, and evidence ID. It rejects text and parse fields and performs no lexical or semantic interpretation. With valid evidence it can materialize a `Proposition`, `PropositionEvidence`, argument nodes, and provenance edges. It leaves uptake and truth distinct: a proposed claim is not accepted merely because it was materialized. See [`bridge_proposition_evidence`](../../../domains/proposition_commitment.py).

The tests establish the API boundary: raw text raises `TypeError`; an unsupported communicative frame raises `ValueError`; explicitly supplied neutral proposition data is preserved/materialized; and lifecycle uptake requires its separate signal and native rule path. Existing source-level fixtures do not establish that ordinary text conversation invokes this ingress. A caller search finds the method definition and tests/evaluators, but no production caller in `substrate/` beyond its own definition. See [`test_semantic_event_ingress.py`](../../../tests/test_semantic_event_ingress.py), [`test_language_neutral_evidence_arbitration.py`](../../../tests/test_language_neutral_evidence_arbitration.py), and [`proposition_event_commitment_measurement.py`](../../../evaluation/proposition_event_commitment_measurement.py).

## Capability boundary

This is a useful integration seam for a gradual responsibility transition: an external language or sensor adapter may propose a typed event; the substrate can record provenance, arbitrate communicative evidence, apply native lifecycle rules, and expose resulting graph state. Current evidence assigns extraction and neutral proposition construction to that upstream provider. It does not show substrate-led natural-language extraction, provider verification, or autonomous creation of new ontology dimensions. An explicit `provider` string records attribution but is not authentication; the adequacy/provider-authentication studies remain the relevant evidence for that limitation.

## Next measurement gate

Use the same counterbalanced fact/query panel across three independently scored stages:

1. **Text extraction:** pass raw statements through the ordinary text route; score predicate, argument/value, polarity, source, ambiguity, and exact value against a locked oracle. Include paraphrase, negation, swapped values, malformed and ambiguous statements.
2. **Neutral semantic ingress:** feed the intended typed proposition to `ingest_semantic_event`; score materialization, event linkage, provenance, no-op rejection for invalid records, and non-acceptance absent uptake. This isolates the substrate's adapter contract from the extractor.
3. **Integrated memory:** connect an explicitly accepted, supported semantic event to the episodic binding path; ask a counterbalanced follow-up through the live query route; separately score retrieval request creation, exact candidate, unknown-cue abstention, and response generation.

Keep the explicit-semantic arm and raw-text arm separate in reported capability claims. Do not attribute adapter-supplied extraction to the substrate. Record input/output graph digests and source locks, worker identity, stage-specific latency, and memory, so failures identify the boundary where capability stops. The preceding episodic audit found the structured memory rules work on explicit graph inputs, while the tested natural-language conversation did not create those inputs or a retrieval request ([cross-capture audit](../../../evaluation/reports/live_structured_memory_boundary_v1_audit_20261003.json); [structured-recall results](SUBSTRATE_STRUCTURED_EPISODIC_RECALL_V1_RESULTS_20261003.md)).
