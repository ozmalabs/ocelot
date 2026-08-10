"""Native substrate integration for graph-selected teacher evidence."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from domains.teacher_dispatch import scan_and_teach  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


class _Dictionary:
    def __init__(self):
        self.calls = []

    def __call__(self, question):
        self.calls.append(question)
        return {
            # Must not be persisted or rendered by this bridge.
            "answer": "raw teacher prose must not become a reply",
            "learn": [{"phrase": "sensor", "description": "an observing instrument",
                       "parts_of_speech": ["noun"]}],
        }


def _fresh() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(manifest_for("instruction_understanding"), agent.agent)
    return agent


def test_native_dispatch_persists_nested_evidence_and_instruction_seed_stages_it():
    agent = _fresh()
    source = agent.s.add_node("Message", {
        "from": "interlocutor", "comp_kind": "instruction",
        "comp_predicate": "calibrate", "comp_content": "sensor",
    })
    agent.inner.add_edge_unchecked(agent.agent, "received", source)
    # The instruction seed is intentionally graph-gated: a routed predicate
    # must be represented by its parsed mention and an instruction-route
    # Concept before it originates teacher work.
    predicate_mention = agent.s.add_node("Mention", {"text": "calibrate"})
    predicate_concept = agent.s.add_node(
        "Concept", {"name": "calibrate", "instruction_route": "world_action"})
    agent.inner.add_edge_unchecked(source, "has_mention", predicate_mention)
    agent.inner.add_edge_unchecked(predicate_mention, "refers_to", predicate_concept)
    agent.tick()
    request = agent.s.nodes("TeacherRequest")[0]

    host = agent.s.add_node("HostActionRequest", {
        "action": "teacher", "source_type": "TeacherRequest", "source": request,
        "status": "requested", "urgency": 1, "residual": 1,
        "estimated_cost": 1, "deadline": 0,
    })
    dictionary = _Dictionary()
    agent._teacher_libraries = {"dictionary": dictionary}

    assert scan_and_teach(agent) == 1
    assert dictionary.calls == ["sensor"]
    evidence = list(agent.inner.neighbours(request, "has_evidence"))
    assert len(evidence) == 1
    attrs = agent.s.node(evidence[0])["attrs"]
    local_prose = "raw teacher prose must not become a reply"
    assert list(attrs["candidate_concepts"]) == [{"name": "sensor", "definition": local_prose}]
    assert list(attrs["semantic_differences"]) == []
    assert list(attrs["candidate_relations"]) == []
    proposals = list(agent.inner.neighbours(evidence[0], "proposes_concept"))
    assert len(proposals) == 1
    proposal = agent.s.node(proposals[0])
    assert proposal["type"] == "TeacherConceptCandidate"
    assert proposal["attrs"]["status"] == "proposed"
    assert proposal["attrs"]["name"] == "sensor"
    categories = list(agent.inner.neighbours(evidence[0], "proposes_lexical_category"))
    assert len(categories) == 1
    assert agent.s.node(categories[0])["attrs"]["lexeme"] == "sensor"
    assert agent.s.node(categories[0])["attrs"]["category"] == "noun"
    assert proposal["attrs"]["definition"] == local_prose
    assert not [node for node in agent.s.nodes("Concept")
                if agent.s.node(node)["attrs"].get("name") == "sensor"], \
        "transport evidence must not be adopted before replay"
    assert agent.s.node(request)["attrs"]["status"] == "completed"
    assert agent.s.node(host)["attrs"]["status"] == "requested", "dispatcher does not own host status"
    assert not agent.s.nodes("HeldAnswer")

    agent.tick()
    lessons = list(agent.s.nodes("LessonCandidate"))
    assert len(lessons) == 1
    # A fixed-point tick may immediately complete the seed's replay/adoption
    # chain after staging; either state proves the graph, not the bridge,
    # owns the lesson lifecycle.
    assert agent.s.node(lessons[0])["attrs"]["status"] in {"staged", "adopted"}
    assert evidence[0] in set(agent.inner.neighbours(lessons[0], "grounded_in_evidence"))
    assert not [node for node in agent.s.nodes("Message")
                if agent.s.node(node)["attrs"].get("from") == "agent"]
    assert not any(local_prose in str(agent.s.node(node)["attrs"])
                   for node in agent.s.nodes("Message")), "teacher prose stays evidence, never a reply"
