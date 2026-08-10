from __future__ import annotations

import json
from pathlib import Path
import subprocess

from scripts.audit_motor_core_manifests import (
    DEFAULT_PROTOCOL,
    audit_seed,
    build_report,
    resolve_baseline_revision,
)


ROOT = Path(__file__).resolve().parents[1]


def _protocol():
    return json.loads(DEFAULT_PROTOCOL.read_text(encoding="utf-8"))


def test_report_schema_and_sheet_area_sums_are_self_consistent():
    report = build_report(root=ROOT, baseline_revision="HEAD")
    protocol = _protocol()
    assert report["schema_version"] == 1
    assert report["benchmark"] == protocol["protocol"]
    assert [row["role"] for row in report["manifests"]] == [
        row["role"] for row in protocol["manifests"]
    ]
    for row in report["manifests"]:
        assert row["rule_count"] == sum(row["sheets"].values())
        assert row["rule_count"] == sum(
            area["total"] for area in row["areas"].values()
        )
        for sheet in ("hard", "soft", "background", "unknown"):
            assert row["sheets"][sheet] == sum(
                area[sheet] for area in row["areas"].values()
            )
    assert report["totals"]["rule_count"] == sum(
        row["rule_count"] for row in report["manifests"]
    )


def test_current_manifests_pass_actor_episode_scope_invariant():
    report = build_report(root=ROOT, baseline_revision="HEAD")
    assert report["invariants"]["passed"] is True
    assert report["invariants"][
        "candidate_selectors_are_actor_or_episode_scoped"
    ] is True
    assert report["totals"]["candidate_selector_count"] > 0
    assert all(
        row["candidate_scope"]["violation_count"] == 0
        for row in report["manifests"]
    )


def test_baseline_comparison_is_derived_from_git_not_magic_targets():
    report = build_report(root=ROOT, baseline_revision="HEAD")
    comparison = report["baseline_comparison"]
    resolved_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert comparison["source"] == "explicit"
    assert comparison["resolved_revision"] == resolved_head
    assert comparison["comparable_hard_delta"] == (
        comparison["comparable_current_hard"]
        - comparison["comparable_baseline_hard"]
    )
    for row in comparison["manifests"]:
        if row["available"]:
            assert row["hard_delta"] == row["current_hard"] - row["hard"]
        else:
            assert row["hard"] is None
            assert row["hard_delta"] is None


def test_default_baseline_is_head_first_parent():
    baseline = resolve_baseline_revision(ROOT)
    first_parent = subprocess.run(
        ["git", "rev-parse", "HEAD^1"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert baseline["resolved_revision"] == first_parent
    assert baseline["source"] in {"merge_parent_first", "head_parent"}


def test_scope_audit_rejects_a_global_candidate_source():
    protocol = _protocol()
    seed = {
        "id": "synthetic",
        "version": "1",
        "area": "motor",
        "latency_class": "hard_realtime",
        "rules": [{
            "name": "bad_global_pick",
            "match": [["agent", "has_episode", "episode"]],
            "where": {
                "type": "Gt",
                "a": {
                    "type": "Count",
                    "source": {
                        "type": "Argmax",
                        "source": {
                            "type": "NodesOfType",
                            "node_type": "DecisionOption",
                        },
                        "var_name": "candidate",
                        "value": {"type": "Lit", "value": 1.0},
                    },
                },
                "b": {"type": "Lit", "value": 0.0},
            },
            "effects": [],
        }],
    }
    row = audit_seed(
        seed,
        role="synthetic",
        path="synthetic.json",
        scope_contract=protocol["candidate_scope_contract"],
    )
    assert row["candidate_scope"]["passed"] is False
    assert row["candidate_scope"]["violation_count"] == 1
    assert "global candidate source" in (
        row["candidate_scope"]["violations"][0]["reasons"][0]
    )
