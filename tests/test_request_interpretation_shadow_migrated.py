"""Independent interpretation evidence becomes a graph-native surprise vector."""
from __future__ import annotations

from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


def _fresh():
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(manifest_for("instruction_understanding"), agent.agent)
    agent.inner.load_seed_manifest(manifest_for("request_interpretation_shadow"), agent.agent)
    return agent


def _attrs(agent, node_type):
    return [agent.s.node(n)["attrs"] for n in agent.s.nodes(node_type)]


def test_question_requests_nonblocking_shadow_of_the_local_graph_parse():
    agent = _fresh()
    message = agent.s.add_node("Message", {
        "from": "interlocutor", "text": "What can you operate?",
        "comp_kind": "question", "comp_predicate": "operate",
        "comp_content": "plans", "comp_dispatch_path": "wordplay",
        "comp_intent": "wordplay:operate", "comp_topic": "plans",
    })
    agent.inner.add_edge_unchecked(agent.agent, "received", message)
    agent.tick()

    requests = [a for a in _attrs(agent, "TeacherRequest")
                if a.get("question_kind") == "shadow_request_interpretation"]
    assert len(requests) == 1
    assert requests[0]["teacher_tier"] == "llm"
    assert requests[0]["blocking"] == 0
    assert requests[0]["local_dispatch_path"] == "wordplay"
    assert requests[0]["instruction_context"] == "What can you operate?"


def test_disagreement_is_retained_by_dimension_and_calculated_as_integer_surprise():
    agent = _fresh()
    message = agent.s.add_node("Message", {
        "from": "interlocutor", "text": "What can you operate?",
        "comp_kind": "question", "comp_predicate": "operate",
        "comp_content": "plans", "comp_dispatch_path": "wordplay",
    })
    agent.inner.add_edge_unchecked(agent.agent, "received", message)
    agent.tick()
    request = [n for n in agent.s.nodes("TeacherRequest")
               if agent.s.node(n)["attrs"].get("question_kind") ==
               "shadow_request_interpretation"][0]
    evidence = agent.s.add_node("TeacherEvidence", {
        "status": "received", "teacher_tier": "llm", "verdict": "corrected",
        "evidence_schema": "interpretation_shadow.v1", "target_scope": "self_graph",
        "answer_mode": "graph_state_description",
    })
    agent.inner.add_edge_unchecked(request, "has_evidence", evidence)
    for dimension in ("target_scope", "answer_mode"):
        difference = agent.s.add_node("InterpretationDifference", {
            "dimension": dimension, "status": "proposed", "source": "llm_shadow"})
        agent.inner.add_edge_unchecked(evidence, "proposes_difference", difference)
    agent.tick()

    residuals = _attrs(agent, "InterpretationResidual")
    assert {a["dimension"] for a in residuals} == {"target_scope", "answer_mode"}
    assert all(a["status"] == "open" and a["source"] == "llm_shadow"
               for a in residuals)
    message_attrs = agent.s.node(message)["attrs"]
    assert message_attrs["interpretation_surprise"] == 2
    assert type(message_attrs["interpretation_surprise"]) is int
    assert message_attrs["shadow_interpretation_status"] == "surprising"
    concerns = [a for a in _attrs(agent, "SelfConcern")
                if a.get("kind") == "interpretation_surprise"]
    assert len(concerns) == 1 and concerns[0]["status"] == "noted"


def test_corroborating_shadow_creates_no_false_gap():
    agent = _fresh()
    message = agent.s.add_node("Message", {
        "from": "interlocutor", "text": "What can you operate?",
        "comp_kind": "question", "comp_predicate": "operate",
        "comp_content": "body plans", "comp_dispatch_path": "self_graph",
    })
    agent.inner.add_edge_unchecked(agent.agent, "received", message)
    agent.tick()
    request = [n for n in agent.s.nodes("TeacherRequest")
               if agent.s.node(n)["attrs"].get("question_kind") ==
               "shadow_request_interpretation"][0]
    evidence = agent.s.add_node("TeacherEvidence", {
        "status": "received", "teacher_tier": "llm", "verdict": "supported",
        "evidence_schema": "interpretation_shadow.v1"})
    agent.inner.add_edge_unchecked(request, "has_evidence", evidence)
    agent.tick()

    assert agent.s.node(message)["attrs"]["interpretation_surprise"] == 0
    assert agent.s.node(message)["attrs"]["shadow_interpretation_status"] == "corroborated"
    assert not [a for a in _attrs(agent, "SelfConcern")
                if a.get("kind") == "interpretation_surprise"]
