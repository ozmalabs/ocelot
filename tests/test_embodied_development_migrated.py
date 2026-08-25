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
    prone = next(
        capability
        for capability in CAPABILITIES
        if capability["name"] == "prone_reach_and_pivot"
    )
    assert prone["desired_body_state_signature"] == [
        ["support_relation", "preserved"],
        ["directed_translation", "increasing"],
        ["orientation_change", "bounded"],
    ]
    crawling = next(
        capability
        for capability in CAPABILITIES
        if capability["name"] == "belly_crawling"
    )
    assert crawling["desired_body_state_signature"] == [
        ["support_topology_change", "cyclic"],
        ["directed_translation", "increasing"],
        ["height_energy_relation", "bounded"],
        ["orientation_change", "bounded"],
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
        "ed_mint_locomotor_phenotype_family_from_receipt",
        "ed_accumulate_locomotor_phenotype_family",
        "ed_bind_locomotor_phenotype_refinement_to_family",
        "ed_verify_recurrent_locomotor_family_on_pareto_basis",
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
    assert "sum_directed_units" in verify
    assert '"type": "Minus"' in verify
    assert '"scalarized": 0' in profile

    family = json.dumps(
        rules["ed_mint_locomotor_phenotype_family_from_receipt"]
    )
    binding = json.dumps(
        rules["ed_bind_locomotor_phenotype_refinement_to_family"]
    )
    assert "development_locomotor_phenotype_family_signature" in family
    assert '"shape_order": 0' in family
    assert "refines_locomotor_phenotype_family" in binding


def test_locomotor_family_accumulates_distinct_dynamic_refinements():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 2,
        "latest_development_receipt_seq": 1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    parent_signature = (
        ("action_intent", "learned_walk"),
        ("support_transition", 1),
        ("support_count", 1),
    )
    parent_key = json.dumps(parent_signature, separators=(",", ":"))

    def add_receipt(seq, refinement):
        signature = (*parent_signature, ("vertical_impulse_sign", refinement))
        receipt = agent.s.add_node("Node", {
            "development_receipt_closed": 1,
            "development_locomotor_cycle_evidence": 1,
            "development_receipt_seq": seq,
            "development_locomotor_phenotype_signature": signature,
            "development_locomotor_phenotype_key": json.dumps(
                signature, separators=(",", ":")
            ),
            "development_locomotor_phenotype_family_signature": parent_signature,
            "development_locomotor_phenotype_family_key": parent_key,
            "development_directed_units": 1,
            "development_translation_units": 1,
            "development_lateral_units": 0,
            "development_energy_units": 1,
            "development_peak_load_units": 1,
        })
        agent.inner.add_edge(
            episode, "has_embodied_development_receipt", receipt
        )

    add_receipt(1, -1)
    agent.tick()
    agent.inner.set_attr(episode, "latest_development_receipt_seq", 2)
    add_receipt(2, 0)
    agent.tick()

    families = agent.inner.neighbours(
        episode, "has_embodied_locomotor_phenotype_family"
    )
    leaves = agent.inner.neighbours(
        episode, "has_embodied_locomotor_phenotype"
    )
    assert len(families) == 1
    assert len(leaves) == 2
    family_attrs = agent.s.node(families[0])["attrs"]
    assert family_attrs["occurrence_count"] == 2
    assert family_attrs["status"] == "verified_basin"
    assert all(agent.inner.neighbours(
        leaf, "refines_locomotor_phenotype_family"
    ) == families for leaf in leaves)


def test_translated_action_mints_shape_without_contact_cycle():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 3,
        "latest_development_receipt_seq": 1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    signature = (
        ("action_intent", "learned_walk"),
        ("developmental_capability", "running"),
        ("motor_program", "aerial_program"),
        ("pre_distal_support_code", 0),
        ("pre_whole_body_support_count", 0),
        ("distal_support_code", 0),
        ("distal_support_transition", 0),
        ("whole_body_support_count", 0),
        ("aerial", 1),
        ("pre_orientation_class", 3),
        ("post_orientation_class", 3),
        ("vertical_impulse_sign", 0),
        ("motion_nonamplifying", 1),
    )
    family_signature = (*signature[:2], *signature[5:11])
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "development_locomotor_cycle_evidence": 0,
        "development_receipt_seq": 1,
        "development_locomotor_phenotype_signature": signature,
        "development_locomotor_phenotype_key": json.dumps(
            signature, separators=(",", ":")
        ),
        "development_locomotor_phenotype_family_signature": family_signature,
        "development_locomotor_phenotype_family_key": json.dumps(
            family_signature, separators=(",", ":")
        ),
        "development_action_intent": "learned_walk",
        "developmental_capability": "running",
        "development_motor_program_key": "aerial_program",
        "development_primary_token": "aerial_program",
        "development_secondary_token": "",
        "development_pre_orientation_class": 3,
        "development_post_orientation_class": 3,
        "development_pre_distal_support_code": 0,
        "development_pre_support_count": 0,
        "development_directed_units": 1,
        "development_translation_units": 1,
        "development_lateral_units": 0,
        "development_energy_units": 1,
        "development_peak_load_units": 0,
    })
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", receipt
    )

    agent.tick()

    leaves = agent.inner.neighbours(
        episode, "has_embodied_locomotor_phenotype"
    )
    assert len(leaves) == 1
    assert agent.s.node(leaves[0])["attrs"]["developmental_capability"] == (
        "running"
    )

    # The exception is foveated to walking. A translated developmental probe
    # without a contact cycle must not enlarge the locomotor hot frontier.
    probe_signature = (
        ("action_intent", "get_up_explore"), *signature[1:]
    )
    probe_attrs = dict(agent.s.node(receipt)["attrs"])
    probe_attrs.update({
        "development_receipt_seq": 2,
        "development_action_intent": "get_up_explore",
        "development_locomotor_phenotype_signature": probe_signature,
        "development_locomotor_phenotype_key": json.dumps(
            probe_signature, separators=(",", ":")
        ),
    })
    probe = agent.s.add_node("Node", probe_attrs)
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", probe
    )
    agent.inner.set_attr(episode, "latest_development_receipt_seq", 2)
    agent.tick()
    assert len(agent.inner.neighbours(
        episode, "has_embodied_locomotor_phenotype"
    )) == 1

    recurrent_attrs = dict(agent.s.node(receipt)["attrs"])
    recurrent_attrs["development_receipt_seq"] = 3
    recurrent_attrs["development_locomotor_phenotype_novel"] = 0
    recurrent = agent.s.add_node("Node", recurrent_attrs)
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", recurrent
    )
    agent.inner.set_attr(episode, "latest_development_receipt_seq", 3)
    agent.tick()

    leaves = agent.inner.neighbours(
        episode, "has_embodied_locomotor_phenotype"
    )
    families = agent.inner.neighbours(
        episode, "has_embodied_locomotor_phenotype_family"
    )
    assert agent.s.node(leaves[0])["attrs"]["occurrence_count"] == 2
    assert len(families) == 1
    assert agent.s.node(families[0])["attrs"]["occurrence_count"] == 2
    assert agent.inner.neighbours(
        leaves[0], "refines_locomotor_phenotype_family"
    ) == families


def test_recurrent_contrary_family_is_not_a_locomotor_basin():
    rules = {row["name"]: row for row in manifest()["rules"]}
    verify = json.dumps(
        rules["ed_verify_recurrent_locomotor_family_on_pareto_basis"]
    )
    assert "sum_directed_units" in verify
    assert "sum_directed_consistency" in verify
    assert '"type": "Minus"' in verify


def test_ambiguous_locomotor_family_escalates_to_program_refinements():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 3,
        "latest_development_receipt_seq": 1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    family_signature = (
        ("action_intent", "learned_walk"),
        ("developmental_capability", "independent_walking"),
        ("distal_support_code", 1),
        ("distal_support_transition", 1),
        ("whole_body_support_count", 1),
        ("aerial", 0),
        ("pre_orientation_class", 3),
        ("post_orientation_class", 3),
    )
    family_key = json.dumps(family_signature, separators=(",", ":"))

    def add_receipt(seq, program, directed):
        signature = (
            *family_signature[:2],
            ("motor_program", program),
            ("pre_distal_support_code", 1),
            ("pre_whole_body_support_count", 1),
            *family_signature[2:],
            ("vertical_impulse_sign", 0),
            ("motion_nonamplifying", 1),
        )
        receipt = agent.s.add_node("Node", {
            "development_receipt_closed": 1,
            "development_locomotor_cycle_evidence": 1,
            "development_receipt_seq": seq,
            "development_locomotor_phenotype_signature": signature,
            "development_locomotor_phenotype_key": json.dumps(
                signature, separators=(",", ":")
            ),
            "development_locomotor_phenotype_family_signature": (
                family_signature
            ),
            "development_locomotor_phenotype_family_key": family_key,
            "development_action_intent": "learned_walk",
            "developmental_capability": "independent_walking",
            "development_motor_program_key": program,
            "development_primary_token": program,
            "development_secondary_token": program,
            "development_pre_orientation_class": 3,
            "development_post_orientation_class": 3,
            "development_pre_distal_support_code": 1,
            "development_pre_support_count": 1,
            "development_directed_units": directed,
            "development_translation_units": abs(directed),
            "development_lateral_units": 0,
            "development_energy_units": 1,
            "development_peak_load_units": 1,
        })
        agent.inner.add_edge(
            episode, "has_embodied_development_receipt", receipt
        )

    for seq, program, directed in (
        (1, "forward", 1),
        (2, "forward", 1),
        (3, "backward", -1),
    ):
        agent.inner.set_attr(
            episode, "latest_development_receipt_seq", seq
        )
        add_receipt(seq, program, directed)
        agent.tick()

    families = agent.inner.neighbours(
        episode, "has_embodied_locomotor_phenotype_family"
    )
    assert len(families) == 1
    attrs = agent.s.node(families[0])["attrs"]
    assert attrs["occurrence_count"] == 3
    assert attrs["sum_directed_units"] == 1
    assert attrs["sum_directed_consistency"] == 2
    assert attrs["status"] == "refinement_required"
    assert attrs["refinement_required"] == 1
    assert attrs["selected_refinement_order"] == 1
    assert not agent.inner.neighbours(
        families[0], "publishes_locomotor_pareto_candidate"
    )
    leaves = agent.inner.neighbours(
        episode, "has_embodied_locomotor_phenotype"
    )
    forward = next(
        leaf for leaf in leaves
        if agent.s.node(leaf)["attrs"]["primary_token"] == "forward"
    )
    forward_attrs = agent.s.node(forward)["attrs"]
    assert forward_attrs["action_intent"] == "learned_walk"
    assert forward_attrs["developmental_capability"] == "independent_walking"
    assert forward_attrs["motor_program_key"] == "forward"
    assert forward_attrs["occurrence_count"] == 2


def test_locomotor_family_evidence_survives_library_round_trip():
    from scripts.jabberwock_humanoid_walk import (
        _motor_library_snapshot,
        _restore_motor_library,
    )
    from substrate.world_adapter import WorldAdapter

    source = WorldAdapter(seeds=(
        "somatomotor_waves", "embodied_development",
    ))
    target = WorldAdapter(seeds=(
        "somatomotor_waves", "embodied_development",
    ))
    source_humanoid = source.s.add_node("HumanoidEpisode", {})
    target_humanoid = target.s.add_node("HumanoidEpisode", {})
    source_development = source.s.add_node("EmbodiedDevelopmentEpisode", {})
    target_development = target.s.add_node("EmbodiedDevelopmentEpisode", {})
    source.inner.add_edge_unchecked(
        source.agent, "has_humanoid_episode", source_humanoid
    )
    target.inner.add_edge_unchecked(
        target.agent, "has_humanoid_episode", target_humanoid
    )
    source.inner.add_edge_unchecked(
        source.agent, "has_embodied_development_episode", source_development
    )
    target.inner.add_edge_unchecked(
        target.agent, "has_embodied_development_episode", target_development
    )
    family = source.s.add_node("EmbodiedLocomotorPhenotypeFamily", {
        "key": "support-family",
        "signature": (
            ("action_intent", "learned_walk"),
            ("developmental_capability", "independent_walking"),
            ("support_transition", 1),
            ("distal_support_code", 1),
            ("whole_body_support_count", 1),
            ("aerial", 0),
            ("pre_orientation_class", 3),
            ("post_orientation_class", 3),
        ),
        "shape_order": 0,
        "status": "verified_basin",
        "occurrence_count": 9,
        "sum_directed_units": 9,
        "sum_translation_units": 12,
        "sum_lateral_units": 2,
        "sum_energy_units": 4,
        "sum_peak_load_units": 5,
        "sum_directed_consistency": 6,
        "last_receipt_seq": 99,
        "output_authority": 0,
        "integer_native": 1,
    })
    source.inner.add_edge_unchecked(
        source_development,
        "has_embodied_locomotor_phenotype_family",
        family,
    )
    leaf_signature = (
        ("action_intent", "learned_walk"),
        ("developmental_capability", "independent_walking"),
        ("motor_program", '["humanoid_actuator_001"]'),
        ("pre_distal_support_code", 1),
        ("pre_whole_body_support_count", 1),
        ("distal_support_code", 1),
        ("distal_support_transition", 1),
        ("whole_body_support_count", 1),
        ("aerial", 0),
        ("pre_orientation_class", 3),
        ("post_orientation_class", 3),
        ("vertical_impulse_sign", 0),
        ("motion_nonamplifying", 1),
    )
    leaf = source.s.add_node("EmbodiedLocomotorPhenotype", {
        "key": json.dumps(leaf_signature, separators=(",", ":")),
        "signature": leaf_signature,
        "family_key": "support-family",
        "shape_order": 1,
        "status": "verified_basin",
        "occurrence_count": 7,
        "sum_directed_units": 11,
        "sum_translation_units": 14,
        "sum_lateral_units": 1,
        "sum_energy_units": 3,
        "sum_peak_load_units": 4,
        "sum_directed_consistency": 5,
        "last_receipt_seq": 99,
        "output_authority": 0,
        "integer_native": 1,
    })
    source.inner.add_edge_unchecked(
        source_development,
        "has_embodied_locomotor_phenotype",
        leaf,
    )

    snapshot = json.loads(json.dumps(_motor_library_snapshot(source)))
    assert snapshot["locomotor_phenotype_families"][0]["attrs"][
        "occurrence_count"
    ] == 9
    assert snapshot["locomotor_phenotypes"][0]["attrs"][
        "occurrence_count"
    ] == 7
    restored = _restore_motor_library(target, snapshot)

    restored_families = target.inner.neighbours(
        target_development, "has_embodied_locomotor_phenotype_family"
    )
    assert restored["locomotor_phenotype_family_count"] == 1
    assert restored["locomotor_phenotype_count"] == 1
    assert len(restored_families) == 1
    attrs = target.s.node(restored_families[0])["attrs"]
    assert attrs["occurrence_count"] == 9
    assert attrs["sum_directed_units"] == 9
    assert attrs["status"] == "hypothesis"
    assert attrs["last_receipt_seq"] == 0
    assert attrs["output_authority"] == 0
    restored_leaves = target.inner.neighbours(
        target_development, "has_embodied_locomotor_phenotype"
    )
    assert len(restored_leaves) == 1
    leaf_attrs = target.s.node(restored_leaves[0])["attrs"]
    assert leaf_attrs["occurrence_count"] == 7
    assert leaf_attrs["sum_directed_units"] == 11
    assert leaf_attrs["shape_order"] == 1
    assert leaf_attrs["status"] == "hypothesis"
    assert leaf_attrs["last_receipt_seq"] == 0
    assert leaf_attrs["output_authority"] == 0


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
    lease_guarded_rules = (
        "ed_defer_exhausted_learning_step_without_progress_or_reset",
        "ed_open_delayed_retention_test_after_varied_competence",
        "ed_release_incomplete_experiment_back_to_frontier",
        "ed_defer_unsatisfied_retention_retest",
        "ed_master_only_after_delayed_successful_retest",
    )
    assert all(
        "active_physical_experiment_lease_count" in json.dumps(rules[name])
        for name in lease_guarded_rules
    )
    store = json.dumps(
        rules["ed_store_mastered_capability_by_structural_body_shape"]
    )
    assert "evidence_kind" in store
    assert "mastery_receipt_seq" in store


def test_recoverable_upward_liftoff_is_projected_elevation_evidence():
    """Contact loss can precede a coarse realized-height bin crossing."""
    rules = {row["name"]: row for row in manifest()["rules"]}
    learning = json.dumps(
        rules["ed_learn_capability_from_causally_closed_receipt"]
    )
    assert "support_reducing_elevation" in learning
    assert "development_post_vertical_velocity_units" in learning
    assert "development_recoverability_units" in learning
    assert "development_support_gain" in learning

    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 21,
        "latest_development_receipt_seq": 1,
        "development_sparse_support_ceiling": 0,
    })
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "name": "two_foot_jump",
            "goal": "support_reducing_elevation",
            "evidence_kind": "support_reducing_elevation",
            "status": "active",
            "attempt_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "last_receipt_seq": 0,
            "activation_receipt_seq": 0,
            "asym_count": 21,
            "q": 0,
            "effector_coverage_scored_count": 0,
        },
    )
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "development_receipt_seq": 1,
        "development_post_support_count": 0,
        "caregiver_protective_support_applied": 0,
        "development_support_gain": -1,
        "development_elevation_units": 0,
        "development_post_vertical_velocity_units": 1,
        "development_recoverability_units": 1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.inner.add_edge(
        episode,
        "has_active_embodied_developmental_capability",
        capability,
    )
    agent.inner.add_edge(
        episode, "has_embodied_development_receipt", receipt
    )

    agent.tick()

    attrs = agent.s.node(capability)["attrs"]
    assert attrs["attempt_count"] == 1
    assert attrs["success_count"] == 1
    assert attrs["failure_count"] == 0


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


def test_learned_failure_still_requests_next_situated_experiment():
    """The reset gate survives learning advancing last_receipt_seq first."""
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 2,
        "latest_development_receipt_seq": 2,
        "embodiment_reset_available": 1,
        "embodiment_reset_cost_units": 6,
        "embodiment_generation": 0,
        "embodiment_terminal": 0,
        "embodied_reset_requested": 0,
    })
    instance = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "name": "supported_transition",
            "goal": "supported_transition",
            "evidence_kind": "support_topology_change",
            "status": "active",
            "attempt_count": 2,
            "success_count": 0,
            "failure_count": 2,
            "last_receipt_seq": 2,
            "activation_receipt_seq": 0,
            "last_reinstantiation_failure_count": 0,
        },
    )
    scenario = agent.s.add_node("EmbodiedResetScenario", {
        "name": "supported_fixture",
        "ordinal": 0,
        "target_goal": "any",
        "fixture_quarter_turn_x": 0,
        "fixture_quarter_turn_y": 0,
        "fixture_quarter_turn_z": 0,
        "selection_count": 0,
        "enabled": 1,
    })
    receipt = agent.s.add_node("Node", {
        "development_receipt_closed": 1,
        "development_experience_retained": 1,
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
    assert agent.s.node(requests[0])["attrs"]["scenario_name"] == (
        "supported_fixture"
    )
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
    target.s.add_node("HumanoidEpisode", {})
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
    target.s.add_node("HumanoidEpisode", {})
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


def test_exact_body_deployment_recall_skips_developmental_reverification():
    from substrate.world_adapter import WorldAdapter

    signature = (("articulated_body", 1), ("link_count", 8))
    agent = WorldAdapter(seeds=("embodied_development",))
    memory = agent.s.add_node("EmbodiedDevelopmentalCapabilityMemory", {
        "name": "developmental_capability:test:deployment-body",
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
        "developmental_deployment_mode": 1,
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
    assert attrs["status"] == "mastered"
    assert attrs["attempt_count"] == 0
    assert attrs["warm_start_requires_verification"] == 0
    assert attrs["output_authority"] == 0


def test_complete_exact_body_library_closes_before_frontier_activation():
    from substrate.world_adapter import WorldAdapter

    signature = (("articulated_body", 1), ("link_count", 8))
    agent = WorldAdapter(seeds=("embodied_development",))
    for capability in CAPABILITIES:
        memory = agent.s.add_node(
            "EmbodiedDevelopmentalCapabilityMemory",
            {
                "name": f"deployment:{capability['name']}",
                "signature": signature,
                "goal": capability["goal"],
                "capability_name": capability["name"],
                "evidence_kind": capability["evidence"],
                "output_authority": 0,
                "integer_native": 1,
            },
        )
        agent.inner.add_edge(
            agent.agent,
            "has_embodied_developmental_capability_memory",
            memory,
        )
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": signature,
        "development_evidence_window": 3,
        "development_learning_active": 0,
        "developmental_deployment_mode": 1,
        "latest_development_receipt_seq": 0,
        "developmental_exact_body_recall_count": 0,
        "output_authority": 0,
        "integer_native": 1,
    })
    agent.inner.add_edge(
        agent.agent, "has_embodied_development_episode", episode
    )

    agent.tick()

    plans = agent.inner.neighbours(
        episode, "has_self_directed_learning_plan"
    )
    assert len(plans) == 1
    assert agent.s.node(plans[0])["attrs"]["status"] == "completed"
    assert agent.inner.neighbours(
        episode, "has_active_embodied_developmental_capability"
    ) == []
    assert agent.inner.neighbours(
        plans[0], "has_selected_learning_plan_step"
    ) == []
    instances = agent.inner.neighbours(
        episode, "has_embodied_developmental_capability"
    )
    assert len(instances) == len(CAPABILITIES)
    assert all(
        agent.s.node(instance)["attrs"]["status"] == "mastered"
        for instance in instances
    )
