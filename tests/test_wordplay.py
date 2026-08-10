"""test_wordplay — the jabberwock's namesake NONSENSE / COINAGE faculty
(domains/wordplay.py) + its live routing through converse.

The agent is named after Carroll's nonsense poem; it must ENGAGE a coinage
(infer a playful reading from its SHAPE) rather than collapse it to "I don't
hold that". These gates are DISCRIMINATIVE: a coinage engages the faculty; a
genuine unknown (a real proper noun / an opaque OOV token) does NOT get a
fabricated wordplay gloss — it still asks back / answers honestly. donkey=0
throughout (the reading is the morphology faculty's, no teacher call).
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from domains import wordplay as wp
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


@pytest.fixture(scope="module")
def agent():
    return _agent()


_ACKS = {"noted", "understood", "got it", "i don't hold that.",
         "i have no reply to that."}


# ---------------------------------------------------------------------------
# DETECTION — from grounded morphology / dictionary signals.
# ---------------------------------------------------------------------------

def test_affix_coinage_detected():
    a = wp.detect_coinage("frobulation")
    assert a is not None and a["kind"] == "affix"
    assert a["suffix"] == "ation"
    # the stem reduces to a REAL word (frob) — grounded, not invented.
    assert a["stem"] == "frob" and a["stem_real"] is True


def test_affix_gloss_and_reply_reference_the_shape():
    a = wp.detect_coinage("frobulation")
    gloss = wp.infer_gloss(a)
    assert "process" in gloss or "act" in gloss
    reply = wp.compose_reply(None, a)
    low = reply.lower()
    assert "frob" in low                       # references the morphology
    assert "act" in low or "process" in low    # the -ation act/process reading
    assert low.strip() not in _ACKS
    # honesty: it is flagged as a shape inference, not a claimed definition.
    assert "shape" in low or "sound" in low or "i'd read" in low or "i'd take" in low


def test_portmanteau_reading():
    a = wp.detect_coinage("slithy", in_definition_request=True)
    assert a is not None and a["kind"] == "blend"
    comps = set(a["components"])
    assert "lithe" in comps and "slimy" in comps      # slimy + lithe
    reply = wp.compose_reply(None, a).lower()
    assert "lithe" in reply and "slimy" in reply


def test_slithy_not_hijacked_outside_a_definition_request():
    # narrative use ("the slithy toves") must NOT be pulled into wordplay.
    assert wp.detect_coinage("slithy", in_definition_request=False) is None


# ---------------------------------------------------------------------------
# COINAGE vs GENUINE UNKNOWN — the pinned distinction.
# ---------------------------------------------------------------------------

def test_proper_noun_is_not_a_coinage():
    # a real place name is a genuine unknown to ASK about, never wordplay-glossed.
    assert wp.detect_coinage("Zanzibar") is None


def test_opaque_unknown_is_not_a_coinage():
    # a word-like OOV token with no morphological hook -> genuine unknown (ask-back).
    for tok in ("quorplezap", "glorp", "blorptangle", "flar"):
        assert wp.detect_coinage(tok) is None


def test_ordinary_known_word_is_not_a_coinage():
    for tok in ("happy", "organisation", "capable", "describe"):
        assert wp.detect_coinage(tok, in_definition_request=True) is None


def test_find_coinage_scans_a_sentence():
    assert wp.find_coinage("Do you find yourself capable of frobulation?")["word"] == "frobulation"
    assert wp.find_coinage("What does slithy mean?")["word"] == "slithy"
    assert wp.find_coinage("Tell me about Zanzibar.") is None
    assert wp.find_coinage("quorplezap the door") is None


# ---------------------------------------------------------------------------
# LIVE — the coinage routes through converse to a playful reply.
# ---------------------------------------------------------------------------

def test_live_frobulation_gets_a_playful_reply(agent):
    t = "Do you find yourself capable of frobulation?"
    reply = agent.converse(t, agent.classify_speech_act(t))
    low = reply.lower()
    assert low.strip() not in _ACKS
    assert "frob" in low
    assert "act" in low or "process" in low


def test_live_portmanteau_gets_a_blend_reading(agent):
    t = "What does slithy mean?"
    reply = agent.converse(t, agent.classify_speech_act(t))
    low = reply.lower()
    assert low.strip() not in _ACKS
    assert "lithe" in low and "slimy" in low


def test_live_genuine_unknown_is_not_wordplay(agent):
    # a genuine unknown proper noun -> honest-unknown, NOT a fabricated gloss.
    t = "What is a Zanzibar?"
    reply = agent.converse(t, agent.classify_speech_act(t))
    low = reply.lower()
    assert "frob" not in low and "blend" not in low     # no wordplay fabrication
    assert "don't know" in low or "not familiar" in low or "zanzibar" in low


def test_donkey_stays_zero(agent):
    # exercise the faculty then confirm no teacher call was made.
    agent.converse("Do you find yourself capable of frobulation?", "question")
    assert agent._donkey["n"] == 0
