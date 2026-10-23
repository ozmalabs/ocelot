import json

from evaluation.process_mastery.p22_development import (
    _select_approved_qualification,
    run_p22_training_proposal_probe,
)
from evaluation.process_mastery.p22_resource_accounting import (
    NativeRuleWorkCapture, native_rule_work_digest_valid,
)
from evaluation.process_mastery.checkpoint_world_adapter import (
    capture_held_process_checkpoint,
)
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.independent_worlds import generate_loopover_world_v2
from evaluation.process_mastery.native_process_execution import params_digest
from substrate.seed_loader import manifest_for


def test_training_only_probe_binds_native_rule_work_to_resource_snapshot():
    result = run_p22_training_proposal_probe(family="loopover",
        training_draws=(286, 287), training_goal_relation="distinct",
        validation_draws=(), search_ticks=1, per_request_attempt_ceiling=1,
        measure_native_rule_work=True)
    snapshot = result["resource_snapshot"]
    assert snapshot["native_rule_work"]["schema"] == "p22_native_rule_work_v2"
    assert native_rule_work_digest_valid(snapshot["native_rule_work"])
    assert snapshot["resource_measurement_coverage"][
        "wall_time_seconds"]["status"] == "MEASURED"
    assert snapshot["runtime_counters"]["search_attempts_reserved"] == sum(
        row["reserved_attempts"] for row in result["search_requests"])
    assert snapshot["resource_event_counts"][
        "candidate_validation_evaluations"] == 0
    ancestor = result["generation_zero_ancestor"]
    assert ancestor["generation"] == 0
    assert ancestor["native_graph_snapshot_json"]
    assert ancestor["checkpoint_digest"]


def test_training_probe_accepts_multiple_pairwise_distinct_goals():
    draws = (286, 287, 288)
    result = run_p22_training_proposal_probe(family="loopover",
        training_draws=draws, training_goal_relation="distinct",
        validation_draws=(), search_ticks=1, per_request_attempt_ceiling=1,
        global_attempt_ceiling=1, measure_native_rule_work=True)
    assert result["training_world_ids"] == [
        f"p22:loopover-v2:train:{draw:04d}" for draw in draws]
    assert len({tuple(goal) for goal in result["training_goal_states"]}) == 3
    assert len(result["training_task_rows"]) == 3
    assert result["resource_snapshot"]["cumulative_resources"][
        "training_task_exposures"] == 3
    assert result["approval_count"] == result["world_receipt_count"] == 0


def test_multi_goal_distinct_relation_rejects_duplicate_goal_anywhere():
    import pytest
    with pytest.raises(ValueError, match="distinct goals"):
        run_p22_training_proposal_probe(family="loopover",
            training_draws=(1, 3, 286), training_goal_relation="distinct",
            validation_draws=(), search_ticks=1, per_request_attempt_ceiling=1,
            global_attempt_ceiling=1, measure_native_rule_work=True)


def test_training_probe_continues_restored_checkpoint_with_cumulative_rule_work():
    family = "loopover"
    size = 9
    source = Agent(track_i=False, extra_seeds=("open_process_search",),
        policy_overrides={"OpenProcessSearchPolicy": {"enabled": 1.0,
            "max_attempts": 30000.0, "max_attempts_per_request": 1.0,
            "max_candidates": 16.0},
            "ProcessSchemaPolicy": {"enabled": 1.0}},
        budget={"enabled": 1.0, "remaining": 100000.0,
            "capacity": 100000.0, "last_refill_epoch": 0.0,
            "refill_per_epoch": 0.0})
    capture = NativeRuleWorkCapture(source.native).start()
    try:
        seed_world = generate_loopover_world_v2(split="train", draw=285)
        domain = source.add_domain("p22-development", "permutation",
            [seed_world["initial_state"]], seed_world["held_processes"])
        source.native.load_seed_manifest(manifest_for("open_process_adoption"),
                                         source.ag)
        source.native.load_seed_manifest(manifest_for("independent_improvement"),
                                         source.ag)
        source.s.set_attr(source.nodes("IndependentImprovementPolicy")[0],
                          "enabled", 1.0)
        for policy in source.nodes("OpenProcessAdoptionPolicy"):
            source.s.set_attr(policy, "enabled", 1.0)
        identity = list(range(size))
        process = source.s.add_node("ProcessSchema", {
            "name": "p22-continuation-test-ancestor", "kind": "permutation",
            "domain_kind": "permutation", "domain": "p22-development",
            "params": identity, "source_digest": params_digest(identity),
            "cost": 1.0, "status": "active", "provenance": "test_ancestor",
            "invariants": [], "source_epoch": 0, "model_epoch": 0,
            "frame_epoch": 0, "probe_epoch": 0, "source_probe_epoch": 0})
        source.s.add_edge(source.ag, "has_process_schema", process, {})
        source.s.add_edge(domain, "has_held_process", process, {})
        rule_work = capture.finish()
        parent = capture_held_process_checkpoint(source, process,
            checkpoint_id="p22-continuation-test-g0",
            runtime_counters={"native_rule_steps": 0, "native_model_calls": 0,
                "search_attempts_reserved": 0, "process_peak_rss_bytes": 64_000_000,
                "wall_time_seconds": 1.0}, native_rule_work=rule_work)
    finally:
        if capture.active:
            capture.close()
        close = getattr(source.s, "close", None)
        if callable(close):
            close()

    result = run_p22_training_proposal_probe(family=family,
        training_draws=(286, 287), training_goal_relation="distinct",
        validation_draws=(), search_ticks=1, per_request_attempt_ceiling=2,
        global_attempt_ceiling=40000, measure_native_rule_work=True,
        parent_checkpoint=parent)
    snapshot = result["resource_snapshot"]
    cumulative_work = snapshot["native_rule_work"]
    assert cumulative_work["schema"] == "p22_native_rule_work_v3"
    assert native_rule_work_digest_valid(cumulative_work)
    assert len(cumulative_work["capture_ids"]) == 2
    assert cumulative_work["rule_identity_coverage"] == "COMPLETE"
    assert snapshot["runtime_counters"]["wall_time_seconds"] >= 1.0
    assert snapshot["runtime_counters"]["process_peak_rss_bytes"] >= 64_000_000
    assert snapshot["cumulative_resources"]["training_task_exposures"] == 2
    assert result["approval_count"] == result["world_receipt_count"] == 0
    assert result["generation_zero_ancestor"]["checkpoint_digest"] == parent.checkpoint_digest
    assert result["parent_checkpoint"]["checkpoint_digest"] == parent.checkpoint_digest
    assert result["inherited_global_attempt_ceiling"] == 30000.0
    assert result["global_attempt_ceiling"] == 40000
    assert snapshot["runtime_counters"]["search_attempts_reserved"] < 40000
    request_caps = [request["max_attempts"]
        for row in result["training_task_rows"]
        for request in row["search_requests"]]
    assert request_caps and set(request_caps) == {2.0}


def test_v2_native_training_proposals_are_qualified_and_scored_nonactionably():
    cases = {
        "d4": ((1, 7), 16),
        "loopover": ((1, 3), 0),
    }
    for family, (training_draws, expected_successes) in cases.items():
        result = run_p22_training_proposal_probe(
            family=family, training_draws=training_draws,
            validation_draws=tuple(range(200)))
        assert result["status"] == "COMPLETED"
        assert result["training_goals_match"]
        assert len(set(result["training_world_ids"])) == 2
        assert len(result["validation_world_ids"]) == 200
        assert result["candidate_count"] > 0
        assert result["approval_count"] == 0
        assert result["world_receipt_count"] == 0
        assert result["resource_snapshot"]["resource_counts"][
            "improvement_proposals"] > 0
        assert result["resource_snapshot"]["cumulative_resources"][
            "training_task_exposures"] == 2
        assert all(row["status"] == "unapproved_candidate"
                   and row["proposal_count"] > 0
                   and row["panel"]["status"] == "nonactionable_validation_panel_scored"
                   and row["panel"]["world_count"] == 200
                   and row["panel"]["approval_created"] is False
                   and row["panel"]["world_receipts_created"] is False
                   for row in result["candidates"])
        assert sum(row["qualification_count"] > 0 for row in result["candidates"]) == 1
        assert sum(row["qualification_count"] == 0 for row in result["candidates"]) == 1
        qualified = next(row for row in result["candidates"]
                         if row["qualification_count"] > 0)
        assert len(qualified["qualifications"]) == 1
        qualification = qualified["qualifications"][0]
        assert qualification["status"] == "qualified_for_candidate_specific_approval"
        assert qualification["declared_trial_count"] == 2.0
        assert len(set(qualification["attempt_ids"])) == 2
        assert len(set(qualification["task_ids"])) == 2
        assert len(set(qualification["training_trial_keys"])) == 2
        assert all(row["panel"]["successes"] == expected_successes
                   for row in result["candidates"])


def test_noncomposable_candidates_do_not_qualify_across_distinct_goals():
    cases = {"d4": (200, 201), "loopover": (206, 207)}
    for family, training_draws in cases.items():
        result = run_p22_training_proposal_probe(family=family,
            training_draws=training_draws, training_goal_relation="distinct",
            validation_draws=tuple(range(201, 209)))
        assert result["training_goal_relation"] == "distinct"
        assert result["training_goals_match"] is False
        assert result["training_goal_states"][0] != result["training_goal_states"][1]
        assert result["candidate_count"] > 0
        assert result["approval_count"] == 0
        assert result["world_receipt_count"] == 0
        assert all(row["qualification_count"] == 0
                   and row["panel"]["world_count"] == 8
                   and row["panel"]["approval_created"] is False
                   and row["panel"]["world_receipts_created"] is False
                   for row in result["candidates"])


def test_distinct_goal_native_composition_qualifies_in_both_families():
    cases = {
        "d4": ((200, 202),
            "8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788",
            [0, 2, 1, 3]),
        "loopover": ((15, 26),
            "f8277f0f8d7df4de63aed09cfc4f265ed2f6d9293034ae73ec18fdb9babfe75d",
            [0, 3, 2, 5, 1, 7, 6, 4, 8]),
    }
    for family, (training_draws, expected_digest, expected_params) in cases.items():
        result = run_p22_training_proposal_probe(family=family,
            training_draws=training_draws, training_goal_relation="distinct",
            validation_draws=())
        assert result["training_goals_match"] is False
        assert result["candidate_count"] >= 1
        assert result["approval_count"] == 0
        assert result["world_receipt_count"] == 0
        qualified = [row for row in result["candidates"]
                     if row["qualification_count"] == 1]
        assert len(qualified) == 1
        source = qualified[0]
        assert source["panel"] is None
        binding = source["approval_binding"]
        assert binding["expression_digest"] == expected_digest
        assert binding["params"] == expected_params
        assert binding["expression_digest"] == source["expression_digest"]
        assert binding["expression_tree"]
        assert binding["effect_digest"]
        assert binding["guard_state"]
        assert binding["source_epoch"] == binding["model_epoch"] == binding["frame_epoch"] == 0
        assert binding["status"] == "unapproved_candidate"
        qualification = source["qualifications"][0]
        assert qualification["kind"] == "independent_goal_composition"
        assert qualification["status"] == "qualified_for_candidate_specific_approval"
        assert len(set(qualification["training_trial_keys"])) == 2
        verified_trials = [trial for trial in source["independent_goal_trials"]
                           if trial["status"] == "verified"]
        assert len(verified_trials) == 1
        assert verified_trials[0]["task_key"] != result["training_world_ids"][0]
        assert len(verified_trials[0]["derived_candidate_ids"]) == 1
        assert verified_trials[0]["derived_candidate_statuses"] == ["unapproved_candidate"]
        assert all(request["attempt_count"] == request["reserved_attempts"]
                   for request in result["search_requests"])


def test_first_trial_no_candidate_is_retained_as_a_terminal_probe_result():
    result = run_p22_training_proposal_probe(family="loopover",
        training_draws=(286, 287), training_goal_relation="distinct",
        validation_draws=tuple(range(386, 394)))
    assert result["status"] == "NO_CANDIDATE_FIRST_TRIAL"
    assert result["failure_reasons"] == [
        "native_search_no_candidate_first_training_task"]
    assert [row["world_id"] for row in result["training_task_rows"]] == \
        result["training_world_ids"]
    assert result["candidate_count"] == 1
    assert result["per_request_attempt_ceiling"] == 5000
    assert result["global_attempt_ceiling"] == 30000
    assert result["inherited_global_attempt_ceiling"] is None
    assert all(row["qualification_count"] == 0 for row in result["candidates"])
    assert result["approval_count"] == 0
    assert result["world_receipt_count"] == 0


def test_probe_rejects_attempt_ceiling_above_native_limit():
    import pytest
    with pytest.raises(ValueError, match="per-request attempt ceiling"):
        run_p22_training_proposal_probe(family="d4",
            training_draws=(286, 287), validation_draws=(386,),
            training_goal_relation="distinct", per_request_attempt_ceiling=30001)
    with pytest.raises(ValueError, match="global attempt ceiling"):
        run_p22_training_proposal_probe(family="d4",
            training_draws=(286, 287), validation_draws=(386,),
            training_goal_relation="distinct", global_attempt_ceiling=120001)


def test_candidate_specific_approval_executes_one_guarded_d4_simulator_action():
    result = run_p22_training_proposal_probe(family="d4",
        training_draws=(200, 202), training_goal_relation="distinct",
        validation_draws=(), measure_native_rule_work=True,
        approved_candidate_binding={
            "family": "d4",
            "expression_digest": "8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788",
            "expression_key": "compose:flip_r:rot90",
            "effect_digest": [[0, 2, 1, 3]],
            "params": [0, 2, 1, 3],
            "guard_state": [0, 1, 2, 3],
            "domain": "p22-development",
            "kind": "permutation",
            "source_epoch": 0,
            "model_epoch": 0,
            "frame_epoch": 0,
            "human_review_seconds": 0.25,
            "training_trial_keys": [
                "p22:d4-v2:train:0200", "p22:d4-v2:train:0202"],
        })
    adoption = result["simulated_adoption"]
    assert adoption["status"] == "COMPLETED"
    assert adoption["approval_count"] == 1
    assert adoption["approval_status"] == "consumed"
    assert adoption["approval_binding"]["params"] == [0, 2, 1, 3]
    assert adoption["receipt_status"] == "verified"
    assert adoption["world_transition_count"] == 1
    assert result["world_receipt_count"] == 1
    assert result["resource_snapshot"]["approval_cost_seconds"] == 0.25
    assert result["resource_snapshot"]["resource_measurement_coverage"][
        "approval_cost"]["status"] == "MEASURED"
    root = adoption["generation_zero_ancestor"]
    child = adoption["generation_one_checkpoint"]
    assert root["generation"] == 0
    assert child["generation"] == 1
    assert child["parent_digest"] == root["checkpoint_digest"]
    assert child["approval_id"] == adoption["approval_id"]
    assert child["receipt_id"] == adoption["receipt_id"]
    assert json.loads(child["resource_snapshot_json"])[
        "approval_cost_seconds"] == 0.25
    assert json.loads(root["resource_snapshot_json"])[
        "approval_cost_seconds"] == 0.0
    root_work = json.loads(root["resource_snapshot_json"])["native_rule_work"]
    child_work = json.loads(child["resource_snapshot_json"])["native_rule_work"]
    assert root_work["snapshot_sha256"]
    assert root_work["rule_identity_coverage"] == "COMPLETE"
    assert child_work["rule_identity_coverage"] == "COMPLETE"


def test_candidate_specific_adoption_requires_human_review_cost():
    import pytest
    with pytest.raises(ValueError, match="human_review_seconds"):
        run_p22_training_proposal_probe(family="d4", training_draws=(200, 202),
            training_goal_relation="distinct", validation_draws=(),
            approved_candidate_binding={"family": "d4",
                "expression_digest": "8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788"})


def test_approved_candidate_checkpoint_capture_rejects_validation_worlds():
    import pytest
    with pytest.raises(ValueError, match="training-only"):
        run_p22_training_proposal_probe(family="d4",
            training_draws=(200, 202), training_goal_relation="distinct",
            validation_draws=(300,), measure_native_rule_work=True,
            approved_candidate_binding={"family": "d4",
                "expression_digest": "8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788",
                "human_review_seconds": 1})


def test_candidate_approval_selects_one_exact_qualification_from_multiple():
    qualifications = [
        {"qualification_id": "#66758", "training_trial_keys": [
            "p22:d4-v2:train:0635", "p22:d4-v2:train:0637"]},
        {"qualification_id": "#66759", "training_trial_keys": [
            "p22:d4-v2:train:0635", "p22:d4-v2:train:0638"]},
    ]
    selected = _select_approved_qualification(qualifications, {
        "qualification_id": "#66758",
        "training_trial_keys": [
            "p22:d4-v2:train:0635", "p22:d4-v2:train:0637"],
    })
    assert selected["qualification_id"] == "#66758"


def test_candidate_approval_requires_exact_qualification_when_ambiguous():
    import pytest
    qualifications = [
        {"qualification_id": "#1", "training_trial_keys": ["a", "b"]},
        {"qualification_id": "#2", "training_trial_keys": ["a", "c"]},
    ]
    with pytest.raises(RuntimeError, match="requires an exact qualification_id"):
        _select_approved_qualification(qualifications, {
            "training_trial_keys": ["a", "b"]})
    with pytest.raises(RuntimeError, match="witnesses differ"):
        _select_approved_qualification(qualifications, {
            "qualification_id": "#1", "training_trial_keys": ["a", "c"]})
