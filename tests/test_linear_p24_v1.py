"""P24 allocation, structural-control and analysis integrity checks."""
from evaluation.process_mastery.analyze_linear_p24_v1 import self_check
from evaluation.process_mastery.linear_p24_v1 import (
    _control, allocation, audit_allocation_disjointness,
)


def test_p24_allocations_are_fixed_and_disjoint():
    development = allocation("development")
    heldout = allocation("heldout")
    assert development["streams_per_pair"] == 8
    assert heldout["streams_per_pair"] == 200
    assert development["controls_per_kind"] == 2
    assert heldout["controls_per_kind"] == 100
    assert audit_allocation_disjointness(development)["status"] == "DISJOINT"
    assert audit_allocation_disjointness(heldout)["status"] == "DISJOINT"
    assert {row["seed"] for row in development["streams"] + development["controls"]}.isdisjoint(
        row["seed"] for row in heldout["streams"] + heldout["controls"])


def test_p24_development_controls_reject_duplicates_stale_and_wrong_maps():
    plan = allocation("development")
    controls = [_control(next(row for row in plan["controls"] if row["kind"] == kind))
                for kind in ("duplicate_receipt", "stale_map", "wrong_source_map")]
    assert [row["status"] for row in controls] == ["PASS"] * 3
    assert controls[0]["observations"] == 1
    assert controls[1]["ordinary_hypothesis_count"] == 1
    assert controls[2]["explicit_verification_status"] == "rejected"
    assert controls[2]["ordinary_hypothesis_count"] == 1


def test_p24_analyzer_flat_panel_is_zero_gain():
    result = self_check()
    assert result["status"] == "PASS"
    assert result["primary_status"] == "NOT_ESTIMATED"
    assert all(row["observed_gain"] == 0
               for row in result["primary_by_family"].values())
