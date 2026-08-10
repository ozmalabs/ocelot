"""Graph-native bridge: verified language proposes; receipts confirm."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.gen_embodied_instruction_goal_seed import manifest
from scripts.gen_embodied_body_ingest_seed import manifest as body_manifest
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "embodied_instruction_goal.json"


def _edge(agent, src, edge_type, tgt):
    agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _attrs(agent, node_type):
    return [agent.s.node(node)["attrs"] for node in agent.s.nodes(node_type)]


def _fresh():
    agent = WorldAdapter(seeds=(
        "instruction_understanding", "cognitive_supervision",
        "humanoid_developmental_curriculum",
    ))
    agent.inner.load_seed_manifest(manifest(), agent.agent)
    return agent


def _verified_instruction(agent, *, local_grounded=1):
    interpretation = agent.s.add_node("InstructionInterpretation", {
        "status": "verified", "local_grounded": local_grounded,
        "predicate": "walk", "content": "forward",
    })
    check = agent.s.add_node("UnderstandingCheck", {"status": "verified"})
    message = agent.s.add_node("Message", {"text": "walk forward"})
    _edge(agent, agent.agent, "holds_interpretation", interpretation)
    _edge(agent, interpretation, "has_understanding_check", check)
    _edge(agent, interpretation, "interprets", message)
    return interpretation


def _situated_capability(agent):
    connection = agent.s.add_node("EmbodiedSimulatorConnection", {
        "attachment_event_ordinal": 1, "current_attachment": 1,
    })
    _edge(agent, agent.agent, "has_embodied_simulator_connection", connection)
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    session = agent.s.add_node("EmbodiedLearningSession", {"trial_seq": 0})
    plan = agent.s.add_node("LearningPlan", {"status": "active"})
    step = agent.s.add_node("LearningPlanStep", {"status": "active"})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "goal": "locomotion", "success_count": 0,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    _edge(agent, episode, "grounded_in_embodied_simulator_connection", connection)
    _edge(agent, episode, "has_embodied_learning_session", session)
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, episode, "has_active_embodied_developmental_capability", capability)
    _edge(agent, plan, "has_learning_plan_step", step)
    _edge(agent, plan, "has_selected_learning_plan_step", step)
    _edge(agent, step, "plans_learning_capability", capability)
    return episode, capability


def test_seed_is_reproducible_integer_native_and_output_null():
    generated = manifest()
    assert json.loads(SEED.read_text(encoding="utf-8")) == generated

    def visit(value):
        assert not isinstance(value, float)
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    visit(generated)
    text = json.dumps(generated).lower()
    assert "llm" in text and "local_grounded" in text
    assert "joint" not in text and "direct_command" not in text


def test_verified_local_instruction_proposes_an_order_n_humanoid_goal_tree():
    agent = _fresh()
    interpretation = _verified_instruction(agent)
    _situated_capability(agent)
    agent.tick()

    proposals = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))
    assert len(proposals) == 1
    proposal = proposals[0]
    assert agent.s.node(proposal)["attrs"] == {
        "status": "accepted", "order_n": 2, "predicate": "walk",
        "content": "forward", "integer_native": 1, "output_authority": 0,
        "confirmation_required": 1, "baseline_trial_seq": 0,
    }
    assert agent.inner.neighbours(proposal, "derives_from_interpretation") == [interpretation]
    selected_capability = agent.inner.neighbours(
        proposal, "requires_embodied_capability"
    )
    assert len(selected_capability) == 1
    assert agent.s.node(selected_capability[0])["attrs"]["status"] == "active"


def test_one_interpretation_scopes_mission_to_unique_current_attachment():
    agent = _fresh()
    interpretation = _verified_instruction(agent)
    older_episode, _older_capability = _situated_capability(agent)
    newer_episode, newer_capability = _situated_capability(agent)
    older_connection = agent.inner.neighbours(
        older_episode, "grounded_in_embodied_simulator_connection"
    )[0]
    newer_connection = agent.inner.neighbours(
        newer_episode, "grounded_in_embodied_simulator_connection"
    )[0]
    agent.s.set_attr(older_connection, "attachment_event_ordinal", 1)
    agent.s.set_attr(older_connection, "current_attachment", 0)
    agent.s.set_attr(newer_connection, "attachment_event_ordinal", 2)
    agent.s.set_attr(newer_connection, "current_attachment", 1)
    agent.tick()
    proposals = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))
    assert len(proposals) == 1
    proposal = proposals[0]
    assert agent.inner.neighbours(
        proposal, "derives_from_interpretation"
    ) == [interpretation]
    root = agent.inner.neighbours(proposal, "proposes_goal")[0]
    assert agent.inner.neighbours(root, "supervises_embodied_episode") == [newer_episode]

    root = agent.inner.neighbours(proposal, "proposes_goal")[0]
    root_attrs = agent.s.node(root)["attrs"]
    assert root_attrs["kind"] == "humanoid_embodied_instruction"
    assert root_attrs["status"] == "active"
    assert root_attrs["order_n"] == 2
    assert root_attrs["output_authority"] == 0
    children = agent.inner.neighbours(root, "has_subgoal")
    assert {"enact_embodied_capability", "verify_embodied_receipt"} <= {
        agent.s.node(child)["attrs"]["kind"] for child in children
    }
    mission_children = [child for child in children if agent.s.node(child)["attrs"].get(
        "kind"
    ) in {"enact_embodied_capability", "verify_embodied_receipt"}]
    assert all(agent.s.node(child)["attrs"]["order_n"] == 1
               for child in mission_children)
    confirmation = agent.inner.neighbours(
        proposal, "requires_embodied_goal_confirmation"
    )[0]
    assert agent.s.node(confirmation)["attrs"]["status"] == "awaiting_competence_receipt"


@pytest.mark.parametrize(("ordinals", "expected"), [
    ((1, 2, 3), (0, 0, 1)),
    ((1, 3, 3), (0, 0, 0)),
    ((1,), (1,)),
])
def test_attachment_currentness_requires_a_unique_global_maximum(ordinals, expected):
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(body_manifest(), agent.agent)
    connections = []
    for ordinal in ordinals:
        connection = agent.s.add_node("EmbodiedSimulatorConnection", {
            "attachment_event_ordinal": ordinal,
        })
        _edge(agent, agent.agent, "has_embodied_simulator_connection", connection)
        connections.append(connection)
    agent.tick()
    assert tuple(agent.s.node(connection)["attrs"].get("current_attachment", 0)
                 for connection in connections) == expected


def test_only_a_later_closed_embodied_receipt_confirms_the_goal():
    agent = _fresh()
    _verified_instruction(agent)
    episode, _ = _situated_capability(agent)
    agent.tick()
    proposal = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))[0]
    capability = agent.inner.neighbours(
        proposal, "requires_embodied_capability"
    )[0]
    root = agent.inner.neighbours(proposal, "proposes_goal")[0]

    # The mission must first adopt a selected developmental subgoal, then a
    # post-mission request pursuing that exact goal can carry its receipt.
    plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")[0]
    step = agent.inner.neighbours(plan, "has_selected_learning_plan_step")[0]
    developmental = agent.s.add_node("Goal", {"status": "active"})
    _edge(agent, step, "pursues_goal", developmental)
    agent.tick()
    request = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "attempt_ordinal": 1,
    })
    _edge(agent, agent.inner.neighbours(
        episode, "has_embodied_learning_session"
    )[0], "has_grounded_external_trial_request", request)
    _edge(agent, request, "pursues_goal", developmental)
    agent.tick()

    agent.tick()
    assert agent.s.node(root)["attrs"]["status"] == "active"

    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "development_receipt_closed": 1,
        "success_delta_units": 1,
    })
    _edge(agent, request, "has_embodied_learning_trial_receipt", receipt)
    # The session rule's write, simulated. Measured progress moved off
    # `success_count` on 2026-08-07: that attribute is the developmental
    # CRITERION's (what mastery is judged on), and mission confirmation was
    # always a delta test over the world's measured progress instead.
    agent.inner.set_attr(capability, "positive_progress_count", 1)
    agent.tick()

    confirmation = agent.inner.neighbours(
        proposal, "requires_embodied_goal_confirmation"
    )[0]
    assert agent.s.node(confirmation)["attrs"]["status"] == "confirmed"
    assert agent.inner.neighbours(confirmation, "grounded_in_embodied_receipt") == [receipt]
    assert agent.s.node(proposal)["attrs"]["status"] == "confirmed"
    assert agent.s.node(root)["attrs"]["status"] == "active"
    assert agent.s.node(root)["attrs"]["progress_units"] == 1
    assert agent.s.node(root)["attrs"]["resolved_units"] == 1


def test_mission_retains_ordered_post_baseline_receipts_until_one_is_positive():
    """A zero-yield probe is evidence, never a one-shot mission terminator."""
    agent = _fresh()
    _verified_instruction(agent)
    episode, _ = _situated_capability(agent)
    agent.tick()
    proposal = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))[0]
    capability = agent.inner.neighbours(
        proposal, "requires_embodied_capability"
    )[0]
    plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")[0]
    step = agent.inner.neighbours(plan, "has_selected_learning_plan_step")[0]
    developmental = agent.s.add_node("Goal", {"status": "active"})
    _edge(agent, step, "pursues_goal", developmental)
    agent.tick()
    session = agent.inner.neighbours(episode, "has_embodied_learning_session")[0]

    zero_request = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "attempt_ordinal": 1,
    })
    zero_receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "development_receipt_closed": 1, "success_delta_units": 0,
    })
    _edge(agent, session, "has_grounded_external_trial_request", zero_request)
    _edge(agent, zero_request, "pursues_goal", developmental)
    _edge(agent, zero_request, "has_embodied_learning_trial_receipt", zero_receipt)
    agent.tick()

    confirmation = agent.inner.neighbours(
        proposal, "requires_embodied_goal_confirmation"
    )[0]
    assert agent.s.node(confirmation)["attrs"]["status"] == "awaiting_competence_receipt"
    assert agent.inner.neighbours(
        confirmation, "has_mission_bound_embodied_receipt"
    ) == [zero_receipt]

    positive_request = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "attempt_ordinal": 2,
    })
    positive_receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "development_receipt_closed": 1, "success_delta_units": 1,
    })
    _edge(agent, session, "has_grounded_external_trial_request", positive_request)
    _edge(agent, positive_request, "pursues_goal", developmental)
    _edge(agent, positive_request, "has_embodied_learning_trial_receipt", positive_receipt)
    # The session rule's write, simulated. Measured progress moved off
    # `success_count` on 2026-08-07: that attribute is the developmental
    # CRITERION's (what mastery is judged on), and mission confirmation was
    # always a delta test over the world's measured progress instead.
    agent.inner.set_attr(capability, "positive_progress_count", 1)
    agent.tick()

    assert agent.inner.neighbours(
        proposal, "has_embodied_mission_trial_request"
    ) == [zero_request, positive_request]
    assert agent.inner.neighbours(
        confirmation, "has_mission_bound_embodied_receipt"
    ) == [zero_receipt, positive_receipt]
    assert agent.s.node(confirmation)["attrs"]["status"] == "confirmed"
    assert agent.inner.neighbours(
        confirmation, "grounded_in_embodied_receipt"
    ) == [positive_receipt]


def test_active_mission_adopts_graph_selected_developmental_goal_not_actuators():
    agent = _fresh()
    _verified_instruction(agent)
    episode, _ = _situated_capability(agent)
    agent.tick()
    mission = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))[0]
    root = agent.inner.neighbours(mission, "proposes_goal")[0]
    plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")[0]
    step = agent.inner.neighbours(plan, "has_selected_learning_plan_step")[0]
    developmental = agent.s.add_node("Goal", {
        "status": "active", "kind": "prone_support", "order_n": 1,
    })
    _edge(agent, step, "pursues_goal", developmental)
    agent.tick()
    assert developmental in agent.inner.neighbours(root, "has_subgoal")
    assert not list(agent.s.nodes("MotorCommand"))


def test_llm_teacher_evidence_is_not_authority_for_humanoid_goal_proposal():
    agent = _fresh()
    interpretation = _verified_instruction(agent, local_grounded=0)
    _, _ = _situated_capability(agent)
    request = agent.s.add_node("TeacherRequest", {"teacher_tier": "llm"})
    evidence = agent.s.add_node("TeacherEvidence", {"verdict": "supported"})
    _edge(agent, interpretation, "seeks_teacher", request)
    _edge(agent, request, "has_evidence", evidence)
    agent.tick()

    assert not _attrs(agent, "EmbodiedInstructionGoalProposal")
    assert not [attrs for attrs in _attrs(agent, "Goal")
                if attrs.get("kind") == "humanoid_embodied_instruction"]
