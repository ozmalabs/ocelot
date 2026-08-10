"""test_reference_overfire — the own-name / reference recognition must fire ONLY on a
GENUINE reference in the INTERLOCUTOR'S utterance, never on a plain self-identity
question, a farewell/greeting/thanks, or merely because the agent is named Jabberwock.

Two bugs, both driven on the REAL converse loop (donkey=0 throughout):

  BUG 1 (over-fire): "What are you?" and a farewell got the Carroll name-as-reference
  explanation instead of a self-identity answer / a closing. The own-name path is now
  gated on `sense_of_reference.is_name_inquiry` (a name word + self-ref, or the literal
  name in the user's text) and comprehend_text routes self-identity questions to the
  self_identity faculty — so the name explanation is reserved for genuine name inquiries.

  BUG 2 (ornate self-question mis-routing): bare "What are you?" fast-pathed the
  construction table to know('you') -> "I don't know you"; "what SORT of thing are you?"
  grounded to the sorting_principle faculty -> a raw "organising PRINCIPLES" dump. Both
  now intercept in comprehend_text to the self_identity faculty (a real self answer).

DISCRIMINATIVE: the endpoint (a genuine name question -> the Carroll explanation) and the
genuine interlocutor references (a gamer "would you kindly" -> BioShock; a graduated
concept) are PRESERVED — the fix narrows the trigger, it does not disable the faculty.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.sense_of_reference as sr


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


_NAME_EXPL = "coinage from carroll"          # a fragment unique to the own-name explanation


# ---------------------------------------------------------------------------
# BUG 1 — over-fire: the name explanation must NOT fire on non-references.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", ["What are you?", "Pray, tell me plainly: what are you?"])
def test_self_identity_question_reaches_self_identity_not_name(agent, text):
    low = agent.converse(text, "question").lower()
    assert _NAME_EXPL not in low                 # NOT the name-as-reference explanation
    assert "i don't know you" not in low         # NOT the know('you') mis-grounding
    assert "jabberwock" in low or "i am" in low  # a real self-identity answer


@pytest.mark.parametrize("text,sa", [
    ("I thank you kindly. I bid you good day.", "statement"),
    ("I bid you good day.", "statement"),
    ("goodbye", "farewell"),
])
def test_farewell_does_not_get_name_explanation(agent, text, sa):
    low = agent.converse(text, sa).lower()
    assert _NAME_EXPL not in low                 # a farewell/closing, never the name explanation


# ---------------------------------------------------------------------------
# BUG 2 — the "organising principles" raw dump / know('you') is gone.
# ---------------------------------------------------------------------------

def test_what_sort_of_thing_reaches_a_real_self_answer(agent):
    low = agent.converse("what sort of thing are you?", "question").lower()
    assert "organising principles" not in low    # NOT the raw sorting_principle dump
    assert "genus" not in low
    assert "jabberwock" in low or "i am" in low   # a real self answer


# ---------------------------------------------------------------------------
# ENDPOINT PRESERVED — a genuine NAME inquiry still gets the Carroll explanation.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Why are you named Jabberwock?",
    "Whence comes your name?",
    "Are you the Jabberwock?",
])
def test_name_inquiry_still_gets_carroll_explanation(agent, text):
    low = agent.converse(text, "question").lower()
    assert "carroll" in low and "reference" in low


# ---------------------------------------------------------------------------
# TRIGGER GATE (unit) — is_name_inquiry is discriminative.
# ---------------------------------------------------------------------------

def test_is_name_inquiry_gate_discriminates():
    # genuine name references (literal name, or a "your name" question) -> True
    for yes in ("Why are you named Jabberwock?", "Whence comes your name?",
                "Are you the Jabberwock?", "What is your name?"):
        assert sr.is_name_inquiry(yes) is True, yes
    # a plain self-identity question / social act / bare topic -> False
    for no in ("What are you?", "what sort of thing are you?", "I bid you good day.",
               "goodbye", "hello", "I thank you kindly.", "How are you organised?",
               "Name one of your rules."):        # leading enumerate verb, not a name inquiry
        assert sr.is_name_inquiry(no) is False, no


def test_recognize_own_name_only_on_inquiry():
    assert sr.recognize_own_name("Are you the Jabberwock?") is not None
    assert sr.recognize_own_name("Whence comes your name?") is not None
    assert sr.recognize_own_name("What are you?") is None
    assert sr.recognize_own_name("I bid you good day.") is None


# ---------------------------------------------------------------------------
# GENUINE INTERLOCUTOR REFERENCE — still fires (manifold-conditioned), donkey=0.
# ---------------------------------------------------------------------------

_GAMER = ["I love BioShock and the city of Rapture.",
          "The respawn mechanics in that playthrough were brutal.",
          "I main a controller for those boss fights."]


def test_live_reference_still_fires_for_a_gamer():
    a = _agent()
    for t in _GAMER:
        a.converse(t, "statement")
    low = a.converse("Would you kindly open the door?", "question").lower()
    assert "bioshock" in low and "a man chooses" in low
    # a graduated concept lands in any manifold
    low2 = a.converse("We went down the rabbit hole on this problem.", "statement").lower()
    assert "wonderland" in low2 or "rabbit" in low2 or "reference" in low2
    assert a._donkey["n"] == 0
