"""Phase 6A: production release must carry cognitive evidence."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402
from domains.production_gate import release_if_gated  # noqa: E402


def _agent():
    return WorldAdapter(seeds=())


def _frame():
    return {"event": "is", "agent": "dog", "patient": "mammal",
            "tense": "present", "intent": "inform"}


def test_release_requires_selected_semantics_parseback_and_commitment():
    wa = _agent()
    committed = wa.s.add_node("Committed", {"utterance": "The dog is a mammal"})
    gate = {"recoverable": True, "coverage": 1.0,
            "mode": "grounded_comprehension"}

    surface = release_if_gated(wa, _frame(), "The dog is a mammal", gate, committed)

    assert surface == "The dog is a mammal"
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["status"] == "released"
    assert attrs["semantic_event"] == "is"
    assert attrs["parse_back_mode"] == "grounded_comprehension"
    assert committed in list(wa.inner.neighbours(receipts[0], "releases"))


def test_repeated_release_for_same_commitment_is_idempotent():
    wa = _agent()
    committed = wa.s.add_node("Committed", {"utterance": "The dog is a mammal"})
    gate = {"recoverable": True, "coverage": 1.0,
            "mode": "grounded_comprehension"}
    assert release_if_gated(wa, _frame(), "The dog is a mammal", gate, committed)
    assert release_if_gated(wa, _frame(), "The dog is a mammal", gate, committed)
    assert len(wa.s.nodes("ProductionGateReceipt")) == 1


@pytest.mark.parametrize("frame, gate, committed", [
    ({}, {"recoverable": True}, True),
    (_frame(), {"recoverable": False}, True),
    (_frame(), {"recoverable": True}, None),
])
def test_release_withholds_when_any_cognitive_evidence_is_missing(frame, gate, committed):
    wa = _agent()
    assert release_if_gated(wa, frame, "The dog is a mammal", gate, committed) is None
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["status"] == "withheld"
    assert attrs["withhold_reasons"]
    assert not list(wa.inner.neighbours(receipts[0], "releases"))


def test_forbidden_fallback_surface_is_withheld_even_with_other_evidence():
    wa = _agent()
    committed = wa.s.add_node("Committed", {"utterance": "noted"})
    gate = {"recoverable": True, "coverage": 1.0, "mode": "recognizer"}

    assert release_if_gated(wa, _frame(), "noted", gate, committed) is None
    receipt = list(wa.s.nodes("ProductionGateReceipt"))[0]
    attrs = wa.s.node(receipt)["attrs"]
    assert attrs["status"] == "withheld"
    assert attrs["withhold_reasons"] == ["forbidden_fallback_surface"]
    assert not list(wa.inner.neighbours(receipt, "releases"))


def test_realized_frame_reply_leaves_release_receipt():
    wa = _agent()
    reply = wa._realize_frame_reply(_frame())

    assert reply
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["surface"] == reply
    assert attrs["recoverable"] is True
    assert attrs["coverage"] == 1.0
    assert attrs["parse_back_mode"] in {"grounded_comprehension", "recognizer"}


def test_output_null_repair_attempts_leave_withheld_receipts(monkeypatch):
    wa = _agent()

    def never_recover(*args, **kwargs):
        return {"recoverable": False, "coverage": 0.0,
                "missing": ["dog", "mammal"], "recovered": [],
                "intended": ["dog", "mammal"], "mode": "test"}

    from domains import self_target_monitor
    monkeypatch.setattr(self_target_monitor, "score_self_target", never_recover)

    assert wa._realize_frame_reply(_frame()) is None
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 2
    assert all(wa.s.node(node)["attrs"]["status"] == "withheld"
               for node in receipts)
    assert all("parse_back_not_recoverable" in wa.s.node(node)["attrs"]["withhold_reasons"]
               for node in receipts)


@pytest.mark.parametrize(
    ("text", "speech_act", "expected_event"),
    [
        ("Please open the north gate.", "statement", "open"),
        # With no antecedent for ``it``, cognition must preserve the
        # unresolved-reference repair state rather than releasing an action.
        ("Move it now.", "statement", "repair"),
        ("Quorplezap the door.", "statement", "repair"),
    ],
)
def test_conversation_action_and_repair_surfaces_release_graph_receipts(
        text, speech_act, expected_event):
    """Action/repair coverage must come from the bridge's graph commitment."""
    wa = _agent()
    reply = wa.converse(text, speech_act=speech_act,
                        context={"interaction_mode": "turn_compatible"})

    assert reply
    assert reply != "noted"
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    released = [wa.s.node(node)["attrs"] for node in receipts
                if wa.s.node(node)["attrs"].get("status") == "released"]
    assert len(released) == 1
    assert released[0]["parse_back_mode"] == "conversation_action_graph"
    assert released[0]["surface"] == reply
    assert released[0]["semantic_event"] == expected_event


def test_unrelated_topic_path_does_not_gain_action_receipt():
    wa = _agent()
    wa.converse("How are you organised?", speech_act="question",
                context={"interaction_mode": "turn_compatible"})

    assert not any(
        wa.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_action_graph"
        for node in wa.s.nodes("ProductionGateReceipt")
    )
