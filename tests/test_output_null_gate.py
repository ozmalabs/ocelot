"""Phase 5: output-null commitment and conversational floor holding."""
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
from domains import self_target_monitor


def _frame():
    return {"event": "is", "agent": "dog", "patient": "mammal",
            "tense": "present", "intent": "inform"}


def test_frame_reply_is_committed_only_after_output_null_gate():
    wa = WorldAdapter(seeds=())
    reply = wa._realize_frame_reply(_frame())

    assert reply
    trace = wa._last_frame_realization
    assert trace["committed"] is not None
    assert len(trace["gate_attempts"]) == 1
    assert trace["gate_attempts"][0]["gate"]["recoverable"] is True
    assert list(wa.s.nodes("OutputNullCandidate"))
    assert list(wa.s.nodes("Committed"))


def test_output_gate_allows_one_repair_then_withholds(monkeypatch):
    wa = WorldAdapter(seeds=())

    def never_recover(*args, **kwargs):
        return {"recoverable": False, "coverage": 0.0,
                "missing": ["dog", "mammal"], "recovered": [],
                "intended": ["dog", "mammal"], "mode": "test"}

    monkeypatch.setattr(self_target_monitor, "score_self_target", never_recover)
    assert wa._realize_frame_reply(_frame()) is None
    trace = wa._last_frame_realization
    assert len(trace["gate_attempts"]) == 2
    assert trace["committed"] is None


def test_floor_holder_matches_register():
    wa = WorldAdapter(seeds=())
    assert wa._floor_holding_reply().endswith(".")
    assert "connects" in wa._floor_holding_reply().lower()
