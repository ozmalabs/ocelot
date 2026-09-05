"""Gate for grounded_representation.ground_categories — the FAITHFUL taxonomy-
enrichment pass.

Domain concepts carry an author-supplied `category` ATTRIBUTE (a domain-correct
classification the seed author wrote) but almost no outgoing EDGES — so they are
edge-poor (SHAPE_AUDIT) and the classification sits only as a plain attr, not as
traversable structure.

`ground_categories` turns that held attr into STRUCTURE: each concept gets a
`genls` edge (is-a — the FORMAL qualia role) to a category-HUB Concept, and
same-category concepts share the one hub. Derived mechanically from what the
concept already carries (its own `category`); nothing invented, no meaning
decided (the author already named the class).

These gates pin exactly that:
  1. a concept with a `category` gains a `genls` edge to a `category:<value>` hub;
  2. same-category concepts share ONE hub (a traversable cluster);
  3. the pass is idempotent (re-running adds no duplicate edge);
  4. the new edge becomes an edge-derived `lexical:formal` coordinate in the
     concept's qualia signature (was attr-only before);
  5. a concept WITHOUT a `category` is untouched;
  6. `mt_name` scopes the pass to one microtheory's concepts.
"""
from __future__ import annotations

import json
import pathlib

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
import domains.grounded_representation as gr

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
VOCAB = ROOT / "seeds" / "shape_vocabulary.json"
QUALIA = ROOT / "seeds" / "qualia_space.json"

# node/edge vocabulary the pass + the signature read touch.
_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension",
       "DimensionEdgeRole")
_ET = ("has_concept", "genls", "built_from", "is_a", "depends_on", "grounds")


def _open(s):
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et, "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})


def _substrate(*, with_qualia: bool = False):
    s = _native.Substrate()
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    ag = s.add_node("Agent", {})
    _open(s)
    if with_qualia:
        for path in (VOCAB, QUALIA):
            s.load_seed_manifest(json.load(open(path)), ag)
    return s, ag


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, mt, name, **attrs):
    a = {"name": name}
    a.update(attrs)
    c = s.add_node("Concept", a)
    s.add_edge(mt, "has_concept", c)
    return c


def _hub(s, category):
    want = gr._category_hub_name(category)
    for c in s.nodes("Concept"):
        if s.node(c)["attrs"].get("name") == want:
            return c
    return None


# ---------------------------------------------------------------------------
# 1 + 2. category attr -> genls edge to a shared hub
# ---------------------------------------------------------------------------
def test_category_becomes_genls_edge_to_shared_hub():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    a = _concept(s, mt, "cache", category="cache_mechanism")
    b = _concept(s, mt, "tlb", category="cache_mechanism")
    lone = _concept(s, mt, "pipeline", category="pipeline_mechanism")

    res = gr.ground_categories(s)
    assert res["edges_added"] == 3
    assert res["concepts_wired"] == 3
    assert res["hubs"] == 2  # two distinct category values

    hub_cache = _hub(s, "cache_mechanism")
    assert hub_cache is not None
    # both same-category concepts genls the SAME hub (a traversable cluster).
    assert hub_cache in set(s.neighbours(a, "genls"))
    assert hub_cache in set(s.neighbours(b, "genls"))
    # the other category has its own hub.
    hub_pipe = _hub(s, "pipeline_mechanism")
    assert hub_pipe is not None and hub_pipe != hub_cache
    assert hub_pipe in set(s.neighbours(lone, "genls"))


# ---------------------------------------------------------------------------
# 3. idempotent
# ---------------------------------------------------------------------------
def test_pass_is_idempotent():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    c = _concept(s, mt, "cache", category="cache_mechanism")
    first = gr.ground_categories(s)
    assert first["edges_added"] == 1
    again = gr.ground_categories(s)
    assert again["edges_added"] == 0  # no duplicate
    assert len(set(s.neighbours(c, "genls"))) == 1


# ---------------------------------------------------------------------------
# 4. the edge becomes an edge-derived lexical:formal coordinate
# ---------------------------------------------------------------------------
def test_genls_edge_enriches_lexical_formal_signature():
    s, _ag = _substrate(with_qualia=True)
    mt = _mt(s, "m")
    c = _concept(s, mt, "cache", category="cache_mechanism")

    before = asr.concept_signature(s, c)
    # before: category present only as an attr-derived coordinate, no genls edge.
    assert not any(pred == "genls" for _dim, pred, _val in before)

    gr.ground_categories(s)
    asr._QUALIA_SCHEMA_CACHE.clear()
    after = asr.concept_signature(s, c)
    # after: a genls edge coordinate, on the FORMAL lexical dimension.
    assert ("lexical:formal", "genls", "concept") in after
    # it is strictly additive — the concept gained a coordinate.
    assert len(after) > len(before)


# ---------------------------------------------------------------------------
# 5. a concept without a category is untouched
# ---------------------------------------------------------------------------
def test_concept_without_category_untouched():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    c = _concept(s, mt, "orphan")  # no category attr
    res = gr.ground_categories(s)
    assert res["edges_added"] == 0
    assert list(s.neighbours(c, "genls")) == []


# ---------------------------------------------------------------------------
# 6. mt_name scopes the pass to one microtheory
# ---------------------------------------------------------------------------
def test_mt_scope_restricts_the_pass():
    s, _ag = _substrate()
    m1, m2 = _mt(s, "m1"), _mt(s, "m2")
    a = _concept(s, m1, "cache", category="cache_mechanism")
    b = _concept(s, m2, "virtue", category="ethics")

    res = gr.ground_categories(s, "m1")
    assert res["mt"] == "m1"
    assert res["edges_added"] == 1
    # only m1's concept was wired.
    assert set(s.neighbours(a, "genls"))
    assert list(s.neighbours(b, "genls")) == []
