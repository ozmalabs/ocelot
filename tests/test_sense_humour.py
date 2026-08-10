"""test_sense_humour — the jabberwock's SENSE OF HUMOUR (domains/sense_of_humour.py): SALIENCE for
BENIGN INCONGRUITY. Recognize that a turn is humorous (an incongruity that resolves playfully) and
respond IN KIND (play along / top it), NOT literally. DISCRIMINATIVE, donkey=0.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

import domains.sense_of_humour as hm


# ===========================================================================
# BENIGN INCONGRUITY -> humorous + a response IN KIND (not literal).
# ===========================================================================
def test_cross_domain_incongruity_is_humorous():
    a = hm.detect_humour("I asked the compiler for relationship advice.")
    assert a["humorous"] is True
    assert a["benign"] is True
    assert a["kind"] == "cross_domain"
    # the response PLAYS ALONG (tops it), it does not literally answer.
    r = a["response"].lower()
    assert "play along" in r
    assert "here is how" not in r and "you should" not in r        # not a literal answer


def test_wordplay_incongruity_is_humorous():
    a = hm.detect_humour("The frobulation was delightful today.")
    assert a["humorous"] is True and a["kind"] == "wordplay"
    assert "play along" in a["response"].lower()


# ===========================================================================
# DISCRIMINATIVE — a plain literal turn is NOT humorous.
# ===========================================================================
def test_plain_literal_turn_is_not_humorous():
    a = hm.detect_humour("The meeting is at three o'clock tomorrow.")
    assert a["humorous"] is False
    assert a["response"] is None


def test_same_domain_turn_is_not_humorous():
    # a technical setup with a technical resolution -> no cross-domain clash, no incongruity.
    a = hm.detect_humour("I asked the compiler to build the project.")
    assert a["humorous"] is False


# ===========================================================================
# BENIGN — a hostile incongruity is NOT play-along (don't play with an insult).
# ===========================================================================
def test_hostile_incongruity_is_not_benign():
    a = hm.detect_humour("You stupid idiot, I hate your relationship advice, damn compiler!")
    assert a["benign"] is False
    assert a["humorous"] is False        # incongruity present but NOT benign -> not play-along


# ===========================================================================
# RESPOND IN KIND — composed from the incongruity parts, register-shaped.
# ===========================================================================
def test_response_is_composed_from_parts_not_a_table():
    a1 = hm.detect_humour("I asked the compiler for relationship advice.")
    a2 = hm.detect_humour("The frobulation was delightful today.")
    # two DIFFERENT incongruities -> two DIFFERENT composed responses (not one canned string).
    assert a1["response"] != a2["response"]


def test_no_bespoke_ml_classifier_in_source():
    import inspect
    src = inspect.getsource(hm)
    for bad in (".fit(", ".backward(", "import numpy", "import torch", "sklearn"):
        assert bad not in src


# ===========================================================================
# LIVE — humour routes through the real converse loop (world_adapter wiring).
# ===========================================================================
pytest.importorskip("substrate_rs")
from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402


def _live_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


def test_live_benign_incongruity_answered_in_kind():
    a = _live_agent()
    reply = a.converse("I asked the compiler for relationship advice.", "statement").lower()
    assert "play along" in reply             # in kind, not a literal answer
    assert reply.strip() != "noted"          # not the plain acknowledgment
    assert a._donkey["n"] == 0


def test_live_plain_statement_still_acknowledged():
    # discriminative regression: a non-humorous statement keeps its canonical 'noted'.
    a = _live_agent()
    assert a.converse("the sky is blue", "statement") == "noted"
