"""CLAUSE DECOMPOSITION — the order-N descent into a multi-clause sentence's
CLAUSES (domains/reading_collapse.decompose_sentence), wired into
reading_scope.read_scope.

The reader's clause grammar was tuned for short SVO sentences; real fable prose
packs several clauses per sentence (subordinate 'when ...', coordinate '... and
...', participial 'Xing ..., ...') and the greedy whole-sentence collapse GLOMS
that structure into one underscore-joined blob argument, so the real verbs never
surface as a predication's relation. Decomposition splits the sentence at
RECOGNISED marker-class boundaries and reads each clause into a CLEAN verb-headed
predication.

DISCIPLINE (CLAUDE.md): the BOUNDARY is a marker-class recognition (CLAUSE_LINK /
IF / CAUSE_SUB / REL, the recogniser's comma regions, AND/OR between two
verb-headed clauses) — no hardcoded Python clause-splitter, no regex, donkey=0.
The main verb is the held is_verb_headed POS Term (+ WordNet inflection); the
role head is the held _clean_head nominal faculty. Additive: read_clause is
UNCHANGED (the battery/scope blob behaviour is untouched — a single-clause SVO
sentence has no boundary marker and does NOT decompose).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_clause_decomposition.py -p no:randomly -q
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

from substrate.boot_core import boot_core                 # noqa: E402
from domains import reading_collapse as rc                 # noqa: E402
from domains import reading_scope as rs                    # noqa: E402
from domains import dictionary_lexicon as dl               # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


@pytest.fixture()
def agent():
    s, node = boot_core()
    return _Agent(s, node)


def _preds(agent, sentence):
    return rc.decompose_sentence(agent, sentence)["predications"]


# --------------------------------------------------------------------------- #
#  PARTICIPIAL OPENER — the headline glom from the Crow gate.
# --------------------------------------------------------------------------- #
def test_participial_opener_surfaces_the_verb(agent):
    """'Picking up some small pebbles, he dropped them into the pitcher one by
    one.' -> the main clause reads as its own clean event drop(he, them), where
    the OLD greedy reading glommed the whole clause into one blob argument
    ['by', 'picking_up_..._pitcher_one', 'one']."""
    preds = _preds(agent, "Picking up some small pebbles, he dropped them into the pitcher one by one.")
    assert ["dropped", "he", "them"] in preds, preds


def test_coordinate_and_subordinate_clauses_split(agent):
    """A coordinated + subordinate sentence decomposes into clean clauses:
    is_a(pitcher, high) (copula, 'but' stripped) AND reach(crow, water)."""
    preds = _preds(agent, "But the pitcher was high and had a narrow neck, "
                          "and no matter how he tried, the Crow could not reach the water.")
    assert ["is_a", "pitcher", "high"] in preds, preds
    assert ["reach", "crow", "water"] in preds, preds


def test_when_subordinator_and_main_clause(agent):
    """A 'when ...' subordinate clause + the main clause both read; the main
    clause yields found(crow, pitcher) with CLEAN nominal heads (not
    'thirsty_crow' / a blob)."""
    preds = _preds(agent, "In a spell of dry weather, when the Birds could find "
                          "very little to drink, a thirsty Crow found a pitcher with a "
                          "little water in it.")
    assert ["found", "crow", "pitcher"] in preds, preds


def test_until_and_result_linker(agent):
    """'With each pebble the water rose a little higher until ... so ...' — the
    leading PP is skipped and the real subject surfaces: rose(water, ...)."""
    preds = _preds(agent, "With each pebble the water rose a little higher until "
                          "at last it was near enough so he could drink.")
    assert any(p[0] == "rose" and p[1] == "water" for p in preds), preds


# --------------------------------------------------------------------------- #
#  CLEAN NOMINAL HEADS — a role is its head noun / pronoun, not a multi-word blob.
# --------------------------------------------------------------------------- #
def test_clean_heads_not_blobs(agent):
    preds = _preds(agent, "But the pitcher was high and had a narrow neck, "
                          "and no matter how he tried, the Crow could not reach the water.")
    for p in preds:
        for arg in p[1:]:
            assert "_" not in arg, ("role head should be a clean atom, not a blob", p)


def test_leading_connective_stripped_from_subject(agent):
    """'but the pitcher' -> the subject is the clean entity 'pitcher' (the 'but'
    belongs to the coherence layer, not the entity)."""
    assert rc._arg_head(agent, "but the pitcher") == "pitcher"
    assert rc._arg_head(agent, "the water") == "water"
    assert rc._arg_head(agent, "some small pebbles") == "pebbles"
    assert rc._arg_head(agent, "them") == "them"     # a pronoun stays itself (coref binds it)


# --------------------------------------------------------------------------- #
#  ADDITIVE — a single-clause SVO sentence does NOT decompose (read_clause /
#  read_scope's blob lattice is untouched; this is what keeps the scope tests green).
# --------------------------------------------------------------------------- #
def test_single_clause_svo_does_not_fire(agent):
    d = rc.decompose_sentence(agent, "The cat chased the mouse.")
    assert d["multi_clause"] is False, d
    assert d["n_boundaries"] == 0, d


def test_no_boundary_no_decomposition_via_read_scope(agent):
    """read_scope on a single SVO clause falls straight through to the greedy
    collapse (source is NOT clause_decomposition) — the backtrack lattice is
    preserved for the multi-verb glom cases the reading_scope tests pin."""
    r = rs.read_scope(agent, "miners extract ore furnaces smelt metal")
    assert r.get("source") != "clause_decomposition", r


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — no `import re`; the boundary is a marker-class
#  recognition (the CLAUSE_LINK marker lexicon), not a Python clause-splitter.
# --------------------------------------------------------------------------- #
def test_no_import_re_in_reading_collapse():
    src = inspect.getsource(rc)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"


def test_boundary_is_a_recognised_marker_class(agent):
    """The clause boundary is a MARKER-CLASS recognition: the CLAUSE_LINK forms
    (when/until/so/...) resolve to the 'CLAUSE_LINK' class in the held marker
    lexicon (graph data), the same lexicon read_clause reads — not a hardcoded
    Python list of split words."""
    rc.ensure_codebook(agent)
    lex = rc._marker_lexicon(agent.s)
    for form in ("when", "until", "so", "while", "though"):
        assert lex.get(form) == "CLAUSE_LINK", (form, lex.get(form))
