"""Data-only causal retrieval and owner-thread candidate staging."""
from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

from domains.causal_retrieval import (
    commit_causal_candidate_payloads,
    retrieve_causal_candidate_payloads,
)
from substrate.world_adapter import WorldAdapter


def test_retrieval_returns_only_cited_typed_cause_claims_without_graph_access():
    calls = []

    def getter(url, *, timeout):
        calls.append((url, timeout))
        params = parse_qs(urlparse(url).query)
        if params.get("action") == ["wbsearchentities"]:
            return {"text": json.dumps({"search": [
                {"id": "Q12156", "label": "malaria"},
                {"id": "Q133969", "label": "Plasmodium malariae"},
                {"id": "Q999999", "label": "malaria parasite"},
                {"id": "not-an-item", "label": "malaria"},
            ]})}
        entity_id = params.get("ids", [""])[0]
        assert entity_id == "Q12156"
        return {"text": json.dumps({"entities": {entity_id: {
            "labels": {"en": {"value": "malaria"}},
            "claims": {"P828": [
                {
                    "id": f"{entity_id}$supported",
                    "rank": "normal",
                    "mainsnak": {"snaktype": "value", "datavalue": {
                        "value": {"id": "Q133969"}}},
                    "references": [{"snaks": {"P854": [{
                        "datavalue": {"value": "https://example.org/source"}
                    }]}}],
                },
                {
                    "id": f"{entity_id}$uncited",
                    "rank": "normal",
                    "mainsnak": {"snaktype": "value", "datavalue": {
                        "value": {"id": "Q1"}}},
                    "references": [],
                },
                {
                    "id": f"{entity_id}$deprecated",
                    "rank": "deprecated",
                    "mainsnak": {"snaktype": "value", "datavalue": {
                        "value": {"id": "Q2"}}},
                    "references": [{"snaks": {"P854": [{
                        "datavalue": {"value": "https://example.org/old"}
                    }]}}],
                },
            ]},
        }}})}

    candidates = retrieve_causal_candidate_payloads(
        "malaria", http_get=getter)
    assert len(candidates) == 1
    assert all(c["property_id"] == "P828" for c in candidates)
    assert all(c["epistemic_status"] == "candidate_unverified" for c in candidates)
    assert all(c["authority"] == "none" for c in candidates)
    assert all(c["references"] for c in candidates)
    assert len(calls) == 2


def test_fuzzy_entity_search_matches_are_not_retrieved_as_causes():
    calls = []

    def getter(url, *, timeout):
        calls.append(url)
        return {"text": json.dumps({"search": [
            {"id": "Q999999", "label": "malaria parasite"},
            {"id": "Q888888", "label": "malaria in children"},
        ]})}

    assert retrieve_causal_candidate_payloads(
        "malaria", http_get=getter) == []
    assert len(calls) == 1
    assert "wbsearchentities" in calls[0]


def test_bound_identity_retrieval_skips_search_and_rejects_label_mismatch():
    calls = []

    def getter(url, *, timeout):
        calls.append(url)
        return {"text": json.dumps({"entities": {"Q12156": {
            "labels": {"en": {"value": "malaria parasite"}},
            "claims": {},
        }}})}

    assert retrieve_causal_candidate_payloads(
        "malaria", entity_id="Q12156", http_get=getter) == []
    assert len(calls) == 1
    assert "wbgetentities" in calls[0]
    assert "ids=Q12156" in calls[0]


def test_owner_commit_stages_candidates_but_never_asserts_causal_evidence():
    agent = WorldAdapter(seeds=())
    request = agent.s.add_node("CausalRetrievalRequest", {
        "schema": "causal_retrieval_request.v1",
        "status": "running",
        "topic": "malaria",
        "topic_entity_id": "Q12156",
        "causal_io_token": "live-token",
        "authority": "none",
    })
    payload = {
        "schema": "causal_retrieval_candidate.v1",
        "provider": "wikidata",
        "query": "malaria",
        "source_entity_id": "Q12156",
        "source_label": "malaria",
        "property_id": "P828",
        "cause_entity_id": "Q133969",
        "statement_id": "Q12156$statement",
        "rank": "normal",
        "references": [{"P854": ["https://example.org/source"]}],
        "source_url": "https://www.wikidata.org/wiki/Q12156",
        "epistemic_status": "candidate_unverified",
        "authority": "none",
    }

    assert commit_causal_candidate_payloads(
        agent, request, [payload], io_token="stale-token") == 0
    assert commit_causal_candidate_payloads(
        agent, request, [payload], io_token="live-token") == 1
    assert agent.s.node(request)["attrs"]["status"] == "candidates_staged"
    candidate = agent.inner.neighbours(request, "has_candidate")[0]
    assert agent.s.node(candidate)["type"] == "CausalRetrievalCandidate"
    assert agent.s.node(candidate)["attrs"]["authority"] == "none"
    assert agent.s.node(candidate)["attrs"]["citation_count"] == 1
    assert agent.inner.neighbours(candidate, "causal_influence") == []
    assert agent.s.nodes("HeldAnswer") == []


def test_unreferenced_or_malformed_payloads_do_not_stage():
    agent = WorldAdapter(seeds=())
    request = agent.s.add_node("CausalRetrievalRequest", {
        "schema": "causal_retrieval_request.v1", "status": "running",
        "topic": "alarm", "topic_entity_id": "Q3",
        "causal_io_token": "token",
    })
    malformed = {
        "schema": "causal_retrieval_candidate.v1", "provider": "wikidata",
        "query": "alarm", "source_entity_id": "Q1", "property_id": "P828",
        "cause_entity_id": "Q2", "references": [],
        "epistemic_status": "candidate_unverified", "authority": "none",
    }
    assert commit_causal_candidate_payloads(
        agent, request, [malformed], io_token="token") == 0
    assert agent.s.node(request)["attrs"]["status"] == "failed"
    assert agent.s.nodes("CausalRetrievalCandidate") == []


def test_owner_commit_rejects_untrusted_source_identity_and_citation_shapes():
    agent = WorldAdapter(seeds=())
    request = agent.s.add_node("CausalRetrievalRequest", {
        "schema": "causal_retrieval_request.v1", "status": "running",
        "topic": "malaria", "topic_entity_id": "Q12156",
        "causal_io_token": "token",
    })
    base = {
        "schema": "causal_retrieval_candidate.v1", "provider": "wikidata",
        "query": "malaria", "source_entity_id": "Q12156",
        "source_label": "malaria", "property_id": "P828",
        "cause_entity_id": "Q133969", "statement_id": "Q12156$abc-123",
        "rank": "normal", "references": [{
            "P854": ["https://example.org/source"]}],
        "source_url": "https://www.wikidata.org/wiki/Q12156",
        "epistemic_status": "candidate_unverified", "authority": "none",
    }
    malformed = []
    for key, value in (
            ("source_label", "malaria parasite"),
            ("statement_id", "Q12156$"),
            ("references", [{"P854": ["http://example.org/source"]}]),
            ("references", [{"P248": ["not-an-entity"]}]),
            ("references", [{"P999": ["citation"]}]),
    ):
        candidate = dict(base)
        candidate[key] = value
        malformed.append(candidate)

    assert commit_causal_candidate_payloads(
        agent, request, malformed, io_token="token") == 0
    assert agent.s.nodes("CausalRetrievalCandidate") == []
    assert agent.s.node(request)["attrs"]["status"] == "failed"


def test_native_request_requires_a_resolved_topic_concept():
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    message = agent.s.add_node("Message", {
        "comp_know_concept": "unmapped topic",
    })
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "cognitive_disposition": "learn",
        "relation_focus": "reason",
        "relation_support": "missing",
        "anaphor": 0,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)
    agent.inner.add_edge_unchecked(interpretation, "interprets", message)

    agent.inner.run_rules()
    assert agent.s.nodes("CausalRetrievalRequest") == []


def test_native_general_reason_scope_can_mint_a_data_only_request():
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    topic = agent.s.add_node("Concept", {"name": "malaria"})
    message = agent.s.add_node("Message", {"comp_know_concept": "malaria"})
    mention = agent.s.add_node("Mention", {"text": "malaria"})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "cognitive_disposition": "learn",
        "relation_focus": "reason",
        "relation_support": "missing",
        "relation_scope": "conceptual_general",
        "anaphor": 0,
    })
    agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation",
                                   interpretation)
    agent.inner.add_edge_unchecked(interpretation, "interprets", message)
    agent.inner.add_edge_unchecked(message, "has_mention", mention)
    agent.inner.add_edge_unchecked(mention, "refers_to", topic)

    agent.inner.run_rules()
    requests = list(agent.s.nodes("CausalRetrievalRequest"))
    assert len(requests) == 1
    assert agent.s.node(requests[0])["attrs"].get("topic_entity_id") is None

    identity = agent.s.add_node("ExternalIdentityEvidence", {
        "schema": "external_identity_evidence.v1",
        "provider": "wikidata", "status": "candidate",
        "entity_id": "Q12156",
    })
    agent.inner.add_edge_unchecked(topic, "has_external_identity", identity)
    agent.inner.run_rules()
    assert agent.s.node(requests[0])["attrs"].get("topic_entity_id") is None
    agent.inner.set_attr(identity, "status", "verified")
    agent.inner.run_rules()
    requests = list(agent.s.nodes("CausalRetrievalRequest"))
    assert len(requests) == 1
    request_attrs = agent.s.node(requests[0])["attrs"]
    assert request_attrs["topic"] == "malaria"
    assert request_attrs["topic_entity_id"] == "Q12156"
    bound_identity = agent.inner.neighbours(requests[0], "bound_identity")
    assert len(bound_identity) == 1
    assert agent.s.node(bound_identity[0])["attrs"]["status"] == "verified"
    assert request_attrs["authority"] == "none"
    assert requests[0] in agent.inner.neighbours(
        interpretation, "requests_causal_retrieval")


def test_native_promotion_requires_verified_identity_for_both_endpoints():
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    report = load_all_seeds(agent)
    assert "communication_causal_evidence_promotion" in report["order"]
    effect = agent.s.add_node("Concept", {"name": "malaria"})
    cause = agent.s.add_node("Concept", {"name": "parasite cause"})
    effect_identity = agent.s.add_node("ExternalIdentityEvidence", {
        "schema": "external_identity_evidence.v1", "provider": "wikidata",
        "status": "verified", "entity_id": "Q12156",
    })
    cause_identity = agent.s.add_node("ExternalIdentityEvidence", {
        "schema": "external_identity_evidence.v1", "provider": "wikidata",
        "status": "candidate", "entity_id": "Q133969",
    })
    agent.inner.add_edge_unchecked(
        effect, "has_external_identity", effect_identity)
    agent.inner.add_edge_unchecked(cause, "has_external_identity", cause_identity)
    message = agent.s.add_node("Message", {
        "comp_know_concept": "malaria", "comp_relation_focus": "reason",
    })
    mention = agent.s.add_node("Mention", {"text": "malaria"})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "cognitive_disposition": "learn", "relation_focus": "reason",
        "relation_support": "missing", "relation_scope": "conceptual_general",
        "anaphor": 0,
    })
    agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation",
                                   interpretation)
    agent.inner.add_edge_unchecked(interpretation, "interprets", message)
    agent.inner.add_edge_unchecked(message, "has_mention", mention)
    agent.inner.add_edge_unchecked(mention, "refers_to", effect)
    agent.inner.run_rules()

    requests = list(agent.s.nodes("CausalRetrievalRequest"))
    assert len(requests) == 1
    request = requests[0]
    assert agent.s.node(request)["attrs"]["topic_entity_id"] == "Q12156"
    agent.inner.set_attr(request, "status", "running")
    agent.inner.set_attr(request, "causal_io_token", "token")
    payload = {
        "schema": "causal_retrieval_candidate.v1", "provider": "wikidata",
        "query": "malaria", "source_entity_id": "Q12156",
        "source_label": "malaria", "property_id": "P828",
        "cause_entity_id": "Q133969", "statement_id": "Q12156$claim",
        "rank": "normal", "references": [{
            "P854": ["https://example.org/claim"]}],
        "source_url": "https://www.wikidata.org/wiki/Q12156",
        "epistemic_status": "candidate_unverified", "authority": "none",
    }
    assert commit_causal_candidate_payloads(
        agent, request, [payload], io_token="token") == 1
    agent.inner.run_rules()
    assert agent.inner.neighbours(cause, "causal_influence") == []
    assert agent.s.nodes("CausalClaimEvidence") == []

    agent.inner.set_attr(cause_identity, "status", "verified")
    agent.inner.run_rules()
    evidence_nodes = list(agent.s.nodes("CausalClaimEvidence"))
    assert len(evidence_nodes) == 1
    evidence = evidence_nodes[0]
    assert agent.s.node(evidence)["attrs"]["schema"] == \
        "causal_claim_evidence.v1"
    assert agent.s.node(evidence)["attrs"]["epistemic_status"] == \
        "externally_sourced_claim"
    assert effect in agent.inner.neighbours(evidence, "about_effect")
    assert cause in agent.inner.neighbours(evidence, "has_cause")
    assert request in agent.inner.neighbours(evidence, "for_request")
    assert agent.inner.neighbours(cause, "causal_influence") == []
    candidate = agent.inner.neighbours(request, "has_candidate")[0]
    assert agent.s.node(candidate)["attrs"]["epistemic_status"] == \
        "externally_supported"
    assert agent.s.node(candidate)["attrs"]["authority"] == \
        "native_identity_bound_claim"
    assert agent.s.node(request)["attrs"]["status"] == "claims_staged"
