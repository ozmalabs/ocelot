"""Phase 6: conversation decision settle-back and habit internalization."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def test_repeated_candidate_internalizes_grounded_value():
    wa = WorldAdapter(seeds=())
    for _ in range(3):
        wa._record_conversation_decision("direct_fact", None)

    options = [n for n in wa.s.nodes("DecisionOption")
               if wa.s.node(n)["attrs"].get("token") == "direct_fact"]
    assert len(options) == 1
    attrs = wa.s.node(options[0])["attrs"]
    assert attrs["decision_experience_count"] == 3.0
    assert attrs["grounded_value"] == 0.90
    assert 0.50 < attrs["learned_value"] < 0.90

    states = list(wa.s.nodes("ConversationDecisionState"))
    assert len(states) == 3
    assert all("grounded_value" in wa.s.node(n)["attrs"] for n in states)
    assert all("learned_value" in wa.s.node(n)["attrs"] for n in states)


def test_settle_mode_returns_to_shallow_after_internalization():
    wa = WorldAdapter(seeds=())
    wa._record_conversation_decision("transitive_relation", None)
    wa._record_conversation_decision("transitive_relation", None)

    states = [n for n in wa.s.nodes("ConversationDecisionState")
              if wa.s.node(n)["attrs"].get("token") == "transitive_relation"]
    assert states[0] != states[1]
    assert wa.s.node(states[0])["attrs"]["settle_mode"] == "deep"
    assert wa.s.node(states[1])["attrs"]["settle_mode"] == "shallow"
