"""test_trope_theme — TROPE RECOGNITION + THEME, one level up from the
story-grammar arc, recognised over the comprehension graph
`comprehension_reader.read_and_comprehend` already builds (step 10, after
`narrative_structure`'s step 9).

Every assertion here reads what `domains.trope_theme.recognize_tropes_and_
theme` mints — never re-derives it. Donkey = 0: no LLM, no regex, no Python
if/else naming a trope directly (see the source audit below) — a trope name
is always `ShapeDecode`'s own set-cover verdict over the `ShapeSignatureTrope`
codebook (`seeds/narrative_tropes.json`).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_trope_theme.py -p no:randomly -q
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
from domains import trope_theme as tt                            # noqa: E402


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


CROW_TEXT = (
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
# GENERAL (not crow-tuned): a different fable, instantiating a DIFFERENT
# trope (pure persistence -- no physical-effect/indirect mechanism at all;
# the mouse just grinds through the obstacle one stone at a time).
MOUSE_TEXT = (
    "Stones blocked the path. A mouse was hungry. But the cheese was locked "
    "behind the stones, and the mouse could not reach it. The mouse took "
    "them away one by one. So the mouse ate the cheese."
)
WOLF_TEXT = "The wolf was hungry. It saw a lamb. It chased the lamb."
NONNARR_TEXT = "The sun rose. A car passed. It rained."


def _entity_result(g: dict, entity: str) -> dict:
    for r in g["trope_theme"]["results"]:
        if r["entity"] == entity:
            return r
    raise AssertionError("no trope_theme result for entity %r" % entity)


def _trope_names(result: dict) -> list:
    return [t["name"] for t in result["tropes"]]


# --------------------------------------------------------------------------- #
#  CROW — both tropes, each traced to the arc structure that earns it.
# --------------------------------------------------------------------------- #
def test_crow_instantiates_ingenuity_and_persistence():
    agent = _fresh()
    g = cr.read_and_comprehend(agent, CROW_TEXT, window=2)
    r = _entity_result(g, "crow")

    assert set(r["tokens"]) == {"TROPE_PROBLEM", "TROPE_INDIRECT",
                                "TROPE_INCREMENTAL", "TROPE_RESOLUTION"}
    assert r["residual"] == []
    names = _trope_names(r)
    assert "INGENUITY_OVER_STRENGTH" in names
    assert "PERSISTENCE_PAYS" in names

    by_name = {t["name"]: t for t in r["tropes"]}
    ingenuity = by_name["INGENUITY_OVER_STRENGTH"]
    persistence = by_name["PERSISTENCE_PAYS"]

    # INGENUITY traces to the PROBLEM + INDIRECT (physical-effect causal)
    # signals -- the clever indirect pebble solution.
    assert set(ingenuity["covered_tokens"]) == {"TROPE_PROBLEM", "TROPE_INDIRECT"}
    # PERSISTENCE traces to the INCREMENTAL (plural affected entity) +
    # RESOLUTION signals -- the incremental 'one by one'.
    assert set(persistence["covered_tokens"]) == {"TROPE_INCREMENTAL", "TROPE_RESOLUTION"}

    # THEME reads off both recognised tropes' own held `theme` line.
    theme = r["theme"]
    assert theme is not None and theme["minted"] is True
    assert set(theme["tropes"]) == {"INGENUITY_OVER_STRENGTH", "PERSISTENCE_PAYS"}
    assert len(theme["lines"]) == 2

    print("\n--- CROW ---")
    for name, t in by_name.items():
        print(" TROPE:", name, "| covers:", t["covered_tokens"],
              "| label:", t["label"]["name"], "(%s)" % t["label"]["source"])
        for ev in tt.trope_evidence(agent, t["_node_obj"]):
            print("    evidence <-", ev["kind"], ev["attrs"].get("role")
                  or ev["attrs"].get("note"))
    print(" THEME:", theme["lines"])


def test_crow_arc_matches_orchestrator_wiring():
    """trope_theme is produced AS A STEP of read_and_comprehend (step 10),
    reading narrative_structure's own step-9 arc — not a side call a caller
    must remember to make."""
    agent = _fresh()
    g = cr.read_and_comprehend(agent, CROW_TEXT, window=2)
    assert "trope_theme" in g
    assert g["trope_theme"]["results"]


# --------------------------------------------------------------------------- #
#  GRAPH-CHECKABLE — every recognised trope traces to real graph structure,
#  never a free-floating label.
# --------------------------------------------------------------------------- #
def test_crow_tropes_are_graph_checkable():
    agent = _fresh()
    g = cr.read_and_comprehend(agent, CROW_TEXT, window=2)
    r = _entity_result(g, "crow")
    assert r["tropes"], "expected at least one recognised trope"
    for t in r["tropes"]:
        node = t["_node_obj"]
        ev = tt.trope_evidence(agent, node)
        assert ev, "trope %r has no graph evidence -- a free-floating label" % t["name"]
        # every covered token must be traceable to SOME evidence entry
        evidenced_kinds = {e["kind"] for e in ev}
        assert evidenced_kinds & {"NarrativeRole", "TropeEvidence"}
        # the NarrativeRole evidence really is a resident graph node with a
        # role attr the ARC (narrative_structure) itself minted, not
        # something trope_theme fabricated.
        for e in ev:
            if e["kind"] == "NarrativeRole":
                assert e["attrs"].get("role") in (
                    "setup", "problem", "solution", "action", "consequence", "resolution")
                assert e["attrs"].get("entity") == "crow"

    # read_tropes is a pure graph read of the SAME Trope nodes.
    held = tt.read_tropes(agent, "crow")
    assert {h["name"] for h in held} == set(_trope_names(r))


# --------------------------------------------------------------------------- #
#  GENERAL (not crow-tuned) — a different short story instantiating a
#  DIFFERENT trope (pure persistence, no indirect/physical-effect
#  mechanism at all).
# --------------------------------------------------------------------------- #
def test_mouse_story_instantiates_persistence_not_ingenuity():
    agent = _fresh()
    g = cr.read_and_comprehend(agent, MOUSE_TEXT, window=2)
    r = _entity_result(g, "mouse")

    assert "TROPE_INDIRECT" not in r["tokens"], (
        "the mouse story's solution has no physical-effect causal edge -- "
        "TROPE_INDIRECT must be honestly absent")
    names = _trope_names(r)
    assert names == ["PERSISTENCE_PAYS"], (
        "expected ONLY persistence (no cleverness signal present), got %r" % names)

    persistence = r["tropes"][0]
    assert set(persistence["covered_tokens"]) == {"TROPE_INCREMENTAL", "TROPE_RESOLUTION"}
    assert persistence["label"]["name"] == "Determinator"
    assert r["theme"]["tropes"] == ["PERSISTENCE_PAYS"]

    print("\n--- MOUSE (general, different trope) ---")
    print(" tokens:", r["tokens"])
    print(" TROPE:", persistence["name"], "| covers:", persistence["covered_tokens"],
          "| label:", persistence["label"]["name"])
    print(" THEME:", r["theme"]["lines"])


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE — an arc that never earns problem/resolution roles at all
#  (the wolf), and a non-narrative event list (no arc at all), both mint NO
#  forced trope.
# --------------------------------------------------------------------------- #
def test_wolf_arc_mints_no_forced_trope():
    agent = _fresh()
    g = cr.read_and_comprehend(agent, WOLF_TEXT, window=2)
    r = _entity_result(g, "wolf")
    assert r["tokens"] == []
    assert r["tropes"] == []
    assert r["theme"] is None
    assert "honest null" in r["reason"]
    assert tt.read_tropes(agent, "wolf") == []

    print("\n--- WOLF (discriminative null) ---")
    print(" reason:", r["reason"])


def test_non_narrative_event_list_mints_no_trope_at_all():
    agent = _fresh()
    g = cr.read_and_comprehend(agent, NONNARR_TEXT, window=2)
    assert g["trope_theme"]["results"] == []
    assert tt.read_tropes(agent) == []
    assert tt.read_theme(agent, "sun") is None


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — graph-native, no Python if/else names a trope, no regex.
# --------------------------------------------------------------------------- #
def test_trope_theme_uses_shape_decode():
    src = inspect.getsource(tt)
    assert '"type": "ShapeDecode"' in src
    assert '"codebook_type": _CODEBOOK_TYPE' in src


def test_no_import_re_in_trope_theme():
    src = inspect.getsource(tt)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"


_TROPE_NAME_STRINGS = ("INGENUITY_OVER_STRENGTH", "PERSISTENCE_PAYS", "NECESSITY_INVENTION")


def test_no_python_if_else_names_a_trope():
    """No function in this module contains an `if`/`elif` branch that
    directly RETURNS or ASSIGNS one of the seeded trope-name strings as a
    literal -- the trope name only ever comes from the decode's own `plan`
    (`step.get('part')`), read off the winning `ShapeSignatureTrope` node's
    `name` attr. The TOKEN-building signals (`_build_tokens`) legitimately
    branch on mechanical facts, but they emit TOKENS (TROPE_*), never a
    trope-name literal."""
    src = inspect.getsource(tt)
    tree = ast.parse(src)
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.If):
                for branch_node in ast.walk(node):
                    if isinstance(branch_node, ast.Constant) and branch_node.value in _TROPE_NAME_STRINGS:
                        raise AssertionError(
                            "function %r's if/else branches on/returns a "
                            "literal trope-name string %r -- the trope must "
                            "come from the ShapeDecode verdict only"
                            % (fn.name, branch_node.value))


def test_no_import_re_in_comprehension_reader_after_wiring():
    src = inspect.getsource(cr)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"


def _func_ast(mod, name):
    src = inspect.getsource(mod)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError("function %r not found" % name)


def test_orchestrator_still_has_no_meaning_if_else_after_wiring():
    fn = _func_ast(cr, "read_and_comprehend")
    if_nodes = [n for n in ast.walk(fn) if isinstance(n, ast.If)]
    assert if_nodes == [], "read_and_comprehend must not branch on meaning"


# --------------------------------------------------------------------------- #
#  HONEST — the codebook is small/finite; NECESSITY_INVENTION's own mechanism
#  is sound (a synthetic BLOCKED+INDIRECT token pair fully covers it) even
#  though none of this suite's three stories happens to trigger a BLOCKED
#  precondition-gap signal.
# --------------------------------------------------------------------------- #
def test_necessity_invention_mechanism_is_sound_though_unexercised_by_corpus():
    agent = _fresh()
    tt.ensure_codebook(agent)
    res = tt._decode(agent, [["TROPE_BLOCKED"], ["TROPE_INDIRECT"]])
    plan = res.get("plan") or []
    assert len(plan) == 1
    assert plan[0]["part"] == "NECESSITY_INVENTION"
    assert sorted(c[0] for c in plan[0]["covers"]) == ["TROPE_BLOCKED", "TROPE_INDIRECT"]
