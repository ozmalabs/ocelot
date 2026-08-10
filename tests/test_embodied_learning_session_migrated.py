"""Focused native gates for the persistent embodied learning session."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from scripts.gen_embodied_learning_session_seed import manifest
from domains.imagination_dispatch import scan_and_imagine
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "embodied_learning_session.json"


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def _assert_integer_native(value):
    if isinstance(value, float):
        raise AssertionError(f"floating-point cognition value: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_integer_native(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_integer_native(nested)


def _session_agent():
    agent = WorldAdapter()
    # Direct native load is intentional: registry installation is owned by the
    # integration layer, while this gate verifies the manifest itself.
    agent.inner.load_seed_manifest(
        manifest_for("counterfactual_experiment"), agent.agent)
    agent.inner.load_seed_manifest(manifest(), agent.agent)
    return agent


def _open_session(agent):
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    body = agent.s.add_node("EmbodiedBodySchema", {"morphology_epoch": 1})
    world = agent.s.add_node("EmbodiedLearningWorld", {"world_epoch": 1})
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    _edge(agent, episode, "has_embodied_body_schema", body)
    _edge(agent, episode, "has_embodied_learning_world", world)
    agent.tick()
    sessions = list(agent.s.nodes("EmbodiedLearningSession"))
    assert len(sessions) == 1
    return episode, world, sessions[0]


def test_seed_is_reproducible_integer_native_and_reuses_embodied_faculties():
    generated = manifest()
    assert json.loads(SEED.read_text(encoding="utf-8")) == generated
    _assert_integer_native(generated)
    assert generated["depends_on"] == [
        "embodied_development", "embodied_motor_priors",
        "embodied_motor_program", "counterfactual_experiment",
    ]
    serialized = json.dumps(generated)
    for interface in (
        "LearningPlan", "EmbodiedSituatedDevelopmentalCapability",
        "EmbodiedMotorPrior", "EmbodiedMotorProgram", "Experiment",
        "EmbodiedResetScenario", "ParetoCandidate",
    ):
        assert interface in serialized
    assert "scalarized" not in serialized


def test_learning_session_rules_refresh_on_checkpoint_resume():
    """A live learner must not retain stale physical-authority rules."""
    from scripts import jabberwock_daemon as daemon

    assert "embodied_learning_session" in daemon._REFRESHABLE_SEEDS
    external = next(
        rule for rule in manifest()["rules"]
        if rule["name"] == "els_request_grounded_external_trial_from_declared_affordances"
    )
    assert daemon._canon_rule_body(external)


def test_session_persists_and_links_active_order_n_goal_frontier_motor_and_counterfactual():
    agent = _session_agent()
    episode, _world, session = _open_session(agent)

    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    goal = agent.s.add_node("Goal", {"status": "active"})
    frontier = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {"success_count": 0})
    motor_episode = agent.s.add_node("EmbodiedMotorEpisode", {})
    hint = agent.s.add_node("EmbodiedMotorPrior", {})
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "integer_native": 1, "predicted_forward_units": 2,
        "predicted_vertical_units": 0, "predicted_energy_units": 3,
        "predicted_peak_load_units": 1, "experience_units": 4,
    })
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_selected_learning_plan_step", step)
    _edge(agent, step, "pursues_goal", goal)
    _edge(agent, episode, "has_active_embodied_developmental_capability", frontier)
    _edge(agent, episode, "has_embodied_motor_episode", motor_episode)
    _edge(agent, motor_episode, "uses_embodied_motor_prior", hint)
    _edge(agent, motor_episode, "has_embodied_motor_program", program)

    agent.tick()
    assert agent.inner.neighbours(session, "has_learning_plan") == [plan]
    assert agent.inner.neighbours(session, "has_active_embodied_goal") == [goal]
    assert agent.s.node(goal)["attrs"]["order_n"] == 1
    assert agent.inner.neighbours(session, "has_developmental_frontier") == [frontier]
    assert agent.inner.neighbours(session, "uses_embodied_motor_hint") == [hint]
    assert agent.inner.neighbours(
        session, "has_selected_embodied_motor_program"
    ) == [program]
    trials = agent.inner.neighbours(session, "has_counterfactual_embodied_trial")
    assert len(trials) == 1
    assert agent.s.node(trials[0])["attrs"]["epistemic_scope"] == "graph_counterfactual"
    requests = agent.inner.neighbours(trials[0], "has_counterfactual_request")
    assert len(requests) == 1
    assert agent.inner.neighbours(requests[0], "focuses_on_node") == [program]
    assert "counterfactually_selects_program" in agent.s.node(requests[0])["attrs"]["hypothesis_template"]

    agent.tick()
    assert list(agent.s.nodes("EmbodiedLearningSession")) == [session]
    assert agent.inner.neighbours(session, "has_counterfactual_embodied_trial") == trials


def test_pose_and_selected_reset_scenario_gate_external_trial_then_grounded_pareto_evidence():
    agent = _session_agent()
    episode, world, session = _open_session(agent)
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 1})
    frontier = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {"success_count": 0})
    motor_episode = agent.s.add_node("EmbodiedMotorEpisode", {})
    hint = agent.s.add_node("EmbodiedMotorPrior", {})
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "integer_native": 1, "predicted_forward_units": 2,
        "predicted_vertical_units": 0, "predicted_energy_units": 3,
        "predicted_peak_load_units": 1, "experience_units": 4,
    })
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_selected_learning_plan_step", step)
    _edge(agent, step, "pursues_goal", goal)
    _edge(agent, episode, "has_active_embodied_developmental_capability", frontier)
    _edge(agent, episode, "has_embodied_motor_episode", motor_episode)
    _edge(agent, motor_episode, "uses_embodied_motor_prior", hint)
    _edge(agent, motor_episode, "has_embodied_motor_program", program)
    agent.tick()
    assert not agent.inner.neighbours(session, "has_grounded_external_trial_request")

    pose = agent.s.add_node("EmbodiedPoseAffordance", {"enabled": 1})
    reset = agent.s.add_node("EmbodiedResetRequest", {"status": "requested"})
    scenario = agent.s.add_node("EmbodiedResetScenario", {"ordinal": 0})
    connection = agent.s.add_node("EmbodiedSimulatorConnection", {
        "current_attachment": 0, "integer_native": 1,
    })
    _edge(agent, world, "has_embodied_pose_affordance", pose)
    _edge(agent, episode, "has_active_embodied_reset_request", reset)
    _edge(agent, reset, "selects_embodied_reset_scenario", scenario)
    _edge(agent, episode, "grounded_in_embodied_simulator_connection", connection)
    agent.tick()
    assert not agent.inner.neighbours(session, "has_grounded_external_trial_request")
    imagine_request = list(agent.s.nodes("ImagineRequest"))[0]
    assert scan_and_imagine(agent) == [imagine_request]
    agent.tick()
    counterfactual = agent.inner.neighbours(
        session, "has_counterfactual_embodied_trial"
    )[0]
    assert agent.s.node(counterfactual)["attrs"]["status"] == "counterfactual_done"
    imagination = agent.inner.neighbours(
        imagine_request, "produced_imagination"
    )[0]
    conclusions = agent.inner.neighbours(imagination, "imagined")
    assert any(
        agent.s.node(node)["attrs"].get("node_type")
        == "EmbodiedCounterfactualMotorProjection"
        for node in conclusions
    )
    # A detached historical episode may finish imagination but cannot command
    # the currently attached body.  The observed attachment transition—not a
    # host policy—releases physical authority.
    assert not agent.inner.neighbours(session, "has_grounded_external_trial_request")
    agent.s.set_attr(connection, "current_attachment", 1)
    agent.tick()
    requests = agent.inner.neighbours(session, "has_grounded_external_trial_request")
    assert len(requests) == 1
    request = requests[0]
    assert agent.s.node(request)["attrs"]["attempt_ordinal"] == 1
    assert agent.inner.neighbours(request, "uses_embodied_pose_affordance") == [pose]
    assert agent.inner.neighbours(request, "uses_embodied_reset_scenario") == [scenario]

    profile = agent.s.add_node("ParetoProfile", {"dimension_count": 3})
    evidence = agent.s.add_node("EmbodiedExternalTrialEvidence", {
        "grounded": 1,
        # Mechanical adapters publish the complete observed vector.  The
        # graph projects it into the active exploratory goal.
            "base_displacement_x_units": 3,
            "base_displacement_y_units": 0,
            "base_displacement_z_units": 0,
            "proprioceptive_configuration_delta_units": [1],
            "proprioceptive_configuration_observed": 1,
        "energy_cost_units": 5, "peak_load_units": 2,
    })
    _edge(agent, plan, "has_learning_decision_profile", profile)
    _edge(agent, request, "has_grounded_external_trial_evidence", evidence)
    # These are the exact mechanical provenance links published by the world
    # transducer.  The graph, not the test/adapter, decides what they mean.
    _edge(agent, evidence, "evidence_for_embodied_trial_request", request)
    _edge(agent, evidence, "measures_embodied_motor_program", program)
    _edge(agent, evidence, "under_embodied_pose_affordance", pose)
    _edge(agent, evidence, "from_embodied_reset_scenario", scenario)
    _edge(agent, evidence, "measures_goal", goal)
    agent.tick()

    assert agent.s.node(request)["attrs"]["status"] == "evidenced"
    assert agent.inner.neighbours(
        session, "has_grounded_external_trial_evidence"
    ) == [evidence]
    candidates = agent.inner.neighbours(evidence, "published_as_pareto_candidate")
    assert len(candidates) == 1
    values = agent.inner.neighbours(candidates[0], "has_pareto_value")
    assert [agent.s.node(value)["attrs"]["signed_value"] for value in values] == [3, -5, -2]

    # The same evidence now becomes a causally closed developmental receipt,
    # updates the reusable program consequence model, and re-arms a fresh
    # reset/rehearsal cycle rather than ending after one host request.
    receipts = agent.inner.neighbours(session, "has_causal_embodied_learning_receipt")
    assert len(receipts) == 1
    receipt = receipts[0]
    receipt_attrs = agent.s.node(receipt)["attrs"]
    assert receipt_attrs["development_receipt_closed"] == 1
    assert receipt_attrs["development_receipt_seq"] == 1
    # THE DEVELOPMENTAL EVIDENCE VOCABULARY IS ON THE RECEIPT.  The curriculum's
    # acquisition criteria read these; when they were absent every criterion
    # silently evaluated false through the `+ 0` null-coalescing idiom, so a
    # missing measurement was indistinguishable from a failed one and no stage
    # could ever complete.  A non-zero proprioceptive delta IS a configuration
    # change, and this path applies no external disturbance.
    assert receipt_attrs["development_configuration_changed"] == 1
    assert receipt_attrs["development_external_event"] == 0
    assert agent.inner.neighbours(
        receipt, "grounded_in_external_trial_evidence"
    ) == [evidence]
    assert agent.inner.neighbours(
        episode, "has_embodied_development_receipt"
    ) == [receipt]
    # The episode-level causal watermark is advanced in the same graph
    # transition as closure.  Re-selecting a capability later must not treat
    # this historical receipt as a fresh observation.
    assert agent.s.node(episode)["attrs"]["latest_development_receipt_seq"] == 1
    assert agent.s.node(frontier)["attrs"]["success_count"] == 1

    program_attrs = agent.s.node(program)["attrs"]
    assert (program_attrs["predicted_forward_units"],
            program_attrs["predicted_energy_units"],
            program_attrs["predicted_peak_load_units"],
            program_attrs["experience_units"]) == (3, 5, 2, 5)
    consequences = agent.inner.neighbours(program, "has_grounded_learned_consequence")
    assert len(consequences) == 1
    assert agent.inner.neighbours(
        consequences[0], "grounded_in_causal_receipt"
    ) == [receipt]
    developmental = agent.inner.neighbours(
        frontier, "has_embodied_developmental_evidence"
    )
    assert len(developmental) == 1
    assert agent.s.node(developmental[0])["attrs"]["success_units"] == 1

    checkins = agent.inner.neighbours(session, "has_embodied_learning_checkin")
    assert len(checkins) == 1
    resets = agent.inner.neighbours(episode, "has_active_embodied_reset_request")
    assert agent.s.node(reset)["attrs"]["status"] == "checkin_complete"
    assert any(agent.s.node(node)["attrs"].get("status") == "requested"
               for node in resets)
    trials = agent.inner.neighbours(session, "has_counterfactual_embodied_trial")
    assert [agent.s.node(trial)["attrs"]["status"] for trial in trials] == [
        "validated", "counterfactual_running"
    ]
    assert not [node for node in agent.s.nodes("EmbodiedExternalTrialRequest")
                if agent.s.node(node)["attrs"].get("status") == "requested"]


def test_nonprogress_receipt_retains_learning_and_recurs_without_confirming_mission():
    agent = _session_agent()
    # Load the real confirmation rule, then create its graph-owned proposal
    # seam.  A closed receipt alone must not satisfy this confirmation.
    agent.inner.load_seed_manifest(
        manifest_for("embodied_instruction_goal"), agent.agent)
    episode, world, session = _open_session(agent)
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 1})
    frontier = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {"success_count": 0})
    motor_episode = agent.s.add_node("EmbodiedMotorEpisode", {})
    hint = agent.s.add_node("EmbodiedMotorPrior", {})
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "integer_native": 1, "predicted_forward_units": 2,
        "predicted_vertical_units": 0, "predicted_energy_units": 3,
        "predicted_peak_load_units": 1, "experience_units": 4,
    })
    mission = agent.s.add_node("EmbodiedInstructionGoalProposal", {"status": "accepted"})
    mission_goal = agent.s.add_node("Goal", {"status": "active"})
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_selected_learning_plan_step", step)
    _edge(agent, step, "pursues_goal", goal)
    _edge(agent, episode, "has_active_embodied_developmental_capability", frontier)
    _edge(agent, episode, "has_embodied_motor_episode", motor_episode)
    _edge(agent, motor_episode, "uses_embodied_motor_prior", hint)
    _edge(agent, motor_episode, "has_embodied_motor_program", program)
    _edge(agent, mission, "proposes_goal", mission_goal)
    _edge(agent, mission, "requires_embodied_capability", frontier)
    agent.tick()
    confirmation = agent.inner.neighbours(
        mission, "requires_embodied_goal_confirmation")[0]
    assert agent.s.node(confirmation)["attrs"]["status"] == "awaiting_competence_receipt"

    pose = agent.s.add_node("EmbodiedPoseAffordance", {"enabled": 1})
    reset = agent.s.add_node("EmbodiedResetRequest", {"status": "requested"})
    scenario = agent.s.add_node("EmbodiedResetScenario", {"ordinal": 0})
    _edge(agent, world, "has_embodied_pose_affordance", pose)
    _edge(agent, episode, "has_active_embodied_reset_request", reset)
    _edge(agent, reset, "selects_embodied_reset_scenario", scenario)
    agent.tick()
    imagine_request = list(agent.s.nodes("ImagineRequest"))[0]
    assert scan_and_imagine(agent) == [imagine_request]
    agent.tick()
    request = agent.inner.neighbours(session, "has_grounded_external_trial_request")[0]
    evidence = agent.s.add_node("EmbodiedExternalTrialEvidence", {
        "grounded": 1,
        "base_displacement_x_units": 0,
        "base_displacement_y_units": 0,
        "base_displacement_z_units": 0,
        "proprioceptive_configuration_delta_units": [0],
        "proprioceptive_configuration_observed": 1,
        "energy_cost_units": 5, "peak_load_units": 2,
    })
    _edge(agent, request, "has_grounded_external_trial_evidence", evidence)
    _edge(agent, evidence, "evidence_for_embodied_trial_request", request)
    _edge(agent, evidence, "measures_embodied_motor_program", program)
    _edge(agent, evidence, "under_embodied_pose_affordance", pose)
    _edge(agent, evidence, "from_embodied_reset_scenario", scenario)
    _edge(agent, evidence, "measures_goal", goal)
    agent.tick()

    receipt = agent.inner.neighbours(
        session, "has_causal_embodied_learning_receipt")[0]
    assert agent.s.node(receipt)["attrs"]["success_delta_units"] == 0
    # A body that did not move reports a configuration change of 0 — the
    # honest negative, now DISTINGUISHABLE from the missing measurement that
    # previously produced the same 0 for every trial.
    assert agent.s.node(receipt)["attrs"]["development_configuration_changed"] == 0
    developmental = agent.inner.neighbours(
        frontier, "has_embodied_developmental_evidence")
    assert len(developmental) == 1
    assert agent.s.node(developmental[0])["attrs"]["success_units"] == 0
    assert agent.s.node(frontier)["attrs"]["success_count"] == 0
    assert agent.s.node(confirmation)["attrs"]["status"] == "awaiting_competence_receipt"
    assert agent.s.node(mission)["attrs"]["status"] == "accepted"

    program_attrs = agent.s.node(program)["attrs"]
    assert (program_attrs["predicted_forward_units"],
            program_attrs["predicted_energy_units"],
            program_attrs["predicted_peak_load_units"],
            program_attrs["experience_units"]) == (0, 5, 2, 5)
    assert len(agent.inner.neighbours(
        program, "has_grounded_learned_consequence")) == 1
    assert len(agent.inner.neighbours(session, "has_embodied_learning_checkin")) == 1
    trials = agent.inner.neighbours(session, "has_counterfactual_embodied_trial")
    assert [agent.s.node(trial)["attrs"]["status"] for trial in trials] == [
        "validated", "counterfactual_running"
    ]
