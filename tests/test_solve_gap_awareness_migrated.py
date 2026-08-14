"""Rung 2 of docs/research/engine_substrate/QUESTION_DRIVER_SOLVER_DISPATCH_
PREREG.md (QUESTION_DRIVER_RUNG2_PREREG.md / RESULTS.md): a solve_* Goal that
walls (Rung 1's own `status:"walled"` write, now paired with a Rung-2 `gap_key`
datum, `domains/solver_dispatch.py::_wall`) is DECIDED, by the new graph rule
`note_solve_exhausted_gap` (`seeds/gap_awareness.json` v1.7.0), to be a
capability gap: it files `SelfConcern{source:"implicit", kind:"solve_failure"}`,
content-deduped on `gap_key`, mint-once via `gap_noted` -- byte-identical shape
to `note_unresolved_topic_gap`'s own precedent for a stuck conversational topic.

Four things are demonstrated, live, over REAL toolbox calls (no stubs):

  1. THREE structurally different solve_* kinds genuinely cannot resolve their
     goal (an unparsable deduction statement; a real CAN network whose real
     treewidth exceeds an artificially tight bound; a decomposition whose
     BEST candidate still exceeds its bound) and each correctly files exactly
     one SelfConcern{kind:"solve_failure"}.
  2. A solve_* goal that DOES resolve normally files NO gap at all -- the
     discriminating proof, not just "gaps get filed."
  3. DEDUP -- the identical failing case, dispatched twice as two separate
     Goal nodes, files exactly one SelfConcern (not two).
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
#  FIXTURES -- the SAME boot shape test_solver_dispatch_migrated.py::agent
#  already established (module-scoped: many goals minted across many tests,
#  each test mints its own fresh Goal node(s), so sharing the substrate is
#  safe).
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    return a


def _pump(adapter, goal, max_iters: int = 32) -> None:
    """The SAME mechanical schedule test_solver_dispatch_migrated.py::_pump
    uses -- fire the question_pursue reflex, run the seeded rules (which now
    includes note_solve_exhausted_gap) to fixpoint each iteration, stop once
    the goal resolves or walls. Because run_rules() runs ALL loaded seeds'
    rules to a fixpoint, a goal that walls inside this SAME iteration's
    fire_reflexes() call already has its gap filed by the time this function
    returns -- no separate 'now run the gap rule' step is needed."""
    for _ in range(max_iters):
        adapter.fire_reflexes()
        adapter.inner.run_rules()
        if adapter.s.node(goal)["attrs"].get("status") in ("resolved", "walled"):
            return


def _resident_mt(agent, index=0):
    """A REAL Bigville resident CAN belief network, the SAME helper
    test_solver_dispatch_migrated.py::_resident_mt builds."""
    native = agent.inner
    bcb.install_productions(native)
    residents = json.load(open(os.path.join(ROOT, "seeds", "bigville_cast100.json")))["residents"]
    built = bcb.build_resident_can_mt(native, residents[index])
    bcb.apply_scenario_evidence(native, built["concepts"])
    native.set_attr(built["mt_node"], "discrete_mode", "3state")
    native.set_attr(built["mt_node"], "can_tick", 0)
    return built["mt_node"], built["resident_node"], built["concepts"]


def _solve_failure_concerns(agent):
    out = []
    for sc in agent.inner.neighbours(agent.agent, "has_self_concern"):
        if not agent.inner.has_node(sc):
            continue
        at = agent.s.node(sc)["attrs"]
        if at.get("kind") == "solve_failure":
            out.append(at)
    return out


def _n_solve_failure_gaps_with_content(agent, content):
    return sum(1 for c in _solve_failure_concerns(agent) if c.get("content") == content)


# --------------------------------------------------------------------------- #
#  1. solve_deduction on an unparsable statement -- honest wall, real gap.
# --------------------------------------------------------------------------- #
def test_solve_deduction_failure_files_a_solve_failure_gap(agent):
    sub = agent.s
    statement = "purple elephants dream sideways rung2"   # unique per test run
    goal = sd.mint_solve_deduction_goal(agent, statement)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "walled", a_.get("note")
    gap_key = a_["gap_key"]
    assert gap_key == "solve_deduction:%s" % statement
    assert a_.get("gap_noted") == 1.0

    matches = [c for c in _solve_failure_concerns(agent) if c.get("content") == gap_key]
    assert len(matches) == 1, matches
    c = matches[0]
    assert c["source"] == "implicit"
    assert c["status"] == "noted"

    # the edge shape mirrors note_unresolved_topic_gap exactly: agent
    # -has_self_concern-> sc -about_goal-> g.
    sc_nodes = [n for n in agent.inner.neighbours(agent.agent, "has_self_concern")
                if agent.s.node(n)["attrs"].get("content") == gap_key]
    assert sc_nodes
    assert goal in agent.inner.neighbours(sc_nodes[0], "about_goal")


# --------------------------------------------------------------------------- #
#  2. solve_can_exact on a REAL CAN network with the treewidth bound set
#     artificially below its real treewidth (~2, per
#     CAN_SOLVER_TRACTABILITY_RESULTS.md sec2) -- a genuine tractability wall,
#     not a contrived input.
# --------------------------------------------------------------------------- #
def test_solve_can_exact_failure_files_a_solve_failure_gap(agent):
    sub = agent.s
    mt, _resident, _concepts = _resident_mt(agent, index=10)
    # NOTE: treewidth_bound=0 would be falsy and silently fall back to the
    # resolver's default (4) -- domains/solver_dispatch.py::solve_can_exact
    # reads `int(at.get("treewidth_bound") or cjt.DEFAULT_TREEWIDTH_BOUND)`,
    # so an explicit 0 is indistinguishable from "not supplied". 1 is a
    # genuine, truthy, tighter-than-real-treewidth (~2) bound.
    goal = sd.mint_solve_can_exact_goal(agent, mt, treewidth_bound=1)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "walled", a_.get("note")
    assert a_["wall_kind"] == "treewidth_exceeds_bound"
    assert a_["treewidth"] > 0   # a REAL measured treewidth exceeded the bound
    gap_key = a_["gap_key"]
    assert gap_key.startswith("solve_can_exact:mt=")

    matches = [c for c in _solve_failure_concerns(agent) if c.get("content") == gap_key]
    assert len(matches) == 1, matches


# --------------------------------------------------------------------------- #
#  3. solve_decompose where the WINNING candidate still exceeds the bound --
#     a genuinely intractable decomposition attempt (bound=0 against real
#     measured treewidth >= 1 candidates).
# --------------------------------------------------------------------------- #
def test_solve_decompose_failure_files_a_solve_failure_gap(agent):
    from domains import problem_decomposition as pdec
    sub = agent.s

    g1 = sd.mint_solve_deduction_goal(agent, "if X is a cat, X can purr")
    g2 = sd.mint_solve_deduction_goal(agent, "if X is a cat, X is furry")
    for g in (g1, g2):
        _pump(agent, g)
        assert sub.node(g)["attrs"]["status"] == "resolved", sub.node(g)["attrs"].get("note")
    schema_nodes = [sd._solve_caps(agent)[g]["result"]["node"] for g in (g1, g2)]
    cand = pdec.project_deduction_shared_attr(sub, schema_nodes)

    goal = sd.mint_solve_decompose_goal(agent, [cand], bound=0)
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "walled", a_.get("note")
    assert a_["wall_kind"] == "treewidth_exceeds_bound"
    gap_key = a_["gap_key"]
    assert gap_key.startswith("solve_decompose:candidates=")

    matches = [c for c in _solve_failure_concerns(agent) if c.get("content") == gap_key]
    assert len(matches) == 1, matches


# --------------------------------------------------------------------------- #
#  4. THE DISCRIMINATING PROOF -- a solve_* goal that resolves normally files
#     NO solve_failure gap at all.
# --------------------------------------------------------------------------- #
def test_solve_success_files_no_gap(agent):
    before = len(_solve_failure_concerns(agent))
    sub = agent.s
    goal = sd.mint_solve_deduction_goal(agent, "if X is a dog, X can bark")
    _pump(agent, goal)
    a_ = sub.node(goal)["attrs"]
    assert a_["status"] == "resolved", a_.get("note")
    assert "gap_key" not in a_ or a_.get("gap_key") is None
    assert a_.get("gap_noted") != 1.0
    after = len(_solve_failure_concerns(agent))
    assert after == before, "a resolved solve_* goal must file no solve_failure gap"


# --------------------------------------------------------------------------- #
#  5. DEDUP -- the SAME failing case dispatched twice (two Goal nodes, same
#     statement -> same gap_key) files exactly ONE SelfConcern, not two.
# --------------------------------------------------------------------------- #
def test_repeated_identical_solve_failure_is_deduped(agent):
    sub = agent.s
    statement = "the sky is green because rung2 dedup case"
    gap_key = "solve_deduction:%s" % statement

    before = _n_solve_failure_gaps_with_content(agent, gap_key)
    assert before == 0, "test isolation: this content must be unused before this test runs"

    g1 = sd.mint_solve_deduction_goal(agent, statement)
    _pump(agent, g1)
    assert sub.node(g1)["attrs"]["status"] == "walled"
    assert _n_solve_failure_gaps_with_content(agent, gap_key) == 1

    g2 = sd.mint_solve_deduction_goal(agent, statement)
    _pump(agent, g2)
    assert sub.node(g2)["attrs"]["status"] == "walled"
    # the SECOND identical failure must NOT file a second gap.
    assert _n_solve_failure_gaps_with_content(agent, gap_key) == 1
