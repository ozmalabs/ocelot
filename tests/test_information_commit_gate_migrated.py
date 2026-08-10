"""Thermodynamic wait/refine/commit is graph cognition, not host policy."""
from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402
from domains.information_commitment import assess  # noqa: E402
from domains.commitment_gate import commit_gate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fresh():
    agent = WorldAdapter(seeds=())
    for name in ("cognitive_areas", "information_commitment"):
        agent.inner.load_seed_manifest(
            json.load(open(os.path.join(ROOT, "seeds", f"{name}.json"))),
            agent.agent,
        )
    return agent


def _footprint(recoverability=0.0, deleted=0, overwritten=0, externality=0):
    return {
        "recoverability": recoverability, "deleted_facts": deleted,
        "overwritten_facts": overwritten, "externality": externality,
    }


def test_high_uncertainty_makes_refinement_win():
    agent = _fresh()
    out = assess(
        agent,
        commit={
            "name": "act", "expected_goal_work": 5, "uncertainty": 5,
            "footprint": _footprint(recoverability=0.0),
        },
        wait={"preservation_value": 1},
        refine={
            "expected_information_gain": 5, "decision_relevance": 2,
            "refinement_cost": 1,
        },
    )
    assert out["decision"] == "refine" and out["authorized"]


def test_high_information_destruction_makes_wait_win():
    agent = _fresh()
    out = assess(
        agent,
        commit={
            "expected_goal_work": 4,
            "footprint": _footprint(deleted=20, recoverability=0.0),
        },
        wait={"preservation_value": 6},
        refine={"refinement_cost": 20},
    )
    assert out["decision"] == "wait"


def test_deadline_and_opportunity_cost_can_make_commit_win():
    agent = _fresh()
    out = assess(
        agent,
        commit={
            "expected_goal_work": 20, "uncertainty": 1,
            "footprint": _footprint(overwritten=1, recoverability=0.5),
        },
        wait={"preservation_value": 4, "delay_cost": 20, "opportunity_cost": 10},
        refine={
            "expected_information_gain": 2, "decision_relevance": 1,
            "refinement_cost": 15, "delay_cost": 15,
        },
    )
    assert out["decision"] == "commit"


def test_unknown_effect_footprint_fails_closed():
    agent = _fresh()
    out = assess(
        agent,
        commit={"expected_goal_work": 100},
        wait={"preservation_value": 1},
        refine={"refinement_cost": 10},
    )
    commit = out["alternatives"]["commit"]
    attrs = agent.s.node(commit)["attrs"]
    assert attrs["hard_veto"] == 1.0
    assert attrs["veto_reason"] == "unknown_effect_footprint"
    assert out["decision"] == "wait"


def test_cognitive_commit_and_hard_host_approval_are_separate():
    kwargs = dict(
        commit={
            "expected_goal_work": 20, "requires_approval": 1,
            "footprint": _footprint(recoverability=1.0),
        },
        wait={"delay_cost": 5},
        refine={"refinement_cost": 5},
    )
    refused = assess(_fresh(), **kwargs)
    assert refused["decision"] == "commit"
    assert refused["authorized"] is False
    assert refused["reason"] == "external_approval_required"

    passed = assess(_fresh(), approver="human", **kwargs)
    assert passed["decision"] == "commit" and passed["authorized"]


def test_every_resolution_leaves_a_durable_decision_record():
    agent = _fresh()
    out = assess(
        agent,
        commit={"expected_goal_work": 1, "footprint": _footprint(recoverability=1)},
        wait={"preservation_value": 2},
        refine={"refinement_cost": 3},
    )
    record = out["record"]
    assert agent.s.node(record)["type"] == "CommitDecision"
    dumped = agent.s.graph_to_dict()
    assert any(n["type"] == "CommitDecision" for n in dumped["nodes"])


def test_general_commitment_choke_point_delegates_to_graph_decision():
    agent = _fresh()
    result = commit_gate(agent, {
        "kind": "world_action",
        "thermodynamic": {
            "commit": {
                "expected_goal_work": 9,
                "footprint": _footprint(recoverability=1),
            },
            "wait": {"delay_cost": 2},
            "refine": {"refinement_cost": 2},
        },
    })
    assert result["decision"] == "commit"
    assert result["allowed"] is True
    assert result["record"] is not None


def test_busy_graph_history_cannot_alias_a_new_context_candidate_set():
    """A decided context must not poison a later unique graph selection.

    This is deliberately a persistent/busy graph rather than a fresh-agent
    happy path.  The scheduler used to cache the selector's Filter from only
    its predicate variables, omitting ``ctx`` from the Filter source.  The
    first context's candidates could then be reused for the second context,
    producing ``no_unique_decision`` despite distinct new scores.
    """
    agent = _fresh()
    historical = agent.s.add_node("DecisionContext", {
        "status": "decided", "decided": 1.0, "decision": "commit",
    })
    for kind, score in (("wait", -0.1), ("refine", 0.3), ("commit", 1.1)):
        option = agent.s.add_node("CommitOption", {
            "name": f"historical_{kind}",
            "decision_kind": kind,
            "hard_veto": 0.0,
            "chosen": 1.0 if kind == "commit" else 0.0,
            "net_value": score,
        })
        agent.inner.add_edge_unchecked(historical, "has_candidate", option)

    out = assess(
        agent,
        commit={
            "expected_goal_work": 1.25,
            "footprint": _footprint(recoverability=1.0),
        },
        wait={"delay_cost": 0.1},
        refine={
            "expected_information_gain": 0.5,
            "decision_relevance": 1.0,
            "refinement_cost": 0.2,
        },
    )

    assert {
        kind: agent.s.node(node)["attrs"]["net_value"]
        for kind, node in out["alternatives"].items()
    } == pytest.approx({"wait": -0.1, "refine": 0.3, "commit": 1.25})
    assert out["decision"] == "commit"
    assert out["authorized"] is True
