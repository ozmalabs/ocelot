"""Development checks for preregistered P4 report analysis."""
from evaluation.substrate_capability.cognition_p4_analysis_v1 import (
    ARMS, analyze, _analyze_e1e2, _self_check,
)
from evaluation.substrate_capability.cognition_p4_heldout_v1 import (
    run as run_p4, run_d5_panel,
)
import pytest


def _full_development_report():
    rows = []
    for family in ("graph_role", "numeric_sequence"):
        for index in range(200):
            arms = {
                "recall_on": {"solved": True, "exact_candidate_checks": 3,
                              "target_digest": f"{family}-{index}"},
                "recall_off": {"solved": True, "exact_candidate_checks": 4,
                               "target_digest": f"{family}-{index}"},
                "mismatched_source": {"solved": False, "exact_candidate_checks": 4,
                                      "target_digest": f"{family}-{index}"},
            }
            rows.append({"family": family, "case_kind": "target",
                         "paired_id": f"{family}-target-{index}", "arms": arms})
            if index < 100:
                rows.append({"family": family, "case_kind": "incompatible_decoy",
                             "paired_id": f"{family}-decoy-{index}",
                             "arms": {arm: {"solved": False,
                                            "false_grounded": False,
                                            "exact_candidate_checks": 4,
                                            "target_digest": f"{family}-decoy-{index}"}
                                      for arm in ARMS}})
    return {"protocol": "cognition_p4_heldout_v1", "prereg_hash": "development",
            "first": 1000, "end": 1200, "rows": rows}


def test_analysis_self_check_covers_null_timeout_and_invariant_violation():
    _self_check()


def test_stale_feasibility_receipt_is_a_null_not_a_certification():
    result = _analyze_e1e2({"model_worlds": [{"world_kind": "feasible", "arms": {
        "bridge_on": {"verified_feasible_candidate": None,
                      "invalid_feasibility_receipt_count": 1,
                      "candidate_count": 1, "refinement_request_count": 0,
                      "funded_refinement_count": 0},
        "bridge_off": {"verified_feasible_candidate": False,
                       "candidate_count": 0, "refinement_request_count": 0,
                       "funded_refinement_count": 0},
        "supplied_path_parity": {"projection_equal": True}}}]})
    assert result["null_results"] > 0
    assert result["decision"] == "NOT_ESTABLISHED"


def test_complete_development_fixture_applies_registered_decision_rules():
    result = analyze(_full_development_report())
    assert result["overall_d5"] == "PASS"
    for family in result["d5_transfer"].values():
        assert family["coverage"]["complete"] is True
        assert family["candidate_check_savings"] == 0.25
        assert family["decision"] == "PASS"
    assert all(item["decision"] == "NOT_ESTABLISHED"
               for item in result["other_registered_families"].values())


def test_timeout_counts_as_failure_and_false_grounding_fails():
    report = _full_development_report()
    row = next(x for x in report["rows"] if x["family"] == "graph_role"
               and x["case_kind"] == "target")
    row["arms"]["recall_on"] = {"solved": False, "timeout": True,
                                 "exact_candidate_checks": 3,
                                 "target_digest": row["arms"]["recall_off"]["target_digest"]}
    result = analyze(report)
    family = result["d5_transfer"]["graph_role"]
    assert family["timeouts"] == 1
    assert family["solve_rate"]["recall_on"]["successes"] == 199

    decoy = next(x for x in report["rows"] if x["family"] == "numeric_sequence"
                  and x["case_kind"] == "incompatible_decoy")
    decoy["arms"]["recall_on"]["false_grounded"] = True
    result = analyze(report)
    assert result["d5_transfer"]["numeric_sequence"]["decision"] == "FAIL"


def test_arm_target_identity_violation_is_not_silently_analyzed():
    report = _full_development_report()
    row = next(x for x in report["rows"] if x["family"] == "graph_role"
               and x["case_kind"] == "target")
    row["arms"]["mismatched_source"]["target_digest"] = "different-target"
    result = analyze(report)
    family = result["d5_transfer"]["graph_role"]
    assert family["decision"] == "FAIL"
    assert family["invalid_results"]


def test_runner_development_draws_are_disjoint_and_d2_d3_parity_executes():
    report = run_p4("0123456789abcdef" * 2 + "01234567", 1000, 1002,
                    development=True)
    assert report["development_only"] is True
    assert [row["draw_index"] for row in report["d2_d3"]["parity_streams"]] == [1000, 1001]
    assert len(report["rows"]) == 8  # paired D5 target and decoy rows
    assert all(all(isinstance(value, dict) for value in row["arms"].values())
               for row in report["rows"])
    assert len(report["e1_e2"]["model_worlds"]) == 2
    assert all(row["world_kind"] in {"feasible", "infeasible", "missing_model"}
               and isinstance(row["arms"]["bridge_on"], dict)
               and isinstance(row["arms"]["bridge_off"], dict)
               for row in report["e1_e2"]["model_worlds"])
    assert report["d2_d3"]["summary"]["parity_passes"] == 2
    assert report["d2_d3"]["summary"]["collision_passes"] == 2
    assert report["c5"]["hidden_residual_episodes"][0]["adapter_on"]["same_epoch_debit"]
    assert report["c5"]["hidden_residual_episodes"][0]["adapter_on"]["unfunded_probe"] is False
    assert report["c5"]["forced_frame_controls"][0]["adapter_on"]["forced_frame_changed"] is False
    assert report["d1"]["orbit_sequences"][0]["bridge_on"]["funded_steps"] == 1
    assert report["d1"]["orbit_sequences"][0]["bridge_on"]["exact_continuation"] is True
    assert all(not row[arm]["unsupported_exact_claim"]
               for row in report["d1"]["unsupported_controls"]
               for arm in ("bridge_on", "bridge_off"))
    analysis = analyze(report)
    assert analysis["d2_d3"]["decision"] == "NOT_ESTABLISHED"
    assert analysis["c5"]["decision"] == "NOT_ESTABLISHED"
    assert analysis["c5"]["unfunded_adapter_on_probes"] == 0
    assert analysis["d1"]["decision"] == "NOT_ESTABLISHED"
    assert analysis["d1"]["coverage"]["orbit_sequences"] == 2
    assert analysis["d1"]["unfunded_inferences"] == 0
    assert analysis["e1_e2"]["decision"] == "NOT_ESTABLISHED"
    assert analysis["e1_e2"]["coverage"]["model_worlds"] == 2
    assert analysis["e1_e2"]["candidate_projection_count"] >= 1
    assert analysis["e1_e2"]["refinement_requests"] == 0
    assert analysis["c5"]["unfunded_adapter_off_probes"] == 2
    assert analysis["other_registered_families"] == {}


def test_native_transfer_actions_and_scorer_analysis():
    prereg = "0123456789abcdef" * 2 + "01234567"
    rows = []
    rows = run_d5_panel(prereg, 1000, 1001, development=True)
    for row in rows:
        outcomes = row["arms"]
        if row["case_kind"] == "target":
            target_key = row["scoring_oracle"]["target_candidate_key"]
            assert outcomes["recall_on"]["selected_candidate"] == target_key
            assert outcomes["recall_off"]["selected_candidate"] == target_key
            assert outcomes["recall_on"]["exact_candidate_checks"] == 1
            assert outcomes["recall_off"]["exact_candidate_checks"] == 2
            assert outcomes["mismatched_source"]["selected_candidate"] is None
        else:
            assert all(value["selected_candidate"] is None
                       for value in outcomes.values())

    result = analyze({"rows": rows})
    assert all(value["null_results"] == 0 for value in result["d5_transfer"].values())
    assert all(value["successful_paired_targets"] == 1
               for value in result["d5_transfer"].values())
    assert all(value["candidate_check_savings"] == 0.5
               for value in result["d5_transfer"].values())
    bad_rows = [dict(row) for row in rows]
    bad_rows[0] = dict(rows[0])
    bad_rows[0]["arms"] = dict(rows[0]["arms"])
    bad_rows[0]["arms"]["recall_on"] = dict(rows[0]["arms"]["recall_on"])
    bad_rows[0]["arms"]["recall_on"]["selected_candidate"] = "wrong-candidate"
    failed = analyze({"rows": bad_rows})
    assert failed["d5_transfer"][rows[0]["family"]]["decision"] == "FAIL"


def test_registered_runner_refuses_unfrozen_worktree_before_drawing():
    with pytest.raises(ValueError, match="freeze commit|COGNITION_PREREG_HASH|frozen artifact"):
        run_p4("0" * 40, 0, 1)
