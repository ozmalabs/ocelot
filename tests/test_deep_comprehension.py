"""test_deep_comprehension — DEEP COMPREHENSION over LONG real Grimm prose: the
reader now tracks WHO the characters are (entity recognition + categorisation +
coref) across a real tale, WITHOUT perturbing the short-fable comprehension.

THE BREAK (reading-corpus summit): on Grimm's 'The Travelling Musicians' the
entity categories were object 36 / person 12 / UNKNOWN 37 (43%) / animal ONLY 2 —
the animal PROTAGONISTS were mis-categorised and not tracked as animals.

THE DIAGNOSIS (measured):
  · COREF-MERGE already WORKS — each protagonist is ONE persistent SmEntity, its
    repeated mentions merged, tracked across the whole tale (coref_mentions).
  · CATEGORISATION was the break, narrower than 43% suggests: most animal names
    (dog/cat/wolf/boar/mouse/sparrow/frog/bird) already ground `animal` via WordNet
    sense-1; the break is the sense-1-NON-animal minority (ass->buttocks,
    cock->stopcock, donkey->donkeywork) that _grounded_category's `patient` slot
    (no animate discrimination) grounds `object`.
  · OVER-SEGMENTATION (adjective/pronoun/quote-fragment entities) is a PARSE-layer
    residual present in the short dev fables too -> byte-identity-LOCKED, reported
    honestly as what inflates the RAW unknown fraction (the clean-real fraction is
    ~half of it).

THE FIX (coref_entities._refine_animacy_from_agency): a graph-native post-read pass
re-grounds each entity that ACTS (agent of a WordNet-eventive verb) with the
`agent` slot and promotes it to `animal` when the animate grounding is animal and
the current category is the un-discriminated object/unknown (clean, non-proper).
The eventive-agent guard = precision lock (a body-part homonym never acts -> never
promoted). On a short dev fable it writes NOTHING -> BYTE-IDENTICAL.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_deep_comprehension.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                        # noqa: E402
from domains import dictionary_lexicon as dl                     # noqa: E402
from domains import comprehension_reader as cr                   # noqa: E402
from domains import coref_entities as ce                         # noqa: E402
import jabberwock_reads_a_tale as tale                           # noqa: E402
import jabberwock_reads_the_crow as jrc                          # noqa: E402
import jabberwock_summit as summit                               # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


@pytest.fixture(scope="module")
def _tales():
    return {rec["label"]: rec for rec in tale.run()}


# --------------------------------------------------------------------------- #
#  THE HARD GUARD — CROW + SUMMIT BYTE-IDENTICAL. The animacy re-grounding pass
#  writes ZERO attrs on a short dev fable (its eventive-agent object/unknown
#  entities have no dominant animal sense), so the situation model is provably
#  byte-identical: an EMPTY rewrite list == zero graph mutations.
# --------------------------------------------------------------------------- #
def test_short_fables_zero_animacy_rewrites_byte_identical():
    """The categorisation fix perturbs the crow + the three summit fables NOT AT
    ALL: the pass returns an empty rewrite list on each (zero graph mutations), so
    the short-fable situation model is byte-identical to its pre-fix value."""
    texts = [("CROW", jrc.FABLE_TEXT)] + [(f["title"], f["text"]) for f in summit.FABLES]
    for name, text in texts:
        r = ce.read_into_situation_model(_fresh(), text)
        assert r["animacy_rewrites"] == [], \
            "the fix mutated the short fable %r: %r" % (name, r["animacy_rewrites"])


def test_crow_qa_still_6_of_6():
    """The crow gate's QA is UNCHANGED at 6/6 — the fix does not touch the crow."""
    result = jrc.run()
    assert result["score"] == 6 and result["score_total"] == 6


def test_summit_animal_categorisation_still_holds():
    """The summit invariant (each unseen fable's protagonist animal is categorised
    `animal`) still holds — the fix does not regress the summit fables."""
    for f in summit.FABLES:
        agent = _fresh()
        g = cr.read_and_comprehend(agent, f["text"], window=2)
        sm = g["spine"]["situation_model"]
        cats = {v.get("coref_category") for v in sm.values()}
        assert "animal" in cats, "summit fable %r lost its animal category" % f["title"]
        assert (g["spine"].get("animacy_rewrites") or []) == []   # byte-identical


# --------------------------------------------------------------------------- #
#  THE NAMED TALE — 'The Travelling Musicians' (the Bremen Town Musicians). The
#  animal protagonists are COREF-TRACKED (one merged entity each) and the
#  sense-1-non-animal animal that ACTS (donkey) is now categorised `animal`.
# --------------------------------------------------------------------------- #
def test_travelling_musicians_coref_merged_one_entity_each(_tales):
    """COREF-MERGE: each protagonist is ONE persistent SmEntity (the ass named /
    pronominalised many times is a SINGLE node, not many), tracked across the
    tale — its mention count proves the merge."""
    rec = _tales["THE TRAVELLING MUSICIANS"]
    ps = rec["prot_state"]
    for name in ("ass", "dog", "cat", "cock"):
        assert name in ps, "protagonist %r not tracked as an entity" % name
    assert ps["ass"]["mentions"] >= 5, "the ass was not coref-merged across the tale"


def test_travelling_musicians_animals_categorised_up(_tales):
    """CATEGORISATION improves: the acting/animal-context animals 'ass', 'cock' and
    'donkey' (WordNet sense-1 = buttocks / penis / donkeywork, previously `object`)
    are re-grounded `animal` from the reader's OWN WordNet knowledge (their
    real-creature senses ass.n.03 / cock.n.04 / domestic_ass.n.01) + the situation
    model, so animals-found rises 2 -> 5; dog + cat + donkey + ass + cock are all
    `animal`.

    DELIBERATE UPDATE (was: 'ass'/'cock' PINNED `object`, rewrites == {donkey}). The
    creator's correction retired that residual: grounding via the reader's own
    WordNet animal senses (across ALL senses) + a context-gate is NOT a hardcoded
    animal list (donkey = 0). This number changed via a reviewed edit to THIS test."""
    rec = _tales["THE TRAVELLING MUSICIANS"]
    assert rec["animals_after"] > rec["animals_before"], \
        "no categorisation improvement: %d -> %d" % (rec["animals_before"], rec["animals_after"])
    ps = rec["prot_state"]
    for name in ("dog", "cat", "donkey", "ass", "cock"):
        assert ps[name]["category"] == "animal", "%r not categorised animal" % name
    assert {r["name"] for r in rec["rewrites"]} == {"ass", "cock", "donkey"}


# --------------------------------------------------------------------------- #
#  GENERALISES across >=3 Grimm tales — the protagonists are categorised animal
#  AND coref-tracked on EACH (not tuned to one tale).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("label,leads", [
    ("OLD SULTAN", ["wolf", "dog", "cat", "boar"]),
    ("CAT AND MOUSE IN PARTNERSHIP", ["cat", "mouse"]),
    ("THE DOG AND THE SPARROW", ["dog", "sparrow"]),
])
def test_generalises_protagonists_animal_and_tracked(_tales, label, leads):
    rec = _tales[label]
    ps = rec["prot_state"]
    for name in leads:
        assert name in ps, "%s: lead %r not tracked" % (label, name)
        assert ps[name]["category"] == "animal", \
            "%s: lead %r categorised %r, not animal" % (label, name, ps[name]["category"])
        assert ps[name]["mentions"] >= 1
        # each lead is in the coref-tracked CHARACTER roster, categorised animal.
        assert any(r["name"] == name and r["category"] == "animal"
                   for r in rec["roster"]), "%s: %r not in the animal roster" % (label, name)
    # the QA answer NAMES real animals (the top character of an animal tale is one).
    qa = tale.qa_who_are_the_protagonists(rec)
    assert qa["animals"], "%s: QA named no animals" % label
    assert qa["roster"] and qa["roster"][0]["category"] == "animal", \
        "%s: the most-tracked character is not an animal (%r)" % (label, qa["roster"][:1])


def test_qa_who_are_the_protagonists_cat_and_mouse_verbatim(_tales):
    """VERBATIM QA — 'Who are the protagonists?' of Cat and Mouse in Partnership:
    the two clear top characters by mention are the cat (x20) and the mouse (x4),
    both categorised `animal`, read straight off the coref-tracked graph."""
    rec = _tales["CAT AND MOUSE IN PARTNERSHIP"]
    qa = tale.qa_who_are_the_protagonists(rec)
    top2 = qa["roster"][:2]
    assert [r["name"] for r in top2] == ["cat", "mouse"], qa["answer"]
    assert all(r["category"] == "animal" for r in top2)
    assert qa["animals"][:2] == ["cat", "mouse"]


# --------------------------------------------------------------------------- #
#  UNKNOWN FRACTION — HONEST before/after. The raw unknown fraction is dominated
#  by PARSE over-segmentation (byte-locked, present in short fables too), so the
#  fix does not drop it; but the clean-REAL unknown fraction is materially lower
#  (about half), which is the honest measure of "who are the characters".
# --------------------------------------------------------------------------- #
def test_unknown_fraction_real_is_materially_below_raw(_tales):
    for label, rec in _tales.items():
        u_all = rec["unknown_all"][2]
        u_real = rec["unknown_real"][2]
        assert u_real < u_all, \
            "%s: clean-real unknown %.1f%% not below raw %.1f%%" % (label, u_real, u_all)


# --------------------------------------------------------------------------- #
#  ANTI-HALLUCINATION HOLDS — verify_grounding ok on every tale (no ungrounded
#  claim leaks, even on long unseen prose).
# --------------------------------------------------------------------------- #
def test_grounding_holds_on_every_tale(_tales):
    for label, rec in _tales.items():
        g = rec["grounding"]
        assert g["ok"], "%s: unresolved pointers %r" % (label, g["unresolved"][:5])
        for c in rec["analysis"].get("claims") or []:
            assert c["graph_pointers"], "%s: ungrounded claim %r" % (label, c["sentence"])


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE / donkey = 0 / no `import re` — the categorisation is a WordNet
#  read + attr write (the SAME adapter status as _grounded_category); no LLM, no
#  regex, no Python decision that PICKS a meaning over graph state.
# --------------------------------------------------------------------------- #
def test_source_audit_graph_native_no_re_no_donkey():
    for mod in (ce, tale):
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name == "re" for a in node.names), "import re in %s" % mod.__name__
            if isinstance(node, ast.ImportFrom):
                assert node.module != "re", "from re import in %s" % mod.__name__
        low = src.lower()
        for banned in ("openai", "anthropic", "call_model", "subprocess",
                       "os.system", '"git ', "'git ", "git commit"):
            assert banned not in low, "banned token %r in %s" % (banned, mod.__name__)
    # the pass DECIDES no meaning: it writes coref_category (WordNet's verdict) and
    # calls no max()/sorted() to pick a winner.
    pass_src = inspect.getsource(ce._refine_animacy_from_agency)
    assert "max(" not in pass_src and "sorted(" not in pass_src
    assert "dictionary_lookup" in inspect.getsource(ce._agent_grounded_category)
    assert 'set_attr(n, "coref_category"' in pass_src
