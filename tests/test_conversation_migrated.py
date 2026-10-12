"""Conversation layer, migrated — the speech-act taxonomy is graph data in the
conversation seed, and tagging / turn-spine / classification run on the
seed-booted WorldAdapter, no CuriousAgent.

  * speech-act taxonomy (Searle's five classes + the specific acts, each
    subtyped under its class) + the conversation Microtheory — all graph data
    the conversation seed installs (vs CuriousAgent's install_conversation).
  * classify_speech_act — the I/O-boundary classifier (surface cues only),
    mirrored on the adapter.
  * inbound/outbound Messages tagged with their speech act + a responds_to turn
    spine — mechanical I/O.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from substrate.boot_core import load_seeds_into
# canonical speech-act data (pure data, the seed's source of truth)
from domains.conversation import _SPEECH_ACTS, _SEARLE_CLASSES


def _booted():
    wa = WorldAdapter()
    load_seeds_into(wa.s, wa.agent, ["conversation"])
    return wa


# --- speech-act taxonomy as graph data ----------------------------------

def test_conversation_microtheory_is_graph_resident():
    wa = _booted()
    mts = {wa.s.node(n)["attrs"].get("name") for n in wa.s.nodes("Microtheory")}
    assert "conversation" in mts


def test_searle_classes_and_speech_acts_are_concepts():
    wa = _booted()
    for cls in _SEARLE_CLASSES:
        assert wa._concept_by_name(cls) is not None, cls
    for act, _cls, _desc in _SPEECH_ACTS:
        assert wa._concept_by_name(act) is not None, act


def test_acts_are_subtyped_under_their_searle_class():
    wa = _booted()
    for act, searle_class, _desc in _SPEECH_ACTS:
        kid = wa._concept_by_name(act)
        parents = {wa.s.node(p)["attrs"].get("name")
                   for p in wa.inner.neighbours(kid, "subtype_of")}
        assert searle_class in parents, f"{act} should subtype {searle_class}"


def test_seed_load_is_idempotent():
    wa = _booted()
    n_concepts = len(wa.s.nodes("Concept"))
    load_seeds_into(wa.s, wa.agent, ["conversation"])
    assert len(wa.s.nodes("Concept")) == n_concepts


# --- I/O-boundary classifier --------------------------------------------

@pytest.mark.parametrize("text,kind", [
    ("what is photosynthesis?", "question"),
    ("is 17 prime?", "question"),
    ("how does this work", "question"),
    ("who said that", "question"),
    ("tell me about X", "question"),
    ("can you help", "question"),
    ("I am Matt", "statement"),
    ("entropy is interesting", "statement"),
    ("hello", "greeting"),
    ("thanks", "thanks"),
    ("read foo.txt", "request"),
    ("Check the pressure.", "request"),
    ("When ready, close the hatch.", "request"),
    ("I check the pressure.", "statement"),
    ("When does the hatch close?", "question"),
    ("", "statement"),
])
def test_classify_speech_act(text, kind):
    assert WorldAdapter().classify_speech_act(text) == kind


# --- tagging + turn spine -----------------------------------------------

def test_inbound_message_tagged_with_speech_act():
    wa = WorldAdapter()
    mid = wa.add_inbound("what is photosynthesis?")
    sa = {wa.s.node(c)["attrs"].get("name")
          for c in wa.inner.neighbours(mid, "has_speech_act")}
    assert sa == {"question"}


def test_outbound_default_statement_tagged():
    wa = WorldAdapter()
    mid = wa.add_outbound("noted.")
    sa = {wa.s.node(c)["attrs"].get("name")
          for c in wa.inner.neighbours(mid, "has_speech_act")}
    assert sa == {"statement"}


def test_outbound_can_be_inquiry():
    wa = WorldAdapter()
    mid = wa.add_outbound("What does X mean?", kind="inquiry")
    sa = {wa.s.node(c)["attrs"].get("name")
          for c in wa.inner.neighbours(mid, "has_speech_act")}
    assert sa == {"inquiry"}


def test_messages_form_a_turn_spine_via_responds_to():
    wa = WorldAdapter()
    m1 = wa.add_inbound("hello")
    m2 = wa.add_outbound("noted.")
    m3 = wa.add_inbound("what is photosynthesis?")
    assert wa.responds_to(m1) == []         # first turn answers nothing
    assert m1 in wa.responds_to(m2)
    assert m2 in wa.responds_to(m3)
