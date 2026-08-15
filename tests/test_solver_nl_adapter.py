"""docs/research/engine_substrate/SOLVER_NL_ADAPTER_PREREG.md/_RESULTS.md --
live regression + demonstration of the FIRST NL-to-structure adapter for the
six previously-unwired `solve_*` resolvers:
`solver_dispatch.mint_solve_reasoning_bridge_goal_from_text`, a front door
onto `solve_reasoning_bridge`'s `deduction_to_can` direction.

Every test parses a REAL, genuine declarative English sentence through the
UNMODIFIED general reading pipeline (`reading_collapse.read_clause`), mints
a real Goal via the UNCHANGED `mint_solve_reasoning_bridge_goal`, and pumps
it through the SAME `qd_bind_resolver` dispatch + `solve_reasoning_bridge`
resolver `tests/test_solver_dispatch_migrated.py` already exercises -- never
a stub, never a hand-injected predication dict. Correctness is checked by
hand against the CAN network's own `external_field` state (the documented
`h_i <- h_i + alpha*evidence` formula, `runners/dsl/src/can_ops.rs`
`apply_evidence_h`), not merely `status == "resolved"`.
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
from worlds import bigville_can_beliefs as bcb              # noqa: E402


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


def _resident_mt(agent, index=0):
    """A REAL Bigville resident CAN belief network -- byte-identical
    construction to `tests/test_solver_dispatch_migrated.py::_resident_mt`
    (the SAME precedent P13b established in SOLVER_MATH_BOUNDARY_RESULTS.md
    for a hand-built network fed to a specific resolver)."""
    native = agent.inner
    bcb.install_productions(native)
    residents = json.load(open(os.path.join(ROOT, "seeds", "bigville_cast100.json")))["residents"]
    built = bcb.build_resident_can_mt(native, residents[index])
    native.set_attr(built["mt_node"], "discrete_mode", "3state")
    native.set_attr(built["mt_node"], "can_tick", 0)
    return built


# --------------------------------------------------------------------------- #
#  SUCCESS -- a real sentence about a real Bigville resident, verified
#  correct by hand against the CAN network's own external_field state.
# --------------------------------------------------------------------------- #
def test_real_sentence_mints_and_resolves_via_unchanged_dispatch(agent):
    built = _resident_mt(agent, 0)
    assert agent.s.node(built["resident_node"])["attrs"]["name"] == "Verity Peaseblossom"
    concept = built["concepts"]["world_safe"]
    before = agent.s.node(concept)["attrs"].get("external_field", 0.0)

    goal = sd.mint_solve_reasoning_bridge_goal_from_text(
        agent, "Verity Peaseblossom is world safe.")
    assert goal is not None
    at_ = agent.s.node(goal)["attrs"]
    assert at_["kind"] == "solve_reasoning_bridge"
    assert at_["direction"] == "deduction_to_can"
    assert at_["entity"] == "verity_peaseblossom"
    assert at_["attr"] == "world_safe"
    assert at_["status"] == "pending"

    _pump(agent, goal)

    at_ = agent.s.node(goal)["attrs"]
    assert at_["status"] == "resolved", at_.get("note")
    # proof the UNCHANGED qd_bind_resolver JOIN did the dispatch, not this test.
    resolvers = agent.inner.neighbours(goal, "resolve_with")
    assert resolvers and agent.s.node(resolvers[0])["attrs"]["name"] == "solve_reasoning_bridge"
    assert at_["answer"]["applied"] is True
    assert at_["answer"]["entity"] == "verity_peaseblossom"
    assert at_["answer"]["attr"] == "world_safe"

    # CORRECTNESS BY HAND -- not just "resolved without erroring": the
    # network's external_field moved by EXACTLY alpha(1.0) * evidence(+1.0),
    # the documented apply_evidence_h formula.
    after = agent.s.node(concept)["attrs"].get("external_field", 0.0)
    assert after - before == pytest.approx(1.0)


def test_real_sentence_negative_topic_unaffected(agent):
    """Applying evidence to ONE concept via a real sentence does not perturb
    a DIFFERENT concept in the same network -- the evidence is targeted, not
    a network-wide nudge."""
    built = _resident_mt(agent, 1)
    other = built["concepts"]["self_worth"]
    before = agent.s.node(other)["attrs"].get("external_field", 0.0)
    goal = sd.mint_solve_reasoning_bridge_goal_from_text(
        agent, "%s is claim credible." % agent.s.node(built["resident_node"])["attrs"]["name"])
    assert goal is not None
    _pump(agent, goal)
    assert agent.s.node(goal)["attrs"]["status"] == "resolved"
    after = agent.s.node(other)["attrs"].get("external_field", 0.0)
    assert after == before


# --------------------------------------------------------------------------- #
#  HONEST WALL (resolver-side) -- a real sentence whose extracted attr does
#  not name any Concept in the resident's own CAN network.
# --------------------------------------------------------------------------- #
def test_real_sentence_with_no_matching_concept_walls_honestly(agent):
    built = _resident_mt(agent, 2)
    name = agent.s.node(built["resident_node"])["attrs"]["name"]
    goal = sd.mint_solve_reasoning_bridge_goal_from_text(agent, "%s is honest." % name)
    assert goal is not None
    at_ = agent.s.node(goal)["attrs"]
    assert at_["entity"] == name.lower().replace(" ", "_")
    assert at_["attr"] == "honest"

    _pump(agent, goal)

    at_ = agent.s.node(goal)["attrs"]
    assert at_["status"] == "walled"
    assert "gap_key" in at_
    assert "honest" in at_["gap_key"]
    assert "holds no Concept named" in at_["note"]


# --------------------------------------------------------------------------- #
#  HONEST DECLINE (adapter-side) -- unsuitable real input mints NOTHING,
#  mirroring the Bug 1 fix precedent (SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md):
#  an adapter that mints garbage from unsuitable input repeats that mistake.
# --------------------------------------------------------------------------- #
def test_question_shaped_sentence_declines_cleanly(agent):
    assert sd.mint_solve_reasoning_bridge_goal_from_text(
        agent, "Is Verity Peaseblossom trustworthy?") is None


def test_non_property_event_sentence_declines_cleanly(agent):
    assert sd.mint_solve_reasoning_bridge_goal_from_text(
        agent, "Verity Peaseblossom likes apples.") is None


def test_empty_and_whitespace_statement_declines_cleanly(agent):
    assert sd.mint_solve_reasoning_bridge_goal_from_text(agent, "") is None
    assert sd.mint_solve_reasoning_bridge_goal_from_text(agent, "   ") is None
    assert sd.mint_solve_reasoning_bridge_goal_from_text(agent, None) is None


def test_decline_mints_no_goal_node_at_all(agent):
    """Not merely 'returns None' -- genuinely no Goal node is created, so a
    caller cannot accidentally dispatch a half-formed one."""
    before = len(agent.s.nodes("Goal"))
    sd.mint_solve_reasoning_bridge_goal_from_text(agent, "Is Verity Peaseblossom trustworthy?")
    sd.mint_solve_reasoning_bridge_goal_from_text(agent, "Verity Peaseblossom likes apples.")
    after = len(agent.s.nodes("Goal"))
    assert after == before


# --------------------------------------------------------------------------- #
#  The resolver's own internals are untouched -- an explicit-attrs Goal
#  minted the OLD way (mint_solve_reasoning_bridge_goal, no text) still
#  produces byte-identical dispatch behaviour.
# --------------------------------------------------------------------------- #
def test_old_direct_mint_path_unaffected(agent):
    built = _resident_mt(agent, 3)
    name = agent.s.node(built["resident_node"])["attrs"]["name"]
    entity = name.lower().replace(" ", "_")
    goal = sd.mint_solve_reasoning_bridge_goal(
        agent, "deduction_to_can", entity=entity, attr="trust_mayor", positive=True)
    _pump(agent, goal)
    at_ = agent.s.node(goal)["attrs"]
    assert at_["status"] == "resolved"
    assert at_["answer"]["applied"] is True
