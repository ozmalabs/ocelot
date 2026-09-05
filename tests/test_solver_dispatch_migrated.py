"""Rung 1 of docs/research/engine_substrate/QUESTION_DRIVER_SOLVER_DISPATCH_
PREREG.md -- live regression + demonstration that the seven-item
reasoning/solving toolbox (propositional_deduction.py,
can_native_orchestration.py, can_junction_tree.py, can_native_bp.py,
reasoning_can_bridge.py, analogical_thinking.py +
propositional_deduction.mint_logical_schema_from_analogy,
problem_decomposition.py) dispatches through the EXISTING, UNCHANGED
`qd_bind_resolver` JOIN (`seeds/question_driving.json`) via seven new
`solve_*`-kind `Resolver` nodes (`seeds/solver_dispatch.json`,
`domains/solver_dispatch.py`).

Every test mints a real `Goal{kind:"solve_*"}` node, pumps the SAME
reflex/rule loop `question_driver.py::_pump` already uses
(`fire_reflexes()` + `run_rules()` to fixpoint), and asserts the goal
reached `status in {"resolved","walled"}` via a REAL underlying toolbox
call -- never a stub. See QUESTION_DRIVER_RUNG1_RESULTS.md for the full
report (namespacing verification, judgment calls, GO/NO-GO).
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
from domains import propositional_deduction as pd          # noqa: E402
from domains import analogical_thinking as at               # noqa: E402
from worlds import bigville_can_beliefs as bcb              # noqa: E402


# --------------------------------------------------------------------------- #
#  FIXTURES
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def agent():
    """Full boot (`load_all_seeds` sweeps every seeds/*.json file, including
    `question_driving` and this rung's own `solver_dispatch`) -- the same
    fixture shape `tests/test_directional_correspondence.py::agent` already
    uses. Module-scoped: this rung mints many goals across many tests and a
    full boot is not free; every test below mints its OWN Goal node(s) so
    module-scoping the substrate is safe (no cross-test node reuse)."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    return a


def _pump(adapter, goal, max_iters: int = 32) -> None:
    """The SAME mechanical schedule `question_driver.py::_pump` already
    uses (fire the `question_pursue` reflex, run the seeded rules to
    fixpoint, stop once the goal resolves or walls) -- inlined here rather
    than imported so this test file has no coupling to `question_driver.py`'s
    `_QDAdapter`-specific internals (this fixture uses a full `WorldAdapter`,
    not the lightweight facade)."""
    for _ in range(max_iters):
        adapter.fire_reflexes()
        adapter.inner.run_rules()
        if adapter.s.node(goal)["attrs"].get("status") in ("resolved", "walled"):
            return


def _resident_mt(agent, index=0):
    """A REAL Bigville resident CAN belief network (treewidth ~2 per
    CAN_SOLVER_TRACTABILITY_RESULTS.md sec2) -- mirrors
    tests/test_can_junction_tree.py::_fresh_resident_mt, built on the SAME
    live substrate this rung's Goal/Resolver machinery already runs on
    (rather than a second isolated substrate), so the `Agent -has_goal->`
    hub and the CAN network coexist exactly the way a real boot would."""
    # CAN-native ops (concept_apply_evidence, mt_energy, run_rules_scoped, ...)
    # live only on the RAW native substrate (`agent.inner`), not the thinner
    # `substrate_rs.Substrate` wrapper (`agent.s`) -- the SAME dual-handle
    # distinction `reasoning_can_bridge.py::_resolve` already documents
    # (`sub`/`native`). Both handles address the SAME underlying graph, so
    # nodes minted here are visible via `agent.s` everywhere else in this file.
    native = agent.inner
    bcb.install_productions(native)
    residents = json.load(open(os.path.join(ROOT, "seeds", "bigville_cast100.json")))["residents"]
    built = bcb.build_resident_can_mt(native, residents[index])
    bcb.apply_scenario_evidence(native, built["concepts"])
    native.set_attr(built["mt_node"], "discrete_mode", "3state")
    native.set_attr(built["mt_node"], "can_tick", 0)
    return built["mt_node"], built["resident_node"], built["concepts"]


# --------------------------------------------------------------------------- #
#  NAMESPACING -- resolves_kind is disjoint from every existing Goal.kind
#  vocabulary this codebase already uses (the prereg's own Sec1.3 risk).
# --------------------------------------------------------------------------- #
def test_solve_kinds_are_solve_prefixed_and_unique():
    kinds = set(sd.SOLVE_RESOLVER_FUNCTIONS.keys())
    assert len(kinds) == 7
    assert all(k.startswith("solve_") for k in kinds)


# --------------------------------------------------------------------------- #
#  1. DEDUCTION -- a real Goal{kind:"solve_deduction"} dispatches through the
#     UNCHANGED qd_bind_resolver JOIN to the new solve_deduction Resolver,
#     which mints a REAL knowledge_logical ShapeSignature via
#     propositional_deduction.mint_logical_schema.
# --------------------------------------------------------------------------- #
def test_solve_deduction_resolves_via_qd_bind_resolver(agent):
    sub = agent.s
    goal = sd.mint_solve_deduction_goal(agent, "if X is a fish, X can swim")
    assert sub.node(goal)["attrs"]["kind"] == "solve_deduction"
    assert sub.node(goal)["attrs"]["status"] == "pending"

    _pump(agent, goal)

    at_ = sub.node(goal)["attrs"]
    assert at_["status"] == "resolved", at_.get("note")
    # the resolve_with edge is the qd_bind_resolver JOIN's own effect -- proof
    # the UNCHANGED rule did the dispatch, not this test.
    resolvers = agent.inner.neighbours(goal, "resolve_with")
    assert resolvers and sub.node(resolvers[0])["attrs"]["name"] == "solve_deduction"
    assert at_["form_used"] == "conditional"
    schema_name = at_["schema_name"]
    schema_node = pd._schema_by_name(sub, schema_name)
    assert schema_node is not None
    schema_attrs = sub.node(schema_node)["attrs"]
    assert schema_attrs["kind"] == "knowledge_logical"
    assert json.loads(schema_attrs["signature"]) == [["holds", "fish"]]
    assert json.loads(schema_attrs["supplies"]) == {"relation": "is_a", "attr": "can_swim"}


def test_solve_deduction_universal_and_existential_forms(agent):
    sub = agent.s
    g_univ = sd.mint_solve_deduction_goal(agent, "All philosophers are mortal", mode="universal")
    _pump(agent, g_univ)
    a1 = sub.node(g_univ)["attrs"]
    assert a1["status"] == "resolved", a1.get("note")
    assert a1["form_used"] == "universal"

    g_exist = sd.mint_solve_deduction_goal(agent, "Some bird is a penguin", mode="existential")
    _pump(agent, g_exist)
    a2 = sub.node(g_exist)["attrs"]
    assert a2["status"] == "resolved", a2.get("note")
    assert a2["form_used"] == "existential"


def test_solve_deduction_honest_wall_on_unparsable_statement(agent):
    sub = agent.s
    goal = sd.mint_solve_deduction_goal(agent, "purple elephants dream sideways")
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "walled"
    assert a_["note"]


# --------------------------------------------------------------------------- #
#  2/3/4. CAN -- three DIFFERENT toolbox facilities, three DIFFERENT solve_*
#     kinds, over the SAME real Bigville resident CAN network.
# --------------------------------------------------------------------------- #
def test_solve_can_relax_resolves_via_qd_bind_resolver(agent):
    sub = agent.s
    mt, _resident, _concepts = _resident_mt(agent, index=1)
    goal = sd.mint_solve_can_relax_goal(agent, mt, k_starts=1)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "resolved", a_.get("note")
    resolvers = agent.inner.neighbours(goal, "resolve_with")
    assert resolvers and sub.node(resolvers[0])["attrs"]["name"] == "solve_can_relax"
    assert "energy" in a_["answer"] and "steps" in a_["answer"]


def test_solve_can_relax_multi_start(agent):
    sub = agent.s
    mt, _resident, _concepts = _resident_mt(agent, index=2)
    goal = sd.mint_solve_can_relax_goal(agent, mt, k_starts=5)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "resolved", a_.get("note")
    assert a_["answer"]["k_starts"] == 5
    assert "frustration" in a_["answer"]


def test_solve_can_exact_resolves_via_qd_bind_resolver(agent):
    sub = agent.s
    mt, _resident, _concepts = _resident_mt(agent, index=3)
    goal = sd.mint_solve_can_exact_goal(agent, mt)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "resolved", a_.get("note")
    resolvers = agent.inner.neighbours(goal, "resolve_with")
    assert resolvers and sub.node(resolvers[0])["attrs"]["name"] == "solve_can_exact"
    assert a_["treewidth"] <= 4  # the real Bigville per-resident treewidth (~2)
    assert "energy" in a_["answer"]


# --------------------------------------------------------------------------- #
#  BUGFIX (QUESTION_DRIVER_BUGFIX_AND_RECHECK_RESULTS.md): treewidth_bound=0
#  must be HONORED as an explicit (if degenerate) request, never silently
#  substituted with cjt.DEFAULT_TREEWIDTH_BOUND -- named as a live footgun in
#  QUESTION_DRIVER_RUNG2_RESULTS.md sec2.1 (found while building that rung's
#  own test), fixed in domains/solver_dispatch.py::solve_can_exact via the
#  new `_at_num` helper (`at.get(key) or default` treats 0/0.0 as "missing";
#  `_at_num` only substitutes `default` when the attr is genuinely absent/
#  None).
# --------------------------------------------------------------------------- #
def _edgeless_single_concept_mt(agent):
    """A REAL, genuinely treewidth-0 CAN network -- one Concept, zero
    `causal_influence` edges -- the concrete case an explicit
    `treewidth_bound=0` request is honestly asking for (CLAUDE.md/the task's
    own framing: "a single-node or edgeless graph" is a real, valid,
    if degenerate, zero-treewidth request, not a contrived input)."""
    native = agent.inner
    bcb.install_productions(native)
    mt = native.add_node("Microtheory", {
        "temperature": 1.0, "discrete_mode": "3state", "can_tick": 0,
    })
    c = native.add_node("Concept", {
        "name": "solo", "state": 0.0, "external_field": 0.3, "identity_field": 0.0,
    })
    native.add_edge(mt, "has_concept", c, {})
    return mt, c


def test_solve_can_exact_treewidth_bound_zero_is_honored_on_a_genuine_zero_treewidth_network(agent):
    """POSITIVE case: bound=0, explicitly supplied, on a REAL network whose
    true treewidth IS 0 (a single concept, no edges) -- must be ATTEMPTED
    and RESOLVED, proving 0 is read as "the caller's real bound," not
    dropped as falsy."""
    sub = agent.s
    mt, _c = _edgeless_single_concept_mt(agent)
    goal = sd.mint_solve_can_exact_goal(agent, mt, treewidth_bound=0)
    assert sub.node(goal)["attrs"]["treewidth_bound"] == 0.0  # mint-side write, unaffected by the bug
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "resolved", a_.get("note")
    assert a_["treewidth"] == 0.0
    stashed = sd._solve_caps(agent)[goal]["result"]
    assert stashed["treewidth_bound"] == 0, (
        "the bound actually PASSED to junction_tree_exact_settle must be the "
        "caller's real 0, never the silently-substituted default")


def test_solve_can_exact_treewidth_bound_zero_is_honored_not_defaulted_on_real_nonzero_network(agent):
    """NEGATIVE/discriminating case: bound=0, explicitly supplied, on a REAL
    Bigville resident network (measured treewidth ~2, well within the
    DEFAULT_TREEWIDTH_BOUND=4 this footgun used to silently fall back to).
    Pre-fix, `at.get("treewidth_bound") or cjt.DEFAULT_TREEWIDTH_BOUND` reads
    the stored `0.0` as falsy and substitutes 4 -- the goal would wrongly
    RESOLVE (2 <= 4). Post-fix, the real 0 is honoured, 2 > 0, and the goal
    correctly WALLS -- this is the exact regression this test pins."""
    from domains import can_junction_tree as cjt
    sub = agent.s
    mt, _resident, _concepts = _resident_mt(agent, index=6)
    goal = sd.mint_solve_can_exact_goal(agent, mt, treewidth_bound=0)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "walled", (
        "treewidth_bound=0 on a real treewidth~2 network must WALL -- a "
        "'resolved' status here means the bug regressed (0 silently read "
        "as the %r default)" % cjt.DEFAULT_TREEWIDTH_BOUND)
    assert a_["wall_kind"] == "treewidth_exceeds_bound"
    assert a_["treewidth"] > 0.0
    stashed = sd._solve_caps(agent)[goal]["result"]
    assert stashed["treewidth_bound"] == 0, (
        "the honest-refusal reason must cite the caller's real bound (0), "
        "not the silently-substituted default (%r)" % cjt.DEFAULT_TREEWIDTH_BOUND)
    assert stashed["treewidth_bound"] != cjt.DEFAULT_TREEWIDTH_BOUND


def test_solve_can_exact_nonzero_and_absent_bound_behaviour_unchanged(agent):
    """REGRESSION PROOF: the pre-existing non-zero-bound behaviour (an
    explicit bound, and the no-bound-supplied default-to-
    DEFAULT_TREEWIDTH_BOUND path) is byte-identical to before the fix --
    both still resolve on a real treewidth~2 network."""
    sub = agent.s
    # (a) no treewidth_bound supplied at all -> falls back to
    #     cjt.DEFAULT_TREEWIDTH_BOUND, exactly as test_solve_can_exact_
    #     resolves_via_qd_bind_resolver (Rung 1, unmodified) already asserts.
    mt_a, _r, _c = _resident_mt(agent, index=7)
    goal_a = sd.mint_solve_can_exact_goal(agent, mt_a)
    assert "treewidth_bound" not in sub.node(goal_a)["attrs"]
    _pump(agent, goal_a)
    a_a = sub.node(goal_a)["attrs"]
    assert a_a["status"] == "resolved", a_a.get("note")
    assert a_a["treewidth"] <= 4

    # (b) an explicit non-zero bound (4, matching the default's own value)
    #     -> still resolves, same as always.
    mt_b, _r2, _c2 = _resident_mt(agent, index=8)
    goal_b = sd.mint_solve_can_exact_goal(agent, mt_b, treewidth_bound=4)
    _pump(agent, goal_b)
    a_b = sub.node(goal_b)["attrs"]
    assert a_b["status"] == "resolved", a_b.get("note")
    assert a_b["treewidth"] <= 4

    # (c) an explicit non-zero bound that IS too tight (1, below the real
    #     ~2 treewidth) -> still walls, same as QUESTION_DRIVER_RUNG2_RESULTS.md
    #     sec2.1's own test_solve_can_exact_failure_files_a_solve_failure_gap.
    mt_c, _r3, _c3 = _resident_mt(agent, index=9)
    goal_c = sd.mint_solve_can_exact_goal(agent, mt_c, treewidth_bound=1)
    _pump(agent, goal_c)
    a_c = sub.node(goal_c)["attrs"]
    assert a_c["status"] == "walled", a_c.get("note")
    assert a_c["wall_kind"] == "treewidth_exceeds_bound"


def test_solve_can_bp_resolves_via_qd_bind_resolver(agent):
    sub = agent.s
    mt, _resident, _concepts = _resident_mt(agent, index=4)
    goal = sd.mint_solve_can_bp_goal(agent, mt)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "resolved", a_.get("note")
    resolvers = agent.inner.neighbours(goal, "resolve_with")
    assert resolvers and sub.node(resolvers[0])["attrs"]["name"] == "solve_can_bp"
    assert "final_state" in a_["answer"]
    assert "converged" in a_["answer"]


# --------------------------------------------------------------------------- #
#  5. REASONING <-> CAN BRIDGE -- a real settled CAN state round-trips into a
#     deduction predication (can_to_deduction direction).
# --------------------------------------------------------------------------- #
def test_solve_reasoning_bridge_can_to_deduction(agent):
    sub = agent.s
    mt, resident, concepts = _resident_mt(agent, index=5)
    # settle the network first (real numbers to bridge, not zeros).
    settle_goal = sd.mint_solve_can_exact_goal(agent, mt)
    _pump(agent, settle_goal)
    assert sub.node(settle_goal)["attrs"]["status"] == "resolved"

    bridge_goal = sd.mint_solve_reasoning_bridge_goal(agent, "can_to_deduction", mt=mt)
    _pump(agent, bridge_goal)
    a_ = sub.node(bridge_goal)["attrs"]
    assert a_["status"] == "resolved", a_.get("note")
    resolvers = agent.inner.neighbours(bridge_goal, "resolve_with")
    assert resolvers and sub.node(resolvers[0])["attrs"]["name"] == "solve_reasoning_bridge"
    assert a_["answer"]["n_predications"] >= 0  # honest: 0 is valid (all-ambivalent state)


# --------------------------------------------------------------------------- #
#  6. ANALOGICAL PROMOTION -- a real, ALREADY-DECIDED DirectionalCorrespondence
#     (built via analogical_thinking.find_analogies, unmodified) promotes into
#     a real knowledge_logical schema via the new solve_analogical_promote
#     Resolver.
# --------------------------------------------------------------------------- #
def _mt(sub, name):
    return sub.add_node("Microtheory", {"name": name})


def _concept(sub, mt, name, definition):
    c = sub.add_node("Concept", {"name": name, "definition": definition, "category": "c"})
    sub.add_edge(mt, "has_concept", c)
    return c


def test_solve_analogical_promote_resolves_via_qd_bind_resolver(agent):
    sub = agent.s
    src, tgt = _mt(sub, "sd_rung1_src"), _mt(sub, "sd_rung1_tgt")
    rich = _concept(sub, src, "sd_rung1_rich",
                     "this gate will schedule and buffer the flow through "
                     "the machine, a store of state")
    sparse = _concept(sub, tgt, "sd_rung1_sparse",
                       "this gate is part of a stage in the machine")
    at._legacy_find_analogies(sub, "sd_rung1_src", ["sd_rung1_tgt"], order_n=2)
    corr = None
    for c in sub.nodes("DirectionalCorrespondence"):
        pair = set(sub.neighbours(c, "about_a")) | set(sub.neighbours(c, "about_b"))
        if {rich, sparse} <= pair:
            corr = c
            break
    assert corr is not None, "find_analogies should have recorded a real correspondence"

    goal = sd.mint_solve_analogical_promote_goal(agent, corr)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "resolved", a_.get("note")
    resolvers = agent.inner.neighbours(goal, "resolve_with")
    assert resolvers and sub.node(resolvers[0])["attrs"]["name"] == "solve_analogical_promote"
    assert a_["direction_verdict"] == "a_source"
    schema_node = pd._schema_by_name(sub, a_["schema_name"])
    schema_attrs = sub.node(schema_node)["attrs"]
    assert schema_attrs["coherence"] == "elaborative"
    assert schema_attrs["provenance"] == "analogical"


# --------------------------------------------------------------------------- #
#  7. DECOMPOSITION, CHAINED FROM DEDUCTION -- the required "chain two
#     facilities" demo. Three solve_deduction Goals mint three REAL
#     knowledge_logical schemas (two sharing an antecedent, one disjoint);
#     a solve_decompose Goal then races project_deduction_shared_attr against
#     project_deduction_complete OVER THOSE SAME MINTED SCHEMA NODES -- the
#     decompose facility's candidates are literally sourced from the
#     deduction facility's own output. See QUESTION_DRIVER_RUNG1_RESULTS.md
#     for why this (not "CAN too complex -> decompose") is the honest chain
#     demo: problem_decomposition's race rescues a WRONG COUPLING GUESS, not
#     a genuinely-high-treewidth true network -- a dense real CAN network's
#     "identity" projection has no better alternative to discover.
# --------------------------------------------------------------------------- #
def test_solve_decompose_chains_from_solve_deduction(agent):
    from domains import problem_decomposition as pdec
    sub = agent.s

    g1 = sd.mint_solve_deduction_goal(agent, "if X is a fish, X can swim")
    g2 = sd.mint_solve_deduction_goal(agent, "if X is a fish, X is aquatic")
    g3 = sd.mint_solve_deduction_goal(agent, "if X is a mammal, X is warm blooded")
    for g in (g1, g2, g3):
        _pump(agent, g)
        assert sub.node(g)["attrs"]["status"] == "resolved", sub.node(g)["attrs"].get("note")

    schema_nodes = [
        sd._solve_caps(agent)[g]["result"]["node"] for g in (g1, g2, g3)
    ]
    cand_shared = pdec.project_deduction_shared_attr(sub, schema_nodes)
    cand_complete = pdec.project_deduction_complete(sub, schema_nodes)
    # the real, MEASURED discrimination this chain demonstrates: the sparse
    # (correct) coupling guess has a strictly lower treewidth than the
    # deliberately-bad "everything related" guess, over the SAME 3 real
    # deduction schemas -- exactly the racing step's own reason to exist.
    from domains.graph_treewidth import min_fill_upper_bound
    tw_shared = min_fill_upper_bound(cand_shared["nodes"], cand_shared["edges"])["treewidth"]
    tw_complete = min_fill_upper_bound(cand_complete["nodes"], cand_complete["edges"])["treewidth"]
    assert tw_shared < tw_complete, (tw_shared, tw_complete)

    goal = sd.mint_solve_decompose_goal(agent, [cand_shared, cand_complete], bound=1)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "resolved", a_.get("note")
    resolvers = agent.inner.neighbours(goal, "resolve_with")
    assert resolvers and sub.node(resolvers[0])["attrs"]["name"] == "solve_decompose"
    assert a_["winner_projection"] == "deduction_shared_attr", (
        "the race (Argmin over min_fill_upper_bound) should have picked the "
        "sparse, correct projection, not the deliberately-overcoupled one")
    assert a_["treewidth"] <= 1

    full = sd._solve_caps(agent)[goal]["result"]
    assert full["attempted"] is True
    assert full["race"]["winner_name"] == "deduction_shared_attr"
