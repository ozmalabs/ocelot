"""test_animal_grounding — grounding ass/cock/... as ANIMALS from the reader's OWN
KNOWLEDGE (WordNet's animal senses across ALL senses + the situation-model context),
NOT a hardcoded animal list and NOT an LLM.

THE CORRECTION (of the donkey=0 residual). The earlier pass promoted only 'donkey':
'ass' agent-slot-grounds the COARSE person sense and 'cock' is never an eventive
agent in the Bremen tale, so both stayed `object` — declared unfixable under
donkey=0. The creator's correction: grounding via the reader's OWN dictionary
knowledge is NOT a hardcoded list — it is the reader KNOWING things. The knowledge
EXISTS in WordNet: 'ass' carries ass.n.03 (a donkey, noun.animal), 'cock' carries
cock.n.04 (a rooster) — just not at frequency sense-1.

THE MECHANISM (coref_entities._refine_animacy_from_agency, graph-native):
  · (b) WordNet ANIMAL SENSE ACROSS ALL SENSES — _has_whole_animal_sense: the word
    has a `noun.animal` synset descended from chordate.n.01 / invertebrate.n.01 (an
    ACTUAL creature). The taxonomy is the precision: a body-part homonym
    (teeth/lips/hair/tail) and a generic animal-counter ('head' = "a head of
    cattle") carry a `noun.animal` synset but are NOT creatures -> rejected.
  · (c) CONTEXT-GATE — the entity ACTS (agency implies animacy) OR is in an
    ANIMAL-CONTEXT (>= 2 clean co-characters are already animals). 'ass' acts;
    'cock' rides the animal-context (a rooster met but never itself acting).
  · precision locks: only an un-discriminated object/unknown is overridden (a clean
    category is kept), a >=3-token parse-glom is skipped, a proper noun is skipped
    (the capitalised 'Crow'/'Birds' -> the crow fable stays byte-identical).

donkey = 0 (no LLM), no `import re`, NEVER git.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_animal_grounding.py -p no:randomly -q -s
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
from domains import coref_entities as ce                         # noqa: E402
from domains import situation_model_reader as smr                # noqa: E402
import jabberwock_reads_a_tale as tale                            # noqa: E402
import jabberwock_reads_the_crow as jrc                           # noqa: E402
import jabberwock_summit as summit                                # noqa: E402


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


# --------------------------------------------------------------------------- #
#  Decision-level helpers — a hand-built graph exercises the pass's LOGIC
#  directly (no parser noise): mint SmEntity nodes + a textbase, run the pass,
#  read back coref_category.
# --------------------------------------------------------------------------- #
def _mint(agent, name, cat):
    sub, _ = ce._resolve(agent)
    nid = smr._entity(agent, name)
    sub.set_attr(nid, "coref_category", cat)
    return nid


def _catof(agent, name):
    sub, _ = ce._resolve(agent)
    return sub.node(smr._entity(agent, name))["attrs"].get("coref_category")


# --------------------------------------------------------------------------- #
#  (1) THE READER'S OWN KNOWLEDGE — WordNet animal sense ACROSS ALL SENSES.
# --------------------------------------------------------------------------- #
def test_wordnet_animal_sense_is_read_across_all_senses_not_sense1():
    """The grounding reads WordNet's animal senses ANYWHERE, not just sense-1:
    'ass' (sense-1 buttocks), 'cock' (sense-1 penis/stopcock), 'donkey' (sense-1
    donkeywork), 'seal' (sense-1 wax) and 'crane' (sense-1 person) all carry a
    real-creature `noun.animal` synset deeper in WordNet -> True."""
    for w in ("ass", "cock", "donkey", "seal", "crane", "kid", "bat",
              "dog", "cat", "sparrow", "mouse", "wolf", "ant", "frog"):
        assert ce._has_whole_animal_sense(w), "%r: creature sense not found" % w


def test_body_parts_and_generic_counters_are_rejected_by_the_taxonomy():
    """The chordate/invertebrate ancestry is the PRECISION: a body-part homonym
    (teeth/lips/hair/tail — a `noun.animal` synset that is a PART) and a generic
    animal-COUNTER ('head' = "a single domestic animal", off domestic_animal.n.01,
    NOT a species) are NOT creatures -> False. Non-animals (robber/king/rock) too."""
    for w in ("teeth", "lips", "hair", "tail", "head",
              "robber", "king", "rock", "water", "cheese"):
        assert not ce._has_whole_animal_sense(w), "%r wrongly read as a creature" % w


def test_grounding_uses_no_hardcoded_animal_list_donkey_zero():
    """donkey = 0: the grounding is a WordNet lexname + hypernymy read, not a list.
    The helper NAMES no animal — it queries `wn.synsets(...)`, filters by the
    `noun.animal` lexname, and tests chordate/invertebrate ancestry. (The docstring
    lists example species for the reader; the CODE contains no animal-name literal
    used as data.)"""
    src = inspect.getsource(ce._has_whole_animal_sense)
    body = src[src.index("try:"):]                  # skip the docstring
    assert "wn.synsets" in body and "noun.animal" in body
    assert "chordate.n.01" in body and "invertebrate.n.01" in body
    # no LLM / shell.
    for mod in (ce, tale):
        low = inspect.getsource(mod).lower()
        for banned in ("openai", "anthropic", "call_model",
                       "subprocess", "os.system", "git commit"):
            assert banned not in low, "banned token %r in %s" % (banned, mod.__name__)
    # no `import re` — an AST check (a substring would false-match import reading_*).
    for mod in (ce, tale):
        tree = ast.parse(inspect.getsource(mod))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name == "re" for a in node.names), mod.__name__
            if isinstance(node, ast.ImportFrom):
                assert node.module != "re", mod.__name__
    # the pass DECIDES no meaning: no Python max()/sorted() picks a winner.
    ps = inspect.getsource(ce._refine_animacy_from_agency)
    assert "max(" not in ps and "sorted(" not in ps
    assert '_has_whole_animal_sense' in ps and '_animal_context' in ps


# --------------------------------------------------------------------------- #
#  (2) CONTEXT-GATE generalization — the SAME mechanism grounds kid/seal/bat as
#  animals in an animal-context, but NOT the non-animal homonym out of context.
# --------------------------------------------------------------------------- #
def test_context_gate_grounds_creatures_in_an_animal_context():
    """seal (sense-1 wax = object) NEVER acts here (it is only ever a grammatical
    OBJECT), yet in an animal-context (dog + cat already animals) it is grounded
    `animal` — the coherent co-characters are animals, so a seal coheres as one."""
    agent = _fresh()
    _mint(agent, "dog", "animal"); _mint(agent, "cat", "animal")
    _mint(agent, "seal", "object"); _mint(agent, "man", "person")
    tb = [{"sentence": "the man met a seal",
           "predications": [["met", "man", "seal"]]}]
    rw = ce._refine_animacy_from_agency(agent, tb)
    assert _catof(agent, "seal") == "animal"
    assert {r["name"] for r in rw} == {"seal"}


def test_context_gate_generalizes_to_kid_and_bat():
    """The gate is NOT a list — kid (kid.n.05 young goat) and bat (bat.n.01) are
    both grounded `animal` in an animal-context, from WordNet + the situation model
    alone."""
    agent = _fresh()
    _mint(agent, "dog", "animal"); _mint(agent, "cat", "animal")
    _mint(agent, "kid", "unknown"); _mint(agent, "bat", "object")
    _mint(agent, "man", "person")
    tb = [{"sentence": "the man met a kid and a bat",
           "predications": [["met", "man", "kid"], ["met", "man", "bat"]]}]
    ce._refine_animacy_from_agency(agent, tb)
    assert _catof(agent, "kid") == "animal"
    assert _catof(agent, "bat") == "animal"


def test_agency_grounds_a_creature_even_out_of_context():
    """Agency implies animacy independently: seal ACTS (swims) with NO animal
    co-characters and is still grounded `animal`."""
    agent = _fresh()
    _mint(agent, "seal", "object")
    tb = [{"sentence": "the seal swam away",
           "predications": [["swam", "seal"]]}]
    ce._refine_animacy_from_agency(agent, tb)
    assert _catof(agent, "seal") == "animal"


# --------------------------------------------------------------------------- #
#  (3) OVER-GROUNDING PRECISION — no false animals.
# --------------------------------------------------------------------------- #
def test_out_of_context_homonym_stays_non_animal():
    """A creature-word that neither acts NOR is in an animal-context stays put:
    'seal' as a grammatical object in a NON-animal text is not grounded animal."""
    agent = _fresh()
    _mint(agent, "seal", "object"); _mint(agent, "man", "person")
    tb = [{"sentence": "the man met a seal",
           "predications": [["met", "man", "seal"]]}]
    rw = ce._refine_animacy_from_agency(agent, tb)
    assert _catof(agent, "seal") == "object"
    assert rw == []


def test_crane_the_machine_in_a_construction_text_is_not_an_animal():
    """OVER-GROUNDING: 'crane' has a real bird sense (crane.n.05), but the crane of
    a construction site neither acts as a creature nor sits in an animal-context,
    so it is NOT grounded animal (no false animal)."""
    agent = _fresh()
    _mint(agent, "crane", "object"); _mint(agent, "beam", "object")
    _mint(agent, "builder", "person")
    tb = [{"sentence": "the builder operated the crane",
           "predications": [["operated", "builder", "crane"]]}]
    rw = ce._refine_animacy_from_agency(agent, tb)
    assert _catof(agent, "crane") != "animal"
    assert rw == []


def test_body_parts_in_an_animal_context_stay_non_animal():
    """The body-part / counter homonyms teeth / lips / tail / head — even inside a
    strong animal-context — are NOT grounded animal (the taxonomy rejects them)."""
    agent = _fresh()
    _mint(agent, "dog", "animal"); _mint(agent, "cat", "animal")
    for w in ("teeth", "lips", "tail", "head"):
        _mint(agent, w, "object")
    tb = [{"sentence": "the dog showed its teeth and its tail and its head and its lips",
           "predications": [["sharp", "teeth"]]}]
    rw = ce._refine_animacy_from_agency(agent, tb)
    for w in ("teeth", "lips", "tail", "head"):
        assert _catof(agent, w) == "object", "%r wrongly grounded animal" % w
    assert rw == []


def test_proper_noun_creature_is_not_promoted():
    """The proper-noun stance is kept: a capitalised creature name ('Seal' as a
    proper noun in its first sentence) is NOT promoted — this is exactly what keeps
    the crow fable's 'Crow'/'Birds' byte-identical."""
    agent = _fresh()
    _mint(agent, "dog", "animal"); _mint(agent, "cat", "animal")
    _mint(agent, "seal", "unknown")
    tb = [{"sentence": "Seal came to the shore",
           "predications": [["came", "seal", "shore"]]}]
    rw = ce._refine_animacy_from_agency(agent, tb)
    assert _catof(agent, "seal") == "unknown"
    assert rw == []


# --------------------------------------------------------------------------- #
#  (4) THE CROW BYTE-IDENTICAL — the HARD guard.
# --------------------------------------------------------------------------- #
def test_crow_and_summit_zero_rewrites_byte_identical():
    """The animal-grounding pass writes ZERO attrs on the crow + the three summit
    fables: their object/unknown entities are non-creatures OR proper OR the text is
    not an animal-context, so the pass returns an EMPTY rewrite list (zero graph
    mutations) — the short-fable situation model is byte-identical."""
    texts = [("CROW", jrc.FABLE_TEXT)] + [(f["title"], f["text"]) for f in summit.FABLES]
    for name, text in texts:
        r = ce.read_into_situation_model(_fresh(), text)
        assert r["animacy_rewrites"] == [], \
            "the fix mutated the short fable %r: %r" % (name, r["animacy_rewrites"])


def test_crow_qa_unchanged_6_of_6():
    result = jrc.run()
    assert result["score"] == 6 and result["score_total"] == 6


# --------------------------------------------------------------------------- #
#  (5) THE TRAVELLING MUSICIANS — before -> after (the headline).
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def _musicians():
    by = tale._load_tales()
    return tale.read_tale("THE TRAVELLING MUSICIANS",
                          by["THE TRAVELLING MUSICIANS"]["text"],
                          ["ass", "dog", "cat", "cock", "donkey"])


def test_travelling_musicians_ass_and_cock_now_animal(_musicians):
    """VERBATIM before->after: 'ass' + 'cock' — the ACTUAL acting leads — now
    categorize ANIMAL (was `object`), alongside donkey/dog/cat. The animacy
    re-groundings are exactly {ass, cock, donkey}."""
    ps = _musicians["prot_state"]
    for name in ("ass", "cock", "dog", "cat", "donkey"):
        assert ps[name]["category"] == "animal", \
            "%r categorised %r, not animal" % (name, ps[name]["category"])
    assert {r["name"] for r in _musicians["rewrites"]} == {"ass", "cock", "donkey"}


def test_travelling_musicians_animal_count_rises(_musicians):
    """The animal count rises from 2 (only dog+cat at sense-1) to 5 (adding
    ass/cock/donkey)."""
    assert _musicians["animals_before"] == 2
    assert _musicians["animals_after"] == 5


def test_travelling_musicians_qa_names_the_ass_as_an_animal(_musicians):
    """The QA/roster now NAMES the `ass` (the lead, x8 mentions) as an animal — the
    QA no longer falls to the top clean-sensed bystander animal (dog)."""
    qa = tale.qa_who_are_the_protagonists(_musicians)
    assert "ass" in qa["animals"], qa["answer"]
    assert qa["roster"][0]["name"] == "ass"
    assert qa["roster"][0]["category"] == "animal"


# --------------------------------------------------------------------------- #
#  (6) NO FALSE ANIMALS across the real tales + anti-hallucination.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def _all_tales():
    return {rec["label"]: rec for rec in tale.run()}


def test_no_false_animals_across_the_tales(_all_tales):
    """Every animacy re-grounding across all four tales is a genuine creature —
    NO body-part / counter homonym is promoted (the CAT-AND-MOUSE 'head' false
    positive a bare animal.n.01 test produced is rejected by the taxonomy)."""
    for label, rec in _all_tales.items():
        for r in rec["rewrites"]:
            assert ce._has_whole_animal_sense(r["name"]), \
                "%s: promoted a non-creature %r" % (label, r["name"])
        # the CAT-AND-MOUSE regression: 'head' is never grounded animal.
        assert rec["sm"].get("head", {}).get("coref_category") != "animal", \
            "%s: 'head' wrongly grounded animal" % label


def test_grounding_holds_on_every_tale(_all_tales):
    for label, rec in _all_tales.items():
        assert rec["grounding"]["ok"], \
            "%s: unresolved pointers %r" % (label, rec["grounding"]["unresolved"][:5])
