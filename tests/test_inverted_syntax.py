"""test_inverted_syntax — ROLE BY ARGUMENT STRUCTURE, NOT POSITION.

Locks the fix for the NON-SVO / INVERTED-verse ceiling that defeated the
Jabberwocky summit: reading_collapse's clause parser assumed SVO by POSITION, so
archaic inverted verse ('the manxome foe he sought' -- OSV; 'Into the room walked
a tall man' -- VS) mis-slotted the subject and the pronoun hero fragmented. The
fix binds verb arguments by the held POS + pronoun CASE (he/she/they = subject,
him/her/them = object) rather than by clause position, and recognises the common
non-SVO orders (fronted object, post-posed subject, verb-subject) from the
argument-structure signals.

Graph-native: role binding is the held argument-structure / POS / case faculty;
no clause-POSITION assumption, no hardcoded inversion literal, no `import re`.

CRITICAL: plain SVO must NOT regress -- the crow's SVO parse is the hard guard
(tests/test_crow_gate.py + jabberwock_reads_the_crow's byte-identity). This file
adds the inverted-order cases + a couple of SVO controls that must stay put.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_inverted_syntax.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                         # noqa: E402
from domains import dictionary_lexicon as dl                      # noqa: E402
from domains import reading_collapse as rc                        # noqa: E402
from domains import coref_entities as ce                          # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _lex(ag):
    rc.ensure_codebook(ag)
    sub, _, _ = rc._resolve(ag)
    return rc._marker_lexicon(sub)


# --------------------------------------------------------------------------- #
#  ROLE BY CASE — the pronoun's case, not its slot, decides subject/object.
# --------------------------------------------------------------------------- #
def test_osv_fronted_object_binds_subject_by_case():
    """'the manxome foe he sought' (OBJECT-fronted, OSV): 'he' (nominative) is the
    SUBJECT though it sits post-object, 'the manxome foe' the fronted OBJECT."""
    ag = _fresh()
    preds = rc._event_predication_graph(
        ag, ["long", "time", "the", "manxome", "foe", "he", "sought"], _lex(ag))
    assert ["sought", "he", "foe"] in preds


def test_vs_locative_inversion_binds_postposed_subject():
    """'Into the room walked a tall man' (VERB-subject, fronted adjunct PP): the
    post-verb nominal 'man' is the SUBJECT, not the PP object 'room'."""
    ag = _fresh()
    preds = rc._event_predication_graph(
        ag, ["into", "the", "room", "walked", "a", "tall", "man"], _lex(ag))
    assert ["walked", "man", "room"] in preds


def test_possessive_her_is_not_an_accusative_object():
    """'her' is BOTH object pronoun and possessive determiner: 'seek her fortune'
    is possessive (fortune is the object), NOT sought(x, her)."""
    ag = _fresh()
    preds = rc._event_predication_graph(
        ag, ["mira", "left", "home", "to", "seek", "her", "fortune"], _lex(ag))
    # subject mira, object the fronted home -- 'her' never lands in a core slot.
    assert preds and preds[0][:2] == ["left", "mira"]
    assert all(p[1] != "her" and (len(p) < 3 or p[2] != "her") for p in preds)


# --------------------------------------------------------------------------- #
#  SVO MUST NOT REGRESS — plain subject-verb-object is byte-for-byte the old parse.
# --------------------------------------------------------------------------- #
def test_plain_svo_unchanged():
    ag = _fresh()
    lex = _lex(ag)
    assert ["dropped", "crow", "pebbles"] in rc._event_predication_graph(
        ag, ["the", "crow", "dropped", "the", "pebbles"], lex)
    # nominative subject + accusative object in canonical order (crow's 'he dropped
    # them') -> unchanged.
    assert ["dropped", "he", "them"] in rc._event_predication_graph(
        ag, ["he", "dropped", "them"], lex)


def test_svo_clause_is_not_an_inversion_fallback():
    """The coref fallback fires ONLY on genuine inversions -- a canonical SVO clause
    returns [] from event_predication_for_sentence so read_clause keeps it
    byte-identical (the mira/mouse throughline reports must not move)."""
    ag = _fresh()
    assert rc.event_predication_for_sentence(ag, "She met a starving dog") == []
    # but a VS / bare-intransitive-pronoun inversion DOES produce a parse.
    assert rc.event_predication_for_sentence(ag, "Into the room walked a tall man")
    assert rc.event_predication_for_sentence(ag, "Slowly he rose") == [["rose", "he"]]


# --------------------------------------------------------------------------- #
#  END-TO-END — the prose inversion test: subject binds, pronoun threads.
# --------------------------------------------------------------------------- #
def test_prose_inversion_subject_binds_and_pronoun_threads():
    """'Into the room walked a tall man. Slowly he rose.' -> walked's subject is the
    MAN (VS), and the next sentence's 'he' (post-adverb subject) resolves to that
    man -- the pronoun subject threads across the inversion."""
    ag = _fresh()
    r = ce.read_into_situation_model(
        ag, "Into the room walked a tall man. Slowly he rose.")
    tb = r["textbase"]
    walked = [p for s in tb for p in s["predications"] if p and p[0] == "walked"]
    assert walked and walked[0][1] == "man"          # subject = man, not 'room'/'into'
    he = [x for x in r["resolutions"] if x["surface"] == "he"]
    assert he and he[0]["resolved"] and he[0]["concept"] == "man"
    assert "man" in r["situation_model"] and "into" not in r["situation_model"]
