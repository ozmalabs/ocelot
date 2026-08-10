"""test_inverted_multirole — ROLE-COMPLETENESS on inverted verse: bind ALL the
core roles through inverted order, not just the case-marked hero, and bind an OOV
NONSENSE noun as an argument.

This extends the argument-structure parse (reading_collapse._event_predication,
built on P1's case/inversion binding) so that MORE of a clause's roles fill through
non-SVO order — the deepest Jabberwocky parse residual (the middle roles of the
quest scattered; `full==0`). Three moves, all keyed on the held POS / case
faculty, all gated so canonical SVO prose is byte-identical:

  (1) LOCATIVE / ADJUNCT INVERSION fills BOTH subject and oblique. A fronted
      adjunct PP that consumes the whole pre-verb span ('Down the dark stair crept
      the frightened child') binds the post-verb nominal as the post-posed SUBJECT
      and the fronted PP's own head as the OBLIQUE — using the FULL fronted-PP span
      (det + adjective(s) + head), so an adjective-modified fronted PP no longer
      leaks its head noun into the subject slot.
  (2) OBLIQUE COMPLEMENT on a post-posed-subject clause ('So rested he by the
      Tumtum tree' -> rested(he, tree)): a genuinely inverted clause with no core
      object still binds its PP complement's head as the oblique argument.
  (3) OOV NOUNS bind as ARGUMENTS: 'his vorpal sword' -> took(he, sword), 'the
      Jabberwock' -> came(jabberwock, ...) — a recognized-but-unknown token is a
      valid nominal role filler (the segmentation-by-recognition OOV convention),
      never dropped.

  Plus the P1-named mis-ID fix: the FINITE MAIN verb is preferred over an earlier
  inflected form that reads noun/adj-primary in situ ('as in uffish thought he
  STOOD': 'stood', not 'thought').

Graph-native: role binding by the held argument-structure / POS / case faculty; no
clause-position assumption, OOV nouns bind as entities, no `import re`, donkey = 0.

CRITICAL: plain SVO must NOT regress — the crow's SVO parse is the hard guard
(tests/test_crow_gate.py + tests/test_inverted_syntax.py). This file adds the
multi-role inverted cases; the SVO controls in test_inverted_syntax stay put.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_inverted_multirole.py -p no:randomly -q
"""
from __future__ import annotations

import ast
import inspect
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
#  CLEAN INVERTED-PROSE MULTI-ROLE — the headline gate. All three core roles
#  bind through inverted order: subject (post-posed), adjunct (fronted PP),
#  object (shared-subject participial VP). Verbatim.
# --------------------------------------------------------------------------- #
def test_clean_inverted_prose_binds_all_three_roles():
    """'Down the dark stair crept the frightened child, clutching a candle.' ->
    SUBJECT = child (post-posed, threaded across both clauses), ADJUNCT = down the
    stair (the fronted PP head), OBJECT = candle. All three roles, not just the
    hero -- the adjective-modified fronted PP ('the DARK stair') no longer leaks
    its head into the subject slot."""
    ag = _fresh()
    d = rc.decompose_sentence(
        ag, "Down the dark stair crept the frightened child, clutching a candle.")
    preds = d["predications"]
    assert ["crept", "child", "stair"] in preds, preds      # subject + adjunct
    assert ["clutching", "child", "candle"] in preds, preds  # subject (threaded) + object
    # the post-posed subject is the CHILD, never the leaked PP head 'stair'.
    assert not any(p[1] == "stair" for p in preds if p[0] != "crept"), preds


def test_locative_inversion_fills_subject_and_oblique():
    """A single fronted-adjunct-PP clause fills BOTH roles: post-posed subject +
    fronted-PP-head oblique."""
    ag = _fresh()
    lex = _lex(ag)
    assert ["crept", "child", "stair"] in rc._event_predication_graph(
        ag, ["down", "the", "dark", "stair", "crept", "the", "frightened", "child"], lex)
    # the existing 'into the room' case (unmodified PP head) still holds.
    assert ["walked", "man", "room"] in rc._event_predication_graph(
        ag, ["into", "the", "room", "walked", "a", "tall", "man"], lex)


def test_postposed_subject_binds_oblique_complement():
    """'So rested he by the Tumtum tree' -> rested(he, tree): the post-posed
    nominative subject 'he' AND the PP complement's head 'tree' both bind, instead
    of collapsing to a bare intransitive that drops the ground."""
    ag = _fresh()
    preds = rc._event_predication_graph(
        ag, ["so", "rested", "he", "by", "the", "tumtum", "tree"], _lex(ag))
    assert ["rested", "he", "tree"] in preds, preds


# --------------------------------------------------------------------------- #
#  OOV NONSENSE NOUN as an ARGUMENT — a recognized-but-unknown token still fills
#  a role; it is never dropped.
# --------------------------------------------------------------------------- #
def test_oov_noun_binds_as_object_argument():
    """'He took his vorpal sword in hand' -> took(he, sword): the OOV-attributed
    noun phrase 'his vorpal sword' binds as the object (its head is a nominal even
    though 'vorpal' is pure nonsense)."""
    ag = _fresh()
    preds = rc._event_predication_graph(
        ag, ["he", "took", "his", "vorpal", "sword", "in", "hand"], _lex(ag))
    assert ["took", "he", "sword"] in preds, preds


def test_oov_noun_binds_as_subject_argument():
    """'The Jabberwock came whiffling ...' -> the OOV proper noun 'jabberwock' is a
    valid SUBJECT filler (0 WordNet synsets, still a nominal), so the event's agent
    is the nonsense entity, not dropped."""
    ag = _fresh()
    preds = rc._event_predication_graph(
        ag, ["the", "jabberwock", "came", "whiffling", "through", "the", "tulgey", "wood"],
        _lex(ag))
    assert preds and preds[0][:2] == ["came", "jabberwock"], preds


# --------------------------------------------------------------------------- #
#  MIS-ID FIX — the finite MAIN verb wins over a noun-primary inflected form.
# --------------------------------------------------------------------------- #
def test_finite_main_verb_preferred_over_noun_primary_inflected():
    """'as in uffish thought he stood' -> the finite verb is STOOD, not 'thought'
    (which morphy-maps to 'think' but reads noun-primary here, the object of
    'in'). The clause's subject 'he' binds to the STOOD event."""
    ag = _fresh()
    flat = ["as", "in", "uffish", "thought", "he", "stood"]
    vi = rc._find_main_verb(flat)
    assert vi is not None and flat[vi] == "stood", (vi, flat[vi] if vi is not None else None)
    preds = rc._event_predication_graph(ag, flat, _lex(ag))
    assert any(p[0] == "stood" and p[1] == "he" for p in preds), preds


# --------------------------------------------------------------------------- #
#  SVO MUST NOT REGRESS — the crow's canonical parse is byte-identical.
# --------------------------------------------------------------------------- #
def test_plain_svo_unchanged():
    ag = _fresh()
    lex = _lex(ag)
    assert ["dropped", "crow", "pebbles"] in rc._event_predication_graph(
        ag, ["the", "crow", "dropped", "the", "pebbles"], lex)
    assert ["dropped", "he", "them"] in rc._event_predication_graph(
        ag, ["he", "dropped", "them"], lex)
    # a canonical SVO clause is NOT treated as an inversion by the fallback.
    assert rc.event_predication_for_sentence(ag, "She met a starving dog") == []


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — no `import re`; role binding rides the held
#  argument-structure / POS / case helpers, no clause-position literal.
# --------------------------------------------------------------------------- #
def test_no_import_re_in_reading_collapse():
    src = inspect.getsource(rc)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re in reading_collapse"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import in reading_collapse"
