"""test_narrative_structure — THE STORY-GRAMMAR ARC, one level up from
discourse coherence, recognised over the comprehension graph
`comprehension_reader.read_and_comprehend` already builds.

Every assertion here reads the arc `domains/narrative_structure.
recognize_narrative_structure` mints (wired as step 9 of the read
orchestrator) — never re-derives it. Donkey = 0: no LLM, no regex, no
Python if/else assigning a story-grammar role directly (see the source
audit below) — the role is always `ShapeDecode`'s own verdict over the
`ShapeSignatureNarrative` codebook (`seeds/narrative_structure.json`).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_narrative_structure.py -p no:randomly -q
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
WOLF_TEXT = "The wolf was hungry. It saw a lamb. It chased the lamb."
NONNARR_TEXT = "The sun rose. A car passed. It rained."


def _roles_by_order(arc: dict) -> dict:
    return {r["order"]: r["role"] for r in arc["roles"]}


# --------------------------------------------------------------------------- #
#  CROW ARC — the full four-role fable form, verbatim.
# --------------------------------------------------------------------------- #
def test_crow_arc_recognises_setup_problem_solution_resolution():
    agent = _fresh()
    g = cr.read_and_comprehend(agent, FABLE_TEXT, window=2)
    arcs = g["narrative_arc"]["arcs"]
    crow_arcs = [a for a in arcs if a["entity"] == "crow"]
    assert len(crow_arcs) == 1
    arc = crow_arcs[0]
    assert arc["goal_sentence"] == 0
    assert arc["remedy"] == "drink"

    by_order = _roles_by_order(arc)
    # SETUP: the goal-establishing sentence (crow.thirsty -> goal=drink).
    assert by_order[0] == "setup"
    # PROBLEM: "But the pitcher was high ... could not reach the water" --
    # the discourse-coherence 'contrast' signal ("But...") into this sentence.
    assert by_order[1] == "problem"
    # SOLUTION: "Picking up some small pebbles, he dropped them ..." -- the
    # attempt carrying the outgoing causal edge (drop -> rise).
    assert by_order[4] == "solution"
    # RESOLUTION: "... he could drink." -- the causal effect sentence whose
    # own recognised words include the goal's remedy token 'drink'.
    assert by_order[5] == "resolution"

    roles = ns.read_narrative_roles(agent, "crow")
    assert [r["role"] for r in sorted(roles, key=lambda r: r["order"])] == [
        "setup", "problem", "solution", "resolution"]


def test_crow_arc_matches_orchestrator_wiring():
    """The arc is produced AS A STEP of read_and_comprehend (step 9), not a
    side call the caller must remember to make."""
    agent = _fresh()
    g = cr.read_and_comprehend(agent, FABLE_TEXT, window=2)
    assert "narrative_arc" in g
    assert g["narrative_arc"]["arcs"]


# --------------------------------------------------------------------------- #
#  GENERAL (not crow-tuned) — the wolf's shorter, honestly partial arc.
# --------------------------------------------------------------------------- #
def test_wolf_arc_recognises_setup_and_action_not_a_forced_problem():
    """No fable-specific code path: the SAME codebook/decode recognises
    'The wolf was hungry.' as setup (goal=eat) and 'saw'/'chased the lamb'
    as plain ACTION (Trabasso & van den Broek's ATTEMPT) -- never forced into
    'problem'/'solution'/'resolution' roles the text never earns (no
    discourse 'contrast', no causal edge, no stated goal-satisfying token)."""
    agent = _fresh()
    g = cr.read_and_comprehend(agent, WOLF_TEXT, window=2)
    arcs = g["narrative_arc"]["arcs"]
    wolf_arcs = [a for a in arcs if a["entity"] == "wolf"]
    assert len(wolf_arcs) == 1
    arc = wolf_arcs[0]
    assert arc["goal_sentence"] == 0
    assert arc["remedy"] == "eat"

    by_order = _roles_by_order(arc)
    assert by_order[0] == "setup"
    assert by_order[1] == "action"
    assert by_order[2] == "action"
    # honest: no problem/solution/resolution role minted anywhere for wolf.
    assert set(by_order.values()) == {"setup", "action"}


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE — a non-narrative event list mints no arc at all.
# --------------------------------------------------------------------------- #
def test_non_narrative_event_list_mints_no_arc():
    """'The sun rose. A car passed. It rained.' has no goal, no character
    pursuing anything -- no need-state for goal-from-state to decode, so the
    enabling chain is empty and this module contributes NOTHING: a low/empty
    arc, never a fabricated one."""
    agent = _fresh()
    g = cr.read_and_comprehend(agent, NONNARR_TEXT, window=2)
    assert g["narrative_arc"]["arcs"] == []
    assert ns.read_narrative_roles(agent) == []


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT.
# --------------------------------------------------------------------------- #
def test_narrative_structure_uses_shape_decode():
    src = inspect.getsource(ns)
    assert '"type": "ShapeDecode"' in src
    assert '"codebook_type": _CODEBOOK_TYPE' in src


def test_no_import_re_in_narrative_structure():
    src = inspect.getsource(ns)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"


_ROLE_STRINGS = ("setup", "problem", "solution", "action", "consequence", "resolution")


def test_no_python_if_else_assigns_a_role_string():
    """No function in this module contains an `if`/`elif` branch that
    directly RETURNS or ASSIGNS one of the six role strings as a literal —
    the role only ever comes from `_role_for`'s graph read of the WINNING
    ShapeSignatureNarrative's own `role` attr (the decode's verdict). The
    TOKEN-building ladder (`_slot_token`/`_effect_token`) legitimately
    branches on mechanical signals, but returns TOKENS (NARR_*), never a
    role string -- checked by AST literal scan of every branch body."""
    src = inspect.getsource(ns)
    tree = ast.parse(src)
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef):
            continue
        for node in ast.walk(fn):
            if isinstance(node, (ast.If,)):
                for branch_node in ast.walk(node):
                    if isinstance(branch_node, ast.Constant) and branch_node.value in _ROLE_STRINGS:
                        raise AssertionError(
                            "function %r's if/else branches on/returns a "
                            "literal role string %r -- the role must come "
                            "from the ShapeDecode verdict only"
                            % (fn.name, branch_node.value))


def test_no_import_re_in_comprehension_reader_after_wiring():
    """The step-9 wiring into the orchestrator must not have introduced
    `import re` or a meaning-deciding if/else there either."""
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
