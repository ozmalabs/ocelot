"""Copular self-classification ('are you an LLM?') must deny the kind, not
Wikipedia-ground the kind noun as an external topic."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    from domains.libraries import attach_libraries
    attach_libraries(a, enable_llm=False)
    return a


def test_comprehend_are_you_llm_routes_self_kind(agent):
    from domains.comprehend_text import comprehend_text
    comp = comprehend_text(agent, "Are you an LLM?")
    d = comp.dispatch or {}
    assert d.get("path") == "meta"
    assert d.get("meta_target") == "self_kind"
    assert str(d.get("meta_arg")).lower() == "llm"
    facts = agent._topic_facts(comp)
    assert facts.get("topic") is None, "copular self-kind must not write external topic"


def test_converse_are_you_llm_denies_not_wiki(agent):
    reply = agent.converse("Are you an LLM?", speech_act="question")
    assert reply
    low = reply.lower()
    assert "jabberwock" in low or "graph-native" in low
    assert "large language model" in low or "not a large language model" in low
    assert "target acquisition" not in low
    assert "llm01" not in low


def test_stale_llm_held_answer_refreshed(agent):
    from domains.topic_grounding import ground_topic
    agent._persist_held_answer(
        "llm",
        "The LLM01 is an adaptive target acquisition module made by Rheinmetall.")
    ans = ground_topic(agent, "llm", allow_web=False)
    assert ans
    assert "large language model" in ans.lower()
    assert "target acquisition" not in ans.lower()
    assert "llm01" not in ans.lower()
