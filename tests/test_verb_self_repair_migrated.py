"""The Jabberwock closes its verb-classification residual with typed evidence."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from domains.dict_teacher import DictionaryTeacher, lookup  # noqa: E402
from domains.substrate_extension import extend_for_gap  # noqa: E402
from domains.teacher_dispatch import scan_and_teach  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
import jabberwock_daemon as daemon  # noqa: E402


def _gap(agent: WorldAdapter):
    return agent.s.add_node("CapabilityGap", {
        "faculty": "lexical_category_evidence",
        "observation": [
            ["read_part_of_speech", "dictionary_entry", "lexical_category"],
            ["compare_category", "lexical_category", "instruction_hypothesis"],
        ],
        "needed_primitive": "dictionary_part_of_speech_read",
        "primitive_kind": "world_io",
        "inputs": ["dictionary_entry"],
        "outputs": ["lexical_category"],
        "example": "WordNet Entry.pos becomes an explicit graph observation",
        "status": "perceived",
    })


def _agent() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(manifest_for("instruction_understanding"), agent.agent)
    daemon._ensure_supervisory_scheduler(agent)
    agent._teacher_libraries = {"dictionary": DictionaryTeacher()}
    return agent


def _unknown_head(agent: WorldAdapter, head_text: str):
    message = agent.s.add_node("Message", {
        "from": "interlocutor", "text": f"{head_text.title()} the target.",
        "comp_kind": "statement",
    })
    head = agent.s.add_node("Mention", {"text": head_text})
    target = agent.s.add_node("Mention", {"text": "target"})
    target_concept = agent.s.add_node("Concept", {"name": "target"})
    agent.inner.add_edge_unchecked(agent.agent, "received", message)
    agent.inner.add_edge_unchecked(message, "has_mention", head)
    agent.inner.add_edge_unchecked(message, "has_mention", target)
    agent.inner.add_edge_unchecked(head, "next_mention", target)
    agent.inner.add_edge_unchecked(target, "prev_mention", head)
    agent.inner.add_edge_unchecked(target, "refers_to", target_concept)
    agent.tick()
    assert scan_and_teach(agent) == 1
    agent.tick()
    return message


def test_agent_identifies_pos_as_a_world_evidence_boundary():
    agent = WorldAdapter(seeds=())
    gap = _gap(agent)

    result = extend_for_gap(agent, gap, verify=True)

    assert result["outcome"] == "primitive_request"
    assert result["residual_kind"] == "world_io"
    assert result["spec"]["name"] == "dictionary_part_of_speech_read"
    assert agent.s.node(gap)["attrs"]["status"] == "needs_primitive"


def test_explicit_wordnet_categories_handle_ambiguous_verb_and_reject_noun():
    run_entry = lookup("run")
    sensor_entry = lookup("sensor")
    assert run_entry is not None and "verb" in run_entry.parts_of_speech
    assert sensor_entry is not None and sensor_entry.parts_of_speech == ["noun"]

    verb_agent = _agent()
    verb_message = _unknown_head(verb_agent, "run")
    assert verb_agent.s.node(verb_message)["attrs"]["comp_kind"] == "instruction"

    noun_agent = _agent()
    noun_message = _unknown_head(noun_agent, "sensor")
    assert noun_agent.s.node(noun_message)["attrs"]["comp_kind"] == "statement"
    assert not noun_agent.s.nodes("InstructionInterpretation")


def test_definition_text_can_no_longer_override_typed_noun_evidence():
    agent = _agent()
    message = agent.s.add_node("Message", {
        "from": "interlocutor", "text": "Sensor the target.", "comp_kind": "statement",
    })
    head = agent.s.add_node("Mention", {"text": "sensor"})
    agent.inner.add_edge_unchecked(agent.agent, "received", message)
    agent.inner.add_edge_unchecked(message, "has_mention", head)
    agent.tick()
    request = next(iter(agent.s.nodes("TeacherRequest")))
    evidence = agent.s.add_node("TeacherEvidence", {"verdict": "supported"})
    misleading = agent.s.add_node("TeacherConceptCandidate", {
        "status": "proposed", "name": "sensor",
        "definition": "contains the word verb but is explicitly a noun",
    })
    noun = agent.s.add_node("TeacherLexicalCategoryCandidate", {
        "status": "proposed", "lexeme": "sensor", "category": "noun",
    })
    agent.inner.add_edge_unchecked(request, "has_evidence", evidence)
    agent.inner.add_edge_unchecked(evidence, "proposes_concept", misleading)
    agent.inner.add_edge_unchecked(evidence, "proposes_lexical_category", noun)
    agent.tick()

    assert agent.s.node(message)["attrs"]["comp_kind"] == "statement"
    assert not agent.s.nodes("InstructionInterpretation")
