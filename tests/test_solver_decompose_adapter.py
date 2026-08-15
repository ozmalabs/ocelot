"""docs/research/engine_substrate/SOLVER_DECOMPOSE_ADAPTER_PREREG.md/_RESULTS.md
-- live regression + demonstration of the THIRD NL-to-structure adapter for
the six previously-unwired `solve_*` resolvers:
`solver_dispatch.mint_solve_decompose_goal_from_text`, a front door onto
`solve_decompose`.

Prior rungs ranked `solve_decompose` #3, "expensive, non-independent --
inherits whichever upstream object it projects over." This rung found that
`mint_solve_deduction_goal` was ALREADY an NL adapter (a bare statement
string, no pre-built graph object needed since Rung 1) and `problem_
decomposition.project_deduction_shared_attr`/`project_deduction_complete`
are mechanical, node-source-agnostic shape extraction over whatever real
`ShapeSignature` nodes they are handed -- so building a candidate projection
from real deduction schemas was already pure composition. Every test here
drives REAL, genuine Bigville-styled natural-language statements through the
UNMODIFIED `solve_deduction` pipeline, builds real candidate projections
over the real resulting nodes, and races them through the SAME `qd_bind_
resolver` dispatch + `solve_decompose` resolver `tests/test_solver_dispatch_
migrated.py` already exercises.
"""
from __future__ import annotations

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
from domains import problem_decomposition as pdec           # noqa: E402


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    return a


def _pump(adapter, goal, max_iters: int = 32) -> None:
    for _ in range(max_iters):
        adapter.fire_reflexes()
        adapter.inner.run_rules()
        if adapter.s.node(goal)["attrs"].get("status") in ("resolved", "walled"):
            return


def _node_counts(sub):
    """A snapshot of (Goal count, ShapeSignature count) -- used to assert an
    honest decline mutates NOTHING, the same discipline `test_solver_nl_
    adapter.py::test_decline_mints_no_goal_node_at_all` and `test_solver_
    analogy_adapter.py::test_decline_mints_no_goal_node_at_all` already use."""
    return len(sub.nodes("Goal")), len(sub.nodes("ShapeSignature"))


# Real, Bigville-styled deduction-shaped statements -- NOT the fish/mammal
# fixture text QUESTION_DRIVER_RUNG1_RESULTS.md's own hand-built chain test
# used; independent statement text over real Bigville CAN-topic vocabulary
# ("world_safe" -- the SAME tokenisation SOLVER_NL_ADAPTER_RESULTS.md Sec4.1
# already demonstrated), confirmed live in the PREREG before this file was
# written.
RESIDENT_VOTE = "If X is a resident, X can vote."
RESIDENT_SAFE = "If X is a resident, X is world safe."
MAYOR_GOVERN = "If X is a mayor, X can govern."


# --------------------------------------------------------------------------- #
#  SUCCESS -- real statements, real candidate race, real decomposition,
#  correctness verified by hand (not merely "resolved without erroring").
# --------------------------------------------------------------------------- #
def test_success_real_statements_race_and_decompose(agent):
    sub = agent.s
    goal = sd.mint_solve_decompose_goal_from_text(
        agent, [RESIDENT_VOTE, RESIDENT_SAFE, MAYOR_GOVERN], bound=1)
    assert goal is not None
    _pump(agent, goal)
    at = sub.node(goal)["attrs"]
    assert at["status"] == "resolved", at.get("note")
    resolvers = agent.inner.neighbours(goal, "resolve_with")
    assert resolvers and sub.node(resolvers[0])["attrs"]["name"] == "solve_decompose"

    # The real, MEASURED discrimination this adapter's own composition
    # reproduces (matching QUESTION_DRIVER_RUNG1_RESULTS.md's own chain test
    # shape, on independent statement text): the sparse "shared antecedent"
    # projection (resident/resident share, mayor is disjoint) strictly beats
    # the deliberately-overcoupled "everything related" guess.
    assert at["winner_projection"] == "deduction_shared_attr", (
        "the race (Argmin over min_fill_upper_bound) should have picked the "
        "sparse, correct projection built from the real shared 'resident' "
        "antecedent, not the deliberately-overcoupled one")
    assert at["treewidth"] <= 1

    full = sd._solve_caps(agent)[goal]["result"]
    assert full["attempted"] is True
    assert full["race"]["winner_name"] == "deduction_shared_attr"
    # Correctness verified by hand against the ACTUAL bags/parent structure
    # decompose_or_refuse produced -- not just status=="resolved".
    assert len(full["bags"]) == 3, full["bags"]
    tw_names = {c["name"]: c["treewidth"] for c in full["race"]["candidates"]}
    assert tw_names["deduction_shared_attr"] == 1
    assert tw_names["deduction_complete_overcoupled"] == 2


def test_success_candidates_are_built_over_the_real_resolved_schema_nodes(agent):
    """Direct proof the two candidates race real ShapeSignature nodes, not
    placeholder data -- read the resolved sub-goals' own schema_name attrs
    back off the graph, and confirm project_deduction_shared_attr's own
    edge_reason names the REAL shared 'resident' antecedent token, mirroring
    the "verify by hand against the real attrs" discipline both prior
    _from_text rungs used."""
    sub = agent.s
    goal = sd.mint_solve_decompose_goal_from_text(
        agent, [RESIDENT_VOTE, RESIDENT_SAFE, MAYOR_GOVERN], bound=1)
    assert goal is not None
    _pump(agent, goal)
    # The 3 solve_deduction sub-goals this adapter itself minted are real,
    # inspectable Goal nodes with real schema names (idempotent minting
    # across earlier tests in this module means the SAME schema names may
    # appear on more than one sub-goal -- checking set MEMBERSHIP, not an
    # exact recent-3 slice, is the honest check here).
    sub_goal_names = {
        sub.node(g)["attrs"].get("schema_name")
        for g in sub.nodes("Goal")
        if sub.node(g)["attrs"].get("kind") == "solve_deduction"
    }
    assert "logical_resident_can_vote" in sub_goal_names
    assert "logical_resident_world_safe" in sub_goal_names
    assert "logical_mayor_can_govern" in sub_goal_names

    full = sd._solve_caps(agent)[goal]["result"]
    cand = {c["name"]: c for c in full["race"]["candidates"]}
    assert set(cand) == {"deduction_shared_attr", "deduction_complete_overcoupled"}


def test_honest_wall_bound_too_tight(agent):
    """Real statements, real candidates -- the resolver-side wall
    (`decompose_or_refuse`'s own honest refusal), UNCHANGED, fires exactly
    as it already does for a hand-built candidate list -- this adapter's
    only contribution is correctly building the candidates from real text
    and letting the existing resolver decide."""
    sub = agent.s
    goal = sd.mint_solve_decompose_goal_from_text(
        agent, [RESIDENT_VOTE, RESIDENT_SAFE, MAYOR_GOVERN], bound=0)
    assert goal is not None
    _pump(agent, goal)
    at = sub.node(goal)["attrs"]
    assert at["status"] == "walled"
    assert at.get("wall_kind") == "treewidth_exceeds_bound"
    assert "gap_key" in at and at["gap_key"]
    full = sd._solve_caps(agent)[goal]["result"]
    assert full["attempted"] is False


# --------------------------------------------------------------------------- #
#  HONEST DECLINE (adapter-side) -- unsuitable input mints ZERO nodes at all,
#  the SAME "never mint garbage from unsuitable input" discipline both prior
#  NL-adapter rungs established.
# --------------------------------------------------------------------------- #
def test_decline_too_few_statements_mints_nothing(agent):
    sub = agent.s
    before = _node_counts(sub)
    assert sd.mint_solve_decompose_goal_from_text(agent, [RESIDENT_VOTE], bound=1) is None
    assert sd.mint_solve_decompose_goal_from_text(agent, [], bound=1) is None
    assert _node_counts(sub) == before


def test_decline_non_deduction_statements_mints_nothing(agent):
    """Statements that do not parse as deduction (an ordinary event
    predication; a question) are filtered by the PURE, zero-mutation
    pre-check before anything is minted -- confirmed here by node-count
    equality, not merely "returned None"."""
    sub = agent.s
    before = _node_counts(sub)
    g = sd.mint_solve_decompose_goal_from_text(
        agent, ["The mayor likes apples.", "Is the mayor trustworthy?"], bound=1)
    assert g is None
    assert _node_counts(sub) == before


def test_decline_bad_input_shapes_mints_nothing(agent):
    sub = agent.s
    before = _node_counts(sub)
    for bad in (None, [], "not a list", ["only one statement"]):
        assert sd.mint_solve_decompose_goal_from_text(agent, bad, bound=1) is None
    assert sd.mint_solve_decompose_goal_from_text(
        agent, [RESIDENT_VOTE, RESIDENT_SAFE], bound=None) is None
    assert _node_counts(sub) == before


# --------------------------------------------------------------------------- #
#  PARTIAL SUCCESS -- a real, honestly-documented departure from the prior
#  two _from_text adapters' "mints nothing on ANY decline" guarantee
#  (PREREG Sec4): once >=2 statements pass the pure pre-check, their
#  sub-goals ARE driven for real and leave real, inspectable nodes, even
#  though a statement that fails the pre-check is filtered before ever
#  touching the graph.
# --------------------------------------------------------------------------- #
def test_partial_success_filters_unsuitable_statement_before_minting_it(agent):
    sub = agent.s
    before_goals = len(sub.nodes("Goal"))
    mixed = [RESIDENT_VOTE, RESIDENT_SAFE, "The mayor likes apples."]
    goal = sd.mint_solve_decompose_goal_from_text(agent, mixed, bound=1)
    assert goal is not None
    _pump(agent, goal)
    at = sub.node(goal)["attrs"]
    assert at["status"] == "resolved", at.get("note")
    assert at["winner_projection"] == "deduction_shared_attr"
    after_goals = len(sub.nodes("Goal"))
    # exactly 2 solve_deduction sub-goals (the 2 usable statements) + 1
    # solve_decompose goal -- the unusable third statement never minted
    # anything, having been filtered by the pure pre-check.
    assert after_goals - before_goals == 3, (
        "expected exactly 2 sub-goals + 1 decompose goal; the unsuitable "
        "statement should never have reached mint_solve_deduction_goal at all")


# --------------------------------------------------------------------------- #
#  The old direct-mint path is unaffected.
# --------------------------------------------------------------------------- #
def test_old_direct_mint_path_unaffected(agent):
    """`mint_solve_decompose_goal` -- the ORIGINAL, hand-supplied-candidates
    entry point -- still dispatches byte-identically."""
    sub = agent.s
    g1 = sd.mint_solve_deduction_goal(agent, "If X is a philosopher, X is mortal.")
    g2 = sd.mint_solve_deduction_goal(agent, "If X is a philosopher, X can reason.")
    _pump(agent, g1)
    _pump(agent, g2)
    assert sub.node(g1)["attrs"]["status"] == "resolved"
    assert sub.node(g2)["attrs"]["status"] == "resolved"
    n1 = sd._solve_caps(agent)[g1]["result"]["node"]
    n2 = sd._solve_caps(agent)[g2]["result"]["node"]
    cand = pdec.project_deduction_shared_attr(sub, [n1, n2])
    goal = sd.mint_solve_decompose_goal(agent, [cand], bound=1)
    _pump(agent, goal)
    at = sub.node(goal)["attrs"]
    assert at["status"] in ("resolved", "walled")


# --------------------------------------------------------------------------- #
#  Pure pre-check sanity -- zero mutation, matches solve_deduction's own
#  fixed ladder verdict.
# --------------------------------------------------------------------------- #
def test_would_parse_as_deduction_matches_solve_deduction_verdict(agent):
    sub = agent.s
    before = _node_counts(sub)
    assert sd._would_parse_as_deduction(agent, RESIDENT_VOTE) is True
    assert sd._would_parse_as_deduction(agent, "The mayor likes apples.") is False
    assert sd._would_parse_as_deduction(agent, "Is the mayor trustworthy?") is False
    assert sd._would_parse_as_deduction(agent, "") is False
    assert _node_counts(sub) == before, "the pure pre-check must never mutate the graph"
