"""Native kind arbitration from language-neutral speech-act evidence."""
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


@pytest.mark.parametrize("text", [
    "Check the pressure.",
    "Open the hatch and check the gauge.",
    "When ready, close the hatch.",
])
def test_explicit_instruction_evidence_reaches_native_kind(text):
    agent = WorldAdapter(seeds=())
    agent.converse(text, speech_act="instruction",
                   context={"interaction_mode": "non_turn"})
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    assert attrs["sak_input_kind"] == "instruction"
    assert attrs["sak_kind"] == "instruction"
    assert attrs["comp_kind"] == "instruction"


def test_question_evidence_does_not_become_instruction():
    agent = WorldAdapter(seeds=())
    agent.converse("What is the pressure?", speech_act="question",
                   context={"interaction_mode": "non_turn"})
    attrs = agent.s.node(agent._last_turn_inbound)["attrs"]
    assert attrs["sak_kind"] == "question"
    assert attrs["comp_kind"] == "question"
