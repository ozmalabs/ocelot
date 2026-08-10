"""test_comprehension_reader — THE READ ORCHESTRATOR (domains/comprehension_
reader.read_and_comprehend) + the prenominal-adjective -> STATE parse gap.

The orchestrator threads the six committed comprehension components onto ONE
shared graph in the CORRECT dependency order (GOAL-FROM-STATE after the
situation model; PHYSICAL-CAUSAL after the DiscourseEvent graph), calling each
component's PUBLIC entry as-is. It is a general read path — NOT crow-specific —
so it is exercised here on a DIFFERENT short narrative. Two source audits pin
the graph-native discipline: the orchestrator only sequences (no comprehension
if/else deciding meaning), and the prenominal-adjective->state recognises the
adjective by the held POS faculty (no hardcoded adjective list), no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_comprehension_reader.py -p no:randomly -q
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
from domains import reading_collapse as rc                       # noqa: E402
from domains import situation_model_reader as smr                # noqa: E402
from domains import character_tom as ctom                        # noqa: E402


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
#  GENERAL — the orchestrator is a general read path, not crow-tuned.
# --------------------------------------------------------------------------- #
def test_orchestrator_reads_a_different_passage_coherently():
    """A DIFFERENT short narrative than the crow fable. The orchestrator builds a
    coherent situation model: 'hungry' grounds as a state, GOAL-FROM-STATE infers
    goal=eat, coref binds 'it' to the wolf (so its later actions land on the wolf,
    not a throwaway 'it'), and a DiscourseEvent node exists per sentence — proving
    the read path is general, not crow-specific."""
    agent = _fresh()
    text = "The wolf was hungry. It saw a lamb. It chased the lamb."
    g = cr.read_and_comprehend(agent, text)

    # goal inferred from the 'hungry' state (need_remedy_hunger schema).
    assert smr.entity_state(agent, "wolf").get("hungry") == 1
    assert ctom.character_goal(agent, "wolf") == "eat"

    # coref bound 'it' to the wolf: the wolf accrued mentions across sentences.
    assert smr.entity_state(agent, "wolf").get("coref_mentions", 0) >= 2

    # a DiscourseEvent node per sentence (three sentences).
    assert len(g["discourse"]["nodes"]) == 3

    # the spine read three sentences into a textbase.
    assert len(g["spine"]["textbase"]) == 3


# --------------------------------------------------------------------------- #
#  PRENOMINAL-ADJECTIVE -> STATE — recognised by the held POS faculty.
# --------------------------------------------------------------------------- #
def test_prenominal_adjective_grounds_as_state_reachable():
    """A prenominal adjective grounds as a STATE on the head entity — reachable by
    goal-from-state. In real multi-clause prose ('When the sun rose, a thirsty
    crow found a pitcher.') the reader cleans the subject to 'crow' and grounds
    crow.thirsty=1 (is_a(crow, thirsty))."""
    agent = _fresh()
    cr.read_and_comprehend(agent, "When the sun rose, a thirsty crow found a pitcher.")
    assert smr.entity_state(agent, "crow").get("thirsty") == 1


def test_prenominal_state_is_pos_driven_not_a_crow_specific_list():
    """The prenominal-adjective->state recogniser is the HELD POS faculty, NOT a
    hardcoded adjective list: a NOVEL adjective absent from the crow fable still
    grounds ('a clever fox' -> fox.clever), while a bare noun head does not."""
    # a novel adjective ('clever') is recognised by POS, not by any list.
    states = rc._prenominal_states("a clever fox", "fox")
    assert ["is_a", "fox", "clever"] in states
    # the head noun itself is never emitted as its own state.
    assert not any(p[2] == "fox" for p in states)
    # a bare noun-headed span with no adjective yields no state.
    assert rc._prenominal_states("a pitcher", "pitcher") == []


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — graph-native discipline.
# --------------------------------------------------------------------------- #
def _func_ast(mod, name):
    src = inspect.getsource(mod)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError("function %r not found" % name)


def test_orchestrator_only_sequences_no_meaning_if_else():
    """The orchestrator makes NO comprehension decision of its own: read_and_
    comprehend contains no `if`/`else` statement that decides meaning — it only
    sequences the components' public calls and threads their output (loops and a
    try/except around a mechanical run_rules are not meaning decisions)."""
    fn = _func_ast(cr, "read_and_comprehend")
    if_nodes = [n for n in ast.walk(fn) if isinstance(n, ast.If)]
    assert if_nodes == [], "read_and_comprehend must not branch on meaning"


def test_no_hardcoded_adjective_list_in_prenominal():
    """The prenominal-adjective recogniser calls the held POS faculty
    (consumption_quality._pos) and holds no literal adjective word-list."""
    fn = _func_ast(rc, "_prenominal_states")
    # strip the docstring (examples legitimately name adjectives) — audit CODE only.
    body = list(fn.body)
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(getattr(body[0], "value", None), ast.Constant)):
        body = body[1:]
    code_src = "\n".join(ast.unparse(n) for n in body)
    assert "_pos" in code_src, "must recognise the adjective via the held POS faculty"
    # no crow-fable adjective appears as a literal in the recogniser's CODE.
    for word in ("thirsty", "poor", "narrow", "small"):
        assert word not in code_src, "found a hardcoded adjective %r" % word


def test_no_import_re_in_orchestrator():
    src = inspect.getsource(cr)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"
