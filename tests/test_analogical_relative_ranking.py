"""Relative-ranking gate for analogical_thinking + the god_object smell.

Two absolute-scalar intrusions were made RELATIVE:

  1. `domains/analogical_thinking.py` baked a FIXED cross-order exchange rate
     (category +2, def-overlap +1, functional-role x3, principle x4,
     meta-shape x5) summed into an absolute `score`. That is gone. Analogies
     now rank by POSITION on the abstraction axis — `order_n`, the highest
     order at which the pair matches — with the COUNT of shared features at
     that order (`feature_count`) as the within-axis tiebreaker.

  2. `seeds/architecture_assessment.json` god_object used an absolute
     `"threshold": 8`. It is now a RELATIVE outlier test: a node is flagged
     when its edge-type diversity is a positive outlier in the graph's own
     distribution (> mean + k*std) — so the same count is flagged in a sparse
     graph and not in a dense one.
"""
from __future__ import annotations

import pathlib

from substrate_rs import _native

import domains.analogical_thinking as at
from domains.architecture_assessment import detect_god_object


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
_NODE_TYPES = ("Microtheory", "Concept", "Analogy", "N")
_EDGE_TYPES = (
    "has_concept", "implements",
    # the god_object diversity vocabulary + a couple of fillers
    "has_reflex", "owns_microtheory", "owns_root", "uses_pattern",
    "authored_in", "current_target", "has_draft", "validated_by",
    "installed_as", "genlMt", "lexicon",
)


def _substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, mt, name, category, definition):
    c = s.add_node("Concept", {"name": name, "category": category,
                               "definition": definition})
    s.add_edge(mt, "has_concept", c)
    return c


def _build_concept_graph():
    """Three source concepts / three target concepts arranged so that one pair
    matches at order 1 (shared category), and two pairs match only at order 0
    (shared name tokens) with different feature counts."""
    s = _substrate()
    src = _mt(s, "src")
    tgt = _mt(s, "tgt")

    # order-1 pair: same category 'storage', no shared name token, no def overlap
    _concept(s, src, "reservoir", "storage", "holds water")
    _concept(s, tgt, "warehouse", "storage", "keeps goods")

    # order-0 pair, 2 shared name tokens (alpha, beta), categories differ
    _concept(s, src, "alpha beta core", "engine", "spins fast")
    _concept(s, tgt, "alpha beta unit", "motor", "runs hot")

    # order-0 pair, 1 shared name token (alpha), categories differ
    _concept(s, src, "alpha delta", "turbine", "turns slow")
    _concept(s, tgt, "alpha zeta", "rotor", "cold spin")
    return s


_RANK_KEY = lambda a: (-a["order_n"], -a["feature_count"], -a["features_total"])


def _pair(results, sc, tc):
    for r in results:
        if r["source_concept"] == sc and r["target_concept"] == tc:
            return r
    raise AssertionError(f"pair ({sc!r},{tc!r}) not found in {[(r['source_concept'], r['target_concept']) for r in results]}")


# ---------------------------------------------------------------------------
# FIX #1 — relative analogy ranking
# ---------------------------------------------------------------------------
def test_no_fixed_cross_order_multipliers_in_source():
    """The hand-set exchange rate (x3 role, x4 principle, x5 meta-shape,
    +2 category) must be GONE from the scoring."""
    src = pathlib.Path(at.__file__).read_text()
    for forbidden in ("len(shared_roles) * 3", "len(shared_p) * 4",
                      "len(shared_m) * 5", "score += 2", "score += 1",
                      '"score"'):
        assert forbidden not in src, forbidden


def test_analogy_stores_position_and_feature_count_not_score():
    s = _build_concept_graph()
    results = at.find_analogies(s, "src", ["tgt"], order_n=1)
    a = _pair(results, "reservoir", "warehouse")
    # relative fields present; absolute score field gone.
    assert set(("order_n", "feature_count", "features_total")) <= set(a)
    assert "score" not in a
    node = at.emit_analogy_as_graph(s, a)
    attrs = s.node(node)["attrs"]
    assert attrs["order_n"] == 1
    assert attrs["feature_count"] == 1
    assert "score" not in attrs


def test_higher_order_match_outranks_lower_order_even_with_fewer_features():
    """A pair that matches at a HIGHER order ranks above one that matches at a
    lower order — even when the lower-order pair shares MORE features. Position
    on the abstraction axis is primary; feature count is only the tiebreaker."""
    s = _build_concept_graph()
    results = at.find_analogies(s, "src", ["tgt"], order_n=1)

    high = _pair(results, "reservoir", "warehouse")          # order 1
    low_many = _pair(results, "alpha beta core", "alpha beta unit")  # order 0, 2 feats
    low_few = _pair(results, "alpha delta", "alpha zeta")    # order 0, 1 feat

    assert high["order_n"] == 1
    assert low_many["order_n"] == 0 and low_many["feature_count"] == 2
    assert low_few["order_n"] == 0 and low_few["feature_count"] == 1

    ranked = sorted(results, key=_RANK_KEY)
    # the order-1 pair wins outright, despite the order-0 pair sharing 2 tokens
    assert (ranked[0]["source_concept"], ranked[0]["target_concept"]) == \
        ("reservoir", "warehouse")
    # same-order pairs order by feature count: 2 tokens before 1 token
    assert ranked.index(low_many) < ranked.index(low_few)


def test_same_order_ranks_by_feature_count():
    s = _build_concept_graph()
    results = at.find_analogies(s, "src", ["tgt"], order_n=0)  # dial = names only
    low_many = _pair(results, "alpha beta core", "alpha beta unit")
    low_few = _pair(results, "alpha delta", "alpha zeta")
    assert low_many["order_n"] == low_few["order_n"] == 0
    assert low_many["feature_count"] > low_few["feature_count"]
    ranked = sorted(results, key=_RANK_KEY)
    assert ranked.index(low_many) < ranked.index(low_few)


# ---------------------------------------------------------------------------
# FIX #2 — god_object is a relative outlier, not an absolute count
# ---------------------------------------------------------------------------
def _hub(s, n_edge_types):
    """A node emitting `n_edge_types` distinct outgoing edge types. All edges
    point at ONE shared sink so a hub adds a single low-diversity node, not a
    fresh leaf per edge type (which would swamp the distribution with zeros)."""
    node = s.add_node("N", {})
    sink = s.add_node("N", {})
    types = ("has_reflex", "owns_microtheory", "owns_root", "uses_pattern",
             "authored_in", "current_target", "has_draft", "validated_by",
             "installed_as", "genlMt", "lexicon")
    for et in types[:n_edge_types]:
        s.add_edge(node, et, sink)
    return node


def test_same_count_flagged_or_not_depending_on_distribution():
    """A node with diversity 5 IS a god-object when its peers are sparse, and
    is NOT one when its peers are equally diverse — the SAME absolute count,
    opposite verdict, because the test is relative to the distribution."""
    spec = {"outlier_k": 2.0}

    # sparse graph: subject stands alone at diversity 5, everyone else ~0.
    s_sparse = _substrate()
    subject = _hub(s_sparse, 5)
    for _ in range(20):
        s_sparse.add_node("N", {})
    flagged = detect_god_object(s_sparse, subject, spec)
    assert any(f"node #{subject}" == inst["location"] for inst in flagged), \
        "diversity 5 should be an outlier among sparse peers"

    # dense graph: many peers ALSO at diversity 5 → subject is unremarkable.
    s_dense = _substrate()
    subject2 = _hub(s_dense, 5)
    for _ in range(12):
        _hub(s_dense, 5)
    flagged2 = detect_god_object(s_dense, subject2, spec)
    assert not any(f"node #{subject2}" == inst["location"] for inst in flagged2), \
        "diversity 5 should NOT be flagged when peers are equally diverse"


def test_god_object_rationale_reports_relative_position():
    spec = {"outlier_k": 2.0}
    s = _substrate()
    subject = _hub(s, 6)
    for _ in range(20):
        s.add_node("N", {})
    flagged = detect_god_object(s, subject, spec)
    assert flagged
    assert "outlier" in flagged[0]["rationale"]
    assert "mean" in flagged[0]["rationale"]
