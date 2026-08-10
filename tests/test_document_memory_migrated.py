"""test_document_memory_migrated — Deep-Reader Wave 4 (final wave of the
unification), mission 1+2: DOCUMENTS GET DEEPLY READ + THE HELDANSWER BRIDGE.

Today an uploaded text document (`domains/file_ingest.py::_ingest_text`)
mints an `UploadedDocument` + tokenises `Mention`s and calls `comprehend()`,
but never reaches the deep reader — its content is invisible to the
topic-answer machinery that already serves conversational facts. This wave
routes an ingested document through the FULL deep read (register-routed
aperture — `register_source.route_reading` decides encyclopedic/narrative/
casual BY SHAPE, never a Python if/else) and mints a HELDANSWER BRIDGE: the
flow's own salient entities' resolved predications become queryable
`HeldAnswer` content via the EXISTING topic-answer rules
(`reply_topic_from_held_answer` / `_answer_topic_reply` / `answer_about`) —
NO new reply machinery, no new routing rule for the QA path itself.

Opt-in, one-shot at ingest, gated by the SAME flag family as the Wave 2
shadow read (`WorldAdapter.deep_ingest`, defaulting to `shadow_read`): a
bench agent that never sets it is byte-unchanged (no flow, no HeldAnswers).
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

from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from domains import dictionary_lexicon as dl                           # noqa: E402
import domains.file_ingest as fi                                       # noqa: E402
import domains.topic_grounding as tg                                   # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh(*, deep_ingest=None, shadow_read=None):
    a = WorldAdapter(seeds=(), shadow_read=shadow_read, deep_ingest=deep_ingest)
    load_all_seeds(a)
    return a


def _write_tmp(text: str, suffix=".txt") -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
        f.write(text)
        return f.name


# A short, clean ENCYCLOPEDIC lead (proper-noun-repeated, impersonal, no
# pronoun-agreement fragility) — deliberately simple so the salient entity
# and its predications are unambiguous for the gate.
ENCYCLOPEDIC_DOC = (
    "Saturn is the sixth planet from the Sun. Saturn has a prominent ring "
    "system made of ice. Jupiter is the largest planet in the solar system.")

# The committed crow-fable corpus (register_source's own proven narrative
# fixture — narrative family, protagonist_by_arc_agency, crow byte-identical).
FABLE_DOC = (
    "In a spell of dry weather, when the Birds could find very little to drink, "
    "a thirsty Crow found a pitcher with a little water in it. But the pitcher "
    "was high and had a narrow neck, and no matter how he tried, the Crow could "
    "not reach the water. The poor thing felt as if he must die of thirst. Then "
    "an idea came to him. Picking up some small pebbles, he dropped them into "
    "the pitcher one by one. With each pebble the water rose a little higher "
    "until at last it was near enough so he could drink.")


def _fail_ground(agent, phrase, **kw):
    """Deterministic stand-in for network grounding: always an honest miss."""
    return None


# --------------------------------------------------------------------------- #
#  MISSION 1 + 2 — encyclopedic ingest -> register verdict + HeldAnswer bridge
#  -> "What do you know about <entity>?" answers from the DOCUMENT.
# --------------------------------------------------------------------------- #
def test_encyclopedic_ingest_mints_flow_register_and_held_answers(monkeypatch):
    monkeypatch.setattr(tg, "ground_topic", _fail_ground)
    a = _fresh(deep_ingest=True, shadow_read=True)
    path = _write_tmp(ENCYCLOPEDIC_DOC)
    try:
        out = fi.ingest_file(a, path, filename="saturn.txt")
    finally:
        os.unlink(path)
    doc = out["document_id"]
    attrs = a.s.node(doc)["attrs"]

    assert attrs.get("deep_read") == 1.0, "deep_ingest=True must run the deep read"
    assert attrs.get("deep_read_error") is None, attrs
    assert attrs.get("register") in ("wikipedia", "encyclopedic"), attrs
    assert attrs.get("read_approach") == "subject_by_salience"
    assert attrs.get("deep_read_flow") is not None

    linked = list(a.inner.neighbours(doc, "read_as"))
    assert linked, "UploadedDocument -read_as-> SentenceParse chain missing"

    held = {a.s.node(n)["attrs"].get("topic"): a.s.node(n)["attrs"].get("text")
            for n in a.s.nodes("HeldAnswer")}
    assert "saturn" in held, held
    assert "saturn" in held["saturn"].lower()

    # Salient-only: bounded, not a HeldAnswer per token (the doc tokenises to
    # dozens of Mentions, but HeldAnswers stay in the single digits).
    assert 0 < len(held) <= WorldAdapter._DOC_HELD_ANSWER_TOP_N

    # The QA path: "What do you know about Saturn?" answers from the
    # document's OWN read structure via the EXISTING topic-answer rules —
    # no network grounding needed (monkeypatched to fail above).
    reply = a.converse("What do you know about Saturn?", speech_act="question")
    assert "saturn" in reply.lower()
    mid = a._last_turn_inbound
    assert a.s.node(mid)["attrs"].get("topic_replied") == 1.0


def test_topic_not_in_document_takes_the_old_path_unchanged(monkeypatch):
    """A topic the document never mentions must be byte-identically the old
    behaviour (grounding attempt, honest floor on a miss) — the bridge only
    ADDS HeldAnswers for what the document actually said."""
    monkeypatch.setattr(tg, "ground_topic", _fail_ground)
    a = _fresh(deep_ingest=True, shadow_read=True)
    path = _write_tmp(ENCYCLOPEDIC_DOC)
    try:
        fi.ingest_file(a, path, filename="saturn.txt")
    finally:
        os.unlink(path)

    held_topics = {a.s.node(n)["attrs"].get("topic") for n in a.s.nodes("HeldAnswer")}
    assert "photosynthesis" not in held_topics

    reply = a.converse("What do you know about photosynthesis?", speech_act="question")
    assert "don't hold anything about" in reply.lower()
    assert "photosynthesis" in reply.lower()


def test_deep_ingest_off_is_byte_identical_to_today():
    off = _fresh(deep_ingest=False, shadow_read=False)
    path = _write_tmp(ENCYCLOPEDIC_DOC)
    try:
        out = fi.ingest_file(off, path, filename="saturn.txt")
    finally:
        os.unlink(path)
    doc = out["document_id"]
    attrs = off.s.node(doc)["attrs"]
    for k in ("deep_read", "deep_read_error", "register", "read_approach", "deep_read_flow"):
        assert k not in attrs, "%r must not be written when deep_ingest is off" % k
    assert list(off.inner.neighbours(doc, "read_as")) == []
    assert list(off.s.nodes("HeldAnswer")) == []
    assert list(off.s.nodes("SentenceParse")) == []


def test_deep_ingest_defaults_to_shadow_read_setting():
    a_off = WorldAdapter(seeds=())
    assert a_off.deep_ingest is False
    a_on = WorldAdapter(seeds=(), shadow_read=True)
    assert a_on.deep_ingest is True
    a_explicit = WorldAdapter(seeds=(), shadow_read=True, deep_ingest=False)
    assert a_explicit.deep_ingest is False


# --------------------------------------------------------------------------- #
#  MISSION 1 (register routing) on NARRATIVE text -> protagonist path,
#  HeldAnswers reflect the arc-salient character.
# --------------------------------------------------------------------------- #
def test_narrative_ingest_routes_protagonist_and_held_answers_are_arc_salient(monkeypatch):
    monkeypatch.setattr(tg, "ground_topic", _fail_ground)
    a = _fresh(deep_ingest=True, shadow_read=True)
    path = _write_tmp(FABLE_DOC)
    try:
        out = fi.ingest_file(a, path, filename="fable.txt")
    finally:
        os.unlink(path)
    doc = out["document_id"]
    attrs = a.s.node(doc)["attrs"]
    assert attrs.get("register") == "narrative", attrs
    assert attrs.get("read_approach") == "protagonist_by_arc_agency"

    held = {a.s.node(n)["attrs"].get("topic"): a.s.node(n)["attrs"].get("text")
            for n in a.s.nodes("HeldAnswer")}
    assert "crow" in held, held
    # The crow is the arc-salient character (highest coref-mention count) --
    # its HeldAnswer text renders actual story predications, not a stub.
    assert "crow" in held["crow"].lower()

    reply = a.converse("What do you know about the crow?", speech_act="question")
    assert "crow" in reply.lower()


# --------------------------------------------------------------------------- #
#  CANON ROUND-TRIP — no new rules were needed for the bridge, but confirm
#  the bridge's own guard rails (the cap constant) stay sane.
# --------------------------------------------------------------------------- #
def test_held_answer_top_n_is_a_real_bound():
    assert 1 <= WorldAdapter._DOC_HELD_ANSWER_TOP_N <= 20
    assert 1 <= WorldAdapter._DOC_HELD_ANSWER_MAX_LINES <= 20
    assert 50 <= WorldAdapter._DOC_HELD_ANSWER_MAX_CHARS <= 2000
