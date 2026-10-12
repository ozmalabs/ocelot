"""Phase 3: inner trajectory hops stay graph-native until final collapse."""
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
from domains import predictive_reading
from domains import train_of_thought
from domains import self_dialogue


def _adapter():
    wa = WorldAdapter(seeds=())
    for word in ("poodle", "dog", "mammal", "animal", "is"):
        wa.learn_sign(word, word)
    nodes = {name: wa.s.add_node("Concept", {"name": name})
             for name in ("poodle", "dog", "mammal", "animal")}
    for left, right in (("poodle", "dog"), ("dog", "mammal"),
                        ("mammal", "animal")):
        wa.inner.add_edge_unchecked(nodes[left], "causal_influence", nodes[right])
    return wa


def test_inner_trajectory_realizes_only_collapsed_final_clause(monkeypatch):
    wa = _adapter()
    calls = []
    original = predictive_reading.realize_goal_clause

    def counted(*args, **kwargs):
        calls.append(args[2])
        return original(*args, **kwargs)

    monkeypatch.setattr(predictive_reading, "realize_goal_clause", counted)
    result = train_of_thought.run_inner_conversation(
        wa, topic="poodle", max_turns=2, novelty_window=None, enqueue=False)

    assert len(result["turns"]) == 2
    assert len(calls) == 1
    assert all(not turn["inner_utterance"] for turn in result["turns"][:-1])
    assert result["turns"][-1]["inner_utterance"]
    assert result["turns"][-1]["mode"] == "collapsed_final"
    assert result["topics_thought"] == ["poodle", "mammal"]


def test_graph_only_self_answer_reports_path_without_surface():
    wa = _adapter()
    answer = __import__("domains.self_dialogue", fromlist=["self_answer"]).self_answer(
        wa, "dog", realize=False)

    assert answer["surface"] == ""
    assert answer["graph_path"] == ["dog", "mammal"]
    assert answer["recovered"] == ["dog", "mammal"]


def test_self_dialogue_concept_lookup_uses_live_exact_name_index():
    wa = WorldAdapter(seeds=())
    first = wa.s.add_node("Concept", {"name": "held_topic"})
    assert not wa.inner.has_attr_index("Concept", "name")

    assert self_dialogue._find_concept(wa.s, "held_topic") == first
    assert wa.inner.has_attr_index("Concept", "name")

    # The maintained index must see later graph writes and preserve the
    # previous exact, case-sensitive name contract.
    duplicate = wa.s.add_node("Concept", {"name": "held_topic"})
    mixed_case = wa.s.add_node("Concept", {"name": "Held_Topic"})
    later = wa.s.add_node("Concept", {"name": "later_topic"})
    assert duplicate != first
    assert self_dialogue._find_concept(wa.s, "held_topic") == first
    assert self_dialogue._find_concept(wa.s, "Held_Topic") == mixed_case
    assert self_dialogue._find_concept(wa.s, "later_topic") == later
