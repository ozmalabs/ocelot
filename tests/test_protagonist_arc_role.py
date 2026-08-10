"""test_protagonist_arc_role — THE PROTAGONIST BY ARC-ROLE, not by frequency.

THE FRONTIER (named at the corpus summit): the reader's QA/roster identifies the
protagonist by FREQUENCY (most-mentioned), so on Grimm's 'The Travelling
Musicians' it names robbers(x5)/mistress(x4) over the four animal MUSICIANS who
DRIVE the story. The protagonist is WHO THE STORY IS ABOUT — the AGENT of the
narrative ARC (the entity whose agency runs across setup -> conflict ->
resolution) — NOT who is named most.

This gate asserts the fix: `domains.narrative_structure.protagonist_by_arc_agency`
decides the protagonist graph-natively (one `Argmax` Term over the clean, animate
character pool, scored by ARC-AGENCY weighted by ARC-SPAN — the DSL evaluator
picks it, Python never `max()`/`sorted()`s the decision) and NAMES the arc-role
lead, changing the answer where frequency was wrong:

  · Travelling Musicians -> an ANIMAL of the acting quartet (the dog), NOT
    robbers/mistress  [the fix CHANGES the answer]
  · Cat and Mouse -> the cat (the deceiver-agent driving the arc)
  · Dog and Sparrow -> the sparrow (the avenger-agent)

THE HARD GUARD: on the short crow fable the protagonist is UNCHANGED (crow) — the
crow is BOTH the arc-agent (agency across the whole fable) AND the salient lead,
so the arc computation names it, byte-identical in outcome to the reader that
already treats the crow as the hero.

donkey = 0 (no LLM), no `import re`. Real (cached) Grimm prose.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_protagonist_arc_role.py -p no:randomly -q
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
from domains import comprehension_reader as cr                   # noqa: E402
from domains import narrative_structure as ns                    # noqa: E402
import jabberwock_reads_a_tale as jt                              # noqa: E402


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


# real (cached) Grimm tales, read once for the whole module (slow) --------------
@pytest.fixture(scope="module")
def tales():
    return {rec["label"]: rec for rec in jt.run()}


# the crow's short fable (the byte-identity guard) reuses test_narrative_structure's
# verbatim FABLE_TEXT / NONNARR_TEXT so the crow arc is exactly the committed one.
FABLE_TEXT = (
    "In a spell of dry weather, when the Birds could find very little to "
    "drink, a thirsty Crow found a pitcher with a little water in it. "
    "But the pitcher was high and had a narrow neck, and no matter how he "
    "tried, the Crow could not reach the water. "
    "The poor thing felt as if he must die of thirst. "
    "Then an idea came to him. "
    "Picking up some small pebbles, he dropped them into the pitcher one by "
    "one. "
    "With each pebble the water rose a little higher until at last it was "
    "near enough so he could drink."
)
NONNARR_TEXT = "The sun rose. A car passed. It rained."


# --------------------------------------------------------------------------- #
#  REAL GRIMM TALES — the arc-role protagonist, not the most-frequent.
# --------------------------------------------------------------------------- #
def test_travelling_musicians_names_an_animal_not_the_robbers(tales):
    """The headline: arc-agency names an ANIMAL of the travelling quartet (the dog
    acts across the whole arc), NOT the most-mentioned entity. The fix CHANGES the
    answer — the arc protagonist differs from the frequency protagonist.

    DELIBERATE UPDATE (was: freq == 'ass'). The argument-structure parse corrections
    (complementizer-'that' embedded-clause split, REL-modifier subject threading, the
    nominal-only character pool, and designate-as-naming) stop minting predicative
    complements as agents and let the robbers' own actions be counted, so the robbers
    re-take the mention LEAD. The specific frequency winner is IMMATERIAL — a
    protagonist is the arc-agent, not the most-mentioned surface (frequency is a
    DECOY). The invariant this test guards is that the arc-role verdict (dog, the
    widest arc-span animal) DIFFERS from whatever the frequency lead is."""
    rec = tales["THE TRAVELLING MUSICIANS"]
    arc = rec["arc_protagonist"]
    freq = rec["freq_protagonist"]["name"]
    assert freq != arc["protagonist"]              # frequency is a DECOY, not the protagonist
    assert arc["protagonist"] not in ("robbers", "mistress", "travellers")
    assert arc["category"] == "animal"             # a beast of the quartet
    assert arc["protagonist"] != freq              # the fix CHANGES the answer
    assert arc["protagonist"] == "dog"             # the top-arc-span animal
    assert arc["argmax_matches_top_of_sort"]


def test_cat_and_mouse_names_the_cat_the_deceiver_agent(tales):
    """The cat is the deceiver-agent driving the arc (it lies about the pot of
    fat, eats it, then the mouse). It acts across nearly the entire arc
    (arc-span ~= the whole tale)."""
    rec = tales["CAT AND MOUSE IN PARTNERSHIP"]
    arc = rec["arc_protagonist"]
    assert arc["protagonist"] == "cat"
    assert arc["category"] == "animal"
    assert arc["arc_span"] > arc["agency"]         # a WIDE arc, not just a big count
    assert arc["argmax_matches_top_of_sort"]


def test_dog_and_sparrow_names_the_sparrow_the_avenger_agent(tales):
    """The sparrow is the avenger-agent: after the carter kills the dog, the
    sparrow pursues its revenge across the back half of the tale — the widest
    arc-span among the acting characters."""
    rec = tales["THE DOG AND THE SPARROW"]
    arc = rec["arc_protagonist"]
    assert arc["protagonist"] == "sparrow"
    assert arc["category"] == "animal"
    assert arc["argmax_matches_top_of_sort"]


def test_generalizes_across_at_least_three_tales(tales):
    """Every real tale yields a NON-None, categorised, arc-agency-decided
    protagonist (>= 3 tales — the generalisation bar)."""
    decided = 0
    for label, rec in tales.items():
        arc = rec["arc_protagonist"]
        if arc["protagonist"] is not None:
            assert arc["category"] in ("animal", "person", "unknown")
            assert arc["agency"] is not None and arc["agency"] >= 1
            assert arc["argmax_matches_top_of_sort"]
            decided += 1
    assert decided >= 3


def test_grounding_holds_on_every_tale(tales):
    """ANTI-HALLUCINATION: the analysis stays grounded on every tale (adding the
    protagonist read-off emits nothing ungrounded)."""
    for rec in tales.values():
        assert rec["grounding"]["ok"]


# --------------------------------------------------------------------------- #
#  THE HARD GUARD — the short crow fable's protagonist is UNCHANGED (crow).
# --------------------------------------------------------------------------- #
def test_crow_fable_protagonist_is_the_crow_unchanged():
    """On the short crow fable the arc-agent AND the salient lead are the SAME
    entity (the crow), so the arc computation names it — the outcome the reader
    already treats as the hero. The crow grounds `unknown` (capitalised proper
    'Crow'), so this also proves the animate pool admits an ungrounded proper-
    named character while the closed-class pronoun exclusion keeps 'he'/'it' out."""
    agent = _fresh()
    cr.read_and_comprehend(agent, FABLE_TEXT, window=2)
    arc = ns.protagonist_by_arc_agency(agent)
    assert arc["protagonist"] == "crow"
    assert arc["agency"] >= 1
    assert arc["argmax_matches_top_of_sort"]


def test_non_narrative_event_list_has_no_protagonist():
    """DISCRIMINATIVE: 'The sun rose. A car passed. It rained.' has no acting
    character — the honest null, no fabricated protagonist."""
    agent = _fresh()
    cr.read_and_comprehend(agent, NONNARR_TEXT, window=2)
    arc = ns.protagonist_by_arc_agency(agent)
    assert arc["protagonist"] is None


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE / donkey=0 SOURCE AUDIT.
# --------------------------------------------------------------------------- #
def test_protagonist_decided_by_argmax_term_not_python_max():
    """The DECISION is a graph-native `Argmax` over the character pool scored by
    ARC-AGENCY (Count of InNeighbours over the 'agent' edge) weighted by ARC-SPAN
    (MaxOver of event time). No `max(`/`sorted(` decides the winner (the sole
    `sort` is the DISPLAY ranking, explicitly documented, mirroring
    discourse_coherence.centrality_ranking)."""
    src = inspect.getsource(ns.protagonist_by_arc_agency)
    src += inspect.getsource(ns._protagonist_score_term)
    src += inspect.getsource(ns._arc_span_term) + inspect.getsource(ns._agency_term)
    assert '"type": "Argmax"' in inspect.getsource(ns._Argmax)
    assert "_Argmax(pool" in src
    assert '"agent"' in inspect.getsource(ns._agency_term)
    assert '"type": "InNeighbours"' in inspect.getsource(ns._InNeighbours)
    assert '"type": "MaxOver"' in inspect.getsource(ns._MaxOver)
    # the winner comes from native.evaluate(Argmax(...)), never a Python max().
    fn = inspect.getsource(ns.protagonist_by_arc_agency)
    assert "native.evaluate(_Argmax(" in fn
    # AST audit: no builtin max()/min() CALL decides anything (sorted() is the
    # permitted DISPLAY-only ranking, the centrality_ranking precedent).
    fn_ast = ast.parse(fn.lstrip())
    for node in ast.walk(fn_ast):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ("max", "min"), "a Python max()/min() decides the winner"


def test_no_import_re_in_narrative_structure():
    tree = ast.parse(inspect.getsource(ns))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re"
