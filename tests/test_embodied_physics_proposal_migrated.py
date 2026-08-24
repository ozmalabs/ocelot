"""Residual-driven physics and analogy motor-proposal mining."""
from __future__ import annotations

import json

from scripts import (
    gen_embodied_development_seed,
    gen_embodied_physics_proposal_seed,
)
from substrate.world_adapter import WorldAdapter


def _edge(agent, src, edge_type, tgt):
    agent.inner.add_edge(src, edge_type, tgt)


def _assert_integer_tree(value):
    if isinstance(value, dict):
        for child in value.values():
            _assert_integer_tree(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _assert_integer_tree(child)
    else:
        assert not isinstance(value, float)


def _fixture():
    # The developmental adapter publishes the plan/capability/receipt side of
    # the otherwise domain-neutral proposal contract.
    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": (("link_count", 8),),
        "development_receipt_seq": 0,
        "integer_native": 1,
    })
    plan = agent.s.add_node("LearningPlan", {"status": "active"})
    step = agent.s.add_node("LearningPlanStep", {
        "status": "active", "evidence_spent_units": 4,
    })
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "name": "supine_prone_rolling",
        "goal": "rolling",
        "evidence_kind": "supported_half_turn",
        "desired_body_state_signature": (
            ("support_topology_change", "required"),
            ("orientation_change", "half_turn"),
            ("angular_momentum", "redirected"),
            ("effector_coupling", "compound"),
            ("height_energy_relation", "decreasing"),
            ("height_energy_relation", "increasing"),
        ),
        "desired_orientation_units": 2,
        "success_count": 0,
        "failure_count": 0,
        "integer_native": 1,
    })
    residual = agent.s.add_node("LearningPlanResidual", {
        "status": "open", "integer_native": 1, "output_authority": 0,
    })
    trajectory = agent.s.add_node("ParetoProfile", {
        "kind": "embodied_program_trajectory", "dimension_count": 4,
    })
    path = agent.s.add_node("ParetoCandidate", {
        "kind": "embodied_program_path",
        "depth": 2,
        "orientation_span_units": 2,
        "boundary_transition_count": 1,
        "energy_units": 7,
        "peak_load_units": 3,
        "replay_count": 0,
        "verified": 1,
        "integer_native": 1,
    })
    transition_a = agent.s.add_node("Node", {
        "verified": 1,
    })
    transition_b = agent.s.add_node("Node", {
        "verified": 1,
    })
    hint = agent.s.add_node("EmbodiedMotorPlanHint", {
        "name": "observed_topology:rolling_analogy",
        "output_authority": 0,
        "integer_native": 1,
    })
    stage = agent.s.add_node("EmbodiedMotorPlanHintStage", {
        "name": "observed_topology:rolling_analogy:stage",
        "signature": (("height_energy_relation", "decreasing"),),
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_learning_plan_step", step)
    _edge(agent, plan, "has_learning_plan_residual", residual)
    _edge(agent, residual, "about_learning_plan_step", step)
    _edge(agent, step, "plans_learning_capability", capability)
    _edge(agent, capability, "has_embodied_program_trajectory", trajectory)
    _edge(agent, trajectory, "has_pareto_candidate", path)
    _edge(agent, path, "contains_embodied_program_transition", transition_a)
    _edge(agent, path, "contains_embodied_program_transition", transition_b)
    _edge(agent, agent.agent, "has_embodied_motor_plan_hint_library", hint)
    _edge(agent, hint, "has_embodied_motor_plan_hint_stage", stage)
    return agent, episode, plan, step, capability, residual, path


def _settle(agent, rounds=8):
    for _ in range(rounds):
        agent.tick()
        agent.dual_process_tick()


def test_manifest_is_output_null_integer_and_rolling_publishes_physics_shape():
    manifest = gen_embodied_physics_proposal_seed.manifest()
    _assert_integer_tree(manifest)
    assert manifest["area"] == "general_cognition"
    assert manifest["depends_on"] == [
        "metacognitive_learning",
        "embodied_program_trajectory",
        "embodied_capability_bootstrap",
    ]
    assert len(gen_embodied_physics_proposal_seed.PARETO_DIMENSIONS) == 6
    assert len(manifest["nodes"]) == 1
    assert manifest["nodes"][0]["type"] == (
        "EmbodiedInverseKinematicsPrinciple"
    )
    principle = manifest["nodes"][0]["attrs"]
    assert principle["kind"] == "invert_local_forward_consequence_model"
    assert principle["analytic_jacobian_required"] == 0
    assert principle["integer_native"] == 1
    assert principle["output_authority"] == 0
    rolling = next(
        node for node in gen_embodied_development_seed.manifest()["nodes"]
        if node["attrs"]["name"] == "supine_prone_rolling"
    )
    attrs = rolling["attrs"]
    assert attrs["desired_orientation_units"] == 2
    assert ["angular_momentum", "redirected"] in attrs[
        "desired_body_state_signature"
    ]
    assert ["effector_coupling", "compound"] in attrs[
        "desired_body_state_signature"
    ]


def test_residual_mines_analogy_and_complete_verified_path_proposal():
    agent, _, _, _, capability, residual, path = _fixture()
    _settle(agent)

    questions = agent.inner.neighbours(
        residual, "has_embodied_physics_question"
    )
    assert len(questions) == 1
    question = questions[0]
    qattrs = agent.s.node(question)["attrs"]
    assert qattrs["output_authority"] == 0
    assert qattrs["trajectory_horizon"] >= 1
    analogies = agent.inner.neighbours(
        question, "has_embodied_physics_analogy"
    )
    assert len(analogies) >= 1
    assert any(
        agent.s.node(analogy)["attrs"]["covered_relation_count"] >= 1
        for analogy in analogies
    )
    assert all(
        agent.s.node(analogy)["attrs"]["output_authority"] == 0
        for analogy in analogies
    )

    proposals = agent.inner.neighbours(question, "has_motor_learning_proposal")
    assert len(proposals) == 1
    proposal = proposals[0]
    attrs = agent.s.node(proposal)["attrs"]
    assert attrs["output_authority"] == 0
    assert attrs["predicted_evidence_units"] == 2
    assert attrs["context_discrimination_units"] == 2
    assert attrs["energy_units"] == 7
    assert attrs["peak_load_units"] == 3
    candidate = agent.inner.neighbours(
        proposal, "has_motor_proposal_pareto_candidate"
    )[0]
    values = agent.inner.neighbours(candidate, "has_pareto_value")
    assert len(values) == 6
    for value in values:
        _assert_integer_tree(agent.s.node(value)["attrs"])
    assert agent.inner.neighbours(
        proposal, "proposes_embodied_program_path"
    ) == [path]
    assert agent.inner.neighbours(
        capability, "has_selected_motor_learning_proposal"
    ) == [proposal]


def test_successful_physical_receipt_promotes_shape_memory_and_resolves_residual():
    agent, episode, _, _, capability, residual, path = _fixture()
    _settle(agent)
    question = agent.inner.neighbours(
        residual, "has_embodied_physics_question"
    )[0]
    proposal = agent.inner.neighbours(
        question, "has_selected_motor_learning_proposal"
    )[0]
    _edge(
        agent, episode,
        "has_active_embodied_developmental_capability", capability,
    )
    agent.inner.set_attr(capability, "success_count", 1)
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "integer_native": 1,
    })
    _edge(agent, episode, "has_embodied_development_receipt", receipt)
    _settle(agent, 3)

    assert agent.s.node(proposal)["attrs"]["status"] == "grounded"
    assert agent.s.node(residual)["attrs"]["status"] == "resolved"
    assert agent.inner.neighbours(
        proposal, "promotes_embodied_program_path"
    ) == [path]
    memories = agent.inner.neighbours(
        proposal, "stores_as_motor_proposal_shape_memory"
    )
    assert len(memories) == 1
    memory = memories[0]
    assert agent.s.node(memories[0])["attrs"][
        "requires_local_verification"
    ] == 1
    assert agent.inner.neighbours(
        agent.agent, "has_motor_proposal_shape_memory"
    ) == [memory]
    body_shapes = agent.inner.neighbours(
        memory, "has_motor_proposal_body_shape_memory"
    )
    assert len(body_shapes) == 1

    # A later situated body can retrieve the result only as a locally
    # verifiable analogy. No path or action is copied across bodies.
    episode_2 = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": (
            ("link_count", 8), ("terminal_count", 4),
        ),
        "integer_native": 1,
    })
    plan_2 = agent.s.add_node("LearningPlan", {"status": "active"})
    step_2 = agent.s.add_node("LearningPlanStep", {"status": "active"})
    capability_2 = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "desired_body_state_signature": agent.s.node(question)["attrs"][
                "desired_body_state_signature"
            ],
            "desired_orientation_units": 2,
            "success_count": 0,
            "failure_count": 0,
            "integer_native": 1,
        },
    )
    residual_2 = agent.s.add_node("LearningPlanResidual", {
        "status": "open", "integer_native": 1, "output_authority": 0,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode_2)
    _edge(agent, episode_2, "has_self_directed_learning_plan", plan_2)
    _edge(agent, plan_2, "has_learning_plan_step", step_2)
    _edge(agent, plan_2, "has_learning_plan_residual", residual_2)
    _edge(agent, residual_2, "about_learning_plan_step", step_2)
    _edge(agent, step_2, "plans_learning_capability", capability_2)
    _settle(agent, 5)
    question_2 = agent.inner.neighbours(
        residual_2, "has_embodied_physics_question"
    )[0]
    recalled = [
        analogy for analogy in agent.inner.neighbours(
            question_2, "has_embodied_physics_analogy"
        )
        if agent.inner.neighbours(
            analogy, "retrieves_motor_proposal_shape_memory"
        ) == [memory]
    ]
    assert len(recalled) == 1
    assert agent.s.node(recalled[0])["attrs"][
        "requires_local_verification"
    ] == 1


def test_failed_physical_receipt_becomes_contextual_negative_knowledge():
    agent, episode, _, _, capability, residual, _ = _fixture()
    _settle(agent)
    question = agent.inner.neighbours(
        residual, "has_embodied_physics_question"
    )[0]
    proposal = agent.inner.neighbours(
        question, "has_selected_motor_learning_proposal"
    )[0]
    _edge(
        agent, episode,
        "has_active_embodied_developmental_capability", capability,
    )
    agent.inner.set_attr(capability, "failure_count", 1)
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "integer_native": 1,
    })
    _edge(agent, episode, "has_embodied_development_receipt", receipt)
    _settle(agent, 3)

    attrs = agent.s.node(proposal)["attrs"]
    assert attrs["status"] == "counterexample_observed"
    assert attrs["eligible"] == 0
    counterexamples = agent.inner.neighbours(
        proposal, "has_motor_proposal_counterexample"
    )
    assert len(counterexamples) == 1
    assert agent.inner.neighbours(
        agent.agent, "has_motor_proposal_counterexample"
    ) == counterexamples
    assert agent.s.node(counterexamples[0])["attrs"]["body_signature"] == (
        ("link_count", 8),
    )
    assert agent.inner.neighbours(
        question, "has_selected_motor_learning_proposal"
    ) == []


def test_physical_proposal_knowledge_survives_motor_library_round_trip():
    from scripts.jabberwock_humanoid_walk import (
        MOTOR_LIBRARY_VERSION,
        _motor_library_snapshot,
        _restore_motor_library,
    )

    source, _, _, _, _, _, _ = _fixture()
    target, _, _, _, _, _, _ = _fixture()
    memory = source.s.add_node("EmbodiedMotorProposalShapeMemory", {
        "name": "fixture_proposal_shape",
        "signature": (("orientation_change", "half_turn"),),
        "body_signature": (("link_count", 8),),
        "predicted_evidence_units": 2,
        "energy_units": 3,
        "peak_load_units": 4,
        "status": "retained",
        "requires_local_verification": 1,
        "output_authority": 0,
        "integer_native": 1,
    })
    body = source.s.add_node("EmbodiedMotorProposalBodyShapeMemory", {
        "name": "fixture_proposal_body",
        "signature": (("link_count", 8),),
        "status": "retained",
        "output_authority": 0,
        "integer_native": 1,
    })
    counterexample = source.s.add_node("MotorProposalCounterexample", {
        "body_signature": (("link_count", 8),),
        "question_signature": (("support_change", "required"),),
        "status": "retained",
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(source, source.agent, "has_motor_proposal_shape_memory", memory)
    _edge(
        source, memory,
        "has_motor_proposal_body_shape_memory", body,
    )
    _edge(
        source, source.agent,
        "has_motor_proposal_counterexample", counterexample,
    )
    humanoid_shape = source.s.add_node("HumanoidBodyShapeSignature", {
        "name": "fixture_humanoid_shape",
        "signature": (("link_count", 8),),
    })
    residual = source.s.add_node("HumanoidResidualRegimeMemory", {
        "ordinal": 0.0,
        "sample_count": 1.0,
    })
    _edge(
        source, source.agent,
        "has_humanoid_body_shape_library", humanoid_shape,
    )
    _edge(
        source, humanoid_shape,
        "stores_humanoid_residual_regime_memory", residual,
    )

    snapshot = json.loads(json.dumps(_motor_library_snapshot(source)))
    assert snapshot["version"] == MOTOR_LIBRARY_VERSION
    assert len(snapshot["body_shapes"]) == 1
    assert snapshot["body_shapes"][0]["attrs"]["name"] == (
        "fixture_humanoid_shape"
    )
    assert len(snapshot["motor_proposal_shape_memories"]) == 1
    assert len(snapshot["motor_proposal_counterexamples"]) == 1

    restored = _restore_motor_library(target, snapshot)
    assert restored["motor_proposal_shape_memory_count"] == 1
    assert restored["motor_proposal_body_shape_memory_count"] == 1
    assert restored["motor_proposal_counterexample_count"] == 1
    memories = target.inner.neighbours(
        target.agent, "has_motor_proposal_shape_memory"
    )
    assert len(memories) == 1
    assert len(target.inner.neighbours(
        memories[0], "has_motor_proposal_body_shape_memory"
    )) == 1
    restored_counterexamples = target.inner.neighbours(
        target.agent, "has_motor_proposal_counterexample"
    )
    assert len(restored_counterexamples) == 1
    assert target.s.node(restored_counterexamples[0])["attrs"][
        "integer_native"
    ] == 1


def test_unseen_compound_is_predicted_selected_then_physically_grounded():
    agent, episode, _, _, capability, residual, _ = _fixture()
    for trajectory in agent.inner.neighbours(
        capability, "has_embodied_program_trajectory"
    ):
        agent.inner.remove_edge(
            capability, "has_embodied_program_trajectory", trajectory
        )
    agent.tick()
    question = agent.inner.neighbours(
        residual, "has_embodied_physics_question"
    )[0]
    program = agent.s.add_node("HumanoidMotorProgram", {
        "status": "counterfactual_predicted",
        "counterfactual_unseen": 1,
        "member_count": 3,
        "predicted_evidence_units": 5,
        "predicted_energy_units": 4,
        "predicted_peak_load_units": 3,
        "predicted_recoverability_units": 2,
        "interaction_uncertainty_units": 3,
        "development_receipt_count": 0,
        "requires_release_envelope_guard": 1,
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(
        agent, question, "has_counterfactual_motor_program", program
    )
    physics_tasks = agent.s.add_node("SystemTwoTaskSet", {
        "area": "embodied_physics_proposal", "enabled": 1,
    })
    pareto_tasks = agent.s.add_node("SystemTwoTaskSet", {
        "area": "cognitive_pareto", "enabled": 1,
    })
    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "fixture_counterfactual_ready",
    })
    _edge(agent, escalation, "recruits_task_set", physics_tasks)
    _edge(agent, escalation, "recruits_task_set", pareto_tasks)
    _settle(agent, 4)

    proposals = agent.inner.neighbours(
        question, "has_motor_learning_proposal"
    )
    assert len(proposals) == 1
    proposal = proposals[0]
    attrs = agent.s.node(proposal)["attrs"]
    assert attrs["kind"] == "unseen_counterfactual_compound_experiment"
    assert attrs["physical_verified"] == 0
    assert attrs["component_count"] == 3
    assert attrs["requires_release_envelope_guard"] == 1
    assert agent.inner.neighbours(
        question, "has_selected_motor_learning_proposal"
    ) == [proposal]

    _edge(
        agent, episode,
        "has_active_embodied_developmental_capability", capability,
    )
    # An unrelated capability receipt cannot settle a compound that has not
    # itself crossed the domain's physical actuation/receipt boundary.
    agent.inner.set_attr(capability, "failure_count", 1)
    unrelated_receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "integer_native": 1,
    })
    _edge(
        agent, episode, "has_embodied_development_receipt",
        unrelated_receipt,
    )
    _settle(agent, 2)
    assert agent.s.node(proposal)["attrs"]["status"] == "trial_requested"

    agent.inner.set_attr(program, "physical_verified", 1)
    agent.inner.set_attr(capability, "success_count", 1)
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "integer_native": 1,
    })
    _edge(agent, episode, "has_embodied_development_receipt", receipt)
    _settle(agent, 3)
    assert agent.s.node(proposal)["attrs"]["status"] == "grounded"
    assert agent.s.node(program)["attrs"]["status"] == "grounded"
    assert agent.s.node(program)["attrs"]["physical_verified"] == 1

    rejected = agent.s.add_node("HumanoidMotorProgram", {
        "status": "counterfactual_predicted",
        "counterfactual_unseen": 1,
        "subsection_composition": 1,
        "subsection_composition_manifold_admissible": 0,
        "member_count": 2,
        "predicted_evidence_units": 5,
        "predicted_energy_units": 1,
        "predicted_peak_load_units": 1,
        "predicted_recoverability_units": 1,
        "interaction_uncertainty_units": 1,
    })
    _edge(agent, question, "has_counterfactual_motor_program", rejected)
    _settle(agent, 2)
    assert not any(
        rejected in agent.inner.neighbours(
            candidate, "proposes_counterfactual_motor_program"
        )
        for candidate in agent.inner.neighbours(
            question, "has_motor_learning_proposal"
        )
    )
