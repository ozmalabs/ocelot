"""test_topic_span_migrated -- BLIND-SPOT CLOSURE R7 (multi-word topic keys
miss the HeldAnswer bridge, e.g. "the Wright brothers").

`world_adapter._topic_facts` (the frame-based NP extraction the general
topic route reads) and `shadow_focus` (`reading_collapse.read_clause`'s own
head-only reduction) both reduce a multi-word proper-noun topic to its HEAD
noun ("wright" / "brothers" for "the Wright brothers") -- never matching the
HeldAnswer bridge's key, the deep reader's OWN multi-word entity name
("wright_brothers", minted at document ingest by
`world_adapter._mint_document_held_answers` off the SAME `coref_entities`
naming convention).

THE CLOSURE (seeds/conversation_topic_span.json::
route_shadow_topic_to_answer): `world_adapter._shadow_read_turn` mechanically
records `shadow_doc_topic` -- does one of THIS turn's newly-minted SmEntities
carry a name that equals an EXISTING HeldAnswer topic (a graph fact, two
independent reads of the same deterministic entity-naming landing on the
same string, never a new NP-span heuristic). The new rule mints the SAME
Goal{kind:answer_topic} shape `route_question_to_topic` mints, keyed on the
richer name; `route_question_to_topic` gained one static deferral guard
(mirroring its existing "your/yours possessive" deferral) so the two rules
never double-mint.
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import dictionary_lexicon as dl
import domains.file_ingest as fi
import domains.topic_grounding as tg


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fail_ground(agent, phrase, **kw):
    """Deterministic stand-in for network grounding: always an honest miss
    (the SAME idiom test_document_memory_migrated.py uses) -- the closure
    proof must come from the document bridge, never a lucky network hit."""
    return None


def _fresh(*, deep_ingest=True, shadow_read=True):
    a = WorldAdapter(seeds=(), shadow_read=shadow_read, deep_ingest=deep_ingest)
    load_all_seeds(a)
    return a


WRIGHT_DOC = (
    "The Wright brothers were American aviation pioneers. They built the "
    "first successful motor-operated airplane. They flew it near Kitty Hawk "
    "in 1903.")


def _ingest(a, text, name="doc.txt"):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        return fi.ingest_file(a, path, filename=name)
    finally:
        os.unlink(path)


def _has_rule(a, name):
    return any(r.get("name") == name for r in a.inner.export_rules())


# --------------------------------------------------------------------------- #
#  THE CLOSURE: the exact failing case -- multi-word document entity.
# --------------------------------------------------------------------------- #
def test_multiword_topic_answers_from_the_document_bridge(monkeypatch):
    monkeypatch.setattr(tg, "ground_topic", _fail_ground)
    a = _fresh()
    assert _has_rule(a, "route_shadow_topic_to_answer")
    out = _ingest(a, WRIGHT_DOC, name="wright.txt")
    assert a.s.node(out["document_id"])["attrs"].get("deep_read") == 1.0

    held = {a.s.node(n)["attrs"].get("topic") for n in a.s.nodes("HeldAnswer")}
    assert "wright_brothers" in held, held

    reply = a.converse("What do you know about the Wright brothers?",
                       speech_act="question")
    assert "don't hold anything about" not in reply.lower(), reply
    assert "wright" in reply.lower(), reply
    mid = a._last_turn_inbound
    at = a.s.node(mid)["attrs"]
    assert at.get("shadow_doc_topic") == "wright_brothers", at
    assert at.get("topic_replied") == 1.0, at
    goals = [g for g in a.inner.neighbours(a.agent, "has_goal")
             if a.s.node(g)["attrs"].get("kind") == "answer_topic"
             and mid in list(a.inner.neighbours(g, "comprehends"))]
    assert len(goals) == 1, "route_question_to_topic must have deferred, not co-fired"
    assert a.s.node(goals[0])["attrs"].get("concept") == "wright_brothers"


# --------------------------------------------------------------------------- #
#  PARITY: single-token topics + the existing document_memory battery stay
#  byte-unchanged (no shadow_doc_topic ever competes with a clean single-word
#  match, and a topic the document never mentions still takes the old path).
# --------------------------------------------------------------------------- #
SATURN_DOC = ("Saturn is the sixth planet from the Sun. Saturn has a "
              "prominent ring system made of ice. Jupiter is the largest "
              "planet in the solar system.")


def test_single_token_topic_unchanged(monkeypatch):
    monkeypatch.setattr(tg, "ground_topic", _fail_ground)
    a = _fresh()
    _ingest(a, SATURN_DOC, name="saturn.txt")
    reply = a.converse("What do you know about Saturn?", speech_act="question")
    assert "saturn" in reply.lower(), reply
    mid = a._last_turn_inbound
    at = a.s.node(mid)["attrs"]
    # the shadow topic, if present at all, agrees with the old parse for a
    # single clean token -- no observable behaviour change either way.
    assert at.get("comp_topic") in (None, "saturn"), at


def test_topic_not_in_any_document_takes_the_old_honest_path(monkeypatch):
    monkeypatch.setattr(tg, "ground_topic", _fail_ground)
    a = _fresh()
    _ingest(a, WRIGHT_DOC, name="wright.txt")
    reply = a.converse("What do you know about photosynthesis?", speech_act="question")
    assert "don't hold anything about" in reply.lower(), reply
    assert "photosynthesis" in reply.lower(), reply
    mid = a._last_turn_inbound
    assert a.s.node(mid)["attrs"].get("shadow_doc_topic") is None


def test_deep_ingest_off_is_byte_identical(monkeypatch):
    monkeypatch.setattr(tg, "ground_topic", _fail_ground)
    a = _fresh(deep_ingest=False, shadow_read=False)
    _ingest(a, WRIGHT_DOC, name="wright.txt")
    assert list(a.s.nodes("HeldAnswer")) == []
    reply = a.converse("What do you know about the Wright brothers?",
                       speech_act="question")
    assert "wright_brothers" not in reply.lower()
    mid = a._last_turn_inbound
    assert a.s.node(mid)["attrs"].get("shadow_doc_topic") is None


def test_self_referential_question_still_defers_to_self_meta(monkeypatch):
    """A genuinely agent-directed question must not be hijacked even if a
    document happens to be loaded -- shadow_doc_topic only ever names an
    entity the SHADOW READ of THIS turn's own text minted, so an unrelated
    'what are you' turn mints no such entity and this path is inert."""
    monkeypatch.setattr(tg, "ground_topic", _fail_ground)
    a = _fresh()
    _ingest(a, WRIGHT_DOC, name="wright.txt")
    reply = a.converse("What are you?", speech_act="question")
    assert "jabberwock" in reply.lower(), reply
    mid = a._last_turn_inbound
    assert a.s.node(mid)["attrs"].get("shadow_doc_topic") is None


# --------------------------------------------------------------------------- #
#  CLOSURE PROOF (agent-in-control): ablating the deferral-aware rule reverts
#  to the OLD head-truncated miss, proving the fix lives in graph data.
# --------------------------------------------------------------------------- #
def test_ablating_the_rule_reverts_to_the_old_head_truncated_miss(monkeypatch):
    monkeypatch.setattr(tg, "ground_topic", _fail_ground)
    a = _fresh()
    _ingest(a, WRIGHT_DOC, name="wright.txt")
    idx = None
    for i, r in enumerate(a.inner.export_rules()):
        if isinstance(r, dict) and r.get("active", True) and \
                r.get("name") == "route_shadow_topic_to_answer":
            idx = i
            break
    assert idx is not None
    assert a.inner.remove_rule(idx) is True

    reply = a.converse("What do you know about the Wright brothers?",
                       speech_act="question")
    assert "wright_brothers" not in reply.lower(), (
        "ablating the rule must revert to the old head-truncated concept", reply)
