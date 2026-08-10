"""Tests for morphology-selectable humanoid developmental transfer."""
from __future__ import annotations

import json
from dataclasses import replace
import importlib.util
from pathlib import Path

from scripts.jabberwock_humanoid_walk import _configuration
from scripts.jabberwock_somatomotor_cross_morphology import (
    trajectory_comparison,
    transfer_comparison,
    warm_start_rows,
)


ROOT = Path(__file__).resolve().parents[1]


def test_transfer_protocol_selects_distinct_declared_morphology():
    protocol = json.loads((
        ROOT / "protocols" / "humanoid_developmental_symmetric_transfer_v1.json"
    ).read_text(encoding="utf-8"))
    configuration = _configuration(protocol)
    assert configuration.asset == "mjcf/humanoid_symmetric.xml"
    assert configuration.initial_base_quarter_turns == (1, 0, 0)
    assert protocol["curriculum"]["somatomotor_waves"] is True


def test_morphology_family_declares_counterbalanced_untuned_bodies():
    family = json.loads((
        ROOT / "protocols" / "somatomotor_cross_morphology_family_v1.json"
    ).read_text(encoding="utf-8"))
    assert family["base_protocol"] == (
        "protocols/humanoid_developmental_symmetric_transfer_v1.json"
    )
    assert family["caregiver_scaffolding"] is True
    assert [row["arm_order"] for row in family["targets"]] == [
        ["cold", "warm"],
        ["warm", "cold"],
        ["cold", "warm"],
    ]
    assert {row["asset"] for row in family["targets"]} == {
        "mjcf/humanoid_symmetric.xml",
        "mjcf/ant.xml",
        "mjcf/walker2d.xml",
    }


def test_alternate_asset_exposes_a_distinct_name_free_relation_system():
    if importlib.util.find_spec("pybullet") is None:
        return
    from domains.pybullet_humanoid_world import PyBulletHumanoidWorld

    source_protocol = json.loads((
        ROOT / "protocols" / "humanoid_developmental_smoke_v1.json"
    ).read_text(encoding="utf-8"))
    target_protocol = json.loads((
        ROOT / "protocols" / "humanoid_developmental_symmetric_transfer_v1.json"
    ).read_text(encoding="utf-8"))
    source_configuration = replace(
        _configuration(source_protocol), settling_frames=1
    )
    target_configuration = replace(
        _configuration(target_protocol), settling_frames=1
    )
    with PyBulletHumanoidWorld(source_configuration) as source_world:
        source_signature = source_world.body_capability_signature()
        source_channels = (len(source_world.actuator_options()) - 1) // 2
    with PyBulletHumanoidWorld(target_configuration) as target_world:
        target_signature = target_world.body_capability_signature()
        target_channels = (len(target_world.actuator_options()) - 1) // 2
    assert source_channels == 21
    assert target_channels == 17
    assert source_signature != target_signature


def test_passive_cycle_and_bounce_publish_motion_without_motor_agency():
    if importlib.util.find_spec("pybullet") is None:
        return
    from domains.pybullet_humanoid_world import PyBulletHumanoidWorld

    protocol = json.loads((
        ROOT / "protocols" / "humanoid_developmental_symmetric_transfer_v1.json"
    ).read_text(encoding="utf-8"))
    configuration = replace(_configuration(protocol), settling_frames=1)
    with PyBulletHumanoidWorld(configuration) as world:
        cycled = world.scaffold_joint_cycle(0)
        bounced = world.scaffold_body_bounce()
    assert cycled["scaffold_configuration_changed"] == 1
    assert len(cycled["scaffold_configuration_trajectory"]) == 4
    assert isinstance(cycled["scaffold_positive_excursion_units"], int)
    assert isinstance(cycled["scaffold_negative_excursion_units"], int)
    assert isinstance(cycled["scaffold_return_residual_units"], int)
    assert isinstance(cycled["scaffold_coupled_channel_count"], int)
    assert cycled["last_actuator_tokens"] == ()
    assert cycled["supplied_energy_joules"] == 0.0
    assert bounced["scaffold_load_changed"] == 1
    assert bounced["scaffold_vertical_direction"] in {-1, 0, 1}
    assert isinstance(bounced["scaffold_support_count_change"], int)
    assert bounced["last_actuator_tokens"] == ()
    assert bounced["supplied_energy_joules"] == 0.0


def test_transfer_comparison_preserves_per_capability_tradeoffs():
    comparison = transfer_comparison(
        {"contact": 90, "reversal": 130},
        {"contact": 70, "support": 115},
    )
    assert comparison["common_mastered_capabilities"] == [{
        "capability": "contact",
        "cold_receipts_to_mastery": 90,
        "warm_receipts_to_mastery": 70,
        "receipts_saved": 20,
    }]
    assert comparison["warm_only_mastered_capabilities"] == ["support"]
    assert comparison["cold_only_mastered_capabilities"] == ["reversal"]
    assert comparison["total_receipts_saved_on_common_capabilities"] == 20


def test_warm_start_reporting_exposes_shape_prior_without_action_authority():
    result = {"stages": [
        {
            "name": "contact",
            "warm_start_overlap": 17,
            "status": "warm_available",
            "attempt_count": 0,
            "last_receipt_seq": 0,
        },
        {
            "name": "unmatched",
            "warm_start_overlap": 0,
            "status": "available",
            "attempt_count": 0,
            "last_receipt_seq": 0,
        },
    ]}
    assert warm_start_rows(result) == [{
        "capability": "contact",
        "shape_overlap": 17,
        "status": "warm_available",
        "attempt_count": 0,
        "last_receipt_seq": 0,
    }]


def test_trajectory_comparison_preserves_program_and_physical_divergence():
    def result(shapes, positions):
        return {"run": {"trace": [
            {
                "motor_configuration_shape_after": shape,
                "motor_bundle_width": sum(shape),
                "position_after": position,
            }
            for shape, position in zip(shapes, positions)
        ]}}

    cold = result(([1, 0], [0, 1]), ([0, 0, 0], [1, 0, 0]))
    warm = result(([1, 0], [1, 1]), ([0, 0, 0], [1, 1, 0]))
    assert trajectory_comparison(cold, warm) == {
        "shared_action_count": 2,
        "compound_program_difference_count": 1,
        "first_compound_program_divergence_action": 1,
        "physical_trajectory_difference_count": 1,
        "first_physical_divergence_action": 1,
        "cold_trace_length": 2,
        "warm_trace_length": 2,
    }
