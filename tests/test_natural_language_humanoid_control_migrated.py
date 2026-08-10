"""Natural language drives one graph-owned humanoid learning cycle."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import jabberwock_daemon as daemon  # noqa: E402
from domains.imagination_dispatch import scan_and_imagine  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def test_language_mission_rehearses_then_requests_and_learns_from_grounded_trial():
    agent = WorldAdapter(seeds=(
        "comprehend_instruction", "embodied_instruction_goal",
        "embodied_learning_session",
    ))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 1,
    })
    body = agent.s.add_node("EmbodiedBodySchema", {
        "morphology": "humanoid", "morphology_epoch": 1,
    })
    world = agent.s.add_node("EmbodiedLearningWorld", {"world_epoch": 1})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "goal": "locomotion", "success_count": 0,
        "name": "supported stepping",
    })
    plan = agent.s.add_node("LearningPlan", {"status": "active"})
    step = agent.s.add_node("LearningPlanStep", {"status": "active"})
    goal = agent.s.add_node("Goal", {
        "status": "active", "kind": "supported_stepping",
    })
    profile = agent.s.add_node("ParetoProfile", {"dimension_count": 3})
    motor_episode = agent.s.add_node("EmbodiedMotorEpisode", {})
    hint = agent.s.add_node("EmbodiedMotorPrior", {})
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "status": "ready", "token": "tonic", "integer_native": 1,
        "predicted_forward_units": 2, "predicted_vertical_units": 0,
        "predicted_energy_units": 3, "predicted_peak_load_units": 1,
        "experience_units": 4,
    })
    pose = agent.s.add_node("EmbodiedPoseAffordance", {"enabled": 1})
    reset = agent.s.add_node("EmbodiedResetRequest", {"status": "requested"})
    scenario = agent.s.add_node("EmbodiedResetScenario", {"ordinal": 0})
    for source, edge_type, target in (
        (agent.agent, "has_embodied_development_episode", episode),
        (episode, "has_embodied_body_schema", body),
        (episode, "has_embodied_learning_world", world),
            (episode, "has_active_embodied_developmental_capability", capability),
            (episode, "has_self_directed_learning_plan", plan),
            # Selected edges identify the current frontier; the plan/step
            # ownership edges retain where that frontier came from. Mission
            # formation requires both so language cannot invent a capability
            # outside the developmental plan.
            (plan, "has_learning_plan_step", step),
            (plan, "has_selected_learning_plan_step", step),
            (step, "plans_learning_capability", capability),
            (step, "pursues_goal", goal),
        (plan, "has_learning_decision_profile", profile),
        (episode, "has_embodied_motor_episode", motor_episode),
        (motor_episode, "uses_embodied_motor_prior", hint),
        (motor_episode, "has_embodied_motor_program", program),
        (world, "has_embodied_pose_affordance", pose),
        (episode, "has_active_embodied_reset_request", reset),
        (reset, "selects_embodied_reset_scenario", scenario),
    ):
        _edge(agent, source, edge_type, target)
    for name in ("humanoid", "forward"):
        concept = agent.s.add_node("Concept", {"name": name})
        _edge(agent, agent.agent, "knows_concept", concept)

    text = "Walk the humanoid forward."
    agent.converse(text, speech_act=agent.classify_speech_act(text))
    agent.tick()

    interpretation = list(agent.s.nodes("InstructionInterpretation"))[0]
    assert agent.s.node(interpretation)["attrs"]["status"] == "verified"
    mission = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))[0]
    assert agent.s.node(mission)["attrs"]["status"] == "accepted"
    session = list(agent.s.nodes("EmbodiedLearningSession"))[0]
    rehearsal = agent.inner.neighbours(
        session, "has_counterfactual_embodied_trial"
    )[0]
    assert agent.s.node(rehearsal)["attrs"]["status"] == "counterfactual_running"
    assert not list(agent.s.nodes("EmbodiedExternalTrialRequest"))

    imagine_request = list(agent.s.nodes("ImagineRequest"))[0]
    assert scan_and_imagine(agent) == [imagine_request]
    agent.tick()
    assert agent.s.node(rehearsal)["attrs"]["status"] == "counterfactual_done"
    external = list(agent.s.nodes("EmbodiedExternalTrialRequest"))[0]

    daemon._ensure_supervisory_scheduler(agent)
    agent.tick()
    hosts = [node for node in agent.s.nodes("HostActionRequest")
             if agent.s.node(node)["attrs"].get("action") == "embodied_trial"]
    assert hosts, {
        "external": agent.s.node(external)["attrs"],
        "host_actions": [agent.s.node(node)["attrs"]
                         for node in agent.s.nodes("HostActionRequest")],
    }
    host = hosts[0]
    assert agent.s.node(host)["attrs"]["status"] == "requested"

    def transduce(observed, selected):
        assert selected == external
        evidence = observed.s.add_node("EmbodiedExternalTrialEvidence", {
            "grounded": 1,
            "base_displacement_x_units": 2,
            "base_displacement_y_units": 0,
            "base_displacement_z_units": 0,
            "proprioceptive_configuration_delta_units": [2],
            "proprioceptive_configuration_observed": 1,
            "energy_cost_units": 3, "peak_load_units": 1,
        })
        _edge(observed, external, "has_grounded_external_trial_evidence", evidence)

    state = daemon.DaemonState(agent, "test")
    state.embodied_trial_executor = transduce
    assert daemon._execute_host_action_requests(state) == 1
    agent.tick()

    assert agent.s.node(external)["attrs"]["status"] == "evidenced"
    assert len(agent.inner.neighbours(
        session, "has_grounded_external_trial_evidence"
    )) == 1
    status = daemon.embodied_learning_status(agent)
    assert status["missions"][0]["attrs"]["status"] == "accepted"
    assert status["sessions"][0]["external_evidence"]
