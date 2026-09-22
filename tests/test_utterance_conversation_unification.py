"""Tests for Phase 1 and Phase 2 of the Conversational Thought-Manifold & Utterance Generation:
Method unification, aliasing, and sustaining non-question dialogue.

Invariants:
- CLAUDE.md compliance: Rust graph substrate is source of truth; Python is world adapter.
- donkey=0: Zero LLM calls at runtime.
- Parity: wa.utterance is wa.converse; wa._render_node is wa.utterance_for.
- Ongoing dialogue: Non-question statements sustain conversation without premature "noted." fallbacks.
"""
from __future__ import annotations

import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _setup_adapter():
    wa = WorldAdapter(seeds=())
    # relation signs
    for form, concept, marker in [
        ("uses", "uses", ""), ("depends", "depends_on", "on"),
        ("runs", "runs_on", "on"), ("is_a", "is_a", ""),
        ("contains", "contains", ""), ("optimised", "optimised_for", "for"),
    ]:
        wa.learn_sign(form, concept, marker)
    # operand signs
    for w in ("process", "graph", "agent", "linux", "mind", "design", "data", "amd", "poodle", "dog", "mammal", "animal"):
        wa.learn_sign(w, w)
    wa.learn_sign("hello", "greeting")
    wa.learn_sign("I heard you.", "acknowledgment")
    wa._donkey = {"n": 0}
    wa.set_self_teacher(lambda q: (wa._donkey.__setitem__("n", wa._donkey["n"] + 1), "D")[1])
    return wa


def test_converse_and_utterance_method_parity():
    """WorldAdapter.utterance is an alias of WorldAdapter.converse, executing
    the canonical turn pipeline with byte-identical outputs."""
    assert WorldAdapter.utterance is WorldAdapter.converse

    wa = _setup_adapter()
    wa.enable_replies()

    res_conv = wa.converse("hello", "greeting")
    res_utt = wa.utterance("hello", "greeting")
    assert res_conv == "hello"
    assert res_conv == res_utt
    assert wa._donkey["n"] == 0


def test_add_inbound_unification_delegates_to_receive_utterance():
    """add_inbound delegates to receive_utterance with speech-act classification."""
    wa = _setup_adapter()
    mid = wa.add_inbound("hello there", speaker="user")
    assert mid is not None
    assert wa.s.has_node(mid)
    attrs = wa.s.node(mid)["attrs"]
    assert attrs.get("text") == "hello there"
    assert attrs.get("from") == "interlocutor"
    # Verify speech act and channel edges
    sas = [wa.s.node(sa)["attrs"].get("name")
           for sa in wa.inner.neighbours(mid, "has_speech_act")]
    assert "greeting" in sas or "statement" in sas
    assert wa._donkey["n"] == 0


def test_utterance_for_relational_meaning_parity():
    """utterance_for routes relational meanings and goal frames with full parity."""
    wa = _setup_adapter()

    # Binary relation
    assert wa.utterance_for({"uses": {"left": "process", "right": "graph"}}) == "process uses graph"
    # Preposition-marked relation
    assert wa.utterance_for({"runs_on": {"left": "agent", "right": "linux"}}) == "agent runs on linux"
    # _render_node alias parity
    assert WorldAdapter._render_node is WorldAdapter.utterance_for
    assert wa._render_node == wa.utterance_for
    assert wa._render_node({"depends_on": {"left": "process", "right": "data"}}) == "process depends on data"
    assert wa._donkey["n"] == 0


def test_non_question_statements_sustain_dialogue():
    """Phase 1 Gate: Non-question declarative statements sustain dialogue for >= 5 turns
    without prematurely terminating with 'noted.' or dropping the floor."""
    wa = _setup_adapter()
    wa.enable_replies()

    # Wire a knowledge network with concepts and relations
    poodle = wa.s.add_node("Concept", {"name": "poodle"})
    dog = wa.s.add_node("Concept", {"name": "dog"})
    mammal = wa.s.add_node("Concept", {"name": "mammal"})
    animal = wa.s.add_node("Concept", {"name": "animal"})
    wa.inner.add_edge_unchecked(poodle, "causal_influence", dog)
    wa.inner.add_edge_unchecked(dog, "causal_influence", mammal)
    wa.inner.add_edge_unchecked(mammal, "causal_influence", animal)

    # Store relational facts
    wa.learn_fact({"uses": {"left": "process", "right": "graph"}})
    wa.learn_fact({"depends_on": {"left": "process", "right": "data"}})

    turns = [
        ("The poodle is a companion dog.", "statement"),
        ("Dogs are loyal quadrupeds.", "statement"),
        ("Mammals are warm-blooded vertebrates.", "statement"),
        ("The process is running.", "statement"),
        ("Data flows into the system.", "statement"),
    ]

    terminal_floor_phrases = {"noted", "noted.", "got it", "got it.", "understood", "understood."}

    for idx, (statement_text, speech_act) in enumerate(turns):
        reply = wa.utterance(statement_text, speech_act=speech_act)
        assert reply is not None, f"Turn {idx + 1} produced silence"
        clean_reply = str(reply).strip().lower()
        assert clean_reply not in terminal_floor_phrases, (
            f"Turn {idx + 1} prematurely terminated with floor acknowledgment: {reply!r}"
        )
        assert len(clean_reply.split()) >= 2, (
            f"Turn {idx + 1} produced insufficient response: {reply!r}"
        )

        # Inbound Message must have ConversationDecisionState stamped
        mid = getattr(wa, "_last_turn_inbound", None)
        assert mid is not None
        decision_states = list(wa.inner.neighbours(mid, "has_decision_state"))
        assert len(decision_states) >= 1, f"Turn {idx + 1} did not record ConversationDecisionState"

    assert wa._donkey["n"] == 0, "All conversational turns executed with donkey=0 (zero LLM)"


def test_ungrounded_statement_falls_back_honestly():
    """An ungrounded statement with no held graph concepts or relations
    returns an explicit diagnostic rather than a dismissive acknowledgment."""
    wa = _setup_adapter()
    wa.enable_replies()

    # "the sky is blue" has no concepts or relations in this bare adapter
    reply = wa.converse("the sky is blue", "statement")
    assert reply == "ERROR: no communicative response could be generated."
    assert wa._donkey["n"] == 0
