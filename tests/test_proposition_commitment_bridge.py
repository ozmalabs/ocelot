"""Focused tests for the bounded neutral proposition bridge."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains.proposition_commitment import (
    EVIDENCE_KIND,
    EVIDENCE_SCHEMA,
    PROPOSITION_SCHEMA,
    bridge_proposition_evidence,
    apply_situation_consequence,
)
from substrate.seed_loader import manifest_for
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


class _Agent:
    def __init__(self, substrate, node):
        self.s = substrate
        self.inner = substrate._inner
        self.agent = node


def _fresh():
    substrate, node = boot_core(seeds=())
    return _Agent(substrate, node)


def _evidence(**updates):
    result = {
        "schema": EVIDENCE_SCHEMA,
        "kind": EVIDENCE_KIND,
        "predicate": "located_at",
        "arguments": {"theme": "glass", "location": "floor"},
        "polarity": "affirmed",
        "provider": "neutral_semantic_adapter",
        "evidence_id": "semantic-001",
        "confidence": 0.9,
        "commitment_status": "proposed",
    }
    result.update(updates)
    return result


def test_supported_neutral_evidence_materializes_proposition_and_attribution():
    agent = _fresh()
    speaker = agent.s.add_node("Interlocutor", {"name": "speaker"})
    addressee = agent.s.add_node("Interlocutor", {"name": "listener"})
    event = agent.s.add_node("DiscourseEvent", {"schema": "discourse_event.v1"})
    ground = agent.s.add_node("CommonGround", {"schema": "common_ground.v1"})

    result = bridge_proposition_evidence(
        agent,
        _evidence(),
        speaker=speaker,
        addressee=addressee,
        source_event=event,
        common_ground=ground,
    )

    assert result["supported"] is True
    proposition = result["proposition"]
    evidence = result["evidence"]
    attrs = agent.s.node(proposition)["attrs"]
    assert attrs["schema"] == PROPOSITION_SCHEMA
    assert attrs["predicate"] == "located_at"
    assert attrs["polarity"] == "affirmed"
    assert attrs["commitment_status"] == "proposed"
    assert agent.s.node(evidence)["attrs"]["provider"] == "neutral_semantic_adapter"

    arguments = list(agent.inner.neighbours(proposition, "has_argument"))
    assert {(agent.s.node(n)["attrs"]["role"], agent.s.node(n)["attrs"]["value"])
            for n in arguments} == {("theme", "glass"), ("location", "floor")}
    assert agent.s.has_edge(proposition, "evidenced_by", evidence)
    assert agent.s.has_edge(speaker, "asserts", proposition)
    assert agent.s.has_edge(proposition, "addressed_to", addressee)
    assert agent.s.has_edge(proposition, "originated_in", event)
    assert agent.s.has_edge(ground, "contains_claim", proposition)


def test_live_neutral_events_bind_claims_to_the_addressed_common_ground():
    agent = WorldAdapter(seeds=())
    first_speaker = agent.s.add_node("Interlocutor", {"name": "first"})
    second_speaker = agent.s.add_node("Interlocutor", {"name": "second"})
    first_ground = agent.s.add_node("Interlocutor", {"name": "first_listener"})
    second_ground = agent.s.add_node("Interlocutor", {"name": "second_listener"})

    results = []
    for index, (speaker, addressee) in enumerate((
            (first_speaker, first_ground), (second_speaker, second_ground))):
        evidence = _evidence(evidence_id="scope-%d" % index)
        result = agent.ingest_semantic_event({
            "event_id": "scope-event-%d" % index,
            "communicative_force": "assertion_or_correction",
            "cognitive_goal": "update_common_ground",
            "grounding_status": "candidate_grounded",
            "proposition": evidence,
        }, provider="neutral_semantic_adapter", speaker=speaker,
           addressee=addressee, conversation_id="shared-conversation")
        results.append(result)

    first_prop = results[0]["proposition"]["proposition"]
    second_prop = results[1]["proposition"]["proposition"]
    # The public claim relation points ledger -> proposition.
    grounds = agent.s.nodes("CommonGround")
    scoped_seen = set()
    for ground in grounds:
        scope = agent.s.node(ground)["attrs"].get("scope_key")
        claims = set(agent.inner.neighbours(ground, "contains_claim"))
        if scope == "addressee:%s" % first_ground:
            scoped_seen.add(scope)
            assert first_prop in claims and second_prop not in claims
        elif scope == "addressee:%s" % second_ground:
            scoped_seen.add(scope)
            assert second_prop in claims and first_prop not in claims
    assert scoped_seen == {"addressee:%s" % first_ground,
                           "addressee:%s" % second_ground}


def test_parse_only_evidence_is_rejected_without_graph_mutation():
    agent = _fresh()
    before = {kind: len(agent.s.nodes(kind)) for kind in (
        "Proposition", "PropositionEvidence", "PropositionArgument")}

    result = bridge_proposition_evidence(agent, _evidence(
        kind="parse_only",
        predications=[["located_at", "glass", "floor"]],
    ))

    assert result["supported"] is False
    assert result["error"] == "unsupported_proposition_evidence"
    assert "surface_or_parse_fields_are_not_supported" in result["reason"]
    assert result["proposition"] is None
    assert {kind: len(agent.s.nodes(kind)) for kind in before} == before


def test_surface_or_unsupported_evidence_fails_closed_without_parse_fallback():
    agent = _fresh()
    before = {kind: len(agent.s.nodes(kind)) for kind in (
        "Proposition", "PropositionEvidence", "PropositionArgument")}

    result = bridge_proposition_evidence(agent, {
        "schema": EVIDENCE_SCHEMA,
        "kind": EVIDENCE_KIND,
        "text": "The glass is on the floor.",
        "predicate": "located_at",
        "arguments": {"theme": "glass", "location": "floor"},
        "polarity": "affirmed",
        "provider": "surface_parser",
        "evidence_id": "parse-001",
    })

    assert result["supported"] is False
    assert result["error"] == "unsupported_proposition_evidence"
    assert "surface_or_parse_fields_are_not_supported" in result["reason"]
    assert {kind: len(agent.s.nodes(kind)) for kind in before} == before


def test_replaying_evidence_id_is_idempotent_and_conflicts_fail_closed():
    agent = _fresh()
    first = bridge_proposition_evidence(agent, _evidence())
    second = bridge_proposition_evidence(agent, _evidence())
    assert second["supported"] is True
    assert second["proposition"] == first["proposition"]
    assert len(agent.s.nodes("Proposition")) == 1


def test_accepted_neutral_proposition_reuses_situation_model_rules():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), agent.agent)
    result = bridge_proposition_evidence(agent, _evidence(
        predicate="drop",
        arguments={"agent": "john", "theme": "glass"},
        commitment_status="proposed",
        uptake_signal="accept",
    ))
    proposition = result["proposition"]
    agent.inner.run_rules()
    assert agent.s.node(proposition)["attrs"]["commitment_status"] == "accepted"

    consequence = apply_situation_consequence(agent, proposition)
    assert consequence["supported"] is True
    assert consequence["ingest"]["kind"] == "change_of_state"
    assert consequence["ingest"]["state"].get("on_floor") == 1
    assert len(agent.s.nodes("SituationModelConsequence")) == 1
    again = apply_situation_consequence(agent, proposition)
    assert again["reason"] == "situation_consequence_already_applied"


def test_unaccepted_or_underspecified_proposition_cannot_change_situation_model():
    agent = _fresh()
    result = bridge_proposition_evidence(agent, _evidence(
        predicate="drop",
        arguments={"agent": "john", "theme": "glass"},
        commitment_status="proposed",
    ))
    out = apply_situation_consequence(agent, result["proposition"])
    assert out["supported"] is False
    assert len(agent.s.nodes("SituationModelConsequence")) == 0


def test_negated_proposition_cannot_mint_positive_situation_state():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), agent.agent)
    result = bridge_proposition_evidence(agent, _evidence(
        predicate="drop",
        arguments={"agent": "john", "theme": "glass"},
        polarity="negated",
        commitment_status="proposed",
        uptake_signal="accept",
    ))
    agent.inner.run_rules()
    out = apply_situation_consequence(agent, result["proposition"])
    assert out["supported"] is False
    assert "nonaffirmed" in out["reason"]
    assert len(agent.s.nodes("SituationModelConsequence")) == 0
    conflict = bridge_proposition_evidence(
        agent, _evidence(predicate="different_relation"))
    assert conflict["supported"] is False
    assert conflict["reason"] == "evidence_id_conflicts_with_existing_proposition"
    assert len(agent.s.nodes("Proposition")) == 1


def test_accepted_non_change_of_state_does_not_mint_situation_consequence():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), agent.agent)
    result = bridge_proposition_evidence(agent, _evidence(
        predicate="resemble",
        arguments={"agent": "john", "theme": "glass"},
        commitment_status="proposed",
        uptake_signal="accept",
    ))
    proposition = result["proposition"]
    agent.inner.run_rules()
    out = apply_situation_consequence(agent, proposition)
    assert out["supported"] is False
    assert "did_not_confirm_change_of_state" in out["reason"]
    assert out["ingest"]["kind"] in {"generic_event", "non_change_of_state"}
    assert len(agent.s.nodes("SituationModelConsequence")) == 0
