from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.gen_embodied_development_seed import CAPABILITIES, manifest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "embodied_development.json"


def _assert_integer_native(value):
    if isinstance(value, float):
        raise AssertionError(f"floating-point cognition value: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_integer_native(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_integer_native(nested)


def test_seed_reproducible_and_integer_native():
    generated = manifest()
    assert json.loads(SEED.read_text(encoding="utf-8")) == generated
    _assert_integer_native(generated)
    assert generated["area"] == "general_cognition"
    assert all(row["attrs"].get("output_authority") == 0
               for row in generated["nodes"])


def test_capability_graph_contains_branching_and_convergence():
    requirements = {row["name"]: set(row["requires"])
                    for row in CAPABILITIES}
    assert requirements["reversible_configuration_control"] == {
        "effector_consequence_survey"
    }
    assert requirements["surface_contact_mapping"] == {
        "spontaneous_general_movement"
    }
    assert requirements["side_lying_transition"] == {
        "surface_contact_mapping", "antigravity_segmental_control"
    }
    assert requirements["supine_prone_rolling"] == {
        "reversible_configuration_control", "side_lying_transition"
    }
    assert requirements["independent_sitting"] == {
        "antigravity_segmental_control", "supine_prone_rolling"
    }
    assert requirements["hands_knees_crawling"] == {
        "quadruped_rocking", "prone_reach_and_pivot"
    }
    # Human crawling is represented and measured, but is not a forced route
    # to upright development: some typically developing children skip it.
    assert "hands_knees_crawling" not in requirements["pull_to_stand"]
    assert requirements["independent_walking"] == {
        "controlled_lowering", "assisted_stepping"
    }


def test_floor_roll_requires_gravity_relative_transition_not_pose_twitch():
    generated = manifest()
    side_lying = next(
        capability
        for capability in CAPABILITIES
        if capability["name"] == "side_lying_transition"
    )
    assert side_lying["desired_body_state_signature"] == [
        ["support_relation", "preserved"],
        ["orientation_change", "quarter_turn"],
    ]
    assert side_lying["desired_orientation_units"] == 1
    rules = {row["name"]: row for row in generated["rules"]}
    tracking = json.dumps(
        rules["ed_track_situated_floor_orientation_trajectory"]
    )
    learning = json.dumps(rules[
        "ed_learn_capability_from_causally_closed_receipt"
    ])
    assert "development_pre_orientation_class" in tracking
    reversal = json.dumps(rules[
        "ed_detect_situated_configuration_reversal"
    ])
    assert "development_pre_configuration_region" in reversal
    assert "development_post_configuration_region" in reversal
    assert "pre_motor_configuration_shape" not in reversal
    assert "development_post_orientation_class" in tracking
    assert "trajectory_half_turn_complete" in tracking
    assert "supported_half_turn" in learning
    assert learning.count("development_half_turn_transition") >= 2
    assert learning.count("trajectory_origin_orientation_class") >= 2
    assert "caregiver_protective_support_applied" in learning


def test_consumed_receipts_leave_hot_edge_but_remain_auditable():
    rules = {row["name"]: row for row in manifest()["rules"]}
    archive = json.dumps(
        rules["ed_archive_consumed_receipt_from_active_working_set"]
    )
    assert "latest_development_receipt_seq" in archive
    assert '"del_edge"' in archive
    assert "has_embodied_development_receipt" in archive
    assert "del_node" not in archive


def test_locomotor_basins_are_recurrent_integer_pareto_shapes():
    generated = manifest()
    rules = {row["name"]: row for row in generated["rules"]}
    assert {
        "ed_instantiate_situated_locomotor_pareto_profile",
        "ed_mint_novel_locomotor_phenotype_from_receipt",
        "ed_accumulate_recurrent_locomotor_phenotype",
        "ed_verify_recurrent_locomotor_basin_on_pareto_basis",
    } <= rules.keys()
    profile = json.dumps(
        rules["ed_instantiate_situated_locomotor_pareto_profile"]
    )
    for dimension in (
        "directed_progress", "path_length", "lateral_excursion",
        "energy", "peak_load", "directed_consistency",
    ):
        assert dimension in profile
    assert "bounded_motion" not in profile
    verify = json.dumps(
        rules["ed_verify_recurrent_locomotor_basin_on_pareto_basis"]
    )
    assert "development_evidence_window" in verify
    assert "has_pareto_candidate" in verify
    assert "sum_directed_consistency" in verify
    assert '"scalarized": 0' in profile


def test_locomotor_consistency_is_relative_to_requested_direction():
    rules = {row["name"]: row for row in manifest()["rules"]}
    mint = json.dumps(
        rules["ed_mint_novel_locomotor_phenotype_from_receipt"]
    )
    accumulate = json.dumps(
        rules["ed_accumulate_recurrent_locomotor_phenotype"]
    )

    # The graph counts agreement with the already-situated heading projection,
    # rather than quietness or a canonical upright pose.  Positive projected
    # movement contributes one recurrence vote; zero/negative movement does
    # not, while directed-progress magnitude remains a separate coordinate.
    assert "development_directed_units" in mint
    assert "sum_directed_consistency" in mint
    assert '"type": "Gt"' in mint
    assert "development_directed_units" in accumulate
    assert "sum_directed_consistency" in accumulate
    assert "development_motion_nonamplifying" not in mint
    assert "development_motion_nonamplifying" not in accumulate


def test_locomotor_pareto_escalation_runs_general_dominance_faculty():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    profile = agent.s.add_node("ParetoProfile", {"dimension_count": 2})
    candidates = []
    for identity, values in (("incumbent", (0, -2)), ("better", (1, -1))):
        candidate = agent.s.add_node("ParetoCandidate", {
            "identity": identity, "verified": 1, "dominated": 0,
        })
        candidates.append(candidate)
        agent.inner.add_edge(profile, "has_pareto_candidate", candidate)
        for ordinal, value in enumerate(values):
            coordinate = agent.s.add_node("ParetoValue", {
                "dimension_ordinal": ordinal,
                "signed_value": value,
                "verified": 1,
            })
            agent.inner.add_edge(candidate, "has_pareto_value", coordinate)
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "area": "cognitive_pareto", "enabled": 1,
    })
    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "test", "epoch": 1,
    })
    agent.inner.add_edge(escalation, "about_context", profile)
    agent.inner.add_edge(escalation, "recruits_task_set", task_set)

    report = agent.dual_process_tick()
    assert report["system_two_escalations"] == 1
    assert agent.inner.neighbours(
        candidates[0], "is_dominated_by_pareto_candidate"
    ) == [candidates[1]]


def test_learning_is_causal_varied_and_retention_gated():
    rules = {row["name"]: row for row in manifest()["rules"]}
    learn = json.dumps(rules[
        "ed_learn_capability_from_causally_closed_receipt"
    ])
    competence = json.dumps(
        rules["ed_open_delayed_retention_test_after_varied_competence"]
    )
    retention = json.dumps(
        rules["ed_master_only_after_delayed_successful_retest"]
    )
    assert "activation_receipt_seq" in learn
    assert "development_receipt_closed" in learn
    assert "has_embodied_developmental_context" in competence
    assert "development_evidence_window" in competence
    assert "retention_start_seq" in retention
    store = json.dumps(
        rules["ed_store_mastered_capability_by_structural_body_shape"]
    )
    assert "evidence_kind" in store
    assert "mastery_receipt_seq" in store


def test_closed_adverse_receipt_is_retained_without_release_or_success_credit():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "retained_developmental_experience_count": 0,
        "caregiver_buffered_experience_count": 0,
        "unbuffered_experience_count": 0,
    })
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "development_experience_retained": 0,
        "development_recoverability_units": 0,
        "development_unbuffered_exposure_units": 1,
        "development_peak_load_units": 999,
        "development_support_gain": -1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", receipt
    )

    agent.tick()

    assert agent.s.node(receipt)["attrs"][
        "development_experience_retained"
    ] == 1
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["retained_developmental_experience_count"] == 1
    assert attrs["caregiver_buffered_experience_count"] == 0
    assert attrs["unbuffered_experience_count"] == 1
    assert "contextual_release_eligible" not in agent.s.node(receipt)["attrs"]


def test_destroyed_embodiment_is_retained_then_graph_selects_reset_scenario():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "latest_development_receipt_seq": 7,
        "retained_developmental_experience_count": 0,
        "caregiver_buffered_experience_count": 0,
        "unbuffered_experience_count": 0,
        "embodiment_reset_available": 1,
        "embodiment_reset_cost_units": 11,
        "last_body_reset_cost_units": 0,
        "embodiment_reset_cost_total_units": 0,
        "embodiment_generation": 3,
        "embodiment_reset_iteration_count": 0,
        "embodiment_terminal": 0,
        "terminal_receipt_seq": 0,
        "embodied_reset_requested": 0,
        "reset_requested": 0,
        "body_reset_seq": 0,
        "embodied_reset_processed_seq": 0,
    })
    instance = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        # Situated instances created by ed_instantiate_capability_in_situated_body
        # expose their identity as `name`, not an auxiliary capability_name.
        "name": "effector_consequence_survey",
        "goal": "effector_discovery",
        "status": "active",
    })
    matching = agent.s.add_node("EmbodiedResetScenario", {
        "name": "effector_fixture",
        "ordinal": 4,
        "target_goal": "effector_discovery",
        "fixture_quarter_turn_x": 1,
        "fixture_quarter_turn_y": 0,
        "fixture_quarter_turn_z": 0,
        "selection_count": 0,
        "enabled": 1,
    })
    generic = agent.s.add_node("EmbodiedResetScenario", {
        "name": "generic_fixture",
        "ordinal": 5,
        "target_goal": "any",
        "fixture_quarter_turn_x": 0,
        "fixture_quarter_turn_y": 0,
        "fixture_quarter_turn_z": 0,
        "selection_count": 9,
        "enabled": 1,
    })
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "development_experience_retained": 0,
        "development_recoverability_units": 0,
        "development_unbuffered_exposure_units": 1,
        "development_receipt_seq": 7,
        "embodiment_destroyed": 1,
        "embodiment_terminal_recorded": 0,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.inner.add_edge(
        episode, "has_active_embodied_developmental_capability", instance
    )
    agent.inner.add_edge(episode, "has_embodied_reset_scenario", matching)
    agent.inner.add_edge(episode, "has_embodied_reset_scenario", generic)
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", receipt
    )

    agent.tick()

    requests = agent.inner.neighbours(
        episode, "has_active_embodied_reset_request"
    )
    assert len(requests) == 1
    request_attrs = agent.s.node(requests[0])["attrs"]
    assert agent.s.node(receipt)["attrs"][
        "development_experience_retained"
    ] == 1
    assert request_attrs["cause_receipt_seq"] == 7
    assert request_attrs["retained_experience_count"] == 1
    assert request_attrs["reinstantiation_spec_ready"] == 1
    assert request_attrs["scenario_name"] == "effector_fixture"
    assert request_attrs["target_capability"] == (
        "effector_consequence_survey"
    )
    assert request_attrs["output_authority"] == 1
    assert agent.s.node(episode)["attrs"]["reset_requested"] == 1

    agent.inner.set_attr(episode, "last_body_reset_cost_units", 11)
    agent.inner.set_attr(episode, "body_reset_seq", 8)
    agent.tick()

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["embodiment_generation"] == 4
    assert attrs["embodiment_reset_iteration_count"] == 1
    assert attrs["embodiment_reset_cost_total_units"] == 11
    assert attrs["retained_developmental_experience_count"] == 1
    assert attrs["reset_requested"] == 0
    assert agent.s.node(requests[0])["attrs"]["status"] == "enacted"


def test_destruction_without_reset_still_becomes_durable_terminal_evidence():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "latest_development_receipt_seq": 1,
        "retained_developmental_experience_count": 0,
        "caregiver_buffered_experience_count": 0,
        "unbuffered_experience_count": 0,
        "embodiment_reset_available": 0,
        "embodiment_terminal": 0,
        "terminal_receipt_seq": 0,
        "embodied_reset_requested": 0,
    })
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "development_experience_retained": 0,
        "development_recoverability_units": 0,
        "development_unbuffered_exposure_units": 1,
        "development_receipt_seq": 1,
        "embodiment_destroyed": 1,
        "embodiment_terminal_recorded": 0,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", receipt
    )

    agent.tick()

    assert agent.s.node(receipt)["attrs"][
        "development_experience_retained"
    ] == 1
    assert agent.s.node(episode)["attrs"]["embodiment_terminal"] == 1
    assert not agent.inner.neighbours(
        episode, "has_active_embodied_reset_request"
    )


def test_failure_window_voluntarily_requests_a_more_informative_scenario():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 2,
        "latest_development_receipt_seq": 2,
        "retained_developmental_experience_count": 0,
        "caregiver_buffered_experience_count": 0,
        "unbuffered_experience_count": 0,
        "embodiment_reset_available": 1,
        "embodiment_reset_cost_units": 6,
        "embodiment_generation": 0,
        "embodiment_terminal": 0,
        "embodied_reset_requested": 0,
    })
    instance = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "capability_name": "surface_contact_mapping",
        "goal": "surface_contact_mapping",
        "evidence_kind": "support_topology_change",
        "status": "active",
        "attempt_count": 1,
        "success_count": 0,
        "failure_count": 1,
        "last_receipt_seq": 1,
        "activation_receipt_seq": 0,
        "last_reinstantiation_failure_count": 0,
    })
    scenario = agent.s.add_node("EmbodiedResetScenario", {
        "name": "contact_rich_fixture",
        "ordinal": 2,
        "target_goal": "surface_contact_mapping",
        "fixture_quarter_turn_x": 1,
        "fixture_quarter_turn_y": 0,
        "fixture_quarter_turn_z": 0,
        "selection_count": 0,
        "enabled": 1,
    })
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "development_experience_retained": 0,
        "development_recoverability_units": 0,
        "development_unbuffered_exposure_units": 1,
        "development_receipt_seq": 2,
        "development_support_topology_changed": 0,
        "embodiment_destroyed": 0,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.inner.add_edge(
        episode, "has_active_embodied_developmental_capability", instance
    )
    agent.inner.add_edge(episode, "has_embodied_reset_scenario", scenario)
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", receipt
    )

    agent.tick()

    requests = agent.inner.neighbours(
        episode, "has_active_embodied_reset_request"
    )
    assert len(requests) == 1
    attrs = agent.s.node(requests[0])["attrs"]
    assert attrs["cause"] == "capability_experiment_stalled"
    assert attrs["scenario_name"] == "contact_rich_fixture"
    assert attrs["reinstantiation_spec_ready"] == 1
    assert agent.s.node(instance)["attrs"][
        "last_reinstantiation_failure_count"
    ] == 2


def test_learning_plan_owns_objective_budget_and_replanning():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 2,
        "latest_development_receipt_seq": 0,
        "retained_developmental_experience_count": 0,
        "caregiver_buffered_experience_count": 0,
        "unbuffered_experience_count": 0,
        "embodiment_reset_available": 1,
        "embodiment_reset_cost_units": 6,
        "embodiment_terminal": 0,
        "embodied_reset_requested": 0,
        "development_effector_coverage_complete": 0,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.tick()

    plans = agent.inner.neighbours(episode, "has_self_directed_learning_plan")
    assert len(plans) == 1
    plan = plans[0]
    plan_attrs = agent.s.node(plan)["attrs"]
    steps = agent.inner.neighbours(plan, "has_learning_plan_step")
    capabilities = agent.inner.neighbours(
        episode, "has_embodied_developmental_capability"
    )
    assert len(steps) == len(capabilities)
    assert plan_attrs["decision_count"] == 1
    assert plan_attrs["replan_count"] == 0
    assert plan_attrs["integer_native"] == 1
    assert plan_attrs["output_authority"] == 0

    profiles = agent.inner.neighbours(plan, "has_learning_decision_profile")
    assert len(profiles) == 1
    profile = profiles[0]
    assert agent.s.node(profile)["attrs"]["scalarized"] == 0
    assert {
        agent.s.node(dimension)["attrs"]["name"]
        for dimension in agent.inner.neighbours(
            profile, "has_pareto_dimension"
        )
    } == {
        "information_gap",
        "prerequisite_unlocks",
        "retention_urgency",
        "transfer_overlap",
        "experiment_cost",
    }
    selected = agent.inner.neighbours(plan, "has_selected_learning_decision")
    assert len(selected) == 1
    assert not agent.inner.neighbours(
        selected[0], "is_dominated_by_pareto_candidate"
    )
    assert len(agent.inner.neighbours(
        selected[0], "has_pareto_value"
    )) == 5

    active = agent.inner.neighbours(
        episode, "has_active_embodied_developmental_capability"
    )
    assert len(active) == 1
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "development_experience_retained": 0,
        "development_recoverability_units": 0,
        "development_unbuffered_exposure_units": 1,
        "development_receipt_seq": 1,
        "development_configuration_changed": 0,
        "development_external_event": 0,
        "embodiment_destroyed": 0,
    })
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", receipt
    )
    agent.inner.set_attr(episode, "latest_development_receipt_seq", 1)

    agent.tick()

    plan_attrs = agent.s.node(plan)["attrs"]
    assert plan_attrs["decision_count"] == 2
    assert plan_attrs["replan_count"] == 1
    assert len(agent.inner.neighbours(
        plan, "has_learning_decision_profile"
    )) == 2
    selected_steps = agent.inner.neighbours(
        plan, "has_selected_learning_plan_step"
    )
    assert len(selected_steps) == 1
    selected_step = selected_steps[0]
    step_attrs = agent.s.node(selected_step)["attrs"]
    assert step_attrs["evidence_spent_units"] >= 1
    initial_budget = step_attrs["evidence_budget_units"]

    reset_request = agent.s.add_node("EmbodiedResetRequest", {
        "status": "requested",
        "cause_receipt_seq": 2,
    })
    agent.inner.add_edge(
        episode, "has_active_embodied_reset_request", reset_request
    )
    agent.tick()

    step_attrs = agent.s.node(selected_step)["attrs"]
    assert step_attrs["revision_count"] == 1
    assert step_attrs["evidence_budget_units"] == initial_budget + 2
    assert agent.inner.neighbours(
        reset_request, "revises_learning_plan_step"
    ) == [selected_step]


@pytest.mark.parametrize(
    ("reset_available", "configuration_changed", "expected_status"),
    (
        (1, 1, "extended"),
        (0, 0, "deferred"),
    ),
)
def test_learning_budget_exhaustion_is_an_explicit_plan_decision(
    reset_available, configuration_changed, expected_status
):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 1,
        "latest_development_receipt_seq": 0,
        "retained_developmental_experience_count": 0,
        "caregiver_buffered_experience_count": 0,
        "unbuffered_experience_count": 0,
        "embodiment_reset_available": reset_available,
        "embodiment_reset_cost_units": 4,
        "embodiment_generation": 0,
        "embodiment_terminal": 0,
        "embodied_reset_requested": 0,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.tick()
    plan = agent.inner.neighbours(
        episode, "has_self_directed_learning_plan"
    )[0]
    step = agent.inner.neighbours(
        plan, "has_selected_learning_plan_step"
    )[0]
    instance = agent.inner.neighbours(
        step, "plans_learning_capability"
    )[0]
    initial_budget = agent.s.node(step)["attrs"]["evidence_budget_units"]
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "development_experience_retained": 0,
        "development_recoverability_units": 0,
        "development_unbuffered_exposure_units": 1,
        "development_receipt_seq": 1,
        "development_configuration_changed": configuration_changed,
        "development_external_event": 0,
        "embodiment_destroyed": 0,
    })
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", receipt
    )
    agent.inner.set_attr(episode, "latest_development_receipt_seq", 1)
    agent.tick()

    if expected_status == "extended":
        assert agent.s.node(step)["attrs"]["evidence_budget_units"] == (
            initial_budget + 1
        )
        assert agent.s.node(plan)["attrs"]["budget_revision_count"] == 1
        revisions = agent.inner.neighbours(
            plan, "has_learning_plan_revision"
        )
        assert len(revisions) == 1
        assert agent.s.node(revisions[0])["attrs"]["reason"] == (
            "observed_learning_progress"
        )
    else:
        assert agent.s.node(step)["attrs"]["status"] == "deferred"
        assert agent.s.node(instance)["attrs"]["status"] == "plan_deferred"
        assert agent.s.node(plan)["attrs"]["deferred_step_count"] == 1


def test_development_reuses_generic_goal_tree_and_effector_subgoals():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 4,
        "latest_development_receipt_seq": 0,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.tick()
    plan = agent.inner.neighbours(
        episode, "has_self_directed_learning_plan"
    )[0]
    steps = agent.inner.neighbours(plan, "has_learning_plan_step")
    effector_step = next(
        step for step in steps
        if agent.s.node(step)["attrs"]["goal"] == "effector_discovery"
    )
    root_goal = agent.inner.neighbours(effector_step, "pursues_goal")[0]
    assert agent.s.node(root_goal)["type"] == "Goal"

    field = agent.s.add_node("SomatomotorWaveField", {})
    cell = agent.s.add_node("SomatomotorWaveCell", {
        "verified_consequence_count": 0,
    })
    effector = agent.s.add_node("Node", {
        "channel_ordinal": 3,
    })
    agent.inner.add_edge(episode, "has_somatomotor_wave_field", field)
    agent.inner.add_edge(field, "has_somatomotor_wave_cell", cell)
    agent.inner.add_edge(cell, "represents_embodied_effector", effector)
    agent.tick()

    consequence_goal = agent.inner.neighbours(
        cell, "has_consequence_goal"
    )[0]
    assert consequence_goal in agent.inner.neighbours(
        root_goal, "has_subgoal"
    )
    assert agent.s.node(consequence_goal)["attrs"]["progress_units"] == 0

    agent.inner.set_attr(cell, "verified_consequence_count", 1)
    agent.tick()
    assert agent.s.node(consequence_goal)["attrs"]["status"] == "resolved"
    assert agent.s.node(consequence_goal)["attrs"]["progress_units"] == 1
    agent.inner.set_attr(cell, "verified_consequence_count", 2)
    agent.tick()
    assert agent.s.node(consequence_goal)["attrs"]["progress_units"] == 1


def test_no_canonical_pose_anatomy_or_direct_actuation_is_encoded():
    text = json.dumps(manifest()).lower()
    for forbidden in (
        "home", "canonical_pose", "joint_angle", "target_torque",
        "left_arm", "right_leg",
    ):
        assert forbidden not in text


def test_output_null_capability_memory_survives_library_round_trip():
    from scripts.jabberwock_humanoid_walk import (
        MOTOR_LIBRARY_VERSION,
        developmental_curriculum_contract,
        _motor_library_snapshot,
        _restore_motor_library,
    )
    from substrate.world_adapter import WorldAdapter

    try:
        source = WorldAdapter(seeds=("somatomotor_waves",))
        target = WorldAdapter(seeds=("somatomotor_waves",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    memory = source.s.add_node("EmbodiedDevelopmentalCapabilityMemory", {
        "name": "developmental_capability:test:related-shape",
        "signature": (("link_count", 9), ("terminal_count", 4)),
        "capability_name": "surface_contact_mapping",
        "goal": "surface_contact_mapping",
        "evidence_kind": "support_topology_change",
        "success_count": 4,
        "failure_count": 1,
        "mastery_receipt_seq": 19,
        "context_count": 3,
        "retention_count": 1,
        "output_authority": 0,
        "integer_native": 1,
    })
    source.inner.add_edge(
        source.agent,
        "has_embodied_developmental_capability_memory",
        memory,
    )
    coupling_memory = source.s.add_node("SomatomotorCouplingMemory", {
        "name": "somatomotor_coupling:test:1",
        "signature": (("link_count", 9), ("terminal_count", 4)),
        "same_command_channel": 0,
        "declared_hard_coupling": 0,
        "mechanical_path_known": 1,
        "mechanical_path_length": 1,
        "same_mount": 0,
        "command_polarity_product": -1,
        "productive_count": 5,
        "unproductive_count": 2,
        "output_authority": 0,
        "integer_native": 1,
    })
    source.inner.add_edge(
        source.agent,
        "has_somatomotor_coupling_memory",
        coupling_memory,
    )
    snapshot = json.loads(json.dumps(_motor_library_snapshot(source)))
    assert snapshot["version"] == MOTOR_LIBRARY_VERSION
    assert snapshot["developmental_curriculum_contract"] == (
        developmental_curriculum_contract()
    )
    assert snapshot["developmental_capabilities"]
    assert snapshot["somatomotor_couplings"]

    restored = _restore_motor_library(target, snapshot)
    assert restored["developmental_curriculum_contract_digest"] == (
        snapshot["developmental_curriculum_contract"]["ontology_sha256"]
    )
    assert restored["developmental_capability_count"] == 1
    assert restored["somatomotor_coupling_count"] == 1
    memories = target.inner.neighbours(
        target.agent, "has_embodied_developmental_capability_memory"
    )
    assert len(memories) == 1
    attrs = target.s.node(memories[0])["attrs"]
    assert attrs["output_authority"] == 0
    assert attrs["integer_native"] == 1
    assert attrs["mastery_receipt_seq"] == 19
    coupling_memories = target.inner.neighbours(
        target.agent, "has_somatomotor_coupling_memory"
    )
    assert len(coupling_memories) == 1
    coupling_attrs = target.s.node(coupling_memories[0])["attrs"]
    assert coupling_attrs["output_authority"] == 0
    assert coupling_attrs["integer_native"] == 1
    assert coupling_attrs["productive_count"] == 5


def test_developmental_library_contract_is_fail_closed_for_missing_or_stale_data():
    from scripts.jabberwock_humanoid_walk import (
        _motor_library_snapshot,
        _restore_motor_library,
    )
    from substrate.world_adapter import WorldAdapter

    try:
        source = WorldAdapter(seeds=("embodied_development",))
        target = WorldAdapter(seeds=("embodied_development",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")

    snapshot = _motor_library_snapshot(source)
    missing = dict(snapshot)
    missing.pop("developmental_curriculum_contract")
    with pytest.raises(ValueError, match="missing developmental_curriculum_contract"):
        _restore_motor_library(target, missing)

    stale = json.loads(json.dumps(snapshot))
    stale["developmental_curriculum_contract"]["ontology_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="curriculum contract mismatch"):
        _restore_motor_library(target, stale)


def test_preserved_legacy_humanoid_library_is_rejected_as_incompatible():
    from scripts.jabberwock_humanoid_walk import _restore_motor_library
    from substrate.world_adapter import WorldAdapter

    artifact = ROOT / "results" / "humanoid_developmental_capability_library_v1.json"
    if not artifact.exists():
        pytest.skip("preserved legacy artifact is unavailable")
    try:
        target = WorldAdapter(seeds=("embodied_development",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    legacy = json.loads(artifact.read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="missing developmental_curriculum_contract"):
        _restore_motor_library(target, legacy)


def test_partial_developmental_experience_round_trip_restores_evidence_not_mastery():
    from scripts.jabberwock_humanoid_walk import (
        _motor_library_snapshot,
        _restore_motor_library,
    )
    from substrate.world_adapter import WorldAdapter

    signature = (("articulated_body", 1), ("link_count", 8))
    source = WorldAdapter(seeds=("embodied_development",))
    target = WorldAdapter(seeds=("embodied_development",))
    memory = source.s.add_node("EmbodiedDevelopmentalExperienceMemory", {
        "name": "developmental_experience:orientation_change:test",
        "signature": signature,
        "capability_name": "side_lying_transition",
        "goal": "orientation_change",
        "evidence_kind": "supported_quarter_turn",
        "status": "retention_due",
        "attempt_count": 149,
        "success_count": 9,
        "failure_count": 140,
        "retention_pending": 1,
        "output_authority": 0,
        "integer_native": 1,
    })
    source.inner.add_edge(
        source.agent,
        "has_embodied_developmental_experience_memory",
        memory,
    )
    context = source.s.add_node(
        "EmbodiedDevelopmentalExperienceContextMemory",
        {
            "signature": (("orientation_class", 1),),
            "output_authority": 0,
            "integer_native": 1,
        },
    )
    source.inner.add_edge(
        memory,
        "has_embodied_developmental_experience_context",
        context,
    )

    snapshot = json.loads(json.dumps(_motor_library_snapshot(source)))
    restored = _restore_motor_library(target, snapshot)
    assert restored["developmental_experience_count"] == 1
    assert restored["developmental_experience_context_count"] == 1

    episode = target.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": signature,
        "development_evidence_window": 9,
        "development_learning_active": 0,
        "latest_development_receipt_seq": 0,
        "embodied_developmental_mastery_count": 0,
        "developmental_exact_body_recall_count": 0,
        "active_embodied_developmental_goal": "inactive",
        "active_embodied_developmental_capability": "inactive",
        "output_authority": 0,
        "integer_native": 1,
    })
    target.inner.add_edge(
        target.agent, "has_embodied_development_episode", episode
    )
    target.tick()

    capability = next(
        node for node in target.inner.neighbours(
            episode, "has_embodied_developmental_capability"
        )
        if target.s.node(node)["attrs"]["goal"] == "orientation_change"
    )
    attrs = target.s.node(capability)["attrs"]
    assert attrs["attempt_count"] == 149
    assert attrs["success_count"] == 9
    assert attrs["failure_count"] == 140
    assert attrs["status"] == "retention_due"
    assert attrs["output_authority"] == 0
    assert len(target.inner.neighbours(
        capability, "has_embodied_developmental_context"
    )) == 1


@pytest.mark.parametrize(
    ("target_signature", "expected_warm_count"),
    (
        (
            (("articulated_body", 1), ("link_count", 9),
             ("terminal_count", 4), ("maximum_chain_order", 3)),
            1,
        ),
        (
            (("articulated_body", 1), ("link_count", 2),
             ("terminal_count", 1), ("maximum_chain_order", 1)),
            0,
        ),
    ),
)
def test_shape_similarity_controls_cross_body_warm_start(
    target_signature, expected_warm_count
):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    memory = agent.s.add_node("EmbodiedDevelopmentalCapabilityMemory", {
        "name": "developmental_capability:test:source-body",
        "signature": (
            ("articulated_body", 1), ("link_count", 8),
            ("terminal_count", 4), ("maximum_chain_order", 3),
        ),
        "goal": "effector_discovery",
        "capability_name": "effector_consequence_survey",
        "evidence_kind": "effector_coverage",
        "output_authority": 0,
        "integer_native": 1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_developmental_capability_memory", memory
    )
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": target_signature,
        "development_evidence_window": 2,
        "development_effector_coverage_complete": 0,
        "development_learning_active": 0,
        "latest_development_receipt_seq": 0,
        "embodied_developmental_mastery_count": 0,
        "developmental_cross_body_warm_start_count": 0,
        "active_embodied_developmental_goal": "inactive",
        "active_embodied_developmental_capability": "inactive",
        "output_authority": 0,
        "integer_native": 1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.tick()

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["developmental_cross_body_warm_start_count"] == (
        expected_warm_count
    )
    survey = next(
        node for node in agent.inner.neighbours(
            episode, "has_embodied_developmental_capability"
        )
        if agent.s.node(node)["attrs"]["goal"] == "effector_discovery"
    )
    survey_attrs = agent.s.node(survey)["attrs"]
    assert survey_attrs["warm_start_requires_verification"] == (
        expected_warm_count
    )
    assert survey_attrs["output_authority"] == 0


def test_exact_body_memory_reopens_retention_but_not_output_authority():
    from substrate.world_adapter import WorldAdapter

    signature = (("articulated_body", 1), ("link_count", 8))
    agent = WorldAdapter(seeds=("embodied_development",))
    memory = agent.s.add_node("EmbodiedDevelopmentalCapabilityMemory", {
        "name": "developmental_capability:test:exact-body",
        "signature": signature,
        "goal": "effector_discovery",
        "capability_name": "effector_consequence_survey",
        "evidence_kind": "effector_coverage",
        "output_authority": 0,
        "integer_native": 1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_developmental_capability_memory", memory
    )
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": signature,
        "development_evidence_window": 3,
        "development_learning_active": 0,
        "latest_development_receipt_seq": 11,
        "developmental_exact_body_recall_count": 0,
        "output_authority": 0,
        "integer_native": 1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.tick()
    survey = next(
        node for node in agent.inner.neighbours(
            episode, "has_embodied_developmental_capability"
        )
        if agent.s.node(node)["attrs"]["goal"] == "effector_discovery"
    )
    attrs = agent.s.node(survey)["attrs"]
    assert attrs["status"] == "retention_due"
    assert attrs["retention_start_seq"] == 8
    assert attrs["warm_start_requires_verification"] == 1
    assert attrs["output_authority"] == 0
