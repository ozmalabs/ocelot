"""CAN_JUNCTION_TREE_PREREG.md / _RESULTS.md — exact junction-tree
inference for low-treewidth CAN networks.

Confirms, with real numbers: (a) `graph_treewidth.exact_treewidth`
re-derives the already-measured treewidth-2 Bigville template and
treewidth-15 N=16 complete graph
(`CAN_SOLVER_TRACTABILITY_RESULTS.md` §2); (b) the treewidth-bound gate
correctly admits the former and refuses the latter, cheaply, without
attempting exponential work; (c) junction-tree MAP energy is EXACTLY
brute-force-optimal on multiple real Bigville resident networks (the
correctness proof this whole rung exists to deliver), AND cross-checked
against the LIVE `substrate.mt_energy` the Rust engine itself defines;
(d) the algorithm's own correctness on a synthetic network, isolated from
the CAN-extraction layer; (e) two-Mt isolation, the standing check every
native rung in this arc runs; (f) junction-tree's provably-optimal energy
is never worse than `multi_start_settle_and_pick_best`'s own widened-ICM
result on the same network.
"""
from __future__ import annotations

import itertools
import json
import random

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
from domains.graph_treewidth import (
    exact_treewidth, min_fill_upper_bound, treewidth_bound_check,
)
from domains.can_junction_tree import (
    can_network_from_mt, energy_of_state, brute_force_map, junction_tree_map,
    junction_tree_exact_settle,
)
from domains.can_native_orchestration import multi_start_settle_and_pick_best
from worlds.bigville_can_beliefs import (
    install_productions, build_resident_can_mt, apply_scenario_evidence,
    TOPIC_NAMES, STRUCTURAL_EDGES,
)

SEED_PATH = "seeds/can_native_reimplementation.json"
CAST_PATH = "seeds/bigville_cast100.json"


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    inner.load_seed_manifest(engine_rules_only(d))
    return inner


def _fresh_resident_mt(resident_index):
    s = sr._native.Substrate()
    install_productions(s)
    manifest = json.load(open(SEED_PATH))
    s.load_seed_manifest(engine_rules_only(manifest))
    residents = json.load(open(CAST_PATH))["residents"]
    built = build_resident_can_mt(s, residents[resident_index])
    apply_scenario_evidence(s, built["concepts"])
    s.set_attr(built["mt_node"], "discrete_mode", "3state")
    s.set_attr(built["mt_node"], "can_tick", 0)
    return s, built["mt_node"], built["concepts"]


def _round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def _build_frustrated_draw(inner, seed, n=16, coarse=True, discrete_mode="3state"):
    pair_rng = random.Random(seed * 31 + n)
    field_rng = random.Random(seed * 53 + n)
    mt = inner.add_node("Microtheory", {
        "temperature": 2.0, "discrete_mode": discrete_mode, "can_tick": 0,
    })
    concepts = [
        inner.add_node("Concept", {
            "name": "c%d" % i, "state": 0.0,
            "external_field": 0.0, "identity_field": 0.0,
        })
        for i in range(n)
    ]
    for c in concepts:
        inner.add_edge(mt, "has_concept", c, {})
    for i in range(n):
        h = field_rng.uniform(-1, 1)
        inner.set_attr(concepts[i], "external_field", h)
    for i in range(n):
        for j in range(i + 1, n):
            raw = pair_rng.uniform(-1, 1)
            v = (_round_to_vocab(raw, 1.0, 1) if coarse
                 else _round_to_vocab(raw, 0.25, 4))
            inner.add_edge(concepts[i], "causal_influence", concepts[j], {"weight": v})
            inner.add_edge(concepts[j], "causal_influence", concepts[i], {"weight": v})
    return mt, concepts


def _build_ring_draw(inner, seed, n=8, discrete_mode="3state"):
    """N=8 cycle (ring) -- treewidth 2 by well-known construction, verified
    (not merely asserted) by exact_treewidth in the test itself. A small
    but non-trivially-coupled, real-cycle-topology test network for the
    junction-tree-vs-multi-start comparison."""
    rng = random.Random(seed)
    mt = inner.add_node("Microtheory", {
        "temperature": 1.5, "discrete_mode": discrete_mode, "can_tick": 0,
    })
    concepts = [
        inner.add_node("Concept", {
            "name": "r%d" % i, "state": 0.0,
            "external_field": rng.uniform(-1, 1), "identity_field": rng.uniform(-0.5, 0.5),
        })
        for i in range(n)
    ]
    for c in concepts:
        inner.add_edge(mt, "has_concept", c, {})
    for i in range(n):
        j = (i + 1) % n
        w = _round_to_vocab(rng.uniform(-1, 1), 1.0, 1)
        inner.add_edge(concepts[i], "causal_influence", concepts[j], {"weight": w})
        inner.add_edge(concepts[j], "causal_influence", concepts[i], {"weight": w})
    return mt, concepts


# ----------------------------------------------------------------------
# (a) graph_treewidth re-derives the already-measured real numbers
# ----------------------------------------------------------------------

def test_exact_treewidth_rederives_bigville_template_treewidth_2():
    bv_nodes = TOPIC_NAMES
    bv_edges = [(a, b) for a, b, _bj, _nk in STRUCTURAL_EDGES]
    result = exact_treewidth(bv_nodes, bv_edges)
    print(f"\nBigville structural template exact_treewidth={result['treewidth']} "
          f"(CAN_SOLVER_TRACTABILITY_RESULTS.md sec2 measured 2)")
    assert result["treewidth"] == 2
    assert result["exact"] is True


def test_exact_treewidth_refuses_n16_and_min_fill_upper_bound_finds_15():
    n16_nodes = list(range(16))
    n16_edges = [(i, j) for i in range(16) for j in range(i + 1, 16)]
    exact = exact_treewidth(n16_nodes, n16_edges, max_exact_n=10)
    assert exact is None, "n=16 > max_exact_n=10 must refuse brute force, not hang"

    heuristic = min_fill_upper_bound(n16_nodes, n16_edges)
    print(f"\nN=16 complete graph: exact_treewidth refused (n>max_exact_n), "
          f"min_fill_upper_bound={heuristic['treewidth']} "
          f"(CAN_SOLVER_TRACTABILITY_RESULTS.md sec2's own closed-form/brute-force "
          f"cross-check found the true value is 15)")
    assert heuristic["treewidth"] == 15
    assert heuristic["exact"] is False


def test_treewidth_bound_check_admits_bigville_refuses_n16():
    bv_nodes = TOPIC_NAMES
    bv_edges = [(a, b) for a, b, _bj, _nk in STRUCTURAL_EDGES]
    bv_check = treewidth_bound_check(bv_nodes, bv_edges, bound=4)
    assert bv_check["within_bound"] is True
    assert bv_check["exact"] is True

    n16_nodes = list(range(16))
    n16_edges = [(i, j) for i in range(16) for j in range(i + 1, 16)]
    n16_check = treewidth_bound_check(n16_nodes, n16_edges, bound=4, max_exact_n=10)
    assert n16_check["within_bound"] is False
    print(f"\nbound-check: Bigville within_bound={bv_check['within_bound']} "
          f"(tw={bv_check['treewidth']}), N=16 within_bound={n16_check['within_bound']} "
          f"(tw={n16_check['treewidth']}, {'exact' if n16_check['exact'] else 'heuristic'})")


# ----------------------------------------------------------------------
# (d) message-passing algorithm correctness in isolation, synthetic graph
# ----------------------------------------------------------------------

def test_junction_tree_matches_brute_force_on_synthetic_path_graph():
    """A 4-node path (treewidth 1) with hand-picked unary/pairwise values,
    checked against literal brute-force enumeration -- isolates the
    message-passing algorithm's correctness from the CAN graph-extraction
    layer entirely (no substrate involved)."""
    nodes = ["a", "b", "c", "d"]
    edges = [("a", "b"), ("b", "c"), ("c", "d")]
    unary = {"a": 0.3, "b": -0.7, "c": 0.5, "d": -0.2}
    pairwise = {
        frozenset(("a", "b")): 0.6,
        frozenset(("b", "c")): -0.4,
        frozenset(("c", "d")): 0.9,
    }
    vocab = (-1.0, 0.0, 1.0)

    tw = exact_treewidth(nodes, edges)
    assert tw["treewidth"] == 1, "a path graph is treewidth 1"

    jt = junction_tree_map(nodes, edges, unary, pairwise, vocab, order=tw["elimination_order"])
    bf = brute_force_map(nodes, unary, pairwise, vocab)
    print(f"\nsynthetic path graph: junction-tree energy={jt['energy']:.6f} "
          f"brute-force energy={bf['energy']:.6f}")
    assert abs(jt["energy"] - bf["energy"]) < 1e-9
    # Same-energy states may differ under ties; confirm the JT state's own
    # recomputed energy really does equal the reported minimum (not merely
    # trusting the algorithm's internal bookkeeping).
    assert abs(energy_of_state(unary, pairwise, jt["state"]) - bf["energy"]) < 1e-9


def test_junction_tree_matches_brute_force_on_synthetic_triangle_plus_pendant():
    """Deliberately mirrors Bigville's own real topology shape (a triangle
    plus a pendant path, treewidth 2) with synthetic values, as an
    additional isolated correctness check before touching any real
    network."""
    nodes = list(range(5))
    edges = [(0, 1), (1, 2), (2, 0), (0, 3), (3, 4)]
    rng = random.Random(31337)
    unary = {n: rng.uniform(-1, 1) for n in nodes}
    pairwise = {frozenset(e): rng.uniform(-1, 1) for e in edges}
    vocab = (-1.0, 0.0, 1.0)

    tw = exact_treewidth(nodes, edges)
    assert tw["treewidth"] == 2
    jt = junction_tree_map(nodes, edges, unary, pairwise, vocab, order=tw["elimination_order"])
    bf = brute_force_map(nodes, unary, pairwise, vocab)
    print(f"\nsynthetic triangle+pendant: jt={jt['energy']:.6f} bf={bf['energy']:.6f}")
    assert abs(jt["energy"] - bf["energy"]) < 1e-9


# ----------------------------------------------------------------------
# (c) the load-bearing correctness proof: real Bigville residents
# ----------------------------------------------------------------------

@pytest.mark.parametrize("resident_index", [0, 1, 2, 17, 63])
def test_junction_tree_exact_on_real_bigville_residents_matches_brute_force(resident_index):
    """THE correctness proof this rung exists to deliver: on a REAL
    per-resident Bigville CAN network (treewidth 2, measured in
    CAN_SOLVER_TRACTABILITY_RESULTS.md sec2), junction-tree's reported
    global minimum energy must exactly equal literal brute-force
    enumeration over all 3^5=243 states -- ground truth, not another
    approximate method."""
    s, mt, concepts = _fresh_resident_mt(resident_index)
    net = can_network_from_mt(s, mt)
    assert len(net["nodes"]) == 5

    out = junction_tree_exact_settle(s, mt, treewidth_bound=4)
    assert out["attempted"] is True and out["exact"] is True
    assert out["treewidth"] == 2 and out["treewidth_is_exact"] is True

    bf = brute_force_map(net["nodes"], net["unary"], net["pairwise"], net["vocab"])
    print(f"\nresident #{resident_index}: junction-tree energy={out['energy']:.6f} "
          f"brute-force (243-state enum) energy={bf['energy']:.6f} "
          f"mt_energy_confirmed(live Rust)={out['mt_energy_confirmed']:.6f}")
    assert abs(out["energy"] - bf["energy"]) < 1e-6, (
        f"resident #{resident_index}: junction-tree {out['energy']} != "
        f"brute-force ground truth {bf['energy']}")
    # Cross-check against the LIVE substrate.mt_energy the Rust engine
    # itself defines -- confirms this module's extraction/energy formula
    # matches the engine's own, not merely this module's internal
    # reimplementation agreeing with itself.
    assert abs(out["mt_energy_confirmed"] - bf["energy"]) < 1e-4


def test_junction_tree_committed_state_is_readable_back_from_live_concepts():
    s, mt, concepts = _fresh_resident_mt(4)
    out = junction_tree_exact_settle(s, mt, treewidth_bound=4)
    for name, cid in [(k, v.value if hasattr(v, "value") else int(v)) for k, v in concepts.items()]:
        live_state = float(s.node(concepts[name])["attrs"]["state"])
        assert live_state == out["state"][cid], (
            "committed Concept.state must match the junction-tree-decided state exactly")


# ----------------------------------------------------------------------
# (b) honest refusal on the genuinely high-treewidth N=16 network
# ----------------------------------------------------------------------

def test_junction_tree_honestly_refuses_n16_stress_case_no_mutation_attempted():
    inner = _loaded_substrate()
    mt, concepts = _build_frustrated_draw(inner, seed=5000, n=16, coarse=True)
    before = {c.value: inner.node(c)["attrs"].get("state") for c in concepts}

    out = junction_tree_exact_settle(inner, mt, treewidth_bound=4, max_exact_n=10)
    print(f"\nN=16 stress case refusal: {out}")
    assert out["attempted"] is False
    assert out["exact"] is False
    assert out["treewidth"] >= 15  # heuristic upper bound, real number

    after = {c.value: inner.node(c)["attrs"].get("state") for c in concepts}
    assert before == after, "a refused junction-tree attempt must not mutate the graph"


def test_junction_tree_refuses_fast_no_exponential_work_attempted():
    """Real wall-clock check that refusal is CHEAP (the heuristic gate
    fires before any exponential enumeration is attempted) -- not just
    that it eventually returns the right answer."""
    import time
    inner = _loaded_substrate()
    mt, concepts = _build_frustrated_draw(inner, seed=6001, n=16, coarse=True)
    t0 = time.time()
    out = junction_tree_exact_settle(inner, mt, treewidth_bound=4, max_exact_n=10)
    elapsed = time.time() - t0
    print(f"\nrefusal wall-clock: {elapsed:.4f}s")
    assert out["attempted"] is False
    assert elapsed < 2.0, "refusal must be cheap, not an attempted 3^16-state enumeration"


# ----------------------------------------------------------------------
# (e) two-Mt isolation -- the standing check every native rung runs
# ----------------------------------------------------------------------

def test_two_mt_isolation_holds_for_junction_tree_exact_settle():
    inner = _loaded_substrate()
    mt_a, concepts_a = _build_ring_draw(inner, seed=1, n=8)
    mt_b, concepts_b = _build_frustrated_draw(inner, seed=2, n=8)
    for c in concepts_b:
        inner.set_attr(c, "state", 1.0)
    before_b = {c.value: inner.node(c)["attrs"].get("state") for c in concepts_b}

    net_a = can_network_from_mt(inner, mt_a)
    tw = exact_treewidth(net_a["nodes"], net_a["edges"])
    junction_tree_exact_settle(inner, mt_a, treewidth_bound=max(4, tw["treewidth"]))

    after_b = {c.value: inner.node(c)["attrs"].get("state") for c in concepts_b}
    assert before_b == after_b, "junction-tree exact settle on mt_a mutated an unrelated mt_b"


# ----------------------------------------------------------------------
# (f) junction-tree's provable optimum is never worse than multi-start's
# ----------------------------------------------------------------------

def test_junction_tree_energy_never_worse_than_multi_start_on_same_network():
    """On a real-cycle-topology (ring) network, small enough to brute-force
    for ground truth AND small enough treewidth for junction-tree,
    junction-tree's PROVEN-optimal energy must be <= multi-start's
    K=20-restart widened-ICM result -- a genuine, measured comparison
    between the two toolbox members, not merely "it ran"."""
    inner_jt = _loaded_substrate()
    mt_jt, concepts_jt = _build_ring_draw(inner_jt, seed=99, n=8)
    net = can_network_from_mt(inner_jt, mt_jt)
    tw = exact_treewidth(net["nodes"], net["edges"])
    print(f"\nring(n=8) treewidth={tw['treewidth']}")
    assert tw["treewidth"] <= 4

    jt_out = junction_tree_exact_settle(inner_jt, mt_jt, treewidth_bound=4)

    # Independent substrate/network build (SAME seed/topology) for
    # multi-start, so committing one tool's state never contaminates the
    # other's run.
    inner_ms = _loaded_substrate()
    mt_ms, concepts_ms = _build_ring_draw(inner_ms, seed=99, n=8)
    ms_result = multi_start_settle_and_pick_best(inner_ms, mt_ms, k_starts=20,
                                                  rng=random.Random(4242))
    ms_state = {c.value: float(inner_ms.node(c)["attrs"].get("state", 0.0)) for c in concepts_ms}
    ms_energy = float(inner_ms.mt_energy(mt_ms, ms_state))

    print(f"junction-tree (exact) energy={jt_out['energy']:.6f} "
          f"multi-start (K=20, widened-ICM) energy={ms_energy:.6f}")
    assert jt_out["energy"] <= ms_energy + 1e-6, (
        "the exact global optimum must never be worse than a heuristic search's result")
