from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from domains.communication_evidence import from_semantic_frame
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "comprehension_divergence" / \
    "language_neutral_variation.json"


def test_non_english_semantic_frames_drive_the_same_arbitration_rules():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["schema"] == "language_neutral_communication_variation.v1"
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    for event in payload["events"]:
        evidence = from_semantic_frame(
            event["semantic_frame"], provider=f"language_adapter:{event['language']}")
        interpretation = agent.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            **evidence,
            "communicative_force": None,
            "cognitive_goal": None,
        })
        agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation", interpretation)
        agent.inner.run_rules()
        attrs = agent.s.node(interpretation)["attrs"]
        assert attrs["communicative_force"] == event["force"], event["text"]
        assert attrs["cognitive_goal"] == event["goal"], event["text"]


def test_live_language_world_frames_feed_neutral_arbitration():
    """Use the existing multilingual text-to-frame adapter, then cross the
    neutral evidence boundary before graph arbitration."""
    try:
        from domains.language_world import LanguageWorld, teacher_stub
    except ModuleNotFoundError as exc:
        pytest.skip(f"LanguageWorld dependency unavailable in local venv: {exc.name}")
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    tasks = [
        {"text": "¿Quién rompió el jarrón?", "language": "es",
         "expected_meaning": {"event": "break", "agent": "?WHO",
                               "patient": "vase", "tense": "past",
                               "speech_act": "question"}},
        {"text": "María ama a Juan.", "language": "es",
         "expected_meaning": {"event": "love", "agent": "Mary",
                               "patient": "John", "tense": "present"}},
        {"text": "誰が花瓶を割った？", "language": "ja",
         "expected_meaning": {"event": "break", "agent": "?WHO",
                               "patient": "vase", "tense": "past",
                               "speech_act": "question"}},
    ]
    world = LanguageWorld(agent.inner, tasks, teacher_stub)
    log = world.run()
    assert len(log) == 3

    for entry in log:
        frame = entry["frame"]
        evidence = from_semantic_frame(
            frame, provider=f"language_world:{entry['language']}")
        interpretation = agent.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            **evidence,
            "communicative_force": None,
            "cognitive_goal": None,
        })
        agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation", interpretation)
        agent.inner.run_rules()
        attrs = agent.s.node(interpretation)["attrs"]
        expected_force = (
            "request_information"
            if frame.get("speech_act") == "question"
            else "assertion_or_correction")
        expected_goal = (
            "answer_or_learn"
            if frame.get("speech_act") == "question"
            else "update_common_ground")
        assert attrs["communicative_force"] == expected_force, entry["text"]
        assert attrs["cognitive_goal"] == expected_goal, entry["text"]
