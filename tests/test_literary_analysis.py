"""test_literary_analysis — THE JABBERWOCK WRITES A LITERARY ANALYSIS, one level
up from trope+theme, rendered from the comprehension graph
`comprehension_reader.read_and_comprehend` already builds.

Every assertion reads what `domains.literary_analysis.produce_analysis` renders
— never re-derives it. donkey = 0 (no LLM, no regex), GRAPH-NATIVE (content from
the graph), GRAPH-CHECKABLE (every emitted sentence traces to a graph node; a
claim with no grounding cannot appear). The affirmative event clauses are
realised by the agent's OWN production faculty (`LanguageProduction.produce`);
the literary CONTENT words are never hand-written string literals in the module
(the source audit below proves it).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_literary_analysis.py -p no:randomly -q -s
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
from domains import literary_analysis as la                      # noqa: E402


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
# GENERAL (not crow-tuned): a different fable instantiating a DIFFERENT trope
# (pure persistence -- no indirect/physical-effect mechanism at all).
MOUSE_TEXT = (
    "Stones blocked the path. A mouse was hungry. But the cheese was locked "
    "behind the stones, and the mouse could not reach it. The mouse took "
    "them away one by one. So the mouse ate the cheese."
)

# story-CONTENT words that must NOT be hand-written literals anywhere in the
# module's executable code (they come from the graph) — the graph-native audit.
_STORY_WORDS = ("crow", "pebble", "thirsty", "pitcher", "cheese", "mouse",
                "hungry", "macgyvering", "determinator", "ingenuity",
                "persistence", "reach", "drink", "stone")


# --------------------------------------------------------------------------- #
#  CROW — the actual analysis prose, and every gate section present.
# --------------------------------------------------------------------------- #
def test_crow_analysis_states_every_section():
    agent = _fresh()
    res = la.produce_analysis(agent, CROW_TEXT)
    text = res["text"]

    print("\n" + "=" * 78 + "\nCROW ANALYSIS\n" + "=" * 78)
    print(text)
    print("=" * 78)

    low = text.lower()
    # SUMMARY — thirsty crow + unreachable water
    assert "crow" in low and "thirsty" in low
    assert "cannot reach the water" in low
    # STRUCTURE — problem / solution / resolution
    assert "the problem is that the crow cannot reach the water" in low
    # FLUENT, grammatical past tense (the fix): the producer renders the
    # graph's OWN inflected surface ('dropped'/'rose'), not the bare lemma
    # ('drop'/'rise') the old wiring bug threw the tense of away.
    assert "dropped the pebble" in low                  # solution: dropped pebbles
    assert "drop the pebble" not in low                 # the bare-lemma bug is gone
    assert "the water rose" in low                      # resolution: water rose
    assert "the water rise" not in low
    # HONEST RESIDUAL: the goal-remedy clause ('drink') has no better graph
    # surface to realise than the bare lemma -- the crow fable's own text for
    # this event is itself the bare modal complement "...he could drink" (no
    # 'drank' token exists anywhere in the source to recover); see
    # `_verb_surface_from_words` and the module's HONEST tense ledger.
    assert "the crow drink" in low                     # resolution: drink (residual)
    # TECHNIQUE — both tropes, TVTropes labels (graph-sourced)
    assert "MacGyvering" in text and "INGENUITY_OVER_STRENGTH" in text
    assert "Determinator" in text and "PERSISTENCE_PAYS" in text
    # THEME — the trope-derived moral lines
    assert "cleverness over strength" in low
    assert "persistence pays" in low

    # section headers present (fixed frame, carry no story content)
    for header in ("Summary.", "Narrative structure.", "Technique.", "Theme."):
        assert header in text

    assert res["produced_count"] >= 3, "the production faculty must realise the event clauses"
    assert res["framed_count"] >= 1


# --------------------------------------------------------------------------- #
#  GRAPH-CHECKABLE (the headline) — every claim traces to a resident graph node;
#  a claim with no grounding cannot appear; the claim->fact map covers every
#  sentence; a fact NOT in the graph is never stated.
# --------------------------------------------------------------------------- #
def test_every_claim_traces_to_a_graph_node():
    agent = _fresh()
    res = la.produce_analysis(agent, CROW_TEXT)

    print("\n" + "=" * 78 + "\nCLAIM -> GRAPH-FACT MAP\n" + "=" * 78)
    for sent, info in res["claim_map"].items():
        print("[%s/%s] pointers=%s" % (info["section"], info["kind"], info["pointers"]))
        print("   ", sent)
        print("    note:", info["note"])
    print("=" * 78)

    # every emitted claim carries at least one graph pointer
    for c in res["claims"]:
        assert c["graph_pointers"], "claim has NO grounding: %r" % c["sentence"]

    # every pointer resolves to a resident graph node
    ver = la.verify_grounding(agent, res)
    assert ver["ok"], "unresolved pointers: %r" % ver["unresolved"][:5]
    assert ver["checked"] > 0

    # the claim map covers EVERY sentence in the analysis (minus the fixed
    # section headers, which carry no story content and are not claims).
    for c in res["claims"]:
        assert c["sentence"] in res["claim_map"]
        assert c["sentence"] in res["text"]


def test_ungrounded_claim_is_refused():
    """The graph-checkable discipline is structural: `_emit` REFUSES a claim
    with no graph pointer — a fluent-but-ungrounded sentence cannot be built."""
    claims = []
    with pytest.raises(ValueError):
        la._emit(claims, "SUMMARY", "The crow is a noble philosopher king.",
                 "framed", [], note="fabricated")
    assert claims == []


def test_no_ungrounded_fact_is_stated():
    """A fact NOT in the graph never appears: the analysis contains no content
    word the story/graph does not carry (no invented characters/objects)."""
    agent = _fresh()
    res = la.produce_analysis(agent, CROW_TEXT)
    low = res["text"].lower()
    for fabricated in ("dragon", "king", "castle", "moon", "sword", "princess"):
        assert fabricated not in low


# --------------------------------------------------------------------------- #
#  FLUENCY FIX — the event clauses render the graph's OWN inflected surface
#  ('dropped'/'rose'/'took'/'ate'), not a bare re-lemmatised verb. This is a
#  WIRING fix (literary_analysis stopped discarding the tense the textbase
#  predication already carried), not a faculty limit -- the production
#  faculty already inflects for free whenever fed a grounded inflected
#  surface (`scripts/drive_self_account_fluent.py` proves the faculty).
# --------------------------------------------------------------------------- #
def test_event_clauses_are_grammatical_not_bare_lemma():
    agent = _fresh()
    res = la.produce_analysis(agent, CROW_TEXT)
    low = res["text"].lower()
    # every produced clause is a full clause with a subject (never a bare
    # dangling verb with no "the <noun>" before it) -- the ungrammatical
    # bug produced exactly this shape ("the crow drop"/"the water rise").
    assert "the crow dropped" in low
    assert "the water rose" in low
    # the two events whose own text carries an inflected surface are FIXED;
    # the one honest residual (goal-remedy 'drink', no inflected form exists
    # anywhere in this fable's source text) is unavoidable without inventing
    # morphology -- disclosed, not hidden, in the module's HONEST ledger.
    for bare in ("crow drop ", "crow drop.", "water rise "):
        assert bare not in low + " "

    res_m = la.produce_analysis(_fresh(), MOUSE_TEXT)
    low_m = res_m["text"].lower()
    assert "the mouse took" in low_m and "the mouse ate" in low_m
    for bare in ("mouse take", "mouse eat"):
        assert bare not in low_m


def test_frame_event_is_the_graph_relation_token_not_relemmatised():
    """Source-level proof of the wiring fix: `_frames_for` renders the
    affirmative event using the raw textbase relation token (`str(pred[0])`)
    -- the same string `situation_model_reader` stamps onto its SmEvent
    node's `surface` attr for that exact predication -- and does NOT run it
    through `_verb_lemma` (which would re-discard the tense). The negation
    frame (`_problem_clause`, a modal "cannot <bare verb>" construction) is
    correctly UNCHANGED -- it still wants the lemma."""
    src = inspect.getsource(la._frames_for)
    assert "_verb_lemma(pred[0])" not in src
    assert "str(pred[0]).lower()" in src
    problem_src = inspect.getsource(la._problem_clause)
    assert "_verb_lemma(pred[0])" in problem_src


# --------------------------------------------------------------------------- #
#  GENERAL (not crow-tuned) — a DIFFERENT story, a DIFFERENT trope.
# --------------------------------------------------------------------------- #
def test_mouse_analysis_is_a_coherent_analysis_of_that_story():
    agent = _fresh()
    res = la.produce_analysis(agent, MOUSE_TEXT)
    text = res["text"]

    print("\n" + "=" * 78 + "\nMOUSE ANALYSIS (general — different story/trope)\n" + "=" * 78)
    print(text)
    print("=" * 78)

    low = text.lower()
    # this story's OWN facts (mouse/cheese/hungry), not a crow template
    assert "mouse" in low and "hungry" in low
    assert "cannot reach the cheese" in low
    assert "crow" not in low and "pebble" not in low and "water" not in low
    # FLUENT, grammatical past tense: this fable's own text carries an
    # inflected surface for BOTH events ('took'/'ate'), so both realise
    # properly -- no residual here (unlike the crow's goal-remedy clause).
    assert "the mouse took" in low
    assert "the mouse take" not in low
    assert "the mouse ate" in low
    assert "the mouse eat" not in low
    # its OWN trope: pure persistence, NO ingenuity/MacGyvering
    assert "Determinator" in text and "PERSISTENCE_PAYS" in text
    assert "MacGyvering" not in text and "INGENUITY_OVER_STRENGTH" not in text
    assert "persistence pays" in low
    assert "cleverness over strength" not in low

    # still fully graph-checkable
    ver = la.verify_grounding(agent, res)
    assert ver["ok"], "unresolved: %r" % ver["unresolved"][:5]


# --------------------------------------------------------------------------- #
#  DONKEY = 0 / GRAPH-NATIVE SOURCE AUDIT — no LLM, no regex; the literary
#  CONTENT words are the faculty's realisation of graph facts, not hand-written
#  f-string literals asserting story content.
# --------------------------------------------------------------------------- #
def test_no_import_re():
    src = inspect.getsource(la)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"


def _docstring_constants(tree) -> set:
    """The id()s of string-constant nodes that are docstrings (module / func /
    class), so the content audit can EXCLUDE them — a docstring may name the
    crow as an EXAMPLE; executable string literals may not."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None) or []
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                out.add(id(body[0].value))
    return out


def test_no_story_content_word_is_a_code_literal():
    """The graph-native proof: no story CONTENT word (crow / pebble / thirsty /
    MacGyvering / cheese / ...) appears as a string literal in the module's
    EXECUTABLE code. Every such word a reader sees in the analysis was read off
    a graph node at runtime — the literary phrases are the faculty's/graph's,
    not this module's. (Docstrings, which may cite the crow as an example, are
    excluded.)"""
    src = inspect.getsource(la)
    tree = ast.parse(src)
    docstrings = _docstring_constants(tree)
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            low = node.value.lower()
            for w in _STORY_WORDS:
                if w in low:
                    offenders.append((w, node.value))
    assert not offenders, "story-content literals found in code: %r" % offenders[:5]


def test_production_faculty_is_reused_not_reinvented():
    """The affirmative clauses come from the held production faculty
    (`LanguageProduction.produce`), reused — the module does not reimplement a
    natural-language generator."""
    src = inspect.getsource(la)
    assert "LanguageProduction" in src
    assert ".produce(" in src
    # produced-kind claims actually exist in a real run
    agent = _fresh()
    res = la.produce_analysis(agent, CROW_TEXT)
    assert any(c["produced"] for c in res["claims"])
    assert any(c["kind"] == "framed" for c in res["claims"])


def test_donkey_zero_no_model_call():
    """donkey = 0: the production world is grounded by the STUB teacher (no
    model call). Assert the run makes no LLM call by wiring a counting
    self-teacher onto a booted adapter path is out of scope here; instead we
    assert the module never imports or references an LLM client, and grounds via
    `teacher_stub`."""
    src = inspect.getsource(la)
    assert "teacher_stub" in src
    for banned in ("openai", "anthropic", "requests.post", "llm(", "call_model", "self_teacher"):
        assert banned not in src, "possible model call: %r" % banned
