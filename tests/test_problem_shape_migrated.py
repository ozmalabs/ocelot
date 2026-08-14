"""Rung 3 of docs/research/engine_substrate/QUESTION_DRIVER_SOLVER_DISPATCH_
PREREG.md -- QUESTION_DRIVER_RUNG3_PREREG.md is the design doc. Live
demonstration that a `ProblemShape` codebook (`seeds/problem_shape_growth.json`,
`domains/problem_shape.py`) recognizes the STRUCTURAL SHAPE of a real,
already-minted `solve_*` Goal (Rung 1's own toolbox, `domains/
solver_dispatch.py`) from its real attrs/edges -- never from its `kind`
string -- via the UNCHANGED `ShapeDecode` sd-loop machinery pointed at a new
`codebook_type='ProblemShape'` node type, and grows a new shape live from
real recurrence (`decompose_shape`, minted from 2 real `solve_decompose`
observations, mirroring `META_SHAPE_FIRST_CLASS_RESULTS.md`'s own
recognize -> residual -> recurrence -> mint -> re-decode -> recognized
loop). Every case is a real toolbox call (deduction schemas, a real
Bigville CAN network, a real coupling-graph race, a real
`find_analogies`-built `DirectionalCorrespondence`) -- no synthetic/stub
inputs, per the discipline QUESTION_DRIVER_RUNG3_PREREG.md Sec1 registered.
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
from domains import problem_shape as ps                    # noqa: E402
from domains import problem_decomposition as pdec          # noqa: E402
from domains import analogical_thinking as at_mod          # noqa: E402
from worlds import bigville_can_beliefs as bcb              # noqa: E402


@pytest.fixture(scope="module")
def agent():
    """The SAME full-boot fixture shape `test_solver_dispatch_migrated.py::agent`
    already uses -- `load_all_seeds` sweeps every `seeds/*.json` including
    this rung's own `problem_shape_growth`."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    return a


def _pump(adapter, goal, max_iters: int = 32) -> None:
    """Byte-identical to `test_solver_dispatch_migrated.py::_pump`."""
    for _ in range(max_iters):
        adapter.fire_reflexes()
        adapter.inner.run_rules()
        if adapter.s.node(goal)["attrs"].get("status") in ("resolved", "walled"):
            return


def _resident_mt(agent, index=0):
    """Byte-identical to `test_solver_dispatch_migrated.py::_resident_mt` --
    a real Bigville resident CAN belief network."""
    native = agent.inner
    bcb.install_productions(native)
    residents = json.load(open(os.path.join(ROOT, "seeds", "bigville_cast100.json")))["residents"]
    built = bcb.build_resident_can_mt(native, residents[index])
    bcb.apply_scenario_evidence(native, built["concepts"])
    native.set_attr(built["mt_node"], "discrete_mode", "3state")
    native.set_attr(built["mt_node"], "can_tick", 0)
    return built["mt_node"], built["resident_node"], built["concepts"]


# --------------------------------------------------------------------------- #
#  0. THE SEEDED CODEBOOK -- present at boot, grounded in >=5 real recurring
#     instances each (QUESTION_DRIVER_RUNG3_PREREG.md Sec1.1/Sec2.3).
# --------------------------------------------------------------------------- #
def test_seeded_codebook_has_two_real_shapes(agent):
    sub = agent.s
    names = {sub.node(n)["attrs"]["name"] for n in sub.nodes("ProblemShape")}
    assert names == {"ps_has_statement=yes", "ps_has_targets_mt=yes"}
    for n in sub.nodes("ProblemShape"):
        a = sub.node(n)["attrs"]
        assert a["support"] >= 5.0, a
        assert a["minted"] == 0.0, "seeded entries are not runtime mints"


# --------------------------------------------------------------------------- #
#  1. RECOGNIZE a real deduction Goal as deduction_shape -- purely from its
#     real `statement` attr, never from `kind`.
# --------------------------------------------------------------------------- #
def test_recognizes_real_deduction_goal_as_deduction_shape(agent):
    sub = agent.s
    g = sd.mint_solve_deduction_goal(agent, "if X is a fish, X can swim")
    _pump(agent, g)
    assert sub.node(g)["attrs"]["status"] == "resolved"

    obs = ps.observe(agent, g)
    a_ = sub.node(obs)["attrs"]
    assert a_["status"] == "recognized", a_
    assert a_["covered_by"] == "ps_has_statement=yes"
    # the extracted signature never mentions `kind` at all -- structural, not
    # a read-back of the Goal's own already-decided classification.
    preds = {p for p, _ in a_["signature"]}
    assert "kind" not in preds


# --------------------------------------------------------------------------- #
#  2. RECOGNIZE a real CAN Goal as can_shape -- purely from its real
#     `targets_mt` edge (over a real Bigville resident belief network).
# --------------------------------------------------------------------------- #
def test_recognizes_real_can_goal_as_can_shape(agent):
    sub = agent.s
    mt, _resident, _concepts = _resident_mt(agent, index=1)
    g = sd.mint_solve_can_exact_goal(agent, mt)
    _pump(agent, g)
    assert sub.node(g)["attrs"]["status"] == "resolved"

    obs = ps.observe(agent, g)
    a_ = sub.node(obs)["attrs"]
    assert a_["status"] == "recognized", a_
    assert a_["covered_by"] == "ps_has_targets_mt=yes"


# --------------------------------------------------------------------------- #
#  3. DISCRIMINATION -- deduction_shape does NOT cover the CAN observation
#     and vice versa (checked directly, not merely inferred from status).
# --------------------------------------------------------------------------- #
def test_deduction_and_can_shapes_do_not_cross_cover(agent):
    sub = agent.s
    g_ded = sd.mint_solve_deduction_goal(agent, "if X is a bird, X can fly")
    _pump(agent, g_ded)
    mt, _r, _c = _resident_mt(agent, index=2)
    g_can = sd.mint_solve_can_exact_goal(agent, mt)
    _pump(agent, g_can)

    sig_ded = ps.goal_signature(sub, agent.inner, g_ded)
    sig_can = ps.goal_signature(sub, agent.inner, g_can)
    assert sig_ded != sig_can
    # the ONE fact each carries is on a DIFFERENT axis -- checked directly
    # against the real extracted signatures, not merely inferred from status.
    ded_evidenced = {p for p, v in sig_ded if v != ps._ABSENT and p != "is_a"}
    can_evidenced = {p for p, v in sig_can if v != ps._ABSENT and p != "is_a"}
    assert ded_evidenced == {"has_statement"}
    assert can_evidenced == {"has_targets_mt"}
    assert ded_evidenced.isdisjoint(can_evidenced)

    # the recognizer, run live, discriminates them the same way: neither
    # cross-recognizes as the OTHER shape.
    obs_ded = ps.observe(agent, g_ded)
    obs_can = ps.observe(agent, g_can)
    assert sub.node(obs_ded)["attrs"]["covered_by"] == "ps_has_statement=yes"
    assert sub.node(obs_can)["attrs"]["covered_by"] == "ps_has_targets_mt=yes"

    # the two seeded shapes' own signatures are distinct
    shapes = {sub.node(n)["attrs"]["name"]: tuple(map(tuple, sub.node(n)["attrs"]["signature"]))
              for n in sub.nodes("ProblemShape")
              if sub.node(n)["attrs"]["name"] in ("ps_has_statement=yes", "ps_has_targets_mt=yes")}
    assert shapes["ps_has_statement=yes"] != shapes["ps_has_targets_mt=yes"]


# --------------------------------------------------------------------------- #
#  4. THE GROWTH LOOP, LIVE -- two real solve_decompose observations recur
#     on the SAME real structural shape (neither has a statement/targets_mt/
#     targets_correspondence/direction -- only `bound`), mirroring
#     META_SHAPE_FIRST_CLASS_RESULTS.md Sec4's own
#     residual -> recurrence -> mint -> re-decode -> recognized loop.
# --------------------------------------------------------------------------- #
def test_decompose_shape_mints_from_real_recurrence_and_redecodes(agent):
    sub = agent.s
    before = {sub.node(n)["attrs"]["name"] for n in sub.nodes("ProblemShape")}
    assert "ps_has_bound=yes" not in before, "must not already exist for this test to prove growth"

    g1 = sd.mint_solve_deduction_goal(agent, "if X is a cat, X can purr")
    g2 = sd.mint_solve_deduction_goal(agent, "if X is a cat, X is furry")
    g3 = sd.mint_solve_deduction_goal(agent, "if X is a dog, X can bark")
    for g in (g1, g2, g3):
        _pump(agent, g)
        assert sub.node(g)["attrs"]["status"] == "resolved"
    schema_nodes = [sd._solve_caps(agent)[g]["result"]["node"] for g in (g1, g2, g3)]
    cand_shared = pdec.project_deduction_shared_attr(sub, schema_nodes)
    cand_complete = pdec.project_deduction_complete(sub, schema_nodes)

    # FIRST real solve_decompose observation -- a genuine residual, no
    # recurrence yet (support=1).
    gd1 = sd.mint_solve_decompose_goal(agent, [cand_shared, cand_complete], bound=1)
    _pump(agent, gd1)
    assert sub.node(gd1)["attrs"]["status"] == "resolved"
    obs1 = ps.observe(agent, gd1)
    assert sub.node(obs1)["attrs"]["status"] == "residual", sub.node(obs1)["attrs"]
    assert sub.node(obs1)["attrs"]["key"] == "ps_has_bound=yes"
    mid_names = {sub.node(n)["attrs"]["name"] for n in sub.nodes("ProblemShape")}
    assert "ps_has_bound=yes" not in mid_names, "a SINGLE occurrence must not mint"

    # SECOND real solve_decompose observation (a genuinely intractable
    # candidate at a real too-tight bound, mirroring Rung 2's own
    # test_solve_decompose_failure_files_a_solve_failure_gap) -- real
    # recurrence, triggers the mint.
    gd2 = sd.mint_solve_decompose_goal(agent, [cand_complete], bound=0)
    _pump(agent, gd2)
    assert sub.node(gd2)["attrs"]["status"] == "walled"
    obs2 = ps.observe(agent, gd2)

    after_names = {sub.node(n)["attrs"]["name"] for n in sub.nodes("ProblemShape")}
    assert "ps_has_bound=yes" in after_names, "recurrence (2 real instances) must mint exactly one entry"
    minted = [n for n in sub.nodes("ProblemShape")
              if sub.node(n)["attrs"]["name"] == "ps_has_bound=yes"]
    assert len(minted) == 1, "mint-once, not once per observation"
    m_attrs = sub.node(minted[0])["attrs"]
    assert m_attrs["minted"] == 1.0
    assert m_attrs["support"] == 2

    # BOTH observations end up recognized against the freshly minted entry
    # (obs2 recognizes directly against the newly-grown codebook at decode
    # time; obs1 re-decodes under the bumped epoch and recognizes too --
    # exactly the pattern META_SHAPE_FIRST_CLASS_RESULTS.md Sec4's own
    # TradeRecord demo shows: "recognized x2, both ms_buyer_is_a_lot_seller").
    assert sub.node(obs1)["attrs"]["status"] == "recognized", sub.node(obs1)["attrs"]
    assert sub.node(obs1)["attrs"]["covered_by"] == "ps_has_bound=yes"
    assert sub.node(obs2)["attrs"]["status"] == "recognized", sub.node(obs2)["attrs"]
    assert sub.node(obs2)["attrs"]["covered_by"] == "ps_has_bound=yes"

    # a THIRD, never-before-seen real decompose observation now recognizes
    # against the grown codebook with no further mint (support stays 2 in
    # the minted node -- new observations use RECOGNIZE, not re-mint).
    gd3 = sd.mint_solve_decompose_goal(agent, [cand_shared], bound=5)
    _pump(agent, gd3)
    obs3 = ps.observe(agent, gd3)
    assert sub.node(obs3)["attrs"]["status"] == "recognized", sub.node(obs3)["attrs"]
    assert sub.node(obs3)["attrs"]["covered_by"] == "ps_has_bound=yes"
    still_one = [n for n in sub.nodes("ProblemShape")
                 if sub.node(n)["attrs"]["name"] == "ps_has_bound=yes"]
    assert len(still_one) == 1


# --------------------------------------------------------------------------- #
#  5. GENUINE SINGLETONS -- a real solve_reasoning_bridge (can_to_deduction)
#     Goal and a real solve_analogical_promote Goal each carry a real
#     structural shape distinct from every seeded/minted entry, and each
#     occurs exactly once in this test run: both must stay `residual`,
#     never forced into an ill-fitting existing shape, and never minted
#     (support=1 < the recurrence floor).
# --------------------------------------------------------------------------- #
def test_singleton_real_shapes_stay_residual_not_forced_or_minted(agent):
    sub = agent.s
    mt, _r, _c = _resident_mt(agent, index=3)
    settle_goal = sd.mint_solve_can_exact_goal(agent, mt)
    _pump(agent, settle_goal)
    assert sub.node(settle_goal)["attrs"]["status"] == "resolved"

    bridge_goal = sd.mint_solve_reasoning_bridge_goal(agent, "can_to_deduction", mt=mt)
    _pump(agent, bridge_goal)
    assert sub.node(bridge_goal)["attrs"]["status"] == "resolved"
    obs_bridge = ps.observe(agent, bridge_goal)
    a_bridge = sub.node(obs_bridge)["attrs"]
    assert a_bridge["status"] == "residual", a_bridge
    assert a_bridge["key"] not in ("ps_has_statement=yes", "ps_has_targets_mt=yes")
    assert "has_direction=can_to_deduction" in a_bridge["key"]

    # a real, ALREADY-DECIDED DirectionalCorrespondence via find_analogies
    # (unmodified) -- the SAME construction
    # test_solve_analogical_promote_resolves_via_qd_bind_resolver uses.
    src = sub.add_node("Microtheory", {"name": "ps_rung3_src"})
    tgt = sub.add_node("Microtheory", {"name": "ps_rung3_tgt"})
    rich = sub.add_node("Concept", {"name": "ps_rung3_rich", "category": "c",
                                     "definition": "this gate will schedule and buffer "
                                                    "the flow through the machine, a store of state"})
    sub.add_edge(src, "has_concept", rich)
    sparse = sub.add_node("Concept", {"name": "ps_rung3_sparse", "category": "c",
                                       "definition": "this gate is part of a stage in the machine"})
    sub.add_edge(tgt, "has_concept", sparse)
    at_mod.find_analogies(sub, "ps_rung3_src", ["ps_rung3_tgt"], order_n=2)
    corr = None
    for c in sub.nodes("DirectionalCorrespondence"):
        pair = set(sub.neighbours(c, "about_a")) | set(sub.neighbours(c, "about_b"))
        if {rich, sparse} <= pair:
            corr = c
            break
    assert corr is not None

    promote_goal = sd.mint_solve_analogical_promote_goal(agent, corr)
    _pump(agent, promote_goal)
    obs_promote = ps.observe(agent, promote_goal)
    a_promote = sub.node(obs_promote)["attrs"]
    assert a_promote["status"] == "residual", a_promote
    assert a_promote["key"] not in ("ps_has_statement=yes", "ps_has_targets_mt=yes")
    assert a_promote["key"] == "ps_has_targets_correspondence=yes"

    # neither singleton minted a ProblemShape -- support=1 each, below the
    # recurrence floor `ps_mint`'s guard requires.
    names = {sub.node(n)["attrs"]["name"] for n in sub.nodes("ProblemShape")}
    assert a_bridge["key"] not in names
    assert a_promote["key"] not in names
