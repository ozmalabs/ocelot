from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "comprehension_divergence" / \
    "phase1_adjudications.json"

ALLOWED = {
    "literal_form": {
        "imperative", "compound_imperative", "declarative",
        "interrogative_with_politeness_preface",
        "imperative_with_politeness_marker",
        "interrogative", "social_expression",
    },
    "communicative_force": {
        "request_information", "request_action", "assertion_or_correction",
        "repair_or_defer", "social_action",
    },
    "cognitive_goal": {
        "answer_or_learn", "act_or_clarify", "update_common_ground",
        "clarify_or_defer", "coordinate_socially",
    },
    "grounding_status": {"grounded", "partially_grounded", "unknown"},
    "interaction_relation": {"standalone", "compound_event"},
    "adjudication": {
        "indirect_information_request", "compound_event", "assertion_report",
        "direct_information_request", "direct_action_request",
        "unresolved_action_request", "social_act",
    },
}


def test_phase1_adjudications_cover_every_kind_disagreement():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    events = payload["events"]
    assert payload["schema"] == "communication_event_adjudication.v1"
    assert len(events) == 20
    assert len({event["text"] for event in events}) == 20

    for event in events:
        for key, values in ALLOWED.items():
            assert event[key] in values, (key, event["text"], event[key])
        assert event["evidence"]


def test_phase1_adjudications_do_not_collapse_force_into_literal_form():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    events = payload["events"]
    information_requests = [
        event for event in events
        if event["communicative_force"] == "request_information"
    ]
    assert len(information_requests) == 12
    assert {event["literal_form"] for event in information_requests} >= {
        "imperative", "interrogative_with_politeness_preface",
        "imperative_with_politeness_marker",
    }


def test_graph_arbitration_matches_adjudicated_force_and_goal():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    # The original ten-event adjudication set is the strict Phase 1 gate.
    # The expanded slice is measured separately below so newly exposed route
    # failures remain visible rather than being hidden by changing labels.
    for event in payload["events"][:10]:
        agent.converse(event["text"], "statement")
        message = agent._last_turn_inbound
        interpretations = agent.inner.neighbours(message, "has_interpretation")
        assert len(interpretations) == 1
        attrs = agent.s.node(interpretations[0])["attrs"]
        assert attrs.get("communicative_force") == event["communicative_force"], (event["text"], attrs)
        assert attrs.get("cognitive_goal") == event["cognitive_goal"], (event["text"], attrs)


def test_expanded_adjudications_report_false_route_metrics():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    mismatches = []
    route_errors = Counter()

    for event in payload["events"]:
        agent.converse(event["text"], event.get("speech_act", "statement"))
        message = agent._last_turn_inbound
        interpretations = agent.inner.neighbours(message, "has_interpretation")
        assert len(interpretations) == 1
        attrs = agent.s.node(interpretations[0])["attrs"]
        actual = (attrs.get("communicative_force"), attrs.get("cognitive_goal"))
        expected = (event["communicative_force"], event["cognitive_goal"])
        if actual != expected:
            if event["communicative_force"] == "request_action":
                route_errors["false_action"] += 1
            elif event["communicative_force"] == "request_information":
                route_errors["false_answer"] += 1
            elif event["communicative_force"] == "repair_or_defer":
                route_errors["false_repair"] += 1
            mismatches.append({
                "text": event["text"],
                "expected": expected,
                "actual": actual,
                "dispatch_path": attrs.get("dispatch_path"),
                "literal_mood": attrs.get("literal_mood"),
                "gap_count": attrs.get("gap_count"),
            })

    # The action-evidence upgrade closes the previous polite-imperative miss.
    # The expanded result is now 20/20 = 100.0%, with no false action, answer,
    # or repair routes in this adjudicated slice.
    assert len(mismatches) == 0, mismatches
    assert route_errors == Counter()
