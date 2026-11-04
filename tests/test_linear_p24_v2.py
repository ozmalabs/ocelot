"""P24 v2 corrected-analysis and untouched-allocation guards."""
from evaluation.process_mastery.analyze_linear_p24_v2 import analyze, self_check
from evaluation.process_mastery.linear_p24_v1 import allocation as allocation_v1
from evaluation.process_mastery.linear_p24_v2 import (
    _control, allocation, audit_allocation_disjointness,
)


def test_p24_v2_allocation_is_disjoint_from_v1_and_prior_protocols():
    old = [allocation_v1(split) for split in ("development", "heldout")]
    new = [allocation(split) for split in ("development", "heldout")]
    old_seeds = {x["seed"] for item in old
                 for x in item["streams"] + item["controls"]}
    new_seeds = {x["seed"] for item in new
                 for x in item["streams"] + item["controls"]}
    old_ids = {x.get("stream_id", x.get("control_id")) for item in old
               for x in item["streams"] + item["controls"]}
    new_ids = {x.get("stream_id", x.get("control_id")) for item in new
               for x in item["streams"] + item["controls"]}
    assert old_seeds.isdisjoint(new_seeds)
    assert old_ids.isdisjoint(new_ids)
    assert all(audit_allocation_disjointness(item)["status"] == "DISJOINT"
               for item in new)


def test_p24_v2_development_controls_and_flat_analyzer_selfcheck():
    plan = allocation("development")
    controls = [_control(next(row for row in plan["controls"] if row["kind"] == kind))
                for kind in ("duplicate_receipt", "stale_map", "wrong_source_map")]
    assert [row["status"] for row in controls] == ["PASS"] * 3
    result = self_check()
    assert result["status"] == "PASS"
    assert result["primary_status"] == "NOT_ESTIMATED"
    assert all(row["observed_gain"] == 0 for row in result["primary_by_family"].values())


def test_p24_v2_heldout_analysis_fails_closed_without_preregistration(tmp_path):
    prereg = tmp_path / "p24v2.md"
    prereg.write_text("P24V2_FREEZE_JSON: {}\n")
    result = analyze({"phase": "linear-p24-v2", "split": "heldout",
                      "status": "heldout_pending_analysis", "allocation": {},
                      "streams": [], "controls": []}, preregistration=prereg,
                     bootstrap_replicates=10)
    assert result["status"] == "FAIL"
    assert "preregistration_invalid" in result["failures"]
