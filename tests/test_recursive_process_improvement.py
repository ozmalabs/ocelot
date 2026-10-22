"""P15.04 persistent graph-owned recursive operator lifecycle."""
from __future__ import annotations

import pytest
pytest.importorskip("substrate_rs")

from evaluation.process_mastery.harness import Agent

SEEDS = ("process_laws", "process_proof_adoption", "invention_operator_authorship",
         "recursive_process_improvement")


def _agent(*, budget=100000.0):
    return Agent(extra_seeds=SEEDS, policy_overrides={
        "InventionOperatorAuthorshipPolicy": {"enabled": 1.0, "max_resource_work": 32},
        "RecursiveProcessImprovementPolicy": {"enabled": 1.0, "max_generations": 3.0,
                                               "generation_work_cap": 100000.0},
    }, budget={"enabled": 1.0, "capacity": budget, "remaining": budget,
               "refill_per_epoch": 0.0, "last_refill_epoch": -100.0})


def _qualify(agent, *, name="commutator_square_v1", proof_failures=0):
    req = agent.s.add_node("OperatorCompositionRequest", {
        "name": "request", "status": "draft", "recipe": "commutator_square",
        "left_operator": "commutator", "right_operator": "commutator",
        "candidate_name": name,
    })
    agent.s.add_edge(agent.ag, "has_operator_composition_request", req, {})
    for _ in range(12): agent.s.tick(4000)
    candidate = agent.nodes("CandidateOperator", name=name)[0]
    for key, value in {"development_yield": 8, "parent_development_yield": 7,
                       "invariant_checks": 20, "parent_invariant_checks": 20,
                       "proof_failures": proof_failures, "candidate_work": 12,
                       "status": "measured"}.items():
        agent.s.set_attr(candidate, key, value)
    for _ in range(12): agent.s.tick(4000)
    return candidate


def _approve(agent, candidate):
    approval = agent.s.add_node("OperatorPromotionApproval", {
        "status": "approved", "approval_kind": "human",
        "candidate_name": "commutator_square_v1",
        "criteria_digest": "pmb-v1-frozen-criteria",
    })
    agent.s.add_edge(agent.ag, "has_promotion_approval", approval, {})
    for _ in range(12): agent.s.tick(4000)
    return approval


def _generations(agent):
    return [n for n in agent.s.nodes()
            if agent.s.node(n)["type"] == "RecursiveProcessGeneration"]


def test_generation_has_complete_ancestry():
    agent = _agent()
    candidate = _qualify(agent)
    children = [g for g in _generations(agent)
                if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_square_v1"]
    assert len(children) == 1
    child = children[0]
    assert agent.s.node(child)["attrs"]["status"] == "pending_approval"
    assert agent.s.neighbours(child, "parent_generation")
    assert agent.s.neighbours(child, "generation_candidate") == [candidate]
    assert agent.s.node(child)["attrs"]["budget_remaining"] == 100000.0
    _approve(agent, candidate)
    assert agent.s.node(child)["attrs"]["status"] == "active"
    assert len(agent.s.neighbours(child, "generation_operator")) == 1


def test_no_human_authored_operator_in_claimed_generation():
    agent = _agent()
    candidate = _qualify(agent)
    _approve(agent, candidate)
    child = next(g for g in _generations(agent)
                 if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_square_v1")
    assert agent.s.node(candidate)["attrs"]["authoring"] == "native_graph_rule"
    assert agent.s.node(child)["attrs"]["human_authored_operator_count"] == 0.0
    assert agent.s.node(child)["attrs"]["autonomy_claim"] == "valid"


def test_failed_generation_not_promoted():
    agent = _agent()
    candidate = _qualify(agent, proof_failures=1)
    assert agent.s.node(candidate)["attrs"]["status"] == "rejected"
    assert not agent.nodes("InventionOperator", name="commutator_square_v1")
    assert not [g for g in _generations(agent)
                if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_square_v1"]


def test_operator_is_suspended_when_shared_budget_denies_generation():
    agent = _agent(budget=10.0)
    candidate = _qualify(agent)
    _approve(agent, candidate)
    operators = agent.nodes("InventionOperator", name="commutator_square_v1")
    assert len(operators) == 1
    assert agent.s.node(operators[0])["attrs"]["status"] == "suspended"
    assert not [g for g in _generations(agent)
                if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_square_v1"]


def test_invariant_failure_rolls_back_active_generation():
    agent = _agent()
    candidate = _qualify(agent)
    _approve(agent, candidate)
    child = next(g for g in _generations(agent)
                 if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_square_v1")
    audit = agent.s.add_node("GenerationInvariantAudit", {
        "status": "failed", "proof_binding": False, "adoption_valid": True,
        "grounding_valid": True, "action_safe": True,
    })
    agent.s.add_edge(child, "has_generation_audit", audit, {})
    for _ in range(8): agent.s.tick(4000)
    assert agent.s.node(child)["attrs"]["status"] == "rolled_back"
    assert agent.s.node(child)["attrs"]["autonomy_claim"] == "invalid"
    assert agent.s.neighbours(child, "rollback_to_generation")
    assert agent.s.node(candidate)["attrs"]["status"] == "promoted"
    assert agent.s.node(agent.s.neighbours(child, "generation_operator")[0])["attrs"]["status"] == "suspended"


def test_restart_keeps_same_generation_budget():
    agent = _agent()
    candidate = _qualify(agent)
    child = next(g for g in _generations(agent)
                 if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_square_v1")
    agent.s.set_attr(child, "budget_remaining", 87654.0)
    snapshot = agent.native.graph_to_dict()
    restored = _agent()
    restored.native.graph_from_dict(snapshot)
    same = next(g for g in _generations(restored)
                if restored.s.node(g)["attrs"].get("candidate_name") == "commutator_square_v1")
    assert restored.s.node(same)["attrs"]["budget_initial"] == 100000.0
    assert restored.s.node(same)["attrs"]["budget_remaining"] == 87654.0
    assert restored.s.neighbours(same, "generation_candidate") == [candidate]
    restored.s.tick(4000)
    assert restored.s.node(same)["attrs"]["budget_remaining"] == 87654.0
