from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "somatomotor_waves.json"


def _contains_float(value) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def test_seed_is_reproducible_integer_and_body_plan_neutral():
    from scripts.gen_somatomotor_waves_seed import manifest

    generated = manifest()
    assert json.loads(SEED.read_text(encoding="utf-8")) == generated
    assert not _contains_float(generated)
    text = json.dumps(generated).lower()
    for forbidden in (
        '"home"', "canonical_pose", "left_arm", "right_arm", "left_leg",
        "right_leg", "target_angle", "desired_pose",
    ):
        assert forbidden not in text
    assert "homeostatic_ignition" in text
    assert "propagate_one_topological_hop" in text
    assert "refract_consumed_wavefront" in text
    assert "single_program" in text
    assert "warm_start_structurally_matching_coupling_hint" in text
    assert "warm_prior_rank" in text
    assert "stronger_coupling" in text
    assert "warm_ignition_coupling" in text
    assert "somatomotorpassivebodymodel" in text
    assert "record_noncontingent_passive_motion_without_handoff_credit" in text
    assert all(
        node["attrs"].get("output_authority") == 0
        for node in generated["nodes"]
    )


def test_topology_generates_a_travelling_compound_wave_and_reafference():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("somatomotor_waves",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "request_seq": 1,
        "somatomotor_wave_enabled": 1,
        "sensorimotor_interrupt_required": 0,
        "reset_requested": 0,
    })
    topology = agent.s.add_node("EmbodiedEffectorTopology", {})
    first = agent.s.add_node("EmbodiedEffector", {
        "ordinal": 0,
        "channel_ordinal": 0,
        "mount_depth": 1,
        "mount_degree": 1,
        "axis_x_class": 0,
        "axis_y_class": 0,
        "axis_z_class": 1,
    })
    second = agent.s.add_node("EmbodiedEffector", {
        "ordinal": 1,
        "channel_ordinal": 1,
        "mount_depth": 2,
        "mount_degree": 2,
        "axis_x_class": 0,
        "axis_y_class": 1,
        "axis_z_class": 0,
    })
    relation = agent.s.add_node("EmbodiedEffectorRelation", {
        "same_command_channel": 0,
        "declared_hard_coupling": 0,
        "mechanical_path_known": 1,
        "mechanical_path_length": 1,
        "same_mount": 0,
        "command_polarity_product": 1,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "latest_development_receipt_seq": 0,
        "body_capability_signature": (("body", 2), ("relation", 1)),
    })
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "developmental_ecology": "floor",
        "evidence_kind": "spontaneous_configuration_change",
    })
    coupling_memory = agent.s.add_node("SomatomotorCouplingMemory", {
        "name": "somatomotor_coupling:related-body:1",
        "signature": (
            ("body", 2),
            ("relation", 1),
            ("source_extra", 1),
        ),
        "same_command_channel": 0,
        "declared_hard_coupling": 0,
        "mechanical_path_known": 1,
        "mechanical_path_length": 1,
        "same_mount": 0,
        "command_polarity_product": 1,
        "source_mount_depth": 1,
        "source_mount_degree": 1,
        "source_axis_x_class": 0,
        "source_axis_y_class": 0,
        "source_axis_z_class": 1,
        "target_mount_depth": 2,
        "target_mount_degree": 2,
        "target_axis_x_class": 0,
        "target_axis_y_class": 1,
        "target_axis_z_class": 0,
        "productive_count": 4,
        "unproductive_count": 1,
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(
        agent,
        agent.agent,
        "has_somatomotor_coupling_memory",
        coupling_memory,
    )
    _edge(agent, episode, "has_embodied_effector_topology", topology)
    _edge(agent, topology, "has_embodied_effector", first)
    _edge(agent, topology, "has_embodied_effector", second)
    _edge(agent, topology, "has_embodied_effector_relation", relation)
    _edge(agent, relation, "has_embodied_effector_source", first)
    _edge(agent, relation, "has_embodied_effector_target", second)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent,
        development,
        "has_active_embodied_developmental_capability",
        capability,
    )

    agent.tick()

    fields = agent.inner.neighbours(episode, "has_somatomotor_wave_field")
    assert len(fields) == 1
    field = fields[0]
    assert agent.s.node(field)["attrs"]["warm_coupling_hint_count"] == 1
    cells = agent.inner.neighbours(field, "has_somatomotor_wave_cell")
    assert len(cells) == 2
    assert sum(
        len(agent.inner.neighbours(cell, "has_somatomotor_wave_coupling"))
        for cell in cells
    ) == 2
    programs = agent.inner.neighbours(field, "has_somatomotor_wave_program")
    assert len(programs) == 1
    first_program = programs[0]
    assert agent.s.node(first_program)["attrs"]["status"] == "ready"
    assert len(agent.inner.neighbours(
        first_program, "includes_somatomotor_wave_cell"
    )) == 1

    agent.inner.set_attr(episode, "request_seq", 2)
    agent.tick()

    states = [agent.s.node(cell)["attrs"]["state"] for cell in cells]
    assert states.count("active") == 2
    assert agent.s.node(field)["attrs"]["ignition_count"] == 1
    assert agent.s.node(field)["attrs"]["collapse_count"] == 2
    second_program = agent.inner.neighbours(
        field, "has_somatomotor_wave_program"
    )[1]
    assert len(agent.inner.neighbours(
        second_program, "includes_somatomotor_wave_cell"
    )) == 2

    agent.inner.set_attr(episode, "request_seq", 3)
    agent.tick()
    states = {agent.s.node(cell)["attrs"]["state"] for cell in cells}
    assert "active" in states
    assert "refractory" in states

    receipt = agent.s.add_node("HumanoidTransition", {
        "development_receipt_closed": 1,
        "development_receipt_seq": 1,
        "development_configuration_changed": 1,
        "development_support_topology_changed": 0,
        "development_orientation_units": 0,
        "development_translation_units": 0,
    })
    _edge(agent, development, "has_embodied_development_receipt", receipt)
    agent.inner.set_attr(development, "latest_development_receipt_seq", 1)
    agent.tick()

    assert agent.s.node(first_program)["attrs"]["status"] == "experienced"
    assert first_program not in agent.inner.neighbours(
        field, "has_somatomotor_wave_program"
    )
    assert first_program in agent.inner.neighbours(
        field, "archives_somatomotor_wave_program"
    )
    assert agent.s.node(field)["attrs"]["verified_reafference_count"] == 1
    first_members = agent.inner.neighbours(
        first_program, "includes_somatomotor_wave_cell"
    )
    assert agent.s.node(first_members[0])["attrs"][
        "productive_consequence_count"
    ] == 1

    productive_pair_receipt = agent.s.add_node("HumanoidTransition", {
        "development_receipt_closed": 1,
        "development_receipt_seq": 2,
        "development_configuration_changed": 1,
        "development_support_topology_changed": 0,
        "development_orientation_units": 0,
        "development_translation_units": 0,
    })
    _edge(
        agent,
        development,
        "has_embodied_development_receipt",
        productive_pair_receipt,
    )
    agent.tick()
    couplings = [
        coupling
        for cell in cells
        for coupling in agent.inner.neighbours(
            cell, "has_somatomotor_wave_coupling"
        )
    ]
    assert {
        agent.s.node(coupling)["attrs"]["strength"]
        for coupling in couplings
    } == {2}
    assert agent.s.node(field)["attrs"][
        "warm_coupling_reverification_count"
    ] == 1
    assert sum(
        agent.s.node(coupling)["attrs"]["warm_prior_reverified"]
        for coupling in couplings
    ) == 1

    for receipt_seq in (10, 11):
        unproductive_program = agent.s.add_node("SomatomotorWaveProgram", {
            "epoch": receipt_seq,
            "status": "ready",
            "receipt_processed": 0,
        })
        _edge(
            agent,
            field,
            "has_somatomotor_wave_program",
            unproductive_program,
        )
        _edge(
            agent,
            unproductive_program,
            "tests_embodied_developmental_capability",
            capability,
        )
        for cell in cells:
            _edge(
                agent,
                unproductive_program,
                "includes_somatomotor_wave_cell",
                cell,
            )
        unproductive_receipt = agent.s.add_node("HumanoidTransition", {
            "development_receipt_closed": 1,
            "development_receipt_seq": receipt_seq,
            "development_configuration_changed": 0,
            "development_support_topology_changed": 0,
            "development_orientation_units": 0,
            "development_translation_units": 0,
        })
        _edge(
            agent,
            development,
            "has_embodied_development_receipt",
            unproductive_receipt,
        )
        agent.tick()
    assert {
        agent.s.node(coupling)["attrs"]["strength"]
        for coupling in couplings
    } == {0}
    assert {
        agent.s.node(coupling)["attrs"]["productive_count"]
        for coupling in couplings
    } == {1}
    assert {
        agent.s.node(coupling)["attrs"]["unproductive_count"]
        for coupling in couplings
    } == {2}

    from scripts.jabberwock_humanoid_walk import _motor_library_snapshot

    snapshot = _motor_library_snapshot(agent)
    assert len(snapshot["somatomotor_couplings"]) == 3
    assert all(
        row["attrs"]["output_authority"] == 0
        and row["attrs"]["integer_native"] == 1
        and isinstance(row["attrs"]["productive_count"], int)
        and isinstance(row["attrs"]["unproductive_count"], int)
        for row in snapshot["somatomotor_couplings"]
    )


def test_wave_sheet_has_one_cell_per_physical_channel_not_command_polarity():
    from domains.embodied_effector_topology import (
        install_name_free_effector_topology,
    )
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("somatomotor_waves",))
    episode = agent.s.add_node("EmbodiedEpisode", {})
    _edge(agent, agent.agent, "has_embodied_episode", episode)
    options = (
        {
            "token": "tonic",
            "actuator_group": -1,
            "tonic_default": 1,
        },
        {
            "token": "channel_0_positive",
            "vector": (0, 1),
            "actuator_group": 0,
            "tonic_default": 0,
        },
        {
            "token": "channel_0_negative",
            "vector": (0, -1),
            "actuator_group": 0,
            "tonic_default": 0,
        },
        {
            "token": "channel_1_positive",
            "vector": (1, 1),
            "actuator_group": 1,
            "tonic_default": 0,
        },
        {
            "token": "channel_1_negative",
            "vector": (1, -1),
            "actuator_group": 1,
            "tonic_default": 0,
        },
    )
    install_name_free_effector_topology(agent, episode, options)
    agent.tick()

    field = agent.inner.neighbours(
        episode, "has_somatomotor_wave_field"
    )[0]
    cells = agent.inner.neighbours(field, "has_somatomotor_wave_cell")
    represented_channels = {
        agent.s.node(agent.inner.neighbours(
            cell, "represents_embodied_effector"
        )[0])["attrs"]["channel_ordinal"]
        for cell in cells
    }
    assert represented_channels == {0.0, 1.0}


def test_passive_scaffold_is_exafferent_and_requires_self_attempt_handoff():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("somatomotor_waves",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "caregiver_scaffold_session_active": 1,
        "caregiver_scaffold_handoff_ready": 0,
        "caregiver_scaffold_request_count": 0,
        "caregiver_scaffold_receipt_count": 0,
        "caregiver_scaffold_mismatch_count": 0,
        "caregiver_bounce_requested": 0,
        "caregiver_bounce_completed": 0,
    })
    topology = agent.s.add_node("EmbodiedEffectorTopology", {})
    effector = agent.s.add_node("EmbodiedEffector", {
        "ordinal": 0,
        "channel_ordinal": 0,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "has_embodied_effector_topology", topology)
    _edge(agent, topology, "has_embodied_effector", effector)
    agent.tick()

    field = agent.inner.neighbours(
        episode, "has_somatomotor_wave_field"
    )[0]
    cell = agent.inner.neighbours(
        episode, "requests_passive_somatomotor_scaffold"
    )[0]
    receipt = agent.s.add_node("SomatomotorScaffoldReceipt", {
        "scaffold_kind": "passive_effector_cycle",
        "exafferent": 1,
        "efference_copy_present": 0,
        "configuration_changed": 1,
        "receipt_processed": 0,
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(agent, episode, "has_somatomotor_scaffold_receipt", receipt)
    _edge(agent, receipt, "scaffolds_somatomotor_wave_cell", cell)
    agent.tick()

    assert agent.s.node(cell)["attrs"]["passive_exposure_count"] == 1
    assert agent.s.node(cell)["attrs"]["passive_contingent_count"] == 1
    passive_model = agent.inner.neighbours(
        cell, "has_somatomotor_passive_body_model"
    )[0]
    assert agent.s.node(passive_model)["attrs"]["contingent_count"] == 1
    assert agent.s.node(field)["attrs"][
        "passive_scaffold_receipt_count"
    ] == 1
    assert agent.s.node(episode)["attrs"]["caregiver_bounce_requested"] == 1
    assert not agent.inner.neighbours(
        episode, "requests_passive_somatomotor_scaffold"
    )

    bounce = agent.s.add_node("SomatomotorScaffoldReceipt", {
        "scaffold_kind": "passive_body_bounce",
        "exafferent": 1,
        "efference_copy_present": 0,
        "load_changed": 1,
        "receipt_processed": 0,
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(agent, episode, "has_somatomotor_scaffold_receipt", bounce)
    agent.tick()
    assert agent.s.node(episode)["attrs"][
        "caregiver_scaffold_handoff_ready"
    ] == 1
    assert agent.s.node(episode)["attrs"][
        "caregiver_scaffold_session_active"
    ] == 0
    assert agent.s.node(episode)["attrs"]["caregiver_scaffold_withdrawn"] == 1
    assert agent.s.node(field)["attrs"][
        "vestibular_scaffold_receipt_count"
    ] == 1


def test_scrambled_passive_motion_is_observed_but_cannot_unlock_handoff():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("somatomotor_waves",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "caregiver_scaffold_session_active": 1,
        "caregiver_scaffold_handoff_ready": 0,
        "caregiver_scaffold_request_count": 0,
        "caregiver_scaffold_receipt_count": 0,
        "caregiver_scaffold_mismatch_count": 0,
        "caregiver_bounce_requested": 0,
        "caregiver_bounce_completed": 0,
    })
    topology = agent.s.add_node("EmbodiedEffectorTopology", {})
    effectors = [agent.s.add_node("EmbodiedEffector", {
        "ordinal": ordinal,
        "channel_ordinal": ordinal,
    }) for ordinal in range(2)]
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "has_embodied_effector_topology", topology)
    for effector in effectors:
        _edge(agent, topology, "has_embodied_effector", effector)
    agent.tick()

    requested = agent.inner.neighbours(
        episode, "requests_passive_somatomotor_scaffold"
    )[0]
    field = agent.inner.neighbours(
        episode, "has_somatomotor_wave_field"
    )[0]
    cells = agent.inner.neighbours(field, "has_somatomotor_wave_cell")
    actual = next(cell for cell in cells if cell != requested)
    receipt = agent.s.add_node("SomatomotorScaffoldReceipt", {
        "scaffold_kind": "passive_effector_cycle",
        "exafferent": 1,
        "efference_copy_present": 0,
        "configuration_changed": 1,
        "receipt_processed": 0,
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(agent, episode, "has_somatomotor_scaffold_receipt", receipt)
    _edge(agent, receipt, "scaffolds_somatomotor_wave_cell", actual)
    agent.tick()

    assert agent.s.node(actual)["attrs"]["passive_exposure_count"] == 1
    assert agent.s.node(actual)["attrs"]["passive_contingent_count"] == 0
    assert agent.s.node(requested)["attrs"]["passive_mismatch_count"] == 1
    assert agent.s.node(episode)["attrs"]["caregiver_scaffold_mismatch_count"] == 1
    assert agent.s.node(episode)["attrs"]["caregiver_scaffold_handoff_ready"] == 0
    assert agent.inner.neighbours(
        episode, "requests_passive_somatomotor_scaffold"
    )


def test_humanoid_bridge_collapses_wave_to_existing_compound_program_path():
    from scripts.gen_humanoid_developmental_curriculum_seed import manifest

    generated = manifest()
    rules = {rule["name"]: rule for rule in generated["rules"]}
    assert {
        "hdc_index_wave_cell_local_commands",
        "hdc_open_humanoid_program_from_somatomotor_wave",
        "hdc_bind_wave_cells_to_least_experienced_local_commands",
        "hdc_collapse_somatomotor_wave_to_one_compound_outcome",
    } <= rules.keys()
    assert "hdc_handoff_passive_body_mapping_to_self_authored_attempt" in rules
    collapse = json.dumps(
        rules["hdc_collapse_somatomotor_wave_to_one_compound_outcome"]
    )
    binding = json.dumps(
        rules["hdc_bind_wave_cells_to_least_experienced_local_commands"]
    )
    assert "indexes_humanoid_wave_local_command" in binding
    assert "models_embodied_effector" not in binding
    assert "includes_humanoid_phase_action_model" in collapse
    assert "has_ready_humanoid_motor_program" in collapse
    assert "spontaneous_somatomotor_wave" in collapse
    assert '"action_ready", 1' in collapse


def test_ablation_canonicalizes_only_the_wave_manipulation():
    from scripts.jabberwock_somatomotor_wave_ablation import (
        _canonical_protocol,
    )

    source = {
        "protocol": "paired",
        "seed": 3,
        "curriculum": {
            "developmental": True,
            "somatomotor_waves": False,
        },
    }
    canonical = _canonical_protocol(source)
    assert canonical == {
        "protocol": "paired",
        "seed": 3,
        "curriculum": {"developmental": True},
    }
    assert source["curriculum"]["somatomotor_waves"] is False
