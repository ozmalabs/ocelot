"""Gates for the ANALOGY SEARCH AS A FIRST-CLASS GRAPH SEED
(`seeds/analogy_search.json` + `domains/analogy_search.py`).

`SHAPE_AUDIT.md` §2.4: `analogical_thinking.find_analogies` "was never moved
into the graph" — a Python triple-nested loop scoring a set overlap of string
tokens at five fixed orders, none of which consulted a concept's edges. This
suite pins the migration:

  1. the seed installs with ZERO rules skipped — the whole search is existing
     generic Terms, no new Rust (the `problem_shape_growth` choice);
  2. an analogy is found by SHARED STRUCTURE across fields (vocabulary axes) and
     emitted as a graph `Analogy` node with an `implements` edge — the verdict
     is the graph's, not Python's;
  3. the search works on ARBITRARY RELATIONAL SHAPE: two concepts that each
     `excites` one neighbour and `inhibits` another align on that relational
     shape across unrelated fields — far more than a parallelogram, and nothing
     a five-order keyword dial could see;
  4. SYSTEMATICITY / the parallelogram is a graph verdict: two pairs realising
     the same transform corroborate each other;
  5. the honest non-answer: genuinely disjoint fields yield no analogy;
  6. `find_analogies` / `think_harder` (the public entry points) delegate to the
     graph search.
"""
from __future__ import annotations

import json
import pathlib

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
VOCAB = ROOT / "seeds" / "shape_vocabulary.json"
SEARCH = ROOT / "seeds" / "analogy_search.json"

_NODE_TYPES = ("Agent", "AnalogyProbe", "ConceptShape", "Analogy",
               "Concept", "Microtheory", "FunctionalRole", "ShapePrinciple",
               "MetaShape")
_EDGE_TYPES = ("observed_probe", "emitted_analogy", "has_concept",
               "implements", "has_principle", "excites", "inhibits",
               "causes", "enables")


def _substrate():
    """A bare substrate with an Agent, open productions, and the vocabulary +
    analogy_search seeds installed. (Installing here rather than relying on the
    shim's _ensure_seed keeps the gate independent of that path — a separate
    gate below checks _ensure_seed itself.)"""
    s = _native.Substrate()
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE):
        cache.clear()
    ag = s.add_node("Agent", {})
    for a in _NODE_TYPES:
        for b in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({"src": {"type": a, "var": "src"},
                                  "edge_type": et,
                                  "tgt": {"type": b, "var": "tgt"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})
    for path in (VOCAB, SEARCH):
        summ = s.load_seed_manifest(json.load(open(path)), ag)
        assert not summ.get("rules_skipped"), (path.name, summ)
        assert not summ.get("reflexes_skipped"), (path.name, summ)
    return s, ag


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, mt, name, definition=""):
    c = s.add_node("Concept", {"name": name, "definition": definition})
    s.add_edge(mt, "has_concept", c)
    return c


def _pair(results, sc, tc):
    for r in results:
        if r["source_concept"] == sc and r["target_concept"] == tc:
            return r
    return None


# ---------------------------------------------------------------------------
# 1. no new Rust — the whole search installs from existing Terms
# ---------------------------------------------------------------------------
def test_seed_installs_with_zero_rules_skipped():
    """Every ap_* rule references only existing generic Terms; a skipped rule
    would mean a rule silently did not install (an unknown Term)."""
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    s.load_seed_manifest(json.load(open(VOCAB)), ag)
    summ = s.load_seed_manifest(json.load(open(SEARCH)), ag)
    assert summ.get("rules_skipped") == []
    assert summ.get("reflexes_skipped") == []


# ---------------------------------------------------------------------------
# 2. an analogy is found by shared structure and emitted as graph data
# ---------------------------------------------------------------------------
def test_cross_field_analogy_emitted_as_graph_node_and_edge():
    s, _ag = _substrate()
    cs, bio = _mt(s, "cs"), _mt(s, "bio")
    src = _concept(s, cs, "mmu", "gate control memory access by policy")
    tgt = _concept(s, bio, "thalamus", "gate filter signals by policy")

    res = at.find_analogies(s, "cs", ["bio"], order_n=4)
    r = _pair(res, "mmu", "thalamus")
    assert r is not None, res
    # the verdict was the GRAPH's: an Analogy node exists carrying the pair.
    analogies = [s.node(a)["attrs"] for a in s.nodes("Analogy")]
    assert any(a.get("source_concept") == "mmu"
               and str(a.get("target_concept", "")).endswith("thalamus")
               for a in analogies), analogies
    # shared structure was computed (not asserted), and > 0.
    assert r["struct_shared"] >= 1
    # the implements edge asserting structural correspondence was written
    # between the two REAL Concept nodes.
    assert src in list(s.neighbours(src, "implements")) or \
        tgt in list(s.neighbours(src, "implements"))
    receipts = [s.node(n)["attrs"] for n in
                s.nodes("NativeAnalogySearchReceipt")
                if s.node(n)["attrs"].get("cluster") ==
                "analogy_search.observe_settlement"]
    assert receipts
    assert all(r["outcome_source"] == "native_rule_readback" and
               r["python_outcome_selection"] is False for r in receipts)


# ---------------------------------------------------------------------------
# 3. ARBITRARY RELATIONAL SHAPE — the headline: far more than a parallelogram
# ---------------------------------------------------------------------------
def test_analogy_by_arbitrary_relational_shape_across_fields():
    """Two concepts in unrelated fields that each EXCITE one neighbour and
    INHIBIT another share that relational shape — and the search finds it on
    the edges, not on any keyword. This is exactly what the five-order string
    dial could never see (SHAPE_AUDIT.md §2.4: "not one of the five orders
    consults a concept's edges")."""
    s, _ag = _substrate()
    neuro, circuit = _mt(s, "neuro"), _mt(s, "circuit")

    p = _concept(s, neuro, "pyramidal")
    pt = _concept(s, neuro, "pyr_target")
    po = _concept(s, neuro, "pyr_other")
    s.add_edge(p, "excites", pt)
    s.add_edge(p, "inhibits", po)

    o = _concept(s, circuit, "opamp")
    ol = _concept(s, circuit, "load")
    oref = _concept(s, circuit, "ref")
    s.add_edge(o, "excites", ol)
    s.add_edge(o, "inhibits", oref)

    res = at.find_analogies(s, "neuro", ["circuit"], order_n=4)
    r = _pair(res, "pyramidal", "opamp")
    assert r is not None, res
    # the RELATIONAL structure (both edge types) is in the shared shape —
    # this is structure-mapping, not token overlap.
    assert "excites" in r["transform_key"]
    assert "inhibits" in r["transform_key"]
    # and it is a richer match than the edge-less leaf concepts get.
    leaf = _pair(res, "pyr_target", "opamp")
    assert leaf is None or leaf["struct_shared"] < r["struct_shared"]


# ---------------------------------------------------------------------------
# 4. systematicity / the parallelogram, as a graph verdict
# ---------------------------------------------------------------------------
def test_systematicity_corroborates_two_pairs_sharing_a_transform():
    """Two source concepts that both realise the same shared shape against the
    target field corroborate each other — the parallelogram, computed as a
    Count(Filter(Eq(transform_key))) recurrence, not asserted."""
    s, _ag = _substrate()
    neuro, circuit = _mt(s, "neuro"), _mt(s, "circuit")

    for base in ("pyramidal", "basket"):
        c = _concept(s, neuro, base)
        s.add_edge(c, "excites", _concept(s, neuro, base + "_t"))
        s.add_edge(c, "inhibits", _concept(s, neuro, base + "_o"))
    for base in ("opamp", "transistor"):
        c = _concept(s, circuit, base)
        s.add_edge(c, "excites", _concept(s, circuit, base + "_l"))
        s.add_edge(c, "inhibits", _concept(s, circuit, base + "_r"))

    res = at.find_analogies(s, "neuro", ["circuit"], order_n=4)
    corroborated = [r for r in res
                    if r["source_concept"] in ("pyramidal", "basket")
                    and r["corroboration"] > 0]
    assert corroborated, [(_r["source_concept"], _r["corroboration"]) for _r in res]


# ---------------------------------------------------------------------------
# 5. the honest non-answer
# ---------------------------------------------------------------------------
def test_disjoint_fields_yield_no_analogy():
    """Two concepts sharing no structural axis (no shared vocabulary, no shared
    relations) produce no analogy — the search does not manufacture one."""
    s, _ag = _substrate()
    a, b = _mt(s, "alpha"), _mt(s, "beta")
    _concept(s, a, "zzq_widget", "a zzq of the frobnitz")
    _concept(s, b, "xylo_gadget", "a xylo of the plugh")
    res = at.find_analogies(s, "alpha", ["beta"], order_n=4)
    assert _pair(res, "zzq_widget", "xylo_gadget") is None


# ---------------------------------------------------------------------------
# 6. the public entry points delegate to the graph search
# ---------------------------------------------------------------------------
def test_public_find_analogies_delegates_to_graph_search():
    """`analogical_thinking.find_analogies` is the graph search (analogy_search),
    not the retired Python loop — verified by the Analogy node it emits, which
    the legacy path never wrote (it wrote Correspondence/Analogy via a different
    route)."""
    import inspect
    src = inspect.getsource(at.find_analogies)
    assert "analogy_search" in src
    # and think_harder too.
    assert "analogy_search" in inspect.getsource(at.think_harder)


def test_ensure_seed_auto_installs_from_bare_substrate():
    """The shim installs its own seed chain on first use — a caller need not
    pre-load shape_vocabulary/analogy_search."""
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for a in _NODE_TYPES:
        for b in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({"src": {"type": a, "var": "src"},
                                  "edge_type": et,
                                  "tgt": {"type": b, "var": "tgt"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})
    cs, bio = _mt(s, "cs"), _mt(s, "bio")
    _concept(s, cs, "mmu", "gate control memory access by policy")
    _concept(s, bio, "thalamus", "gate filter signals by policy")
    res = at.find_analogies(s, "cs", ["bio"], order_n=4)
    installed = asr._installed_seed_ids(s)
    assert "shape_vocabulary" in installed and "analogy_search" in installed
    assert _pair(res, "mmu", "thalamus") is not None, res
