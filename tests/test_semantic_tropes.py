"""test_semantic_tropes — RICH SEMANTIC TROPES: the moral from CONTENT RELATIONS,
not arc shape.

The ceiling (test_generic_reading) learns a COARSE structural trope
(LEARNED_PROBLEM / LEARNED_INCREMENTAL) — a shape, not a moral. This suite gates
the fix: `domains.trope_theme.recognize_semantic_trope` decodes the
PARTICIPANT-RELATION pattern (who acts on whom, read off the situation model's
own SmEvent nodes) + the OUTCOME VALENCE (which protagonist ends acting/gaining)
against a ShapeSignatureSemanticTrope codebook that GROWS via the sd_mint_quantum
loop. Every assertion reads what the recogniser MINTS — never re-derives it.
Donkey = 0: no LLM, no regex, no Python literal naming a semantic trope (source
audit below) — the moral is ShapeDecode's own set-cover verdict over the content
tokens, read off the winning ShapeSignatureSemanticTrope's own `theme`; a novel
content relation mints a learned quantum; tropes_teacher only NAMES an
already-decided trope.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_semantic_tropes.py -p no:randomly -q -s
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

from substrate.boot_core import boot_core                               # noqa: E402
from domains import dictionary_lexicon as dl                            # noqa: E402
from domains import reading_drive as rd                                # noqa: E402
from domains import trope_theme as tt                                   # noqa: E402
from domains import comprehension_reader as cr                          # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg                  # noqa: E402
import jabberwock_reads_the_moral as jrm                                # noqa: E402
import tests.test_order_n_nested_story as t2b                           # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _one(sem, name):
    for t in sem["tropes"]:
        if t["name"] == name:
            return t
    raise AssertionError("no %r trope in %r" % (name, [t["name"] for t in sem["tropes"]]))


# --------------------------------------------------------------------------- #
#  1. LION AND MOUSE — RECIPROCITY (a kindness is repaid), NOT LEARNED_INCREMENTAL.
#     The content relation is the cross-episode role-reversal (RETURN_ACTION),
#     read off the SmEvent participant relations — a REAL moral, verbatim.
# --------------------------------------------------------------------------- #
def test_lion_mouse_learns_reciprocity_a_real_moral():
    res = jrm.read_moral_nested(jrm.LION_MOUSE)
    sem = res["semantic"]
    assert sem["tokens"] == ["REVERSAL"]
    names = [t["name"] for t in sem["tropes"]]
    assert names == ["RECIPROCITY"], "expected RECIPROCITY, got %r" % names
    # it is NOT the coarse structural placeholder the ceiling produced.
    assert "LEARNED_INCREMENTAL" not in names and "LEARNED_PROBLEM" not in names
    r = _one(sem, "RECIPROCITY")
    # a REAL moral theme, verbatim (seed data, read off — never invented).
    assert r["theme"] == "a kindness is repaid"
    assert r["valence"] == "mutual"
    assert r["line"].startswith("A kindness is repaid -- the one who was spared returns the deed.")
    assert r["learned"] is False
    # named by tropes_teacher (a citable TVTropes label for the decided trope).
    assert r["label"]["name"] == "LaserGuidedKarma" and r["label"]["source"] == "tvtropes"
    # graph-checkable: the REVERSAL traces to the two SmEvents (lion->mouse, mouse->lion).
    ev = tt.semantic_trope_evidence(res["agent"], r["_node_obj"])
    pairs = {(e["agent"], e["patient"]) for e in ev}
    assert ("lion", "mouse") in pairs and ("mouse", "lion") in pairs


# --------------------------------------------------------------------------- #
#  2. FLATTERY + FORESIGHT — each a REAL content-relation moral (honest about
#     the coarser detection: flattery = speech-then-deed by one agent; foresight
#     = store-then-consume-own-store).
# --------------------------------------------------------------------------- #
def test_fox_crow_learns_flattery():
    res = jrm.read_moral_flat(jrm.FLATTERY)
    sem = res["semantic"]
    assert sem["tokens"] == ["SPEECH_DEED"]
    f = _one(sem, "FLATTERY")
    assert f["theme"] == "flattery is used to gain another's loss"
    assert f["valence"] == "asymmetric"
    assert "flatterer" in f["line"] and "praise is a means" in f["line"]
    # the computed OUTCOME VALENCE: the flatterer (fox) is the final actor/gainer.
    assert f["protagonist"] == "fox"
    assert "fox" in f["outcome"] and "acts/gains" in f["outcome"]
    assert f["label"]["name"] == "ManipulativeBastard" and f["label"]["source"] == "tvtropes"
    ev = tt.semantic_trope_evidence(res["agent"], f["_node_obj"])
    verbs = {e["verb"] for e in ev}
    assert "praise" in verbs and "snatch" in verbs


def test_ant_grasshopper_learns_foresight():
    res = jrm.read_moral_flat(jrm.FORESIGHT)
    sem = res["semantic"]
    assert sem["tokens"] == ["STORE_CONSUME"]
    f = _one(sem, "FORESIGHT")
    assert f["theme"] == "the provident outlast the idle"
    assert f["valence"] == "split"
    assert "Foresight outlasts idleness" in f["line"]
    # the provider (ant) is the final actor; the idler (grasshopper) is left passive.
    assert f["protagonist"] == "ant" and "ant" in f["outcome"]
    assert f["label"]["name"] == "CrazyPrepared" and f["label"]["source"] == "tvtropes"
    ev = tt.semantic_trope_evidence(res["agent"], f["_node_obj"])
    verbs = sorted(e["verb"] for e in ev)
    assert verbs == ["eat", "store"]


# --------------------------------------------------------------------------- #
#  3. GENERAL — a NOVEL content relation (mutual flattery, no deed returned)
#     mints a LEARNED semantic trope (the sd_mint_quantum precedent at the
#     content level), NOT a structural placeholder.
# --------------------------------------------------------------------------- #
def test_novel_content_relation_mints_a_learned_semantic_trope():
    res = jrm.read_moral_flat(jrm.NOVEL)
    sem = res["semantic"]
    assert sem["tokens"] == ["MUTUAL_SPEECH"]
    learned = sem.get("learned")
    assert learned is not None and learned["minted"] is True
    t = _one(sem, "LEARNED_MUTUAL_SPEECH")
    assert t["learned"] is True
    # the theme is a CONTENT-relation abstraction (who does what), not an arc SHAPE
    # (no TROPE_PROBLEM / problem-faced structural placeholder).
    assert "content-relation moral the reader LEARNED" in t["theme"]
    assert "exchange words with no deed returned" in t["theme"]
    assert "coarser than a hand-authored moral" in t["theme"]
    for structural in ("TROPE_PROBLEM", "TROPE_INCREMENTAL", "a problem is faced"):
        assert structural not in t["theme"]


def test_learned_semantic_trope_is_a_persistent_codebook_quantum():
    # dynamic quantization at the CONTENT level: the mint GROWS the
    # ShapeSignatureSemanticTrope codebook by exactly one quantum, idempotently.
    ag = _fresh()
    tt.ensure_semantic_codebook(ag)
    sub, native = tt._resolve(ag)
    before = len(ag.s.nodes("ShapeSignatureSemanticTrope"))
    a = tt._mint_learned_semantic_trope(ag, sub, native, ["BETRAYAL"])
    assert a["minted"] is True
    assert len(ag.s.nodes("ShapeSignatureSemanticTrope")) == before + 1
    b = tt._mint_learned_semantic_trope(ag, sub, native, ["BETRAYAL"])
    assert b["minted"] is False
    assert len(ag.s.nodes("ShapeSignatureSemanticTrope")) == before + 1


# --------------------------------------------------------------------------- #
#  4. DISCRIMINATIVE — a story with no content-relation signal is an honest null
#     (nothing fabricated).
# --------------------------------------------------------------------------- #
def test_crow_has_no_content_relation_signal_honest_null():
    res = jrm.read_moral_flat(jpafg.CROW)
    sem = res["semantic"]
    assert sem["tokens"] == [] and sem["tropes"] == []
    assert "honest null" in sem["reason"]


# --------------------------------------------------------------------------- #
#  5. NO REGRESSION — the crow's arc-shape tropes are BYTE-IDENTICAL; the
#     semantic recogniser is purely additive (recognize_tropes_and_theme
#     untouched).
# --------------------------------------------------------------------------- #
def test_crow_arc_shape_tropes_unchanged():
    agent = _fresh()
    g = cr.read_and_comprehend(agent, jrm.CROW, window=2)
    r = next(x for x in g["trope_theme"]["results"] if x["entity"] == "crow")
    names = {t["name"] for t in r["tropes"]}
    assert names == {"INGENUITY_OVER_STRENGTH", "PERSISTENCE_PAYS"}
    assert r["residual"] == []


def test_crow_report_byte_identical():
    rep = jpafg.analyse(jrm.CROW)["report"]
    assert rep == t2b._CROW_REPORT, (
        "the semantic-trope addition changed the crow report — the arc-shape path "
        "must be untouched (recognize_tropes_and_theme byte-identical)")


# --------------------------------------------------------------------------- #
#  6. GRAPH-NATIVE AUDIT — the content-pattern is a ShapeDecode over the situation
#     model's participant relations + valence; NO moral-name literal drives the
#     mint; the mint is sd_mint_quantum; the name comes from tropes_teacher; no
#     import re; donkey = 0.
# --------------------------------------------------------------------------- #
_SEMANTIC_TROPE_NAMES = ("RECIPROCITY", "FLATTERY", "FORESIGHT")


def test_semantic_decode_is_shape_decode_over_content_signals():
    src = inspect.getsource(tt._decode_semantic)
    assert '"type": "ShapeDecode"' in src
    assert '"codebook_type": _SEM_CODEBOOK_TYPE' in src
    # the content tokens are read off the situation model's own SmEvent nodes.
    ce = inspect.getsource(tt._content_events)
    assert 'nodes("SmEvent")' in ce and "idx_protagonist" in ce and "arg1" in ce


def test_no_moral_name_literal_drives_the_mint():
    """The DECISION functions (token build + decode + mint) never contain a
    seeded semantic-trope-name string literal — the moral name is only ever the
    decode's own verdict, read off the winning ShapeSignatureSemanticTrope node's
    `name` attr (seed data). The moral names live ONLY in seeds/semantic_tropes."""
    for fn in (tt._build_content_tokens, tt._reversal_signal, tt._speech_deed_signal,
               tt._store_consume_signal, tt._mutual_speech_signal,
               tt._decode_and_mint_semantic, tt._mint_semantic_trope,
               tt._mint_learned_semantic_trope, tt.recognize_semantic_trope):
        src = inspect.getsource(fn)
        for moral in _SEMANTIC_TROPE_NAMES:
            assert moral not in src, (
                "function %r contains the moral-name literal %r — the moral must "
                "be the ShapeDecode verdict only" % (fn.__name__, moral))


def test_learned_semantic_mint_is_sd_mint_quantum():
    mint_src = inspect.getsource(tt._mint_learned_semantic_trope)
    assert "add_node(_SEM_CODEBOOK_TYPE" in mint_src and '"learned": 1' in mint_src
    # the learned name is DERIVED from the residual content tokens, not hardcoded.
    name_src = inspect.getsource(tt._learned_semantic_name)
    assert "LEARNED_" in name_src
    for moral in _SEMANTIC_TROPE_NAMES:
        assert moral not in mint_src and moral not in name_src


def test_naming_comes_from_tropes_teacher():
    lab_src = inspect.getsource(tt._sem_label_for)
    assert "_teacher()" in lab_src and "lookup(phrase)" in lab_src
    assert '"source": "tvtropes"' in lab_src and '"source": "self_authored"' in lab_src


def test_no_import_re_no_donkey_in_trope_theme():
    src = inspect.getsource(tt)
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            assert not any(a.name == "re" for a in n.names), "import re in trope_theme"
        if isinstance(n, ast.ImportFrom):
            assert n.module != "re", "from re import ... in trope_theme"
    for banned in ("openai", "anthropic", "requests.post", "call_model"):
        assert banned not in src, "donkey token %r in trope_theme" % banned
