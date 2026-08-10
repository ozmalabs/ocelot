"""Ambiguous tech acronyms ground to the correct sense, not WordNet's default."""
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


def test_dict_teacher_misses_llm_for_wiki_fallback():
    from domains.dict_teacher import lookup
    assert lookup("llm") is None


def test_ground_topic_llm_is_large_language_model(agent):
    from domains.topic_grounding import ground_topic
    ans = ground_topic(agent, "llm", allow_web=False)
    assert ans
    assert "large language model" in ans.lower()
    assert "law degree" not in ans.lower()
    assert "advanced law" not in ans.lower()


def test_converse_what_is_llm(agent):
    reply = agent.converse("What is an LLM?", speech_act="question")
    assert reply
    low = reply.lower()
    assert "large language model" in low or "neural network" in low
    assert "law degree" not in low
    assert "advanced law" not in low
