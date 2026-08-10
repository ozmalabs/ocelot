"""GENDER AS A DYNAMIC DECODED SHAPE — the animal-hero pronoun unblock.

THE CREATOR'S REFRAME: "gender is about SHAPE — but is also extremely dynamic.
But languages that gender words do so by word dequant and object properties."

Coreference for animal heroes broke at the AGREEMENT layer: a 'he' pronoun could
not bind an animal-category hero (animals were treated as neuter/object — an
'animal' category was NOT in the person-pronoun's fixed {person, unknown} filter),
so the ass/dog pronouns never resolved. This test locks the FIX: gender is not a
static table (he=person-male) — it is a SHAPE, DYNAMICALLY DEQUANTIZED, decoded
per entity from (a) WORD-DEQUANT (the word's gendered form — Spanish -o/-a, German
der/die/das), (b) OBJECT-PROPERTIES (natural gender king->male / queen->female,
read from the WordNet gloss), (c) CONTEXT (the pronouns the story USES — the sd-loop
dequant that establishes an underspecified gender on the first gendered pronoun).

Agreement is PERMISSIVE while a gender is underspecified (an animate character can
take a gendered pronoun, establishing its gender) and STRICT once established (a
male entity rejects 'she'). This makes the animal hero COMPATIBLE (the ass, animate
via WordNet's ass.n.03, decoded 'he' -> male) so it RESOLVES.

  · GRAPH-NATIVE — the gender-shape is decoded ShapeSignature attrs on the SmEntity
    (coref_animate / coref_gender); the AGREEMENT is a graph Term (Filter over those
    attrs); the DEQUANT is a graph mutation after the native Argmax. NOT a Python
    gender table (a hardcoded pronoun->gender map for the PRONOUN's own shape is
    fine; the REFERENT's gender is DECODED). No `import re`; donkey = 0; no LLM.
  · CROW BYTE-IDENTICAL — the crow's coref (he->crow, him->crow, them->birds) is
    unchanged; the crow pool has no animal-category entity and no pronoun-surface
    competitor, so every new factor contributes 0. test_crow_gate / test_summit
    stay green (asserted by their own suites).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_gender_shape.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import coref_entities as ce              # noqa: E402
from domains import gender_shape as gs                # noqa: E402


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


def _binds(rec):
    return [(x["surface"], x.get("concept")) for x in rec["resolutions"] if x.get("resolved")]


# --------------------------------------------------------------------------- #
#  (a) ANIMAL-HERO PRONOUN BINDING — the headline. 'he' binds the animal hero,
#  the he/the-ass chain merges into ONE entity, the actions attribute to it.
#  BEFORE/AFTER is proven at the agreement Term itself: the OLD person filter
#  ({person, unknown}) REJECTS an animal; the NEW gender-shape filter ADMITS it.
# --------------------------------------------------------------------------- #
def test_animal_hero_he_binds_and_chain_merges():
    ag = _fresh()
    r = ce.read_into_situation_model(ag, "The ass was old. He was tired. He ran away.")
    binds = _binds(r)
    assert ("he", "ass") in binds
    assert sum(1 for s, c in binds if s == "he" and c == "ass") == 2   # both 'he' merge
    ass = r["situation_model"]["ass"]
    # the ass is an ANIMAL HERO: mis-grounded 'object' by its buttocks sense-1 yet
    # ANIMATE via WordNet's ass.n.03 — exactly the case the old filter excluded.
    assert ass["coref_animate"] == 1.0
    assert ass["coref_gender"] == "male"          # context dequantized male
    assert ass["coref_mentions"] == 3.0           # he / he / the-ass are ONE entity
    assert "he" not in r["situation_model"]        # no throwaway pronoun node


def test_before_after_at_the_agreement_term():
    """BEFORE/AFTER, verbatim at the Term: with ONLY an animal entity resident, the
    OLD person filter (category in {person, unknown}) finds NO candidate (the animal
    hero was excluded — the break), while the NEW gender-shape agreement admits it."""
    ag = _fresh()
    ce._touch_entity(ag, "The dog barked.", "dog", "agent", 1)   # animal, animate
    _sub, native = ce._resolve(ag)

    def _V(n): return {"type": "Var", "name": n}

    def _Attr(nd, k): return {"type": "Attr", "node": nd, "key": k}

    def _Eq(a, b): return {"type": "Eq", "a": a, "b": b}
    old_person = {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "SmEntity"},
                  "var_name": "e",
                  "predicate": {"type": "Or", "items": [
                      _Eq(_Attr(_V("e"), "coref_category"), {"type": "Lit", "value": "person"}),
                      _Eq(_Attr(_V("e"), "coref_category"), {"type": "Lit", "value": "unknown"})]}}
    old_pool = native.evaluate(old_person, {}) or []
    assert not old_pool                                   # BEFORE: animal rejected

    new_pool = native.evaluate(ce.candidate_term({**ce._PRONOUNS["he"], "gender": "male"}), {}) or []
    names = {ag.s.node(e)["attrs"].get("name") for e in new_pool}
    assert "dog" in names                                 # AFTER: animal admitted


# --------------------------------------------------------------------------- #
#  (b) DYNAMIC — the SAME word takes a DIFFERENT gender by context; the decode is
#  from evidence (the story's pronoun), not a lookup. + STRICT once established.
# --------------------------------------------------------------------------- #
def test_dynamic_same_word_different_gender():
    a1 = _fresh()
    r1 = ce.read_into_situation_model(a1, "The ass was tired. He lay down.")
    a2 = _fresh()
    r2 = ce.read_into_situation_model(a2, "The ass was tired. She lay down.")
    assert r1["situation_model"]["ass"]["coref_gender"] == "male"      # context he -> male
    assert r2["situation_model"]["ass"]["coref_gender"] == "female"    # context she -> female
    assert ("he", "ass") in _binds(r1)
    assert ("she", "ass") in _binds(r2)


def test_strict_once_established_male_rejects_she():
    ag = _fresh()
    ce._touch_entity(ag, "The ass slept.", "ass", "agent", 1)
    # first 'he' dequantizes the ass to male
    ce.resolve_pronoun(ag, "he", "He woke.", 2, ce._current_cb(ag))
    assert ag.s.node(_entity(ag, "ass"))["attrs"]["coref_gender"] == "male"
    # a later 'she' is now STRICTLY rejected by the shape-match (male != female)
    rec = ce.resolve_pronoun(ag, "she", "She left.", 3, ce._current_cb(ag))
    assert rec["resolved"] is False


def test_permissive_while_underspecified():
    """An underspecified animate entity (no natural gender) accepts the first
    gendered pronoun of EITHER gender — permissive until context establishes."""
    for pron in ("he", "she"):
        ag = _fresh()
        ce._touch_entity(ag, "The cat sat.", "cat", "agent", 1)
        assert ag.s.node(_entity(ag, "cat"))["attrs"]["coref_gender"] == ""   # underspecified
        rec = ce.resolve_pronoun(ag, pron, "%s moved." % pron.capitalize(), 2, ce._current_cb(ag))
        assert rec["resolved"] is True and rec["concept"] == "cat"


def _entity(ag, name):
    from domains import situation_model_reader as smr
    return smr._entity(ag, name)


# --------------------------------------------------------------------------- #
#  (c) COMPOSES WITH THE SALIENT CACHE — on a real Grimm tale read as prose, the
#  animal-hero gendered pronouns resolve ACROSS the tale (the ass/dog/sparrow take
#  he/him), and the antagonist is opposition-decided. (The RAW corpus text is
#  hard-wrapped and mis-detected as VERSE — a SEPARATE pre-existing layer that
#  licenses a throwaway 'he' metrical-hero, masking this; reading the hard-wrapped
#  prose AS prose exercises the fixed agreement. See the gate script's honest
#  ledger.)
# --------------------------------------------------------------------------- #
def test_composes_on_real_grimm_prose():
    import domains.reading_corpus as rc
    from domains import comprehension_reader as cr
    from domains import salient_cache as sc
    from domains import narrative_structure as ns
    grimm = [x for x in rc.SOURCES if x["key"] == "grimm"]
    by = {u["label"]: u for u in rc.load_units(sources=grimm)}
    text = " ".join(by["THE DOG AND THE SPARROW"]["text"].split())   # hard-wrap -> prose
    ag = _fresh()
    sc.install(ag)
    g = cr.read_and_comprehend(ag, text, window=2, max_sentences=60)
    res = g["spine"]["resolutions"]
    gendered = [(x["surface"], x["concept"]) for x in res
                if x.get("resolved") and x["surface"] in ("he", "him", "she", "her")
                and x["concept"] in ("dog", "sparrow")]
    assert gendered, "no gendered pronoun bound an animal hero"
    # the sparrow (the avenger animal hero) takes gendered pronouns across the tale
    assert any(c == "sparrow" for _s, c in gendered)
    prot = ns.protagonist_by_arc_agency(ag)
    ant = ns.antagonist_by_arc_opposition(ag, prot=prot)
    assert ant.get("antagonist") is not None
    assert ant.get("decided_by") == "opposition"


# --------------------------------------------------------------------------- #
#  (d) CROSS-LINGUISTIC — word-dequant (Spanish -o/-a, German der/die/das) +
#  object-properties (WordNet natural gender). Language-general DECODE, not a table.
# --------------------------------------------------------------------------- #
def test_cross_linguistic_word_dequant():
    assert gs.decode_gender("asno", "el asno viejo", "es") == "male"
    assert gs.decode_gender("reina", "la reina", "es") == "female"
    assert gs.decode_gender("gato", "un gato", "es") == "male"        # -o suffix
    assert gs.decode_gender("perra", "la perra", "es") == "female"    # article
    assert gs.decode_gender("Esel", "der Esel", "de") == "male"
    assert gs.decode_gender("Katze", "die Katze", "de") == "female"
    assert gs.decode_gender("Pferd", "das Pferd", "de") == "neuter"


def test_object_property_natural_gender():
    assert gs.decode_gender("king", "", "en") == "male"
    assert gs.decode_gender("queen", "", "en") == "female"
    assert gs.decode_gender("cock", "", "en") == "male"
    assert gs.decode_gender("hen", "", "en") == "female"
    # a non-natural-gender animal is UNDERSPECIFIED (context decides) — NOT a table
    assert gs.decode_gender("ass", "", "en") == ""
    assert gs.decode_gender("dog", "", "en") == ""
    assert gs.decode_gender("crow", "", "en") == ""


def test_queen_is_female_by_object_property_and_rejects_he():
    ag = _fresh()
    r = ce.read_into_situation_model(ag, "The queen was proud. She ruled the land.")
    assert r["situation_model"]["queen"]["coref_gender"] == "female"
    # a queen (natural female) STRICTLY rejects 'he'
    ce._touch_entity(ag, "The queen sat.", "queen", "agent", 5)
    rec = ce.resolve_pronoun(ag, "he", "He ruled.", 6, ce._current_cb(ag))
    assert rec["resolved"] is False or rec["concept"] != "queen"


# --------------------------------------------------------------------------- #
#  CROW BYTE-IDENTITY — the crow's coref chain is the known-good fingerprint; the
#  fix extends to animal heroes WITHOUT perturbing the working crow.
# --------------------------------------------------------------------------- #
def test_crow_coref_chain_unchanged():
    import jabberwock_reads_the_crow as jrc
    from domains import comprehension_reader as cr
    ag = _fresh()
    cr.read_and_comprehend(ag, jrc.FABLE_TEXT, window=2)
    sub = ag.s
    chains = sorted(
        (sub.node(m)["attrs"].get("surface"), sub.node(nb)["attrs"].get("name"))
        for m in sub.nodes("SmMention")
        for nb in sub.neighbours(m, "refers_to"))
    assert ("he", "crow") in chains
    assert ("him", "crow") in chains
    assert ("them", "birds") in chains


# --------------------------------------------------------------------------- #
#  ANTI-HALLUCINATION — a pronoun with no shape-compatible salient referent stays
#  HELD OPEN (honest null), never force-bound.
# --------------------------------------------------------------------------- #
def test_anti_hallucination_incompatible_gender_held_open():
    ag = _fresh()
    ce._touch_entity(ag, "The king spoke.", "king", "agent", 1)   # natural male
    rec = ce.resolve_pronoun(ag, "she", "She spoke.", 2, ce._current_cb(ag))
    assert rec["resolved"] is False
    sub, _ = ce._resolve(ag)
    held = [sub.node(n)["attrs"] for n in sub.nodes("SmMention")
            if sub.node(n)["attrs"].get("surface") == "she"]
    assert held and held[0].get("held_open") == 1.0


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — the agreement is a Term over the decoded gender-
#  shape attrs; the decision is an Argmax; the referent gender is DECODED (no
#  per-referent Python table); no `import re`.
# --------------------------------------------------------------------------- #
def test_agreement_is_graph_native_shape_match():
    term = ce.antecedent_argmax_term({**ce._PRONOUNS["he"], "gender": "male"}, None)
    assert term["type"] == "Argmax"

    def _finds(node, key, val):
        if isinstance(node, dict):
            if node.get("type") == "Attr" and node.get("key") == key:
                return True
            return any(_finds(v, key, val) for v in node.values())
        if isinstance(node, list):
            return any(_finds(v, key, val) for v in node)
        return False
    # the agreement Filter reads the decoded gender-shape attrs (animate + gender).
    assert _finds(term["source"], "coref_animate", None)
    assert _finds(term["source"], "coref_gender", None)


def test_no_import_re_and_referent_gender_is_decoded():
    for mod in ("gender_shape.py", "coref_entities.py"):
        src = open(os.path.join(ROOT, "domains", mod)).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name == "re" for a in node.names), "import re in %s" % mod
            if isinstance(node, ast.ImportFrom):
                assert node.module != "re", "from re import in %s" % mod
    # the referent gender is decoded from a morphological rule OR the word's OWN
    # dictionary definition — NOT a per-referent {name: gender} literal table.
    assert gs.decode_gender("ass", "", "en") == ""           # not tabled to male
    assert gs.decode_gender("ass", "an ass brayed", "es") == ""   # es: no -o/-a, no es-article
    assert gs.decode_gender("perro", "", "es") == "male"     # decoded from -o morphology
    assert gs.decode_gender("perra", "", "es") == "female"   # decoded from -a morphology
