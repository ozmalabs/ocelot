"""Held-out probes for graph-native communication force arbitration."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "comprehension_divergence" / \
    "phase1_generalization.json"


def test_graph_arbitration_generalizes_to_held_out_events():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["schema"] == "communication_event_generalization.v1"

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    for event in payload["events"]:
        agent.converse(event["text"], event["speech_act"])
        message = agent._last_turn_inbound
        interpretations = agent.inner.neighbours(message, "has_interpretation")
        assert len(interpretations) == 1, event["text"]
        attrs = agent.s.node(interpretations[0])["attrs"]
        assert attrs.get("communicative_force") == event["communicative_force"], (event["text"], attrs)
        assert attrs.get("cognitive_goal") == event["cognitive_goal"], (event["text"], attrs)
