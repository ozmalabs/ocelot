"""test_thematic_oblique -- THE THEMATIC LAYER via ORDER-N: oblique PP participants.

A canonical SVO clause's post-verbal prepositional phrase carries a thematic-role
PARTICIPANT ('drove his cart OVER the poor dog') that the SVO head-reduction
DROPPED -- so the dog never entered the thematic layer and a later 'crushed HIM'
had no dog to bind and fell to raw salience (which is what once dequantised the
sparrow male). reading_collapse now DESCENDS into the post-verbal PP (the order-N
descent) and registers an ANIMATE oblique head as a participant [verb, subj, obl],
so the thematic layer HOLDS it.

This is PREVENTION AT THE SOURCE: with the dog held as a live theme participant,
the crushing chain binds the correct referent by plain recency + gender and the
sparrow is never mis-gendered male -- the revision backstop no longer needs to
fire for it (0 sparrow gender revisions).

GATED to a WHOLE-CREATURE head (the WordNet chordate/invertebrate ancestry) marking
a genuine thematic-role PP (VerbNet prep->role), so an inanimate adjunct ('with a
little water', 'into the pitcher' -- pitcher.n.01 is a baseball player, a person-
sense trap the whole-creature gate excludes) is NOT captured and the crow fable is
byte-identical.

donkey = 0 (no LLM), no `import re`. Real (cached) Grimm prose + synthetic clauses.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_thematic_oblique.py -p no:randomly -q
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                        # noqa: E402
from domains import dictionary_lexicon as dl                     # noqa: E402
from domains import coref_entities as ce                         # noqa: E402
from domains import reading_collapse as rcol                     # noqa: E402
from domains import reading_corpus as rc                         # noqa: E402


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


# --------------------------------------------------------------------------- #
#  THE ANIMACY GATE -- whole creatures IN, artifacts / substances / person-sense
#  traps OUT (so the crow's inanimate PPs never capture and it stays byte-ident).
# --------------------------------------------------------------------------- #
def test_animate_nominal_gates_creatures_not_artifacts():
    for creature in ("dog", "sparrow", "horse", "cat", "mouse", "wolf"):
        assert rcol._animate_nominal(creature), creature
    # artifacts / substances / person-sense homonyms are NOT whole creatures.
    for thing in ("water", "pitcher", "cart", "whip", "milk", "jug", "pebble",
                  "hatchet", "window"):
        assert not rcol._animate_nominal(thing), thing


# --------------------------------------------------------------------------- #
#  OBLIQUE CAPTURE -- an animate PP head is registered as a participant on a
#  CANONICAL clause; an inanimate adjunct is not.
# --------------------------------------------------------------------------- #
def test_oblique_participant_captured_on_canonical_clause():
    agent = _fresh()
    lex = rcol._marker_lexicon(agent.s)

    def preds(clause):
        return rcol._event_predication_graph(agent, clause.split(), lex)

    # animate oblique -> an extra [verb, subj, creature] participant predication.
    dog = preds("the man drove his cart over the dog")
    assert ["drove", "man", "dog"] in dog
    assert ["drove", "man", "cart"] in dog          # the core object still stands

    sparrow = preds("the boy aimed a blow at the sparrow")
    assert ["aimed", "boy", "sparrow"] in sparrow

    # inanimate adjunct -> NO oblique participant captured (the crow byte-identity
    # guard). 'pitcher' here is the legitimate core OBJECT, not an oblique; the
    # inanimate PP head 'water' is dropped, so only the single SVO predication
    # stands (no extra [verb, subj, water]).
    water = preds("he filled the pitcher with water")
    assert ["filled", "he", "pitcher"] in water
    assert not any(p[-1] == "water" for p in water)
    milk = preds("she poured the milk into the jug")
    assert not any(p[-1] == "jug" for p in milk)


# --------------------------------------------------------------------------- #
#  PREVENTION AT THE SOURCE -- the sparrow is read female WITHOUT a gender
#  revision, because the dog enters the thematic layer as a participant.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def dog_sparrow_read():
    grimm = [s for s in rc.SOURCES if s["key"] == "grimm"]
    units = {u["label"]: u for u in rc.load_units(sources=grimm)}
    agent = _fresh()
    graph = ce.read_into_situation_model(agent, units["THE DOG AND THE SPARROW"]["text"],
                                         max_sentences=60)
    return graph


def test_sparrow_is_female_and_not_misgendered_at_source(dog_sparrow_read):
    graph = dog_sparrow_read
    sm = graph["situation_model"]
    assert sm.get("sparrow", {}).get("coref_gender") == "female"
    assert sm.get("dog", {}).get("coref_gender") == "male"
    # NO pronoun ever dequantises the sparrow male (prevention at the source) ...
    mis = [r for r in graph["resolutions"]
           if r.get("concept") == "sparrow" and r.get("gender") == "male"]
    assert mis == [], mis
    # ... so the revision backstop never needs to overturn the sparrow's gender.
    sparrow_revs = [r for r in graph["resolutions"]
                    if r.get("revision") and r["revision"].get("entity") == "sparrow"]
    assert sparrow_revs == [], sparrow_revs


def test_dog_held_as_a_thematic_participant(dog_sparrow_read):
    """The dog is a live participant of the reading -- it is tracked, animal, and
    (via the oblique descent + the crushing chain) recurs as a theme, which is what
    lets the crushing 'him' bind it instead of the sparrow."""
    sm = dog_sparrow_read["situation_model"]
    dog = sm.get("dog")
    assert dog is not None
    assert dog.get("coref_category") == "animal"
    assert float(dog.get("coref_mentions", 0.0) or 0.0) >= 2.0


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT -- graph data, no new Python decision, no import re.
# --------------------------------------------------------------------------- #
def test_oblique_capture_emits_graph_data_not_a_decision():
    # the oblique candidate is PRECOMPUTED via held lexical reads (WordNet animacy +
    # the VerbNet prep->role table) as EventClause attrs; the DECISION to append the
    # participant predication is graph-native (the VerbFrame decode + _ground_event
    # reading obl_animate/obl_role_ok), not a Python branch on graph state.
    src = inspect.getsource(rcol._precompute_role_candidates)
    assert "_oblique_prep_head" in src
    assert "_animate_nominal" in src
    assert "preposition_role" in src
    ground = inspect.getsource(rcol._ground_event)
    assert "obl_canon_head" in ground and "obl_animate" in ground


def test_no_import_re_in_reading_collapse_oblique_helpers():
    for fn in (rcol._animate_nominal, rcol._oblique_prep_head):
        tree = ast.parse(inspect.getsource(fn))
        for node in ast.walk(tree):
            assert not isinstance(node, (ast.Import, ast.ImportFrom)) or all(
                getattr(a, "name", "") != "re" for a in getattr(node, "names", []))
