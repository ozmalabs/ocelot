"""Graph-native bootstrap from opaque integer body affordances."""
from __future__ import annotations

import json
import sys
import copy
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from gen_embodied_motor_bootstrap_seed import manifest  # noqa: E402
from scripts.gen_embodied_learning_session_seed import manifest as session_manifest  # noqa: E402
from domains.imagination_dispatch import scan_and_imagine  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


SEED = ROOT / "seeds" / "embodied_motor_bootstrap.json"


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


def test_retained_reselection_cannot_oscillate_with_current_counterfactual():
    """Historical coordination loses authority if the old program is current."""
    motor_rule = next(
        rule for rule in manifest()["rules"]
        if rule["name"]
        == "emb_supersede_undispatched_counterfactual_after_coordination_recollapse"
    )
    rehearsal_rule = next(
        rule for rule in session_manifest()["rules"]
        if rule["name"] == "els_request_counterfactual_trial_before_external_trial"
    )
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest({
        "id": "retained_reselection_oscillation_gate",
        "rules": [motor_rule, rehearsal_rule],
    }, agent.agent)

    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    session = agent.s.add_node("EmbodiedLearningSession", {})
    motor_episode = agent.s.add_node("EmbodiedMotorEpisode", {})
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {})
    context = agent.s.add_node("EmbodiedMotorCoordinationContext", {})
    reselection = agent.s.add_node("EmbodiedMotorCoordinationReselection", {})
    old_selection = agent.s.add_node("EmbodiedMotorBootstrapSelection", {})
    current_selection = agent.s.add_node("EmbodiedMotorBootstrapSelection", {})
    program = agent.s.add_node("EmbodiedMotorProgram", {})
    goal = agent.s.add_node("Goal", {"status": "active"})
    counterfactual = agent.s.add_node(
        "Experiment", {"status": "counterfactual_running"})
    for source, edge, target in (
        (episode, "has_embodied_learning_session", session),
        (episode, "has_embodied_motor_episode", motor_episode),
        (episode, "has_active_embodied_developmental_capability", capability),
        (capability, "has_embodied_motor_coordination_context", context),
        (context, "has_coordination_reselection", reselection),
        (reselection, "supersedes_embodied_motor_selection", old_selection),
        (old_selection, "selects_embodied_motor_program", program),
        (motor_episode, "has_embodied_motor_bootstrap_selection", current_selection),
        (current_selection, "selects_embodied_motor_program", program),
        (session, "has_active_embodied_goal", goal),
        (session, "has_selected_embodied_motor_program", program),
        (session, "has_counterfactual_embodied_trial", counterfactual),
        (counterfactual, "tests_embodied_motor_program", program),
    ):
        _edge(agent, source, edge, target)

    before = set(agent.s.nodes("Experiment"))
    assert agent.tick(max_steps=20) < 20
    assert agent.inner.neighbours(
        session, "has_counterfactual_embodied_trial"
    ) == [counterfactual]
    assert set(agent.s.nodes("Experiment")) == before


def _agent():
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(manifest_for("cognitive_pareto"), agent.agent)
    agent.inner.load_seed_manifest(manifest(), agent.agent)
    return agent


def _session_agent():
    """Real session/receipt graph around the bootstrap, still no host policy."""
    agent = WorldAdapter(seeds=())
    for seed in (
        manifest_for("cognitive_pareto"),
        manifest_for("counterfactual_experiment"),
        session_manifest(),
        manifest(),
    ):
        agent.inner.load_seed_manifest(seed, agent.agent)
    return agent


def _install_body(agent, *, tokens, direct=True, maximum_observation_horizon_frames=169):
    episode = agent.s.add_node(
        "EmbodiedDevelopmentEpisode", {"development_learning_active": 1}
    )
    body = agent.s.add_node("EmbodiedBodySchema", {
        "morphology_epoch": 17, "integer_native": 1,
    })
    world = agent.s.add_node("EmbodiedLearningWorld", {"integer_native": 1})
    contract = agent.s.add_node("EmbodiedMotorBootstrapContract", {
        "integer_native": 1,
        "simulator_weight_scale_units": 7,
        "minimum_nonzero_weight_units": 1,
        "minimum_actuation_frames": 13,
        "maximum_observation_horizon_frames": maximum_observation_horizon_frames,
        "displacement_units_per_metre": 1000,
        "energy_units_per_joule": 100,
        "load_units_per_newton": 10,
        "maximum_actuator_bundle_members": len(tokens),
    })
    projection = agent.s.add_node("EmbodiedMeasurementProjectionAffordance", {
        "projection_kind": "cartesian_displacement", "axis": 0, "sign": 1,
        "available": 1, "integer_native": 1,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    _edge(agent, episode, "has_embodied_body_schema", body)
    _edge(agent, episode, "has_embodied_learning_world", world)
    _edge(agent, world, "has_embodied_motor_bootstrap_contract", contract)
    _edge(agent, contract, "has_embodied_measurement_projection", projection)
    effectors = []
    for ordinal, token in enumerate(tokens):
        effector = agent.s.add_node("EmbodiedOpaqueActuatorAffordance", {
            "opaque_token": token,
            # The ordinal and tonic bit are mechanical interface facts; no
            # directional/anatomical interpretation is supplied to graph.
            "ordinal": ordinal,
            "opaque_group_ordinal": ordinal,
            "tonic_default": 0,
            "integer_native": 1,
        })
        effectors.append(effector)
        if direct:
            _edge(agent, body, "has_opaque_embodied_actuator_affordance", effector)
    return episode, body, world, effectors


@pytest.mark.parametrize("count", [1, 5])
def test_bootstrap_is_morphology_and_count_agnostic_and_preserves_each_opaque_token(count):
    agent = _agent()
    tokens = tuple(f"opaque::body-17::channel/{ordinal}" for ordinal in range(count))
    episode, _body, _world, effectors = _install_body(agent, tokens=tokens)

    agent.tick(max_steps=100)

    motor_episode = agent.inner.neighbours(episode, "has_embodied_motor_episode")
    assert len(motor_episode) == 1
    motor_episode = motor_episode[0]
    candidates = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_candidate"
    )
    assert len(candidates) == count
    assert not agent.inner.neighbours(motor_episode, "has_embodied_motor_program")
    assert not agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    )
    assert all(agent.inner.neighbours(
        effector, "has_singleton_candidate_in_motor_episode"
    ) == [motor_episode] for effector in effectors)

    programs_by_token = {}
    for candidate in candidates:
        assert agent.s.node(candidate)["attrs"]["output_authority"] == 0
        assert agent.inner.neighbours(candidate, "models_opaque_affordance") in [
            [effector] for effector in effectors
        ]
        program = agent.inner.neighbours(
            candidate, "proposes_embodied_motor_program"
        )
        assert len(program) == 1
        attrs = agent.s.node(program[0])["attrs"]
        assert attrs["output_authority"] == 0
        assert attrs["integer_native"] == 1
        assert isinstance(attrs["simulator_tokens"], list)
        assert len(attrs["simulator_tokens"]) == 1
        assert isinstance(attrs["simulator_weight_units"], list)
        assert all(isinstance(value, int) for value in attrs.values()
                   if isinstance(value, int))
        programs_by_token[attrs["simulator_tokens"][0]] = attrs

    assert set(programs_by_token) == set(tokens)
    for ordinal, token in enumerate(tokens):
        assert programs_by_token[token]["simulator_weight_units"] == [1]
        assert programs_by_token[token]["simulator_frames"] == 13


def test_detached_embodiment_freezes_its_motor_pareto_profile():
    agent = _agent()
    episode, _body, _world, _effectors = _install_body(
        agent, tokens=("opaque/detached/0",)
    )
    connection = agent.s.add_node(
        "EmbodiedSimulatorConnection", {"current_attachment": 1}
    )
    _edge(agent, episode, "grounded_in_embodied_simulator_connection", connection)
    agent.tick(max_steps=100)
    motor = agent.inner.neighbours(episode, "has_embodied_motor_episode")[0]
    profile = agent.inner.neighbours(
        motor, "has_embodied_motor_bootstrap_profile"
    )[0]
    assert agent.s.node(profile)["attrs"].get("pareto_suspended") is None

    agent.inner.set_attr(connection, "current_attachment", 0)
    agent.tick(max_steps=100)

    assert agent.s.node(profile)["attrs"]["pareto_suspended"] == 1


def test_compound_expansion_batches_every_branch_before_closing_search():
    generated = manifest()
    synthesis = next(
        rule for rule in generated["rules"]
        if rule["name"]
        == "emb_synthesize_local_compound_from_grounded_consequence_and_topology"
    )
    generated["rules"] = [synthesis]
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(generated, agent.agent)
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    body = agent.s.add_node("EmbodiedBodySchema", {})
    motor = agent.s.add_node("EmbodiedMotorEpisode", {})
    candidate = agent.s.add_node("EmbodiedMotorBootstrapCandidate", {
        "member_count": 1,
    })
    source = agent.s.add_node("EmbodiedOpaqueActuatorAffordance", {
        "integer_native": 1, "tonic_default": 0, "opaque_group_ordinal": 0,
    })
    targets = [
        agent.s.add_node("EmbodiedOpaqueActuatorAffordance", {
            "integer_native": 1, "tonic_default": 0,
            "opaque_group_ordinal": ordinal,
        }) for ordinal in (1, 2)
    ]
    program = agent.s.add_node("EmbodiedMotorProgram", {})
    consequence = agent.s.add_node("EmbodiedLearnedConsequence", {})
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "grounded": 1, "causal_closed": 1,
        "success_delta_units": 1, "goal_progress_units": 1,
    })
    for source_node, edge, target_node in (
        (episode, "has_embodied_body_schema", body),
        (episode, "has_embodied_motor_episode", motor),
        (motor, "has_embodied_motor_bootstrap_candidate", candidate),
        (candidate, "models_opaque_affordance", source),
        (candidate, "proposes_embodied_motor_program", program),
        (program, "has_grounded_learned_consequence", consequence),
        (consequence, "grounded_in_causal_receipt", receipt),
    ):
        _edge(agent, source_node, edge, target_node)
    relations = []
    for ordinal, target in enumerate(targets, 1):
        relation = agent.s.add_node("EmbodiedRawEffectorTopologyRelation", {
            "relation_kind": "directed_mechanical_link_adjacency",
            "source_group_ordinal": 0, "target_group_ordinal": ordinal,
            "mechanical_path_length": 1, "grounded": 1, "integer_native": 1,
        })
        relations.append(relation)
        _edge(agent, body, "has_opaque_embodied_effector_topology_relation", relation)
        _edge(agent, relation, "has_source_opaque_embodied_effector", source)
        _edge(agent, relation, "has_target_opaque_embodied_effector", target)

    agent.tick(max_steps=20)

    assert len(agent.inner.neighbours(
        body, "has_opaque_actuator_bundle_affordance"
    )) == 2
    assert set(agent.inner.neighbours(
        program, "has_opened_compound_topology_relation"
    )) == set(relations)
    assert agent.s.node(program)["attrs"][
        "compound_topology_expansion_complete"
    ] == 1
    agent.tick(max_steps=20)
    assert len(agent.inner.neighbours(
        body, "has_opaque_actuator_bundle_affordance"
    )) == 2


def test_graph_selects_a_compound_bundle_after_pareto_frontier_without_semantic_alias():
    agent = _agent()
    tokens = ("@[a7]", "opaque/2:beta", "servo?gamma")
    episode, body, _world, effectors = _install_body(agent, tokens=tokens, direct=False)
    bundle = agent.s.add_node("OpaqueActuatorBundleAffordance", {
        "ordinal": 41, "integer_native": 1,
    })
    _edge(agent, body, "has_opaque_actuator_bundle_affordance", bundle)
    # The graph receives an arbitrary topology set, not a named synergy.
    for effector in effectors:
        _edge(agent, bundle, "has_opaque_embodied_actuator_affordance", effector)

    agent.tick(max_steps=100)
    motor_episode = agent.inner.neighbours(episode, "has_embodied_motor_episode")[0]
    candidates = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_candidate"
    )
    assert len(candidates) == 1
    candidate = candidates[0]
    program = agent.inner.neighbours(candidate, "proposes_embodied_motor_program")[0]
    program_attrs = agent.s.node(program)["attrs"]
    assert program_attrs["simulator_tokens"] == list(tokens)
    assert program_attrs["simulator_weight_units"] == [1, 1, 1]
    assert "token" not in program_attrs
    assert not agent.inner.neighbours(motor_episode, "has_embodied_motor_program")

    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 2})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "integer_native": 1,
    })
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_selected_learning_plan_step", step)
    _edge(agent, step, "pursues_goal", goal)
    _edge(agent, episode, "has_active_embodied_developmental_capability", capability)
    session = agent.s.add_node("EmbodiedLearningSession", {
        "integer_native": 1, "output_authority": 0,
    })
    _edge(agent, episode, "has_embodied_learning_session", session)
    agent.tick(max_steps=100)

    selection = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    )
    assert len(selection) == 1
    assert agent.s.node(selection[0])["attrs"]["output_authority"] == 0
    assert agent.inner.neighbours(
        selection[0], "selects_embodied_motor_program"
    ) == [program]
    # Only graph selection—not body ingestion or candidate construction—opens
    # the compatibility edge consumed by embodied_learning_session.
    assert agent.inner.neighbours(
        motor_episode, "has_embodied_motor_program"
    ) == [program]
    assert agent.inner.neighbours(
        motor_episode, "uses_embodied_motor_prior"
    ) == agent.inner.neighbours(candidate, "uses_embodied_motor_prior")
    assert not list(agent.s.nodes("EmbodiedExternalTrialRequest"))


def test_positive_singleton_receipt_opens_only_a_local_unknown_compound_hypothesis():
    """A direct topology edge is necessary but insufficient without receipt data.

    The proposed pair has no fake forward/energy/load conclusion.  Its initial
    Pareto point contains only verified topology/information dimensions; the
    existing session-owned three-axis outcome profile is the only place where
    measured motion cost can later appear.
    """
    agent = _agent()
    tokens = ("opaque/local/0", "opaque/local/1", "opaque/distal/2")
    episode, body, _world, effectors = _install_body(agent, tokens=tokens)
    relation = agent.s.add_node("EmbodiedRawEffectorTopologyRelation", {
        "relation_kind": "directed_mechanical_link_adjacency",
        "relation_ordinal": 0,
        "source_group_ordinal": 0,
        "target_group_ordinal": 1,
        "mechanical_path_length": 1,
        "grounded": 1,
        "integer_native": 1,
    })
    _edge(agent, body, "has_opaque_embodied_effector_topology_relation", relation)
    agent.tick(max_steps=100)
    assert agent.inner.neighbours(
        relation, "has_source_opaque_embodied_effector"
    ) == [effectors[0]]
    assert agent.inner.neighbours(
        relation, "has_target_opaque_embodied_effector"
    ) == [effectors[1]]
    assert not agent.inner.neighbours(body, "has_opaque_actuator_bundle_affordance")

    motor = agent.inner.neighbours(episode, "has_embodied_motor_episode")[0]
    # This is the real generic developmental provenance shape: a receipt is
    # for the selected step's goal, rather than requiring a language-specific
    # root goal to supervise the episode directly.
    plan = agent.s.add_node("LearningPlan", {"status": "active"})
    step = agent.s.add_node("LearningPlanStep", {"status": "active"})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 1})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "integer_native": 1,
    })
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_selected_learning_plan_step", step)
    _edge(agent, step, "pursues_goal", goal)
    _edge(agent, episode, "has_active_embodied_developmental_capability", capability)
    session = agent.s.add_node("EmbodiedLearningSession", {
        "integer_native": 1, "output_authority": 0,
    })
    _edge(agent, episode, "has_embodied_learning_session", session)
    # Establish the ordinary singleton collapse before the positive receipt
    # introduces a coordination hypothesis.
    agent.tick(max_steps=100)
    source_candidate = next(
        candidate for candidate in agent.inner.neighbours(
            motor, "has_embodied_motor_bootstrap_candidate"
        ) if agent.s.node(candidate)["attrs"]["actuator_ordinal"] == 0
    )
    source_program = agent.inner.neighbours(
        source_candidate, "proposes_embodied_motor_program"
    )[0]
    consequence = agent.s.add_node("EmbodiedLearnedConsequence", {
        "grounded": 1, "integer_native": 1,
    })
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed", "grounded": 1, "causal_closed": 1,
        "success_delta_units": 1, "goal_progress_units": 3,
        "energy_cost_units": 17, "peak_load_units": 9,
        "integer_native": 1,
    })
    _edge(agent, source_program, "has_grounded_learned_consequence", consequence)
    _edge(agent, consequence, "grounded_in_causal_receipt", receipt)
    _edge(agent, receipt, "caused_for_embodied_goal", goal)
    agent.tick(max_steps=100)
    agent.tick(max_steps=100)
    # The context atomically re-collapses the still-local choice to the exact
    # graph-selected compound without an extra host trial.
    agent.tick(max_steps=100)

    bundles = agent.inner.neighbours(body, "has_opaque_actuator_bundle_affordance")
    assert len(bundles) == 1
    bundle = bundles[0]
    assert agent.s.node(bundle)["attrs"]["interaction_prediction_verified"] == 0
    assert agent.s.node(bundle)["attrs"]["predicted_forward_units"] == 0
    assert agent.s.node(bundle)["attrs"]["predicted_energy_units"] == 0
    assert agent.s.node(bundle)["attrs"]["predicted_peak_load_units"] == 0
    assert agent.inner.neighbours(
        bundle, "has_opaque_embodied_actuator_affordance"
    ) == [effectors[0], effectors[1]]
    assert agent.inner.neighbours(
        bundle, "grounded_in_source_embodied_receipt"
    ) == [receipt]
    assert agent.inner.neighbours(
        source_program, "has_opened_compound_topology_relation"
    ) == [relation]
    assert agent.s.node(source_program)["attrs"][
        "compound_topology_expansion_complete"
    ] == 1
    contexts = agent.inner.neighbours(
        capability, "has_embodied_motor_coordination_context"
    )
    assert len(contexts) == 1
    assert agent.s.node(capability)["attrs"]["coordination_exploration_required"] == 1
    assert agent.inner.neighbours(
        contexts[0], "targets_embodied_goal"
    ) == [goal]

    compound_candidate = next(
        candidate for candidate in agent.inner.neighbours(
            motor, "has_embodied_motor_bootstrap_candidate"
        ) if agent.s.node(candidate)["attrs"]["member_count"] == 2
    )
    compound_program = agent.inner.neighbours(
        compound_candidate, "proposes_embodied_motor_program"
    )[0]
    assert agent.s.node(compound_program)["attrs"]["simulator_tokens"] == list(tokens[:2])
    # The singleton was selected before the receipt-derived coordination
    # question existed.  The context must therefore reopen that unexecuted
    # collapse and let the normal Pareto frontier select the compound—without
    # a Python actuator decision or an extra host trial.
    selections = agent.inner.neighbours(
        motor, "has_embodied_motor_bootstrap_selection"
    )
    assert len(selections) == 1
    assert agent.inner.neighbours(
        selections[0], "selects_pareto_candidate"
    ) == [compound_candidate]
    assert agent.inner.neighbours(
        selections[0], "selects_embodied_motor_program"
    ) == [compound_program]
    values = agent.inner.neighbours(compound_candidate, "has_pareto_value")
    assert len(values) == 6
    # No fabricated zero-cost performance values: these six positions are the
    # verified hypothesis profile, whose last axis is information value.
    assert {agent.s.node(value)["attrs"]["dimension_ordinal"] for value in values} == set(range(6))
    assert not agent.inner.neighbours(
        compound_candidate, "has_receipt_grounded_motor_outcome"
    )

    # A known singleton's real 3D outcome belongs to the shared
    # receipt-grounded performance profile.  The untested compound is not a
    # member, so its placeholder zeros cannot dominate by pretending to be
    # measured energy/load values.
    measured = agent.s.add_node("ParetoProfile", {
        "dimension_count": 3, "integer_native": 1, "scalarized": 0,
    })
    known_singleton = agent.s.add_node("ParetoCandidate", {
        "kind": "grounded_embodied_external_trial", "verified": 1,
        "integer_native": 1,
    })
    _edge(agent, measured, "has_pareto_candidate", known_singleton)
    for ordinal, raw, signed in ((0, 3, 3), (1, 17, -17), (2, 9, -9)):
        value = agent.s.add_node("ParetoValue", {
            "dimension_ordinal": ordinal, "raw_value": raw,
            "signed_value": signed, "verified": 1,
            "integer_native": 1,
        })
        _edge(agent, known_singleton, "has_pareto_value", value)
    agent.tick(max_steps=100)
    assert compound_candidate not in agent.inner.neighbours(
        measured, "has_pareto_candidate"
    )
    assert known_singleton not in agent.inner.neighbours(
        compound_candidate, "is_dominated_by_pareto_candidate"
    )
    assert compound_candidate not in agent.inner.neighbours(
        known_singleton, "is_dominated_by_pareto_candidate"
    )


def test_duplicate_epoch_paths_collapse_to_one_live_motor_selection():
    """Resumed duplicate epoch paths cannot fan one frontier into many outputs."""
    agent = _agent()
    episode, _body, _world, _effectors = _install_body(
        agent, tokens=("opaque/left", "opaque/right"),
    )
    agent.tick(max_steps=100)
    motor = agent.inner.neighbours(episode, "has_embodied_motor_episode")[0]
    plan = agent.s.add_node("LearningPlan", {"status": "active"})
    step = agent.s.add_node("LearningPlanStep", {"status": "active"})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 1})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "integer_native": 1,
    })
    for source, edge, target in (
        (episode, "has_self_directed_learning_plan", plan),
        (plan, "has_selected_learning_plan_step", step),
        (step, "pursues_goal", goal),
        (episode, "has_active_embodied_developmental_capability", capability),
    ):
        _edge(agent, source, edge, target)
    agent.tick(max_steps=100)

    # Model a resumed graph whose old rules left two *live* selections for the
    # same program across two epochs.  This is not an actuator choice: the
    # duplicate must be re-collapsed by graph rules rather than keeping either
    # historical edge as accidental authority.
    selection = agent.inner.neighbours(
        motor, "has_embodied_motor_bootstrap_selection"
    )[0]
    candidate = agent.inner.neighbours(
        selection, "selects_pareto_candidate"
    )[0]
    program = agent.inner.neighbours(
        selection, "selects_embodied_motor_program"
    )[0]
    prior = agent.inner.neighbours(selection, "uses_embodied_motor_prior")[0]
    duplicate_epoch = agent.s.add_node("EmbodiedMotorSelectionEpoch", {
        "kind": "opaque_motor_bootstrap", "settled_experience_units": 1,
        "integer_native": 1, "output_authority": 0,
    })
    duplicate = agent.s.add_node("EmbodiedMotorBootstrapSelection", {
        "status": "selected", "integer_native": 1, "output_authority": 0,
    })
    for source, edge, target in (
        (motor, "has_current_embodied_motor_selection_epoch", duplicate_epoch),
        (motor, "has_embodied_motor_bootstrap_selection", duplicate),
        (duplicate, "selects_pareto_candidate", candidate),
        (duplicate, "selects_embodied_motor_program", program),
        (duplicate, "uses_embodied_motor_prior", prior),
        (duplicate, "is_in_embodied_motor_selection_epoch", duplicate_epoch),
    ):
        _edge(agent, source, edge, target)

    # A second path in the same newer epoch is the historical shape that once
    # produced a Cartesian repair fan-out.  Both paths must resolve to the
    # same idempotent replacement node before the older epoch is retired.
    same_epoch_duplicate = agent.s.add_node("EmbodiedMotorBootstrapSelection", {
        "status": "selected", "integer_native": 1, "output_authority": 0,
    })
    for source, edge, target in (
        (motor, "has_embodied_motor_bootstrap_selection", same_epoch_duplicate),
        (same_epoch_duplicate, "selects_pareto_candidate", candidate),
        (same_epoch_duplicate, "selects_embodied_motor_program", program),
        (same_epoch_duplicate, "uses_embodied_motor_prior", prior),
        (same_epoch_duplicate, "is_in_embodied_motor_selection_epoch", duplicate_epoch),
    ):
        _edge(agent, source, edge, target)

    assert len(agent.inner.neighbours(
        motor, "has_embodied_motor_bootstrap_selection"
    )) == 3
    agent.tick(max_steps=100)
    agent.tick(max_steps=100)
    selections = agent.inner.neighbours(
        motor, "has_embodied_motor_bootstrap_selection"
    )
    assert len(selections) == 1
    assert len(agent.inner.neighbours(
        motor, "has_embodied_motor_program"
    )) == 1
    assert len(agent.inner.neighbours(
        motor, "has_current_embodied_motor_selection_epoch"
    )) == 1


def test_receipt_grounded_compound_is_physically_enacted_by_real_pybullet():
    """A graph-discovered pair crosses the real boundary as one exact action."""
    pytest.importorskip("pybullet")
    from domains.pybullet_humanoid_trial_transducer import (
        PyBulletHumanoidTrialTransducer,
    )

    agent = WorldAdapter(seeds=("embodied_motor_bootstrap",))
    transducer = PyBulletHumanoidTrialTransducer.from_protocol(
        ROOT / "protocols" / "humanoid_developmental_smoke_v1.json", seed=19,
    )
    try:
        transducer.publish_body_world_capabilities(agent)
        assert agent.tick(max_steps=1_000) < 1_000
        episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))[0]
        motor = agent.inner.neighbours(episode, "has_embodied_motor_episode")[0]
        session = agent.inner.neighbours(episode, "has_embodied_learning_session")[0]
        plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")[0]
        step = agent.inner.neighbours(plan, "has_selected_learning_plan_step")[0]
        goal = agent.inner.neighbours(step, "pursues_goal")[0]
        selection = agent.inner.neighbours(
            motor, "has_embodied_motor_bootstrap_selection"
        )[0]
        body = agent.inner.neighbours(episode, "has_embodied_body_schema")[0]
        source_groups = {
            agent.s.node(relation)["attrs"]["source_group_ordinal"]
            for relation in agent.inner.neighbours(
                body, "has_opaque_embodied_effector_topology_relation"
            )
        }
        source_candidate = next(
            candidate for candidate in agent.inner.neighbours(
                motor, "has_embodied_motor_bootstrap_candidate"
            )
            for effector in agent.inner.neighbours(
                candidate, "models_opaque_affordance"
            )
            if agent.s.node(candidate)["attrs"]["member_count"] == 1
            and agent.s.node(effector)["attrs"].get("tonic_default") == 0
            and agent.s.node(effector)["attrs"].get("opaque_group_ordinal")
            in source_groups
        )
        source_program = agent.inner.neighbours(
            source_candidate, "proposes_embodied_motor_program"
        )[0]

        # Supply the same kind of positive causal singleton fact retained by
        # the live developmental run.  The compound observation below—not
        # this premise—is what crosses PyBullet in this test.
        consequence = agent.s.add_node("EmbodiedLearnedConsequence", {
            "grounded": 1, "integer_native": 1,
        })
        source_receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
            "status": "closed", "grounded": 1, "causal_closed": 1,
            "success_delta_units": 1, "goal_progress_units": 1,
            "integer_native": 1,
        })
        _edge(agent, source_program, "has_grounded_learned_consequence", consequence)
        _edge(agent, consequence, "grounded_in_causal_receipt", source_receipt)
        _edge(agent, source_receipt, "caused_for_embodied_goal", goal)
        assert agent.tick(max_steps=2_000) < 2_000

        compound_selection = agent.inner.neighbours(
            motor, "has_embodied_motor_bootstrap_selection"
        )
        assert len(compound_selection) == 1
        compound_program = agent.inner.neighbours(
            compound_selection[0], "selects_embodied_motor_program"
        )[0]
        assert len(agent.s.node(compound_program)["attrs"]["simulator_tokens"]) == 2

        assert scan_and_imagine(agent)
        assert agent.tick(max_steps=2_000) < 2_000
        requests = [request for request in agent.inner.neighbours(
            session, "has_grounded_external_trial_request"
        ) if agent.s.node(request)["attrs"].get("status") == "requested"]
        assert len(requests) == 1
        assert agent.inner.neighbours(
            requests[0], "enacts_embodied_motor_program"
        ) == [compound_program]
        transducer(agent, requests[0])
        assert agent.tick(max_steps=2_000) < 2_000
        receipts = agent.inner.neighbours(
            requests[0], "has_embodied_learning_trial_receipt"
        )
        assert len(receipts) == 1
        assert agent.s.node(receipts[0])["attrs"]["grounded"] == 1
        assert agent.inner.neighbours(
            receipts[0], "caused_by_embodied_motor_program"
        ) == [compound_program]
    finally:
        transducer.close()


def test_shape_decoded_receipt_memory_warm_starts_a_fresh_local_program():
    """A successful program transfers by shape, never by stale token handle.

    The source has a positive causal receipt on ordinal 1 while the cold
    frontier would pick ordinal 0.  A target body has fresh opaque token
    strings but the same observed relation shape; therefore the graph must
    select local ordinal 1 with the learned aperture/predictions, and still
    mark it pending a target-local verification.
    """
    agent = _agent()
    source, source_body, _world, _effectors = _install_body(
        agent, tokens=("source/channel-0", "source/channel-1"),
    )
    source_raw = agent.s.add_node("EmbodiedRawBodyObservation", {
        "body_shape_relations": [["body", 2, 2, 2], ["support", 2]],
        "grounded": 1, "integer_native": 1,
    })
    _edge(agent, source_body, "grounded_in_embodied_raw_body", source_raw)
    agent.tick(max_steps=100)
    source_motor = agent.inner.neighbours(source, "has_embodied_motor_episode")[0]
    source_candidate = next(
        candidate
        for candidate in agent.inner.neighbours(
            source_motor, "has_embodied_motor_bootstrap_candidate"
        )
        if agent.s.node(candidate)["attrs"]["actuator_ordinal"] == 1
    )
    source_program = agent.inner.neighbours(
        source_candidate, "proposes_embodied_motor_program"
    )[0]
    # This represents values written only by the normal receipt closure in a
    # source episode.  The target never imports its opaque token string.
    for key, value in (
        ("simulator_frames", 34),
        ("predicted_forward_units", 7),
        ("predicted_vertical_units", 3),
        ("predicted_energy_units", 19),
        ("predicted_peak_load_units", 23),
        ("experience_units", 2),
    ):
        agent.s.set_attr(source_program, key, value)
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "grounded": 1, "success_delta_units": 1,
        "integer_native": 1,
    })
    source_request = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "integer_native": 1,
    })
    source_proposal = agent.s.add_node("EmbodiedInstructionGoalProposal", {
        "status": "confirmed", "predicate": "move", "integer_native": 1,
    })
    source_goal = agent.s.add_node("Goal", {
        "status": "active", "integer_native": 1,
    })
    consequence = agent.s.add_node("EmbodiedLearnedConsequence", {
        "grounded": 1, "integer_native": 1,
    })
    _edge(agent, source_program, "has_grounded_learned_consequence", consequence)
    _edge(agent, consequence, "grounded_in_causal_receipt", receipt)
    _edge(agent, receipt, "caused_by_embodied_trial_request", source_request)
    _edge(agent, source_proposal, "has_embodied_mission_trial_request", source_request)
    _edge(agent, source_proposal, "proposes_goal", source_goal)
    agent.tick(max_steps=100)

    memories = agent.inner.neighbours(agent.agent, "has_embodied_motor_shape_memory")
    assert len(memories) == 1
    memory = memories[0]
    assert agent.inner.neighbours(
        memory, "derived_from_embodied_motor_program"
    ) == [source_program]
    assert agent.inner.neighbours(
        memory, "grounded_in_causal_embodied_receipt"
    ) == [receipt]

    target, target_body, _world, _effectors = _install_body(
        agent, tokens=("target/fresh-0", "target/fresh-1"),
    )
    target_raw = agent.s.add_node("EmbodiedRawBodyObservation", {
        "body_shape_relations": [["body", 2, 2, 2], ["support", 2]],
        "grounded": 1, "integer_native": 1,
    })
    _edge(agent, target_body, "grounded_in_embodied_raw_body", target_raw)
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 2})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "integer_native": 1,
        "warm_start_requires_verification": 0,
    })
    target_proposal = agent.s.add_node("EmbodiedInstructionGoalProposal", {
        "status": "accepted", "predicate": "move", "integer_native": 1,
    })
    target_goal = agent.s.add_node("Goal", {
        "status": "active", "integer_native": 1,
    })
    for left, edge, right in (
        (target, "has_self_directed_learning_plan", plan),
        (plan, "has_selected_learning_plan_step", step),
        (step, "pursues_goal", goal),
        (target, "has_active_embodied_developmental_capability", capability),
        (target_proposal, "requires_embodied_capability", capability),
        (target_proposal, "proposes_goal", target_goal),
        (target_goal, "supervises_embodied_episode", target),
    ):
        _edge(agent, left, edge, right)
    agent.tick(max_steps=200)

    target_motor = agent.inner.neighbours(target, "has_embodied_motor_episode")[0]
    selection = agent.inner.neighbours(
        target_motor, "has_embodied_motor_bootstrap_selection"
    )
    assert len(selection) == 1
    selected_candidate = agent.inner.neighbours(
        selection[0], "selects_pareto_candidate"
    )[0]
    selected_program = agent.inner.neighbours(
        selection[0], "selects_embodied_motor_program"
    )[0]
    assert agent.s.node(selected_candidate)["attrs"]["actuator_ordinal"] == 1
    assert agent.s.node(capability)["attrs"]["warm_start_requires_verification"] == 1
    # Transfer is explanatory evidence, never fraudulent local practice.
    assert agent.s.node(selected_candidate)["attrs"]["experience_units"] == 0
    attrs = agent.s.node(selected_program)["attrs"]
    assert attrs["simulator_tokens"] == ["target/fresh-1"]
    # THE APERTURE DOES NOT CROSS BODIES. The memory's 34 frames is an aperture
    # measured on the SOURCE body; how long you must watch is a fact about the
    # target body's own dynamics and resolution. The target reads its own
    # body's aperture instead, which is the whole point of moving the aperture
    # off the program. Predictions still transfer -- they are claims about the
    # ACTION, not about the observer.
    assert attrs["simulator_frames"] != 34
    assert attrs["aperture_source"] == "body_scaled_hint"
    assert attrs["predicted_forward_units"] == 7
    assert attrs["experience_units"] == 0
    assert attrs["transferred_evidence_units"] == 2
    assert attrs["warm_start_pending_local_verification"] == 1
    warm_starts = agent.inner.neighbours(
        selected_program, "has_embodied_motor_warm_start"
    )
    assert len(warm_starts) == 1
    assert agent.inner.neighbours(
        warm_starts[0], "transfers_from_embodied_motor_program"
    ) == [source_program]
    assert not agent.inner.neighbours(
        warm_starts[0], "has_local_embodied_motor_verification"
    )
    target_receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "grounded": 1, "success_delta_units": 1,
        "integer_native": 1,
    })
    _edge(agent, target_receipt, "caused_by_embodied_motor_program", selected_program)
    agent.tick(max_steps=100)
    assert agent.s.node(selected_program)["attrs"][
        "warm_start_pending_local_verification"
    ] == 0
    verification = agent.inner.neighbours(
        warm_starts[0], "has_local_embodied_motor_verification"
    )
    assert len(verification) == 1
    assert agent.inner.neighbours(
        verification[0], "grounded_in_local_embodied_receipt"
    ) == [target_receipt]

    # Same shape alone is insufficient: a different instruction predicate
    # retains the structural-novelty/reuse Pareto tradeoff on discovery, so
    # the ordinary cold (ordinal-zero) frontier remains selected.
    novel, novel_body, _world, _effectors = _install_body(
        agent, tokens=("novel/fresh-0", "novel/fresh-1"),
    )
    novel_raw = agent.s.add_node("EmbodiedRawBodyObservation", {
        "body_shape_relations": [["body", 2, 2, 2], ["support", 2]],
        "grounded": 1, "integer_native": 1,
    })
    _edge(agent, novel_body, "grounded_in_embodied_raw_body", novel_raw)
    novel_plan = agent.s.add_node("LearningPlan", {})
    novel_step = agent.s.add_node("LearningPlanStep", {})
    novel_goal = agent.s.add_node("Goal", {"status": "active", "order_n": 2})
    novel_capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "integer_native": 1,
        "warm_start_requires_verification": 0,
    })
    novel_proposal = agent.s.add_node("EmbodiedInstructionGoalProposal", {
        "status": "accepted", "predicate": "turn", "integer_native": 1,
    })
    novel_root = agent.s.add_node("Goal", {"status": "active", "integer_native": 1})
    for left, edge, right in (
        (novel, "has_self_directed_learning_plan", novel_plan),
        (novel_plan, "has_selected_learning_plan_step", novel_step),
        (novel_step, "pursues_goal", novel_goal),
        (novel, "has_active_embodied_developmental_capability", novel_capability),
        (novel_proposal, "requires_embodied_capability", novel_capability),
        (novel_proposal, "proposes_goal", novel_root),
        (novel_root, "supervises_embodied_episode", novel),
    ):
        _edge(agent, left, edge, right)
    agent.tick(max_steps=200)
    novel_motor = agent.inner.neighbours(novel, "has_embodied_motor_episode")[0]
    novel_selection = agent.inner.neighbours(
        novel_motor, "has_embodied_motor_bootstrap_selection"
    )[0]
    novel_candidate = agent.inner.neighbours(
        novel_selection, "selects_pareto_candidate"
    )[0]
    assert agent.s.node(novel_candidate)["attrs"]["actuator_ordinal"] == 0
    assert agent.s.node(novel_capability)["attrs"]["warm_start_requires_verification"] == 0
    assert not agent.inner.neighbours(
        novel_capability, "has_embodied_motor_retention_context"
    )


def test_embodied_seed_rules_refresh_on_checkpoint_resume_without_churn():
    """The normal daemon reconcile path must replace stale motor rule bodies."""
    import jabberwock_daemon as daemon

    assert {"embodied_motor_bootstrap", "embodied_instruction_goal"} <= set(
        daemon._REFRESHABLE_SEEDS
    )
    current = manifest()
    selection_name = "emb_select_ready_motor_program_from_pareto_frontier"
    canonical = next(rule for rule in current["rules"] if rule["name"] == selection_name)
    adapter = WorldAdapter(seeds=())
    adapter.inner.load_seed_manifest(current, adapter.agent)
    live = list(adapter.inner.export_rules())
    original_index = next(
        index for index, rule in enumerate(live)
        if rule.get("active") and rule.get("name") == selection_name
    )
    adapter.inner.remove_rule(original_index)
    stale = copy.deepcopy(canonical)
    stale["comment"] = "deliberately stale checkpoint body"
    adapter.inner.load_seed_manifest(
        {"id": "embodied_motor_bootstrap", "rules": [stale]}, adapter.agent
    )
    assert daemon._reconcile_seed_rules(adapter) > 0
    refreshed = [
        rule for rule in adapter.inner.export_rules()
        if rule.get("active") and rule.get("name") == selection_name
    ]
    assert len(refreshed) == 1
    assert daemon._canon_rule_body(refreshed[0]) == daemon._canon_rule_body(canonical)
    # Other optional seed files may be malformed and retry independently; the
    # embodied rule itself must not churn on a later normal reconcile pass.
    daemon._reconcile_seed_rules(adapter)
    assert len([
        rule for rule in adapter.inner.export_rules()
        if rule.get("active") and rule.get("name") == selection_name
    ]) == 1


def test_grounded_receipt_reopens_frontier_instead_of_permanently_reusing_first_program():
    agent = _agent()
    episode, _body, _world, _effectors = _install_body(
        agent, tokens=("opaque/first", "opaque/second")
    )
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 2})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "integer_native": 1,
    })
    session = agent.s.add_node("EmbodiedLearningSession", {
        "integer_native": 1, "output_authority": 0,
    })
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_selected_learning_plan_step", step)
    _edge(agent, step, "pursues_goal", goal)
    _edge(agent, episode, "has_active_embodied_developmental_capability", capability)
    _edge(agent, episode, "has_embodied_learning_session", session)
    agent.tick(max_steps=100)

    motor_episode = agent.inner.neighbours(episode, "has_embodied_motor_episode")[0]
    first_selection = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    )[0]
    first_candidate = agent.inner.neighbours(
        first_selection, "selects_pareto_candidate"
    )[0]
    first_program = agent.inner.neighbours(
        first_selection, "selects_embodied_motor_program"
    )[0]
    first_prior = agent.inner.neighbours(
        first_selection, "uses_embodied_motor_prior"
    )[0]
    request = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "status": "evidenced", "integer_native": 1,
    })
    evidence = agent.s.add_node("EmbodiedExternalTrialEvidence", {
        "grounded": 1, "integer_native": 1,
    })
    counterfactual = agent.s.add_node("Experiment", {
        "status": "counterfactual_done", "integer_native": 1,
    })
    _edge(agent, session, "has_grounded_external_trial_request", request)
    _edge(agent, request, "has_grounded_external_trial_evidence", evidence)
    _edge(agent, session, "has_counterfactual_embodied_trial", counterfactual)
    _edge(agent, session, "has_selected_embodied_motor_program", first_program)
    _edge(agent, session, "uses_embodied_motor_hint", first_prior)
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed", "causal_closed": 1, "grounded": 1,
        "integer_native": 1,
    })
    _edge(agent, request, "enacts_embodied_motor_program", first_program)
    _edge(agent, evidence, "evidence_for_embodied_trial_request", request)
    _edge(agent, evidence, "measures_embodied_motor_program", first_program)
    _edge(agent, counterfactual, "tests_embodied_motor_program", first_program)
    _edge(agent, request, "has_embodied_learning_trial_receipt", receipt)
    _edge(agent, receipt, "grounded_in_external_trial_evidence", evidence)
    _edge(agent, receipt, "caused_by_embodied_motor_program", first_program)
    candidate_count_before_receipt = len(list(agent.s.nodes("ParetoCandidate")))
    program_count_before_receipt = len(list(agent.s.nodes("EmbodiedMotorProgram")))
    agent.tick(max_steps=100)

    assert agent.s.node(first_candidate)["attrs"]["experience_units"] == 1
    assert agent.inner.neighbours(
        first_selection, "settled_by_grounded_evidence"
    ) == [evidence]
    # Retirement and the next graph-side collapse occur in one fixed point;
    # the newly selected probe is different because it is less practised.
    next_selection = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    )
    assert len(next_selection) == 1
    assert next_selection[0] != first_selection
    next_program = agent.inner.neighbours(
        next_selection[0], "selects_embodied_motor_program"
    )[0]
    assert next_program != first_program
    assert len(list(agent.s.nodes("ParetoCandidate"))) == candidate_count_before_receipt
    assert len(list(agent.s.nodes("EmbodiedMotorProgram"))) == program_count_before_receipt
    assert not agent.inner.neighbours(session, "has_grounded_external_trial_request")
    assert not agent.inner.neighbours(session, "has_counterfactual_embodied_trial")


def test_stale_program_evidence_cannot_retire_current_motor_selection():
    agent = _agent()
    episode, _body, _world, _effectors = _install_body(
        agent, tokens=("opaque/current", "opaque/stale")
    )
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 2})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "integer_native": 1,
    })
    session = agent.s.add_node("EmbodiedLearningSession", {
        "integer_native": 1, "output_authority": 0,
    })
    for source, edge, target in (
        (episode, "has_self_directed_learning_plan", plan),
        (plan, "has_selected_learning_plan_step", step),
        (step, "pursues_goal", goal),
        (episode, "has_active_embodied_developmental_capability", capability),
        (episode, "has_embodied_learning_session", session),
    ):
        _edge(agent, source, edge, target)
    agent.tick(max_steps=100)
    motor_episode = agent.inner.neighbours(episode, "has_embodied_motor_episode")[0]
    selection = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    )[0]
    current_candidate = agent.inner.neighbours(
        selection, "selects_pareto_candidate"
    )[0]
    current_program = agent.inner.neighbours(
        selection, "selects_embodied_motor_program"
    )[0]

    stale_program = next(
        program for program in agent.s.nodes("EmbodiedMotorProgram")
        if program != current_program
    )
    request = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "status": "evidenced", "integer_native": 1,
    })
    evidence = agent.s.add_node("EmbodiedExternalTrialEvidence", {
        "grounded": 1, "integer_native": 1,
    })
    counterfactual = agent.s.add_node("Experiment", {
        "status": "counterfactual_done", "integer_native": 1,
    })
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed", "causal_closed": 1, "grounded": 1,
        "integer_native": 1,
    })
    for source, edge, target in (
        (session, "has_grounded_external_trial_request", request),
        (request, "has_grounded_external_trial_evidence", evidence),
        (request, "enacts_embodied_motor_program", stale_program),
        (evidence, "evidence_for_embodied_trial_request", request),
        (evidence, "measures_embodied_motor_program", stale_program),
        (session, "has_counterfactual_embodied_trial", counterfactual),
        (counterfactual, "tests_embodied_motor_program", stale_program),
        (request, "has_embodied_learning_trial_receipt", receipt),
        (receipt, "grounded_in_external_trial_evidence", evidence),
        (receipt, "caused_by_embodied_motor_program", stale_program),
    ):
        _edge(agent, source, edge, target)
    agent.tick(max_steps=100)

    assert agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    ) == [selection]
    assert agent.s.node(current_candidate)["attrs"]["experience_units"] == 0
    assert not agent.inner.neighbours(selection, "settled_by_grounded_evidence")
    assert agent.inner.neighbours(session, "has_grounded_external_trial_request") == [request]


@pytest.mark.parametrize(
    ("evidence_attrs", "maximum_observation_horizon_frames", "expected_kind"),
    [
        pytest.param(
            {"goal_progress_units": 0,
             "proprioceptive_configuration_l1_units": 0,
             "energy_cost_units": 1},
            169, "receipt_grounded_temporal_aperture", id="zero_consequence_widens",
        ),
        pytest.param(
            {"goal_progress_units": 0,
             "proprioceptive_configuration_l1_units": 1,
             "energy_cost_units": 1},
            169, "receipt_grounded_distinct_motor_program", id="configuration_change_explores_breadth",
        ),
        pytest.param(
            {"goal_progress_units": 1,
             "proprioceptive_configuration_l1_units": 0,
             "energy_cost_units": 1},
            169, "receipt_grounded_distinct_motor_program", id="goal_progress_explores_breadth",
        ),
        pytest.param(
            {"goal_progress_units": 0,
             "proprioceptive_configuration_l1_units": 0,
             "energy_cost_units": 1},
            13, "receipt_grounded_distinct_motor_program", id="horizon_cap_releases_breadth",
        ),
    ],
)
def test_supervisory_residual_selects_temporal_or_breadth_revision_from_receipt(
    evidence_attrs, maximum_observation_horizon_frames, expected_kind,
):
    """A supervisor replan becomes a causally grounded motor revision.

    This fixture supplies the exact post-supervisor graph state rather than
    reimplementing cognitive supervision in Python: the motor seed must retain
    its residual/check-in evidence, restore only the suspended continuation,
    and select a different least-practised opaque program.
    """
    agent = _agent()
    episode, _body, _world, _effectors = _install_body(
        agent, tokens=("opaque/current", "opaque/revision"),
        maximum_observation_horizon_frames=maximum_observation_horizon_frames,
    )
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {"status": "meta_suspended"})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 2})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "meta_suspended", "integer_native": 1,
    })
    session = agent.s.add_node("EmbodiedLearningSession", {
        "integer_native": 1, "output_authority": 0,
    })
    process = agent.s.add_node("CognitiveProcess", {
        "status": "replan_required", "continuation_authority": 0,
        "integer_native": 1,
    })
    policy = agent.s.add_node("CognitiveSupervisionPolicy", {
        "enabled": 0, "integer_native": 1,
    })
    checkin = agent.s.add_node("CognitiveCheckIn", {
        "status": "replan_required", "integer_native": 1,
    })
    residual = agent.s.add_node("LearningPlanResidual", {
        "status": "open", "kind": "inefficient_cognitive_process_window",
        "causal_yield_units": 0, "integer_native": 1,
    })
    for source, edge, target in (
        (episode, "has_self_directed_learning_plan", plan),
        (plan, "has_selected_learning_plan_step", step),
        (step, "pursues_goal", goal),
        (step, "plans_learning_capability", capability),
        (episode, "has_active_embodied_developmental_capability", capability),
        (episode, "has_embodied_learning_session", session),
        (episode, "has_cognitive_process", process),
        (process, "governed_by_cognitive_supervision_policy", policy),
        (process, "supervises_learning_plan_step", step),
        (process, "supervises_learning_capability", capability),
        (process, "has_cognitive_checkin", checkin),
        (plan, "has_learning_plan_residual", residual),
        (step, "has_learning_plan_residual", residual),
        (residual, "about_learning_plan_step", step),
        (residual, "raised_by_cognitive_checkin", checkin),
    ):
        _edge(agent, source, edge, target)
    agent.tick(max_steps=100)
    motor_episode = agent.inner.neighbours(episode, "has_embodied_motor_episode")[0]
    first_selection = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    )[0]
    old_program = agent.inner.neighbours(
        first_selection, "selects_embodied_motor_program"
    )[0]
    old_prior = agent.inner.neighbours(first_selection, "uses_embodied_motor_prior")[0]
    # This is the exact release performed by
    # ed_release_dominated_process_for_checkin_replanning: the supervisor
    # has retained the evidence but withdrawn ordinary selection authority.
    agent.inner.remove_edge_unchecked(
        episode, "has_active_embodied_developmental_capability", capability
    )
    agent.inner.remove_edge_unchecked(plan, "has_selected_learning_plan_step", step)

    request = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "status": "evidenced", "integer_native": 1,
    })
    evidence = agent.s.add_node("EmbodiedExternalTrialEvidence", {
        "grounded": 1, "integer_native": 1, **evidence_attrs,
    })
    counterfactual = agent.s.add_node("Experiment", {
        "status": "counterfactual_done", "integer_native": 1,
    })
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed", "causal_closed": 1, "grounded": 1,
        "integer_native": 1,
    })
    for source, edge, target in (
        (session, "has_grounded_external_trial_request", request),
        (session, "has_selected_embodied_motor_program", old_program),
        (session, "uses_embodied_motor_hint", old_prior),
        (session, "has_counterfactual_embodied_trial", counterfactual),
        (session, "has_causal_embodied_learning_receipt", receipt),
        (request, "has_grounded_external_trial_evidence", evidence),
        (request, "enacts_embodied_motor_program", old_program),
        (evidence, "evidence_for_embodied_trial_request", request),
        (evidence, "measures_embodied_motor_program", old_program),
        (counterfactual, "tests_embodied_motor_program", old_program),
        (request, "has_embodied_learning_trial_receipt", receipt),
        (receipt, "grounded_in_external_trial_evidence", evidence),
        (receipt, "caused_by_embodied_motor_program", old_program),
    ):
        _edge(agent, source, edge, target)
    candidate_count = len(list(agent.s.nodes("ParetoCandidate")))
    program_count = len(list(agent.s.nodes("EmbodiedMotorProgram")))
    agent.tick(max_steps=200)

    revisions = list(agent.s.nodes("EmbodiedMotorProgramRevision"))
    assert len(revisions) == 1
    revision = revisions[0]
    assert agent.s.node(revision)["attrs"]["status"] == "enacted"
    assert agent.inner.neighbours(
        revision, "revises_embodied_motor_program"
    ) == [old_program]
    new_program = agent.inner.neighbours(
        revision, "selects_embodied_motor_program"
    )[0]
    assert agent.s.node(revision)["attrs"]["kind"] == expected_kind
    if expected_kind == "receipt_grounded_temporal_aperture":
        assert new_program == old_program
        # THE APERTURE IS RAISED ON THE BODY, NOT ON THE PROGRAM. This assertion
        # used to read the program's doubled frame count, and that was the
        # defect: the climb was real and it was discarded the next time a
        # different program was selected (measured live -- 44 of 45 programs
        # sat at the bottom of the ladder). Incrementing the body's exponent by
        # 1 IS the same doubling, held where it is true, and every program in
        # the episode now reads it.
        body = agent.inner.neighbours(episode, "has_embodied_body_schema")[0]
        body_attrs = agent.s.node(body)["attrs"]
        assert body_attrs["temporal_aperture_log_units"] == 1
        assert body_attrs["temporal_aperture_measured"] == 1
        assert agent.s.node(new_program)["attrs"]["simulator_frames"] == 26
    else:
        assert new_program != old_program
    assert agent.inner.neighbours(
        revision, "resolves_learning_plan_residual"
    ) == [residual]
    assert agent.s.node(residual)["attrs"]["status"] == "resolved"
    # Supervision remains inspectable; only the revision's enactment restores
    # authority for the same process/step/capability.
    assert agent.s.node(checkin)["attrs"]["status"] == "motor_program_revised"
    assert agent.s.node(process)["attrs"]["status"] == "monitoring"
    assert agent.s.node(process)["attrs"]["continuation_authority"] == 1
    assert agent.s.node(policy)["attrs"]["enabled"] == 1
    assert agent.inner.neighbours(plan, "has_selected_learning_plan_step") == [step]
    assert agent.inner.neighbours(
        episode, "has_active_embodied_developmental_capability"
    ) == [capability]
    assert agent.inner.neighbours(
        motor_episode, "has_embodied_motor_program"
    ) == [new_program]
    assert len(list(agent.s.nodes("ParetoCandidate"))) == candidate_count
    assert len(list(agent.s.nodes("EmbodiedMotorProgram"))) == program_count


def test_two_causal_session_receipts_rearm_selection_and_counterfactual_without_candidate_growth():
    """Exercise the real session receipt rule twice, with boundary evidence.

    The only hand-authored material is integer external evidence—the same
    responsibility as a simulator transducer.  Session, receipt, retirement,
    successor selection, and successor counterfactual are all graph rules.
    """
    agent = _session_agent()
    episode, _body, world, _effectors = _install_body(
        agent, tokens=("opaque/first", "opaque/second")
    )
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 2})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "status": "active", "integer_native": 1,
    })
    pose = agent.s.add_node("EmbodiedPoseAffordance", {"enabled": 1})
    reset = agent.s.add_node("EmbodiedResetRequest", {"status": "requested"})
    scenario = agent.s.add_node("EmbodiedResetScenario", {"ordinal": 0})
    for source, edge, target in (
        (episode, "has_self_directed_learning_plan", plan),
        (plan, "has_selected_learning_plan_step", step),
        (step, "pursues_goal", goal),
        (episode, "has_active_embodied_developmental_capability", capability),
        (world, "has_embodied_pose_affordance", pose),
        (episode, "has_active_embodied_reset_request", reset),
        (reset, "selects_embodied_reset_scenario", scenario),
    ):
        _edge(agent, source, edge, target)
    agent.tick(max_steps=200)

    motor_episode = agent.inner.neighbours(
        episode, "has_embodied_motor_episode"
    )[0]
    session = agent.inner.neighbours(episode, "has_embodied_learning_session")[0]
    candidate_count = len(list(agent.s.nodes("ParetoCandidate")))
    program_count = len(list(agent.s.nodes("EmbodiedMotorProgram")))

    def complete_current_graph_selected_trial(receipt_progress):
        # Detached counterfactual is run by its ordinary boundary dispatcher;
        # it is not marked complete by the test.
        assert scan_and_imagine(agent)
        agent.tick(max_steps=200)
        request = agent.inner.neighbours(
            session, "has_grounded_external_trial_request"
        )[0]
        program = agent.inner.neighbours(
            request, "enacts_embodied_motor_program"
        )[0]
        evidence = agent.s.add_node("EmbodiedExternalTrialEvidence", {
            "grounded": 1, "integer_native": 1,
            "base_displacement_x_units": receipt_progress,
            "base_displacement_y_units": 0,
            "base_displacement_z_units": 0,
            "proprioceptive_configuration_delta_units": [1],
            "proprioceptive_configuration_observed": 1,
            "energy_cost_units": 2, "peak_load_units": 3,
        })
        for source, edge, target in (
            (request, "has_grounded_external_trial_evidence", evidence),
            (evidence, "evidence_for_embodied_trial_request", request),
            (evidence, "measures_embodied_motor_program", program),
            (evidence, "under_embodied_pose_affordance", pose),
            (evidence, "from_embodied_reset_scenario", scenario),
            (evidence, "measures_goal", goal),
        ):
            _edge(agent, source, edge, target)
        agent.tick(max_steps=300)
        return program

    first_selection = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    )[0]
    first_program = complete_current_graph_selected_trial(1)
    second_selection = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    )[0]
    second_program = agent.inner.neighbours(
        second_selection, "selects_embodied_motor_program"
    )[0]
    assert second_selection != first_selection
    assert second_program != first_program
    assert len(list(agent.s.nodes("ParetoCandidate"))) == candidate_count
    assert len(list(agent.s.nodes("EmbodiedMotorProgram"))) == program_count

    complete_current_graph_selected_trial(1)
    selections = agent.inner.neighbours(
        motor_episode, "has_embodied_motor_bootstrap_selection"
    )
    assert len(selections) == 1
    third_program = agent.inner.neighbours(
        selections[0], "selects_embodied_motor_program"
    )[0]
    assert len(list(agent.s.nodes("EmbodiedLearningTrialReceipt"))) == 2
    assert len(list(agent.s.nodes("ParetoCandidate"))) == candidate_count
    assert len(list(agent.s.nodes("EmbodiedMotorProgram"))) == program_count

    running = [trial for trial in agent.inner.neighbours(
        session, "has_counterfactual_embodied_trial"
    ) if agent.s.node(trial)["attrs"].get("status") == "counterfactual_running"]
    assert len(running) == 1
    assert agent.inner.neighbours(
        running[0], "tests_embodied_motor_program"
    ) == [third_program]


def test_real_pybullet_two_receipts_keep_43_motor_pool_stable_and_revision_causal():
    """A physical 43-effector body remains one fixed 43-program pool.

    This is deliberately an end-to-end regression: PyBullet contributes only
    quantized observations/evidence, while imagination, receipts, selection
    retirement, successor epochs, and zero-yield supervisory repair remain
    graph rules.  The second repair must bind receipt two, rather than reuse
    inspectable history from receipt one.
    """
    pytest.importorskip("pybullet")
    from domains.pybullet_humanoid_trial_transducer import (
        PyBulletHumanoidTrialTransducer,
    )

    agent = WorldAdapter(seeds=("embodied_motor_bootstrap",))
    transducer = PyBulletHumanoidTrialTransducer.from_protocol(
        ROOT / "protocols" / "humanoid_developmental_smoke_v1.json", seed=9,
    )
    try:
        transducer.publish_body_world_capabilities(agent)
        assert agent.tick(max_steps=1_000) < 1_000
        episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))[0]
        motor_episode = agent.inner.neighbours(
            episode, "has_embodied_motor_episode"
        )[0]
        session = agent.inner.neighbours(
            episode, "has_embodied_learning_session"
        )[0]

        def motor_pool_counts():
            candidates = [candidate for candidate in agent.s.nodes("ParetoCandidate")
                          if agent.s.node(candidate)["attrs"].get("kind")
                          == "opaque_motor_topology_bootstrap"]
            return len(candidates), len(list(agent.s.nodes("EmbodiedMotorProgram")))

        initial_counts = motor_pool_counts()
        # Each physical action yields all three Cartesian coordinates.  A
        # measurement projection is a graph interpretation of that retained
        # vector, not a reason to clone the same opaque actuator six times.
        assert initial_counts == (43, 43)

        for receipt_sequence in (1, 2):
            assert scan_and_imagine(agent)
            assert agent.tick(max_steps=300) < 300
            requests = [request for request in agent.inner.neighbours(
                session, "has_grounded_external_trial_request"
            ) if agent.s.node(request)["attrs"].get("status") == "requested"]
            assert len(requests) == 1
            transducer(agent, requests[0])
            assert agent.tick(max_steps=300) < 300
            assert motor_pool_counts() == initial_counts
            assert len(agent.inner.neighbours(
                motor_episode, "has_embodied_motor_bootstrap_selection"
            )) == 1

            receipt_sequences = sorted(
                agent.s.node(agent.inner.neighbours(
                    revision, "grounded_in_embodied_learning_receipt"
                )[0])["attrs"]["development_receipt_seq"]
                for revision in agent.s.nodes("EmbodiedMotorProgramRevision")
            )
            assert receipt_sequences == list(range(1, receipt_sequence + 1))
            if receipt_sequence == 2:
                revisions = sorted(
                    agent.s.nodes("EmbodiedMotorProgramRevision"),
                    key=lambda revision: agent.s.node(agent.inner.neighbours(
                        revision, "grounded_in_embodied_learning_receipt"
                    )[0])["attrs"]["development_receipt_seq"],
                )
                assert [agent.s.node(revision)["attrs"]["kind"]
                        for revision in revisions] == [
                    "receipt_grounded_distinct_motor_program",
                    "receipt_grounded_temporal_aperture",
                ]
                temporal = revisions[-1]
                temporal_program = agent.inner.neighbours(
                    temporal, "selects_embodied_motor_program"
                )[0]
                assert agent.inner.neighbours(
                    temporal, "revises_embodied_motor_program"
                ) == [temporal_program]
                contract = list(agent.s.nodes("EmbodiedMotorBootstrapContract"))[0]
                assert agent.s.node(temporal_program)["attrs"]["simulator_frames"] == (
                    2 * agent.s.node(contract)["attrs"]["minimum_actuation_frames"]
                )
    finally:
        transducer.close()


def test_seed_is_reproducible_integer_native_and_declares_its_boundary_dependency():
    generated = manifest()
    assert json.loads(SEED.read_text(encoding="utf-8")) == generated
    _assert_integer_native(generated)
    assert generated["depends_on"] == ["embodied_body_ingest", "cognitive_pareto"]
    serialized = json.dumps(generated)
    for interface in (
        "EmbodiedOpaqueActuatorAffordance", "OpaqueActuatorBundleAffordance",
        "EmbodiedMotorBootstrapContract", "EmbodiedMotorPrior",
        "EmbodiedMotorProgram", "EmbodiedMotorBootstrapSelection",
    ):
        assert interface in serialized
    assert "joint" not in serialized.lower()
    assert "limb" not in serialized.lower()
