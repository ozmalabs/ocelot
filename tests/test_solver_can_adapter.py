"""Live demonstration + regression for `domains/solver_dispatch.
grow_can_network_from_text`/`ensure_can_native_engine_loaded` -- the fourth
NL-adapter rung in the solver-dispatch arc (docs/research/engine_substrate/
SOLVER_CAN_ADAPTER_PREREG.md/_RESULTS.md).

Unlike the prior three `_from_text` rungs, this one does NOT mint a
solve_* Goal itself -- it grows real `causal_influence` EDGE structure on
an already-built CAN Microtheory (`worlds.bigville_can_beliefs.
build_resident_can_mt`, UNCHANGED) from real declarative sentences, via
`seeds/can_native_reimplementation.json`'s Hebbian mint-on-recurrence
mechanism (UNCHANGED). The grown network is then dispatched through the
UNCHANGED `solve_can_relax`/`solve_can_exact`/`solve_can_bp` resolvers,
exactly as any hand-built network already would be.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402
from domains import solver_dispatch as sd                  # noqa: E402
from domains import can_junction_tree as cjt                # noqa: E402
from worlds import bigville_can_beliefs as bcb              # noqa: E402


# --------------------------------------------------------------------------- #
#  FIXTURES
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    bcb.install_productions(a.inner)
    return a


def _pump(adapter, goal, max_iters: int = 32) -> None:
    for _ in range(max_iters):
        adapter.fire_reflexes()
        adapter.inner.run_rules()
        if adapter.s.node(goal)["attrs"].get("status") in ("resolved", "walled"):
            return


def _built_mt(agent, index: int):
    """A fresh real Bigville resident CAN network (own Concept nodes each
    call -- `build_resident_can_mt`'s own per-resident-node design, matching
    `tests/test_solver_dispatch_migrated.py::_resident_mt`'s precedent) with
    scenario evidence applied and a first settle+baseline-growth tick
    already run, mirroring PREREG Sec6's own step 1."""
    residents = json.load(open(os.path.join(ROOT, "seeds", "bigville_cast100.json")))["residents"]
    built = bcb.build_resident_can_mt(agent.inner, residents[index])
    bcb.apply_scenario_evidence(agent.inner, built["concepts"])
    agent.inner.set_attr(built["mt_node"], "discrete_mode", "3state")
    agent.inner.set_attr(built["mt_node"], "can_tick", 0.0)
    agent.inner.run_rules()
    agent.inner.set_attr(built["mt_node"], "can_tick", 1.0)
    agent.inner.run_rules()
    return built


def _undirected_edges(agent, mt):
    net = cjt.can_network_from_mt(agent.inner, mt)
    return set(net["edges"])


# --------------------------------------------------------------------------- #
#  0. engine-load idempotency guard
# --------------------------------------------------------------------------- #
def test_ensure_can_native_engine_loaded_is_idempotent(agent):
    before = agent.inner.rule_count()
    r1 = sd.ensure_can_native_engine_loaded(agent)
    mid = agent.inner.rule_count()
    r2 = sd.ensure_can_native_engine_loaded(agent)
    after = agent.inner.rule_count()
    assert mid > before, "first call must actually install the rules"
    assert r1 is True
    assert r2 is False, "second call must be a no-op (already installed)"
    assert after == mid, "must not double-install on a second call"
    names = [r.get("name") for r in agent.inner.export_rules()]
    assert names.count("can_native_hebbian_mint") == 1


# --------------------------------------------------------------------------- #
#  1. SUCCESS -- real sentences grow a real, genuinely NEW edge pair, then
#     dispatch through all three UNCHANGED CAN resolvers.
# --------------------------------------------------------------------------- #
def test_grow_from_text_mints_genuinely_new_edges_not_in_the_template(agent):
    built = _built_mt(agent, 1)  # "Ida Ditchwater"
    mt = built["mt_node"]
    before_edges = _undirected_edges(agent, mt)

    result = sd.grow_can_network_from_text(
        agent, mt,
        ["Ida Ditchwater is self worth.", "Ida Ditchwater is debtor trustworthy."])

    assert result is not None
    assert result["grown"] is True
    assert len(result["applied"]) == 2
    assert result["after_edge_count"] > result["before_edge_count"]

    after_edges = _undirected_edges(agent, mt)
    new_pairs = after_edges - before_edges
    assert new_pairs, "at least one genuinely new undirected pair must appear"

    # None of build_resident_can_mt's own STRUCTURAL_EDGES pairs are in the
    # new set -- this is real NEW structure, not a re-confirmation of the
    # hand-authored template.
    structural = {frozenset(p[:2]) for p in bcb.STRUCTURAL_EDGES}
    for a, b in new_pairs:
        name_a = agent.s.node(a)["attrs"]["name"]
        name_b = agent.s.node(b)["attrs"]["name"]
        assert frozenset((name_a, name_b)) not in structural, (
            f"({name_a},{name_b}) is a hand-authored structural edge, not new growth")


def test_grown_network_dispatches_through_solve_can_exact_correctly(agent):
    built = _built_mt(agent, 2)
    mt = built["mt_node"]
    concepts_by_id = {v.value: k for k, v in built["concepts"].items()}

    result = sd.grow_can_network_from_text(
        agent, mt,
        ["Garnet Hollow is self worth.", "Garnet Hollow is debtor trustworthy."])
    assert result is not None and result["grown"] is True

    goal = sd.mint_solve_can_exact_goal(agent, mt, treewidth_bound=10, max_exact_n=10, commit=False)
    _pump(agent, goal)
    attrs = agent.s.node(goal)["attrs"]
    assert attrs["status"] == "resolved"
    state = attrs["answer"]["state"]
    by_name = {concepts_by_id[int(k)]: v for k, v in state.items()}
    # The exact MAP assignment must reflect the applied positive evidence:
    # both evidenced concepts settle to +1.
    assert by_name["self_worth"] == 1.0
    assert by_name["debtor_trustworthy"] == 1.0


def test_grown_network_dispatches_through_solve_can_relax_and_bp(agent):
    built = _built_mt(agent, 3)
    mt = built["mt_node"]

    result = sd.grow_can_network_from_text(
        agent, mt,
        ["Alby Marsh is self worth.", "Alby Marsh is debtor trustworthy."])
    assert result is not None

    g_relax = sd.mint_solve_can_relax_goal(agent, mt)
    _pump(agent, g_relax)
    assert agent.s.node(g_relax)["attrs"]["status"] == "resolved"

    g_bp = sd.mint_solve_can_bp_goal(agent, mt)
    _pump(agent, g_bp)
    attrs_bp = agent.s.node(g_bp)["attrs"]
    assert attrs_bp["status"] == "resolved"
    assert "final_state" in attrs_bp["answer"]


# --------------------------------------------------------------------------- #
#  2. CONTROL -- the SAME tick schedule with NO evidence applied never
#     grows the pair (rules out "would have happened anyway").
# --------------------------------------------------------------------------- #
def test_control_no_evidence_never_grows_the_pair(agent):
    built = _built_mt(agent, 4)
    mt = built["mt_node"]
    concepts = built["concepts"]

    def has_edge(x, y):
        return concepts[y] in agent.inner.neighbours(concepts[x], "causal_influence")

    for tick in range(2, 8):
        agent.inner.set_attr(mt, "can_tick", float(tick))
        agent.inner.run_rules()
    assert not has_edge("self_worth", "debtor_trustworthy"), (
        "the pair must NOT co-activate/mint without text evidence, ruling out "
        "'would have happened anyway'")


# --------------------------------------------------------------------------- #
#  3. HONEST DECLINE (adapter-side, zero graph mutation)
# --------------------------------------------------------------------------- #
def test_decline_fewer_than_two_statements_mints_nothing(agent):
    built = _built_mt(agent, 5)
    mt = built["mt_node"]
    before_nodes = agent.s.node_count()
    assert sd.grow_can_network_from_text(agent, mt, ["Barnaby Furlong is self worth."]) is None
    assert sd.grow_can_network_from_text(agent, mt, []) is None
    assert sd.grow_can_network_from_text(agent, mt, "not a list") is None
    assert agent.s.node_count() == before_nodes


def test_decline_non_property_or_question_statements_mint_nothing(agent):
    built = _built_mt(agent, 6)
    mt = built["mt_node"]
    before_nodes = agent.s.node_count()
    result = sd.grow_can_network_from_text(
        agent, mt,
        ["Is Thaddeus Ramskin trustworthy?", "Thaddeus Ramskin likes apples."])
    assert result is None
    assert agent.s.node_count() == before_nodes


def test_decline_static_discrete_mode_is_not_overridden(agent):
    """A Mt deliberately configured to discrete_mode='static' (the SAME
    isolation convention `tests/test_can_native_reimplementation.py` uses to
    keep item-3's relaxation rules from interfering) must be left alone --
    this function must not silently flip it to '3state'."""
    native = agent.inner
    mt = native.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0.0})
    a = native.add_node("Concept", {"name": "a", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    b = native.add_node("Concept", {"name": "b", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    native.add_edge(mt, "has_concept", a, {})
    native.add_edge(mt, "has_concept", b, {})
    result = sd.grow_can_network_from_text(
        agent, mt, ["Ida Ditchwater is self worth.", "Ida Ditchwater is debtor trustworthy."])
    assert result is None
    assert native.node(mt)["attrs"]["discrete_mode"] == "static"


# --------------------------------------------------------------------------- #
#  4. HONEST WALL (resolver-side -- real evidence applied, but too few
#     statements resolved to a real Concept inside THIS Mt)
# --------------------------------------------------------------------------- #
def test_wall_when_attr_does_not_exist_in_target_mt(agent):
    built = _built_mt(agent, 7)
    mt = built["mt_node"]
    result = sd.grow_can_network_from_text(
        agent, mt,
        ["Cuthbert Wold is self worth.", "Cuthbert Wold is honest."])
    assert result is not None
    assert result["grown"] is False
    assert len(result["applied"]) == 1
    assert "reason" in result
