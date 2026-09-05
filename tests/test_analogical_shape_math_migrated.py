"""Gates for `ANALOGICAL_THINKING_SHAPE_MATH_PREREG.md`.

`SHAPE_AUDIT.md` §2.4: `_compute_analogy` treated a string-token overlap as the
verdict at all five orders. These gates pin the four things that changed:

  1. the vocabulary match is ANCHORED at token starts (`io` no longer matches
     `operation`), and anchoring can only ever WITHDRAW a hit;
  2. an abstract-order claim (n >= 2) must be structurally supported — aligned
     evidence or corroboration — or it is withheld, down to an honest `None`;
  3. two pairs realising the SAME held witness corroborate each other (the
     concept-grain reading of the 2x2 parallelogram in
     `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §4);
  4. the `implements` edge asserts structure only when structure was computed.

Plus a source audit: the structural judgement is made by Rust Terms, not by a
Python function's own opinion.

NOTE (analogy-search migration): these gates pin the RETIRED pure-Python
faculty, now `at._legacy_find_analogies` — the shape-math internals
(`_pair_witness`, anchored vocabulary, MAC/FAC withholding) it tests are
retained and unchanged. The public `at.find_analogies` is now the first-class
graph search (`seeds/analogy_search.json`, `domains/analogy_search.py`) per
`SHAPE_AUDIT.md` §2.4; its behaviour is gated separately in
`tests/test_analogy_search_migrated.py`.
"""
from __future__ import annotations

import json
import os
import pathlib

from substrate_rs import _native

import domains.analogical_thinking as at

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
VOCAB = ROOT / "seeds" / "shape_vocabulary.json"


# ---------------------------------------------------------------------------
def _substrate():
    s = _native.Substrate()
    at._CONCEPT_READING_CACHE.clear()
    at._VOCAB_KEYS_CACHE.clear()
    at._METASHAPE_COUNT_CACHE.clear()
    d = json.load(open(VOCAB))
    local = {}
    for n in d["nodes"]:
        local[n["local_id"]] = s.add_node(n["type"], n["attrs"])
    for e in d["edges"]:
        s.add_edge_unchecked(local[e["src"]["local"]], e["type"],
                             local[e["tgt"]["local"]])
    # `emit_analogy_as_graph` writes through the CHECKED `add_edge`, so Γ has to
    # admit `implements` or the edge is refused for a reason unrelated to this
    # rung (the same open-production preamble `test_analogical_relative_ranking`
    # uses).
    for a in ("Concept", "Microtheory", "Analogy"):
        for b in ("Concept", "Microtheory", "Analogy"):
            for et in ("implements", "has_concept"):
                s.add_production({"src": {"type": a, "var": "src"},
                                  "edge_type": et,
                                  "tgt": {"type": b, "var": "tgt"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})
    return s


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, mt, name, definition, category="c"):
    c = s.add_node("Concept", {"name": name, "definition": definition,
                               "category": category})
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


def _pair(results, sc, tc):
    for r in results:
        if r["source_concept"] == sc and r["target_concept"] == tc:
            return r
    return None


# ---------------------------------------------------------------------------
# 1. anchoring
# ---------------------------------------------------------------------------
def test_keyword_matches_at_a_token_start_not_inside_a_word():
    """`io` (FunctionalRole input_output) matched `operat|io|n` — 39.6% of every
    vocabulary hit in the booted graph. It must not."""
    s = _substrate()
    assert "input_output" not in at._vocab_hits(
        s, "FunctionalRole", "an operation on a satisfaction fold")
    assert "gating" not in at._vocab_hits(
        s, "FunctionalRole", "aggregates of skandhas")
    # …while the genuine hits, including STEM keywords, still fire.
    assert "input_output" in at._vocab_hits(s, "FunctionalRole", "the input buffer")
    assert "regulate" in at._vocab_hits(s, "FunctionalRole", "it regulates the flow")
    assert "communicate" in at._vocab_hits(s, "FunctionalRole", "it communicates upstream")


def test_underscore_is_a_word_boundary():
    """snake_case names are the dominant form in this corpus, so `_` must be a
    separator or the anchoring would throw away real hits."""
    s = _substrate()
    assert "hierarchical_abstraction" in at._vocab_hits(
        s, "ShapePrinciple", "typographic_hierarchy")


def test_anchoring_can_only_withdraw_never_add():
    """Anchoring is a strict refinement of the substring test: every anchored
    hit was already a substring hit."""
    s = _substrate()
    texts = ["an operation on a satisfaction fold", "the input buffer",
             "typographic_hierarchy", "aggregates of skandhas",
             "a scheduler with a priority queue", "predicts the next frame"]
    for t in texts:
        for voc in ("FunctionalRole", "ShapePrinciple"):
            anchored = at._vocab_hits(s, voc, t)
            substring = set()
            for n in at._vocab_nodes(s, voc):
                a = n if isinstance(n, int) else n
                attrs = s.node(a)["attrs"]
                if any(str(k) in t.lower() for k in (attrs.get("keywords") or ())):
                    substring.add(attrs.get("name"))
            assert anchored <= substring, (t, voc, anchored - substring)


# ---------------------------------------------------------------------------
# 2. the honest non-answer
# ---------------------------------------------------------------------------
def test_a_spurious_substring_hit_is_no_longer_an_analogy():
    """Two concepts whose ONLY connection was `io` inside a longer word.

    Before: `{order_n: 2, rationale: "shared functional role: input_output"}`.
    After: nothing — there is no analogy here to report."""
    s = _substrate()
    src, tgt = _mt(s, "src"), _mt(s, "tgt")
    _concept(s, src, "satisfaction_fold", "a fold over satisfaction", "one")
    _concept(s, tgt, "operation_primitive", "a primitive operation", "two")
    assert at._legacy_find_analogies(s, "src", ["tgt"], order_n=4) == []


def test_surface_orders_survive_when_the_abstract_claim_is_withheld():
    """Withholding an unsupported n>=2 claim DEMOTES to the surface evidence the
    pair genuinely has; it does not delete a real name/category match.

    Here the role IS genuinely shared (`gating`), but the two concepts are
    evidenced for it in DIFFERENT slots — one in its own name, one buried in
    prose — so the held witness does not fix that axis and the abstraction is
    withheld. The real order-0 name-token match survives."""
    s = _substrate()
    src, tgt = _mt(s, "src"), _mt(s, "tgt")
    _concept(s, src, "alpha gate", "a thing", "one")
    _concept(s, tgt, "alpha widget", "this will gate the flow", "two")
    res = at._legacy_find_analogies(s, "src", ["tgt"], order_n=4)
    r = _pair(res, "alpha gate", "alpha widget")
    assert r is not None
    assert r["order_n"] <= 1, r["rationale"]
    assert "WITHHELD" in r["rationale"]
    assert "shared name tokens" in r["rationale"]


# ---------------------------------------------------------------------------
# 3. structural alignment + the name-slot tier
# ---------------------------------------------------------------------------
def test_evidence_in_the_name_slot_outranks_the_same_evidence_in_prose():
    """`META_SHAPE_FIRST_CLASS_RESULTS.md` §2's load-bearing key, one grain
    over: an item whose SLOT is the shape beats an item that talks about it.
    Both pairs reach the same order with the same feature count; only the slot
    the evidence came from separates them, and the old key could not see it."""
    s = _substrate()
    src, tgt = _mt(s, "src"), _mt(s, "tgt")
    _concept(s, src, "gate_unit", "a component of the machine")
    _concept(s, tgt, "gate_stage", "a stage of the machine")
    _concept(s, src, "widget_one", "this thing will gate the flow")
    _concept(s, tgt, "widget_two", "this other thing will gate the flow")
    res = at._legacy_find_analogies(s, "src", ["tgt"], order_n=2)
    named = _pair(res, "gate_unit", "gate_stage")
    prose = _pair(res, "widget_one", "widget_two")
    assert named is not None and prose is not None
    assert named["order_n"] == prose["order_n"] == 2
    assert named["name_shared"] > 0
    assert prose["name_shared"] == 0
    assert at.RANK_KEY(named) < at.RANK_KEY(prose)


def test_structural_evidence_is_recorded_not_asserted():
    s = _substrate()
    src, tgt = _mt(s, "src"), _mt(s, "tgt")
    _concept(s, src, "gate_unit", "a component")
    _concept(s, tgt, "gate_stage", "a stage")
    r = _pair(at._legacy_find_analogies(s, "src", ["tgt"], order_n=2),
              "gate_unit", "gate_stage")
    assert r["struct_shared"] >= 1
    assert "structurally aligned" in r["rationale"]


# ---------------------------------------------------------------------------
# 4. corroboration — the parallelogram
# ---------------------------------------------------------------------------
def test_pairs_realising_the_same_transform_corroborate_each_other():
    """Four concepts, two source and two target, arranged so both cross pairs
    induce the SAME held witness. Each is then the other's corroborating corner.
    A pair with a transform nothing else realises stays at 0."""
    s = _substrate()
    src, tgt = _mt(s, "src"), _mt(s, "tgt")
    _concept(s, src, "store_a", "it stores the value")
    _concept(s, src, "store_b", "it stores the value")
    _concept(s, tgt, "cache_a", "it caches the value and predicts the next")
    res = at._legacy_find_analogies(s, "src", ["tgt"], order_n=4)
    a = _pair(res, "store_a", "cache_a")
    b = _pair(res, "store_b", "cache_a")
    assert a is not None and b is not None
    assert a["corroboration"] == 1 and b["corroboration"] == 1
    assert "corroborated by 1 pair" in a["rationale"]


def test_corroboration_ranks_within_an_order_never_across_orders():
    """`order_n` stays PRIMARY — that is the previous rung's registered, gated
    result (`test_analogical_relative_ranking.py`) and this rung does not
    relitigate it. Corroboration is the WITHIN-order discriminator."""
    high = {"order_n": 3, "corroboration": 0, "name_shared": 0,
            "struct_shared": 0, "feature_count": 1, "features_total": 1}
    low = {"order_n": 2, "corroboration": 9, "name_shared": 9,
           "struct_shared": 9, "feature_count": 9, "features_total": 9}
    assert at.RANK_KEY(high) < at.RANK_KEY(low)


# ---------------------------------------------------------------------------
# 5. the `implements` edge
# ---------------------------------------------------------------------------
def test_implements_edge_requires_computed_structure_not_an_ordinal():
    """It used to be written on `order_n >= 2` with the comment *"n >= 2
    indicates genuine structural correspondence"* — an ordinal asserting a
    structure nothing had computed (`SHAPE_AUDIT.md` §2.4)."""
    s = _substrate()
    src, tgt = _mt(s, "src"), _mt(s, "tgt")
    a = _concept(s, src, "gate_unit", "a component")
    b = _concept(s, tgt, "gate_stage", "a stage")
    r = _pair(at._legacy_find_analogies(s, "src", ["tgt"], order_n=2),
              "gate_unit", "gate_stage")
    assert at.emit_analogy_as_graph(s, r) is not None
    assert s.has_edge(a, "implements", b)

    # …and an order-2 record carrying NO structural evidence writes no edge.
    s2 = _substrate()
    src2, tgt2 = _mt(s2, "s2"), _mt(s2, "t2")
    c = _concept(s2, src2, "x_one", "nothing in the vocabulary here")
    d = _concept(s2, tgt2, "x_two", "nothing in the vocabulary either")
    forged = {"source_concept": "x_one", "target_concept": "x_two",
              "source_mt": "s2", "target_mt": "t2", "source_node": c,
              "target_node": d, "order_n": 4, "feature_count": 1,
              "features_total": 1, "struct_shared": 0, "name_shared": 0,
              "corroboration": 0, "rationale": "forged"}
    assert at.emit_analogy_as_graph(s2, forged) is not None
    assert not s2.has_edge(c, "implements", d)


# ---------------------------------------------------------------------------
# 6. contract + source audit
# ---------------------------------------------------------------------------
def test_public_contract_is_unchanged():
    s = _substrate()
    src, tgt = _mt(s, "src"), _mt(s, "tgt")
    _concept(s, src, "gate_unit", "a component")
    _concept(s, tgt, "gate_stage", "a stage")
    r = at._legacy_find_analogies(s, "src", ["tgt"], order_n=2)[0]
    for k in ("source_concept", "target_concept", "source_mt", "target_mt",
              "source_node", "target_node", "order_n", "feature_count",
              "features_total", "rationale"):
        assert k in r, k
    assert "score" not in r
    assert not any(k.startswith("_") for k in r), sorted(r)


def test_the_structural_judgement_is_made_by_held_terms():
    """No Python function decides structural similarity by its own judgement:
    the meet, the fixed-leaf count and the cover are all Rust Terms."""
    src = pathlib.Path(at.__file__).read_text()
    for term in ('"AntiUnifyWitness"', '"FixedCount"', '"Covers"',
                 '"StringIndexOf"'):
        assert term in src, term
    # the old unanchored predicate is gone
    assert '"Gte"' not in src
