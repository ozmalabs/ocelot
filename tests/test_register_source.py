"""test_register_source — REGISTER / SOURCE AS A WIDER SHAPE, by-shape + by-hint,
order-N, routing the reading approach.

Gates the `domains/register_source.py` faculty:

  (a) REGISTER BY SHAPE — the Marie Curie lead recognised ENCYCLOPEDIC (by shape,
      no hint) -> routes subject-by-salience -> subject == 'curie' (NOT the sister
      'bronisława').
  (b) REGISTER BY HINT — source='wikipedia' pre-arms the encyclopedic approach on
      a short/ambiguous chunk (weak shape evidence, the hint holds).
  (c) HINT+SHAPE COMBINE — hint agrees -> confirmed; hint=encyclopedia vs a
      confident narrative fable -> shape WINS and the mismatch is FLAGGED.
  (d) CUT-AND-PASTE — a wikipedia paragraph embedded in casual text is recognised
      as an encyclopedic region BY SHAPE (no hint).
  (e) ROUTING — encyclopedic(Curie) -> subject by salience; narrative(fable) ->
      protagonist by arc-agency (crow BYTE-IDENTICAL to the committed query).
  (f) GENERIC / EXTENSIBLE — >=3 registers recognised; a new register addable (by
      hint) and mintable (on residual, the sd loop); the discipline holds on a
      covered text.

donkey=0: no LLM, no `import re`. Graph-native: register is a decoded
ShapeSignatureRegister; the hint is a graph-resident RegisterPrior; routing reads
the winning register's read_approach off the graph and dispatches a held Argmax.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_register_source.py -p no:randomly -q
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

from substrate.boot_core import boot_core                         # noqa: E402
from domains import dictionary_lexicon as dl                      # noqa: E402
from domains import comprehension_reader as cr                    # noqa: E402
from domains import narrative_structure as ns                     # noqa: E402
from domains import register_source as rs                         # noqa: E402


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
#  Corpus — real Wikipedia lead (cached) + the committed crow fable + samples.
# --------------------------------------------------------------------------- #
_CURIE_CACHE = os.path.join(ROOT, "data", "register", "curie.txt")

FABLE = (
    "In a spell of dry weather, when the Birds could find very little to drink, "
    "a thirsty Crow found a pitcher with a little water in it. But the pitcher "
    "was high and had a narrow neck, and no matter how he tried, the Crow could "
    "not reach the water. The poor thing felt as if he must die of thirst. Then "
    "an idea came to him. Picking up some small pebbles, he dropped them into "
    "the pitcher one by one. With each pebble the water rose a little higher "
    "until at last it was near enough so he could drink.")

CASUAL = ("omg i can't believe you did that lol. it was so funny, you should've "
          "seen his face!! anyway wanna grab food later? i'm starving haha")

CODE = ("def foo(x):\n    if x > 0:\n        return x * 2\n    return 0\n"
        "class Bar:\n    def run(self):\n        return self.x")

WIKI_PARA = (
    "Marie Curie (7 November 1867 - 4 July 1934) was a Polish and "
    "naturalised-French physicist and chemist. She conducted pioneering research "
    "on radioactivity and was the first woman to win a Nobel Prize, winning it in "
    "1903 and again in 1911.")


def _curie_lead(n=1800):
    with open(_CURIE_CACHE) as f:
        return f.read()[:n]


# The Marie Curie lead is cached under data/ (gitignored). Fetch, if absent:
#   curl -s "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&\
#   explaintext=1&titles=Marie%20Curie&format=json&redirects=1" ... -> curie.txt
_HAVE_CURIE = os.path.exists(_CURIE_CACHE)
_needs_curie = pytest.mark.skipif(not _HAVE_CURIE,
                                  reason="data/register/curie.txt cache absent")


# --------------------------------------------------------------------------- #
#  (a) REGISTER BY SHAPE -> the encyclopedic subject is the salient entity.
# --------------------------------------------------------------------------- #
@_needs_curie
def test_a_curie_lead_is_encyclopedic_by_shape_and_routes_to_subject():
    ag = _fresh()
    lead = _curie_lead()
    shape = rs.decode_by_shape(ag, lead[:700])
    assert shape["family"] == "encyclopedic", shape
    assert shape["register"] in ("wikipedia", "encyclopedic"), shape
    # route the full lead: encyclopedic -> subject-by-salience -> curie.
    r = rs.route_reading(_fresh(), lead)
    assert r["family"] == "encyclopedic"
    assert r["read_approach"] == "subject_by_salience"
    assert r["answer"] == "curie", r["result"]["ranking"][:4]
    names = [row["name"] for row in r["result"]["ranking"]]
    assert names[0] == "curie"
    # the subject is the SALIENT subject, NOT the sister bronisława.
    assert r["answer"] != "bronisława"
    if "bronisława" in names:
        assert names.index("curie") < names.index("bronisława")


# --------------------------------------------------------------------------- #
#  (b) REGISTER BY HINT -> pre-arm on a short/ambiguous chunk.
# --------------------------------------------------------------------------- #
def test_b_hint_prearms_encyclopedic_on_short_chunk():
    short = "She won it in 1911."
    plain = rs.decode_register(_fresh(), short)
    assert not plain["confident"]          # too little text -> weak evidence
    d = rs.decode_register(_fresh(), short, hint="source=wikipedia")
    assert d["source"] == "hint (pre-armed)", d
    assert d["family"] == "encyclopedic"
    assert d["register"] == "wikipedia"
    assert d["mismatch"] is False
    # the prior is GRAPH-RESIDENT (a RegisterPrior node), not a Python variable.
    ag = _fresh()
    rs.arm_register(ag, "you are reading an encyclopedia")
    assert any(ag.s.node(n)["attrs"].get("family") == "encyclopedic"
               for n in ag.s.nodes("RegisterPrior"))


# --------------------------------------------------------------------------- #
#  (c) HINT+SHAPE COMBINE — confirm on agreement; shape overrides + flags on a
#      confident mismatch.
# --------------------------------------------------------------------------- #
def test_c_hint_confirms_then_shape_overrides_and_flags_mismatch():
    # agreement: hint=wikipedia + a wiki lead shape -> confirmed.
    conf = rs.decode_register(_fresh(), WIKI_PARA, hint="wikipedia")
    assert conf["source"] == "hint+shape"
    assert conf["mismatch"] is False
    assert conf["family"] == "encyclopedic"
    # mismatch: hint=encyclopedia but a CONFIDENT narrative fable -> shape wins,
    # mismatch FLAGGED (signal, not silent).
    mis = rs.decode_register(_fresh(), FABLE, hint="you are reading an encyclopedia")
    assert mis["shape"]["confident"] is True
    assert mis["family"] == "narrative"
    assert mis["source"] == "shape (override)"
    assert mis["mismatch"] is True
    assert "mismatch_note" in mis


# --------------------------------------------------------------------------- #
#  (d) CUT-AND-PASTE — a wiki paragraph embedded in casual text, by shape.
# --------------------------------------------------------------------------- #
def test_d_embedded_wikipedia_paragraph_in_casual_text():
    doc = ("hey so i was reading about this scientist lol here's the thing i copied\n\n"
           + WIKI_PARA +
           "\n\nanyway isn't that wild?? you should totally read more about her i can't even")
    emb = rs.embedded_regions(_fresh(), doc)
    assert emb["document"]["family"] == "casual", emb["document"]
    foreign = emb["embedded"]
    assert len(foreign) == 1, foreign
    assert foreign[0]["family"] == "encyclopedic"
    assert foreign[0]["register"] in ("wikipedia", "encyclopedic")


# --------------------------------------------------------------------------- #
#  (e) ROUTING — the SAME reader routes by register; the fable protagonist is
#      BYTE-IDENTICAL to the committed narrative query.
# --------------------------------------------------------------------------- #
def test_e_same_reader_routes_by_register_fable_protagonist_byte_identical():
    r = rs.route_reading(_fresh(), FABLE)
    assert r["family"] == "narrative"
    assert r["read_approach"] == "protagonist_by_arc_agency"
    assert r["answer"] == "crow"
    # BYTE-IDENTITY: the committed protagonist query on the same fable graph.
    ag = _fresh()
    cr.read_and_comprehend(ag, FABLE)
    committed = ns.protagonist_by_arc_agency(ag)["protagonist"]
    assert committed == "crow"
    assert r["answer"] == committed


# --------------------------------------------------------------------------- #
#  (f) GENERIC / EXTENSIBLE — >=3 registers; addable by hint; mintable on
#      residual; the discipline holds on a covered text.
# --------------------------------------------------------------------------- #
def test_f1_three_plus_registers_recognized():
    ag = _fresh()
    got = {}
    for name, text in (("encyclopedic", WIKI_PARA), ("narrative", FABLE),
                       ("casual", CASUAL), ("code", CODE)):
        fam = rs.decode_by_shape(ag, text)["family"]
        got[name] = fam
    assert got["encyclopedic"] == "encyclopedic"
    assert got["narrative"] == "narrative"
    assert got["casual"] == "casual"
    assert got["code"] == "code"
    assert len({v for v in got.values()}) >= 3


def test_f2_new_register_addable_by_hint():
    ag = _fresh()
    before = {r["name"] for r in rs.registers(ag)}
    res = rs.add_register(ag, "legalese",
                          ["dense", "refs", "nodefn", "impersonal", "charlight",
                           "nocontr", "flat", "proselayout"],
                          family="legal", read_approach="subject_by_salience")
    assert res["added"] is True
    after = {r["name"] for r in rs.registers(ag)}
    assert "legalese" in after and len(after) == len(before) + 1


def test_f3_mint_on_residual_then_discipline_holds():
    # a text no register covers well -> residual -> mint -> re-decode recognizes.
    ag = _fresh()
    weird = "AAAA! ?? 123 %%% @@@ ;;; ~~~ zzz? qqq! 456 (((( ))))"
    m = rs.mint_register_on_residual(ag, weird, name_hint="glitch", family="noise")
    assert m["minted"] is True
    assert m["recognized"] is True and m["reobserved"] == "glitch"
    assert m["fit_after"] > m["fit_before"]
    # the DISCIPLINE: a well-covered text mints NOTHING.
    ag2 = _fresh()
    hold = rs.mint_register_on_residual(ag2, WIKI_PARA, family="x")
    assert hold["minted"] is False


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE / donkey=0 SOURCE AUDIT — no `import re`; the register decision
#  is a ShapeDecode, the subject decision an Argmax; no Python register table.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_decisions_are_graph_native():
    src = inspect.getsource(rs)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(a.name != "re" for a in node.names), "no import re"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "no import re"
    # the register decode goes through the Rust ShapeDecode (compose_design_for_goal)
    assert "compose_design_for_goal" in src
    # the subject decision is a held Argmax Term, not a Python max/sorted.
    assert "_Argmax" in src
    subj = inspect.getsource(rs.subject_by_salience)
    assert "native.evaluate" in subj
