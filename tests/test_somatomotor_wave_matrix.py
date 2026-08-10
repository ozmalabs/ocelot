"""Structural tests for the counterbalanced somatomotor-wave assay."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.jabberwock_somatomotor_wave_matrix import (
    condition_protocol,
    library_mastery_receipts,
    rediscovery_summary,
)


ROOT = Path(__file__).resolve().parents[1]


def test_matrix_is_explicitly_counterbalanced_over_two_by_two_family():
    matrix = json.loads((
        ROOT / "protocols" / "somatomotor_wave_fixture_body_matrix_v1.json"
    ).read_text(encoding="utf-8"))
    conditions = matrix["conditions"]
    assert len(conditions) == 4
    assert {
        tuple(row["fixture_quarter_turns"]) for row in conditions
    } == {(1, 0, 0), (-1, 0, 0)}
    assert {
        (
            row["maximum_joint_force_scale"]["numerator"],
            row["maximum_joint_force_scale"]["denominator"],
        )
        for row in conditions
    } == {(1, 1), (3, 4)}
    assert sum(
        row["arm_order"][0] == "wave_enabled" for row in conditions
    ) == 2
    assert sum(bool(row["retention_source"]) for row in conditions) == 1


def test_condition_transform_changes_only_declared_boundary_and_wave_gate():
    base = {
        "protocol": "base",
        "body": {
            "initial_base_quarter_turns": [0, 0, 0],
            "maximum_joint_force": 48.0,
            "position_gain": 0.3,
        },
        "curriculum": {"developmental": True},
    }
    condition = {
        "fixture_quarter_turns": [-1, 0, 0],
        "maximum_joint_force_scale": {"numerator": 3, "denominator": 4},
    }
    transformed = condition_protocol(base, condition, "wave_ablated")
    assert transformed["body"] == {
        "initial_base_quarter_turns": [-1, 0, 0],
        "maximum_joint_force": 36.0,
        "position_gain": 0.3,
    }
    assert transformed["curriculum"] == {
        "developmental": True,
        "somatomotor_waves": False,
    }
    assert base["body"]["maximum_joint_force"] == 48.0


def test_rediscovery_reports_raw_receipt_counts_without_collapsing_failures():
    summary = rediscovery_summary(
        {"surface_mapping": 70, "reversal": 120},
        {"surface_mapping": 12},
    )
    assert summary["cold_mastered_count"] == 2
    assert summary["retained_remastered_count"] == 1
    assert summary["comparable_capability_count"] == 1
    assert summary["total_receipts_saved"] == 58
    assert summary["all_cold_capabilities_retained_within_assay"] is False
    rows = {row["capability"]: row for row in summary["capabilities"]}
    assert rows["reversal"]["receipts_saved"] is None
    assert rows["surface_mapping"]["receipts_saved"] == 58


def test_library_mastery_receipts_uses_consolidated_causal_sequence(tmp_path):
    library = tmp_path / "library.json"
    library.write_text(json.dumps({
        "developmental_capabilities": [
            {"attrs": {
                "capability_name": "surface_mapping",
                "mastery_receipt_seq": 73,
                "output_authority": 0,
            }},
            {"attrs": {
                "capability_name": "reversal",
                "mastery_receipt_seq": 121.0,
                "output_authority": 0,
            }},
        ],
    }), encoding="utf-8")
    assert library_mastery_receipts(library) == {
        "surface_mapping": 73,
        "reversal": 121,
    }
