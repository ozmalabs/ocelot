"""test_antagonist — THE ARC-ROLE ANTAGONIST, the OPPOSING agency, not frequency.

A story's shape is PROTAGONIST vs ANTAGONIST. `protagonist_by_arc_agency` already
names WHO THE STORY IS ABOUT (the arc-agent). This gate asserts the OTHER pole:
`domains.narrative_structure.antagonist_by_arc_opposition` names the opposing
agency the protagonist overcomes — the entity the arc-role protagonist correctly
REJECTED as the lead now NAMED as the opposition:

  · Travelling Musicians -> dog (protagonist) VS ROBBERS (antagonist)
  · Old Sultan          -> sultan (the dog hero) VS WOLF
  · Dog and the Sparrow -> sparrow VS the MAN (the carter)
  · Cat and Mouse       -> cat VS MOUSE

The DECISION is a graph-native `Argmax` Term over the clean animate character pool
(EXCLUDING the protagonist, qualified as sustained opposition), scored from the
arc's CONFLICT/OPPOSITION structure — co-participation with the protagonist
(Intersect of the two event sets, the DOMINANT term), then conflict-target
(theme), then arc-agency, then salience. The DSL evaluator picks it (native Rust,
with the protagonist node bound as `p` in the env); Python never `max()`/`sorted()`s
the decision.

OPPOSITION, NOT FREQUENCY. Two proofs:
  · SYNTHETIC — a bystander 'crowd' (mentions 10, agency 4) loses to an adversary
    'adversary' (mentions 3) that SHARES the protagonist's conflict events. Pure
    frequency and pure agency both pick 'crowd'; opposition picks 'adversary'.
  · REAL — the highest NON-protagonist arc-AGENCY entity is an ALLY (Dog-and-
    Sparrow's dead friend 'dog', agency 3; Cat-and-Mouse's 'cousin', agency 2), so
    a naive 2nd-highest-agency picker (the protagonist method minus the winner)
    would name the ALLY. Opposition correctly names the man / the mouse instead.

HONEST NULL: a single-character fable (the crow, alone with a pitcher) has NO
opposing character — antagonist=None, never fabricated (the incidental setup
'birds' fails the sustained-opposition qualification).

THE HARD GUARD: the crow fable's PROTAGONIST is UNCHANGED (crow) — this module only
ADDS a function; it never perturbs the protagonist computation.

donkey = 0 (no LLM), no `import re`. Real (cached) Grimm prose.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_antagonist.py -p no:randomly -q
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
import jabberwock_reads_a_tale as jt                             # noqa: E402


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


@pytest.fixture(scope="module")
def tales():
    return {rec["label"]: rec for rec in jt.run()}


# the crow's short fable — the byte-identity guard reuses the committed FABLE_TEXT.
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
#  REAL GRIMM TALES — the OPPOSING agency, named verbatim.
# --------------------------------------------------------------------------- #
def test_travelling_musicians_antagonist_is_the_robbers(tales):
    """dog (protagonist) VS ROBBERS (antagonist). The robbers — the frequency lead
    the arc-role protagonist correctly REJECTED — are the opposing force. The
    all-pronoun conflict USED to dissolve every dog<->robber edge (the honest
    `agency+salience` limit); the self-growth descent surfaced that floor (bridging
    anaphora was NOT BUILT) and grew the minimal set-membership primitive, so the
    singular pronoun now individuates a `member_of` the group, the member's conflict
    propagates to the group, and the arc-opposition Argmax re-derives OPPOSITION
    (see test_bridging_anaphora_migrated)."""
    rec = tales["THE TRAVELLING MUSICIANS"]
    prot = rec["arc_protagonist"]
    ant = rec["arc_antagonist"]
    assert prot["protagonist"] == "dog"
    assert ant["antagonist"] == "robbers"
    assert ant["antagonist"] != prot["protagonist"]     # never the protagonist
    assert ant["antagonist"] not in ("mistress",)       # not a scene bystander
    assert ant["decided_by"] == "opposition"            # bridging bound the conflict
    assert float(ant.get("co_participation") or 0.0) >= 1.0
    assert ant["argmax_matches_top_of_sort"]


def test_old_sultan_antagonist_is_the_wolf(tales):
    """sultan (the dog hero) VS WOLF. The wolf directly opposes sultan (it shares a
    conflict event — co-participation >= 1), so the DIRECT opposition structure
    decides it, over the passive rescued CHILD (agency 0, a victim sultan HELPS)."""
    rec = tales["OLD SULTAN"]
    prot = rec["arc_protagonist"]
    ant = rec["arc_antagonist"]
    assert prot["protagonist"] == "sultan"
    assert ant["antagonist"] == "wolf"
    assert ant["antagonist"] != "child"                 # not the rescued victim
    assert ant["co_participation"] >= 1                 # shares sultan's conflict
    assert ant["decided_by"] == "opposition"
    assert ant["argmax_matches_top_of_sort"]


def test_dog_and_sparrow_antagonist_is_the_man(tales):
    """sparrow VS the MAN (the carter). The carter kills the sparrow's friend (the
    dog) and the sparrow avenges it — the carter shares the sparrow's conflict
    events by OPPOSITION (co_participation + conflict_target). This gate depends on
    the sparrow being read as FEMALE: an early stray 'he' once dequantised the
    sparrow male, so every 'her' scattered onto junk and the carter never connected
    to the sparrow's conflict. The revisable-feature-belief loop revises that weak
    mis-gender when the sparrow's own feminine pronouns pile up, which is what lets
    'kill her' / 'aimed a blow at the sparrow' bind and names the carter here.
    The dead-friend ALLY 'dog' is present in the ranking but is the HELPED party,
    never the opposition."""
    rec = tales["THE DOG AND THE SPARROW"]
    prot = rec["arc_protagonist"]
    ant = rec["arc_antagonist"]
    assert prot["protagonist"] == "sparrow"
    assert ant["antagonist"] == "carter"
    assert ant["antagonist"] != "dog"                   # NOT the sparrow's ally
    assert ant["co_participation"] >= 1
    assert ant["decided_by"] == "opposition"
    names = {r["name"] for r in ant["ranking"]}
    assert "dog" in names                               # the ally is ranked ...
    assert ant["antagonist"] != "dog"                   # ... but never chosen


def test_cat_and_mouse_antagonist_is_the_mouse(tales):
    """cat VS MOUSE. The mouse is the cat's partner-turned-victim — the recurring
    conflict-target (theme >= 2). The higher-arc-agency 'cousin' is NOT chosen:
    opposition (being the target of the arc's conflict) beats raw agency."""
    rec = tales["CAT AND MOUSE IN PARTNERSHIP"]
    prot = rec["arc_protagonist"]
    ant = rec["arc_antagonist"]
    assert prot["protagonist"] == "cat"
    assert ant["antagonist"] == "mouse"
    assert ant["conflict_target"] >= 2
    assert ant["decided_by"] in ("conflict", "opposition")
    assert ant["argmax_matches_top_of_sort"]


def test_antagonist_named_on_at_least_three_tales(tales):
    """>= 3 real tales yield a NON-None, categorised antagonist that is NOT the
    protagonist — the protagonist-VS-antagonist opposition, generalised."""
    named = 0
    for rec in tales.values():
        prot = rec["arc_protagonist"]
        ant = rec["arc_antagonist"]
        if ant["antagonist"] is not None:
            assert ant["antagonist"] != prot["protagonist"]
            assert ant["category"] in ("animal", "person", "unknown")
            assert ant["argmax_matches_top_of_sort"]
            named += 1
    assert named >= 3


def test_grounding_holds_with_antagonist(tales):
    """ANTI-HALLUCINATION: adding the antagonist read-off emits nothing ungrounded;
    every tale stays grounded, and no antagonist is fabricated where none exists."""
    for rec in tales.values():
        assert rec["grounding"]["ok"]


# --------------------------------------------------------------------------- #
#  HONEST NULL — no antagonist where there is no opposing character.
# --------------------------------------------------------------------------- #
def test_crow_fable_has_no_antagonist():
    """The crow is ALONE with a pitcher — no human/animal adversary. The incidental
    setup 'birds' (one shared action, mentions 2) fails the sustained-opposition
    qualification; the passive 'pitcher' never acts. antagonist=None, not forced."""
    agent = _fresh()
    cr.read_and_comprehend(agent, FABLE_TEXT, window=2)
    ant = ns.antagonist_by_arc_opposition(agent)
    assert ant["antagonist"] is None
    assert ant["argmax_matches_top_of_sort"]


def test_non_narrative_event_list_has_no_antagonist():
    """DISCRIMINATIVE: 'The sun rose. A car passed. It rained.' has no character at
    all — no protagonist, so no antagonist. The honest null."""
    agent = _fresh()
    cr.read_and_comprehend(agent, NONNARR_TEXT, window=2)
    ant = ns.antagonist_by_arc_opposition(agent)
    assert ant["antagonist"] is None


# --------------------------------------------------------------------------- #
#  THE HARD GUARD — the crow PROTAGONIST is unchanged (this module only ADDS).
# --------------------------------------------------------------------------- #
def test_crow_protagonist_unchanged_by_antagonist_addition():
    """The crow fable's protagonist is STILL the crow — computing the antagonist
    does not perturb the protagonist computation (byte-identical outcome)."""
    agent = _fresh()
    cr.read_and_comprehend(agent, FABLE_TEXT, window=2)
    prot = ns.protagonist_by_arc_agency(agent)
    assert prot["protagonist"] == "crow"
    # and the antagonist read on the SAME agent still yields the crow protagonist:
    ant = ns.antagonist_by_arc_opposition(agent, prot=prot)
    assert ant["protagonist"] == "crow"
    assert ant["antagonist"] is None


# --------------------------------------------------------------------------- #
#  OPPOSITION, NOT FREQUENCY — the synthetic separation.
# --------------------------------------------------------------------------- #
def test_opposition_beats_frequency_and_agency_synthetic():
    """A protagonist 'hero'; an adversary 'adversary' that SHARES hero's conflict
    events (co-participation) with mentions 3; a bystander 'crowd' with mentions 10
    and agency 4 that NEVER engages hero. Pure frequency AND pure agency both pick
    'crowd'; the opposition Argmax picks 'adversary' — the decision is from the
    conflict structure, not frequency."""
    a = _fresh()
    s, native = a.s, a.inner

    def ent(name, ment):
        return s.add_node("SmEntity", {"name": name, "coref_category": "person",
                                       "coref_cleanliness": 1.0, "coref_mentions": float(ment)})

    hero = ent("hero", 5)
    ent("adversary", 3)
    ent("crowd", 10)

    def find(nm):
        for n in s.nodes("SmEntity"):
            if s.node(n)["attrs"].get("name") == nm:
                return n
        return None

    A = find("adversary"); B = find("crowd")

    def ev(t, ag, th):
        e = s.add_node("SmEvent", {"verb": "fight", "t": float(t)})
        native.add_edge_unchecked(e, "agent", ag)
        if th is not None:
            native.add_edge_unchecked(e, "theme", th)

    ev(1, hero, A); ev(2, A, hero); ev(3, hero, A)      # hero <-> adversary conflict
    ev(4, B, None); ev(5, B, None); ev(6, B, None); ev(7, B, None)  # crowd acts alone

    ant = ns.antagonist_by_arc_opposition(a, prot={"protagonist": "hero", "node": None})
    assert ant["antagonist"] == "adversary"             # NOT the more-frequent 'crowd'
    assert ant["co_participation"] >= 1
    # 'crowd' is both more frequent AND more active, yet is NOT the antagonist:
    crowd_row = next((r for r in ant["ranking"] if r["name"] == "crowd"), None)
    adv_row = next((r for r in ant["ranking"] if r["name"] == "adversary"), None)
    assert crowd_row is not None and adv_row is not None
    assert crowd_row["mentions"] > adv_row["mentions"]  # frequency would pick crowd
    assert crowd_row["agency"] > adv_row["agency"]      # agency would pick crowd
    assert adv_row["score"] > crowd_row["score"]        # opposition picks adversary


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE / donkey=0 SOURCE AUDIT.
# --------------------------------------------------------------------------- #
def test_antagonist_decided_by_argmax_over_opposition_terms():
    """The DECISION is a graph-native `Argmax` over the qualified pool, scored by
    OPPOSITION (Intersect of the two participation-event sets) + conflict-target
    (InNeighbours 'theme') + agency. No `max(`/`sorted(` decides the winner (the
    sole `sort` is the DISPLAY ranking, mirroring protagonist_by_arc_agency)."""
    fn = inspect.getsource(ns.antagonist_by_arc_opposition)
    assert "native.evaluate(_Argmax(" in fn
    assert '"type": "Argmax"' in inspect.getsource(ns._Argmax)
    assert '"type": "Intersect"' in inspect.getsource(ns._Intersect)
    assert '"type": "Union"' in inspect.getsource(ns._Union)
    assert '"type": "InNeighbours"' in inspect.getsource(ns._InNeighbours)
    assert "_co_term" in inspect.getsource(ns._antagonist_score_term)
    assert "_Intersect" in inspect.getsource(ns._co_term)
    # AST audit: no builtin max()/min() CALL decides anything.
    fn_ast = ast.parse(fn.lstrip())
    for node in ast.walk(fn_ast):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ("max", "min"), "a Python max()/min() decides the winner"


def test_no_import_re_in_narrative_structure():
    tree = ast.parse(inspect.getsource(ns))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(al.name == "re" for al in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re"
