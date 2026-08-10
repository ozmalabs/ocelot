"""Psychology Mt — mental-state vocabulary + theory-of-mind, migrated to the
seed-booted WorldAdapter (no CuriousAgent).

The psychology taxonomy is graph data — the `psychology` seed manifest (Mt +
mental-state taxonomy under genlMt/subtype_of, mind + ToM concepts, the
`demonstrates` links to the machinery that realises each, and the mental-verb
signs). The agent BOOTS it; the adapter only queries it (has_theory_of_mind /
mental_states / taught_signs) and renders mental-state meanings via the
predicate-argument Pred render. Covers tests/test_psychology.py.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from domains.psychology import (_MENTAL_STATES, _MENTAL_STATE_PARENT,
                                _MIND_CONCEPTS, _PSYCHOLOGY_MT, _TOM_CONCEPTS)
from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter

_PSY = CORE_SEEDS + ("psychology",)


def _agent():
    return WorldAdapter(seeds=_PSY)


def _out(a, nid, edge):
    return set(a.inner.neighbours(nid, edge))


# --- taxonomy ------------------------------------------------------------

def test_install_creates_psychology_mt():
    a = _agent()
    assert a.microtheory(_PSYCHOLOGY_MT) is not None


def test_install_creates_mental_state_taxonomy():
    a = _agent()
    parent = a._concept_by_name(_MENTAL_STATE_PARENT)
    assert parent is not None
    for name, _desc in _MENTAL_STATES:
        cid = a._concept_by_name(name)
        assert cid is not None, name
        assert parent in _out(a, cid, "subtype_of"), name


def test_install_creates_mind_concepts():
    a = _agent()
    for name, _desc in _MIND_CONCEPTS:
        assert a._concept_by_name(name) is not None, name


def test_install_creates_tom_concepts():
    a = _agent()
    for name, _desc in _TOM_CONCEPTS:
        assert a._concept_by_name(name) is not None, name
    assert a._concept_by_name("theory_of_mind") is not None


def test_install_is_idempotent():
    a = _agent()
    toms = [n for n in a.s.nodes("Concept")
            if a.s.node(n)["attrs"].get("name") == "theory_of_mind"]
    assert len(toms) == 1


# --- capability links ----------------------------------------------------

def test_theory_of_mind_demonstrated_by_belief_attribution_perspective():
    a = _agent()
    assert a.has_theory_of_mind() is True


def test_belief_demonstrated_by_interlocutor_concept():
    a = _agent()
    assert a._concept_by_name("interlocutor") in _out(
        a, a._concept_by_name("belief"), "demonstrates")


def test_desire_demonstrated_by_goal_concept():
    a = _agent()
    assert a._concept_by_name("goal") in _out(
        a, a._concept_by_name("desire"), "demonstrates")


# --- verb signs + production ---------------------------------------------

def test_mental_verbs_grounded_in_lexicon():
    a = _agent()
    forms = {s.get("form") for s in a.taught_signs()}
    for verb in ("believe", "want", "intend", "see", "perceive"):
        assert verb in forms, verb


def test_agent_can_produce_belief_meaning():
    a = _agent()
    text = a.utterance_for({"believe": {"of": "photosynthesis"}})
    assert text is not None
    assert "believe" in text
    assert "photosynthesis" in text


# --- mental_states helper -----------------------------------------------

def test_mental_states_helper_lists_taxonomy():
    a = _agent()
    states = a.mental_states()
    for expected in ("belief", "desire", "intention", "knowledge", "perception"):
        assert expected in states
