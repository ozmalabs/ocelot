from copy import deepcopy
import json
import hashlib

import pytest

from evaluation.process_mastery.p22_resource_accounting import (
    NativeRuleWorkCapture, analyzer_resource_record, compare_resource_snapshots,
    merge_native_rule_work_snapshots, native_rule_work_digest_valid,
    resource_snapshot_digest_valid, snapshot_native_resources,
)
from tests.test_open_process_search import _agent as _p19_agent


def test_native_snapshot_retains_failed_and_pending_search_and_budget_usage():
    agent, _domain = _p19_agent(attempts=32)
    try:
        budget = agent.nodes("ThinkingBudget")[0]
        agent.s.set_attr(budget, "remaining", 73.0)
        for status in ("failed", "timed_out", "pending"):
            attempt = agent.s.add_node("OpenProcessSearchAttempt", {"status": status})
            agent.s.add_edge(agent.ag, "has_open_process_search_attempt", attempt, {})

        snapshot = snapshot_native_resources(agent)
        counts = {(row["type"], row["status"]): row["count"]
                  for row in snapshot["status_counts"]}
        assert snapshot["thinking_budget_capacity"] == 100.0
        assert snapshot["thinking_budget_remaining"] == 73.0
        assert snapshot["thinking_budget_spent"] == 27.0
        assert snapshot["resource_counts"]["search_attempts"] == 3
        assert counts[("OpenProcessSearchAttempt", "failed")] == 1
        assert counts[("OpenProcessSearchAttempt", "timed_out")] == 1
        assert counts[("OpenProcessSearchAttempt", "pending")] == 1
        assert snapshot["serialized_graph_bytes"] > 0
        assert snapshot["graph_node_count"] == len(agent.s.nodes())
        assert snapshot["graph_edge_count"] == agent.s.edge_count()
        assert snapshot["serialized_graph_bytes"] == len(json.dumps(
            agent.native.graph_to_dict(), sort_keys=True,
            separators=(",", ":"), default=str).encode("utf-8"))
        assert snapshot["native_graph_memory_bytes"] == agent.native.memory_total_bytes()
    finally:
        del agent


def test_resource_comparison_checks_digest_and_keeps_each_arm_vector():
    agent, _domain = _p19_agent(attempts=32)
    try:
        legacy = snapshot_native_resources(agent)
        missing_runtime = compare_resource_snapshots(
            {"unchanged": legacy, "full": deepcopy(legacy)})
        assert not missing_runtime["all_resource_dimensions_match"]
        assert "native_rule_steps" in missing_runtime["unavailable_dimensions"]

        before = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 0, "native_model_calls": 0})
        after = deepcopy(before)
        result = compare_resource_snapshots({"unchanged": before, "full": after})
        assert not result["all_resource_dimensions_match"]
        assert result["matched"]["native_rule_steps"]
        assert "event:candidate_validation_evaluations" in result["unavailable_dimensions"]
        assert not result["all_contract_dimensions_measured"]
        assert "retrieval_work" in result["contract_measurement_gaps"]
        assert result["failure_statuses_retained"]
        assert result["arms"]["full"]["thinking_budget_spent"] == 0.0

        after["resource_counts"]["search_attempts"] += 1
        with pytest.raises(ValueError, match="digest does not verify"):
            compare_resource_snapshots({"unchanged": before, "full": after})
    finally:
        del agent


def test_resource_snapshot_counts_training_exposure_and_native_work():
    agent, _domain = _p19_agent(attempts=32)
    try:
        evidence = agent.s.add_node("ProcessCurriculumEvidence", {"split": "training"})
        heldout = agent.s.add_node("ProcessCurriculumEvidence", {"split": "heldout"})
        outcome = agent.s.add_node("ProcessCurriculumOutcome", {"split": "training"})
        task = agent.s.add_node("SolveTask", {
            "split": "training", "steps": 3, "moves": 5.5})
        attempt = agent.s.add_node("OpenProcessSearchAttempt", {"work_cost": 4.0})
        proposal = agent.s.add_node("IndependentImprovementProposal", {})
        qualification = agent.s.add_node("IndependentImprovementQualification", {})
        approved = agent.s.add_node("ThinkingBudgetRequest", {
            "status": "approved", "cost": 2.0,
            "requester_kind": "open_process_search"})
        denied = agent.s.add_node("ThinkingBudgetRequest", {
            "status": "denied", "cost": 1.5,
            "requester_kind": "recursive_process_generation"})
        snapshot = snapshot_native_resources(agent)
        resources = snapshot["cumulative_resources"]
        assert resources["training_evidence_exposures"] == 1
        assert resources["training_outcomes"] == 1
        assert resources["training_task_exposures"] == 1
        assert resources["native_solver_steps"] == 3.0
        assert resources["native_solver_primitive_work"] == 5.5
        assert resources["search_declared_primitive_work"] == 4.0
        assert resources["budget_requested"] == 3.5
        assert resources["budget_approved"] == 2.0
        assert resources["budget_denied_cost"] == 1.5
        assert snapshot["budget_request_cost_by_requester"] == {
            "open_process_search": 2.0,
            "recursive_process_generation": 1.5,
        }
        assert snapshot["resource_event_counts"]["proposal_events"] == 2
        assert snapshot["resource_event_counts"]["qualification_events"] == 1
        assert snapshot["resource_measurement_coverage"]["proposal_work"][
            "status"] == "PARTIAL_EVENT_COUNT"
        training_records = []
        for node_id in agent.s.nodes():
            record = agent.s.node(node_id)
            attrs = record["attrs"]
            if ((record["type"] == "ProcessCurriculumEvidence"
                    or record["type"] == "ProcessCurriculumOutcome"
                    or record["type"] == "SolveTask") and attrs.get("split") == "training"):
                training_records.append({"node_id": str(node_id), "type": record["type"],
                                         "attrs": attrs})
        expected_bytes = len(json.dumps(training_records, sort_keys=True,
            separators=(",", ":"), default=str).encode("utf-8"))
        assert snapshot["training_data_bytes"] == expected_bytes
        assert snapshot["resource_measurement_coverage"]["training_data_bytes"][
            "status"] == "MEASURED_NODE_PAYLOAD_BYTES"
        assert snapshot["snapshot_sha256"]
    finally:
        del agent


def test_runtime_rule_steps_are_digest_bound_and_comparison_detects_mismatch():
    agent, _domain = _p19_agent(attempts=32)
    try:
        low = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 120, "native_model_calls": 0})
        high = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 121, "native_model_calls": 0})
        result = compare_resource_snapshots({"low": low, "high": high})
        assert not result["all_resource_dimensions_match"]
        assert result["matched"]["native_rule_steps"] is False
        assert result["matched"]["native_model_calls"] is True
        with pytest.raises(ValueError, match="native_rule_steps"):
            snapshot_native_resources(agent,
                runtime_counters={"native_rule_steps": True})
    finally:
        del agent


def test_search_reservation_counter_is_digest_bound_and_comparable():
    agent, _domain = _p19_agent(attempts=32)
    try:
        low = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 1, "native_model_calls": 0,
                              "search_attempts_reserved": 0})
        high = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 1, "native_model_calls": 0,
                              "search_attempts_reserved": 1})
        result = compare_resource_snapshots({"low": low, "high": high})
        assert result["matched"]["search_attempts_reserved"] is False
        assert result["matched"]["native_model_calls"] is True
        with pytest.raises(ValueError, match="search_attempts_reserved"):
            snapshot_native_resources(agent,
                runtime_counters={"native_rule_steps": 1, "native_model_calls": 0,
                                  "search_attempts_reserved": True})
    finally:
        del agent


def test_isolated_process_peak_rss_is_digest_bound_and_comparable():
    agent, _domain = _p19_agent(attempts=32)
    try:
        low = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 1, "native_model_calls": 0,
                              "process_peak_rss_bytes": 1000,
                              "process_peak_rss_observations": [{"pid": 101,
                                  "observed_at_unix_ns": 501,
                                  "peak_rss_bytes": 1000, "scope": "test"}],
                              "wall_time_seconds": 1.25})
        high = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 1, "native_model_calls": 0,
                              "process_peak_rss_bytes": 1001,
                              "process_peak_rss_observations": [{"pid": 102,
                                  "observed_at_unix_ns": 502,
                                  "peak_rss_bytes": 1001, "scope": "test"}],
                              "wall_time_seconds": 1.5})
        assert low["runtime_counters"]["process_peak_rss_observations"][0]["pid"] == 101
        assert resource_snapshot_digest_valid(low)
        result = compare_resource_snapshots({"low": low, "high": high})
        assert result["matched"]["process_peak_rss_bytes"] is False
        assert result["matched"]["wall_time_seconds"] is False
        with pytest.raises(ValueError, match="process_peak_rss_bytes"):
            snapshot_native_resources(agent,
                runtime_counters={"native_rule_steps": 1, "native_model_calls": 0,
                                  "process_peak_rss_bytes": -1})
        with pytest.raises(ValueError, match="wall_time_seconds"):
            snapshot_native_resources(agent,
                runtime_counters={"native_rule_steps": 1, "native_model_calls": 0,
                                  "wall_time_seconds": -0.1})
        with pytest.raises(ValueError, match="maximum must match"):
            snapshot_native_resources(agent,
                runtime_counters={"native_rule_steps": 1, "native_model_calls": 0,
                    "process_peak_rss_bytes": 1000,
                    "process_peak_rss_observations": [{"pid": 103,
                        "observed_at_unix_ns": 503,
                        "peak_rss_bytes": 999, "scope": "test"}]})
        tampered = deepcopy(low)
        tampered["runtime_counters"]["process_peak_rss_observations"][0]["pid"] = 999
        assert not resource_snapshot_digest_valid(tampered)
    finally:
        del agent


def test_analyzer_resource_adapter_preserves_measurement_gaps_and_sources():
    agent, _domain = _p19_agent(attempts=32)
    try:
        snapshot = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 4, "native_model_calls": 0,
                "search_attempts_reserved": 2, "process_peak_rss_bytes": 4096,
                "native_candidate_validation_evaluations": 3})
        adapted = analyzer_resource_record(snapshot,
            cumulative_primitive_work=7, wall_time_seconds=0.25)
        values = adapted["resources"]
        measurements = adapted["resource_measurements"]
        assert values["native_rule_steps"] == 4
        assert values["native_rule_term_evaluations"] is None
        assert values["native_model_calls"] == 0
        assert values["process_peak_rss_bytes"] == 4096
        assert values["wall_time_seconds"] == 0.25
        assert measurements["wall_time_seconds"]["status"] == "MEASURED"
        assert measurements["native_rule_term_evaluations"]["status"] == "UNAVAILABLE"
        assert measurements["training_data_bytes"]["status"] == "MEASURED_NODE_PAYLOAD_BYTES"
        assert measurements["proposal_work"]["status"] == "UNAVAILABLE"
        assert values["retrieval_work"] is None
        assert measurements["retrieval_work"]["status"] == "UNAVAILABLE"
        assert adapted["resource_snapshot_sha256"] == snapshot["snapshot_sha256"]
        with pytest.raises(ValueError, match="cumulative primitive work"):
            analyzer_resource_record(snapshot, cumulative_primitive_work=True)
        agent.s.add_node("SolveTask", {"split": "training", "steps": 1, "moves": 2})
        work_snapshot = snapshot_native_resources(agent)
        with pytest.raises(ValueError, match="below measured snapshot work"):
            analyzer_resource_record(work_snapshot, cumulative_primitive_work=1)
        tampered = deepcopy(snapshot)
        tampered["serialized_graph_bytes"] += 1
        with pytest.raises(ValueError, match="digest does not verify"):
            analyzer_resource_record(tampered, cumulative_primitive_work=7)
    finally:
        del agent


def test_classified_native_rule_work_measures_operation_categories_without_overlap():
    agent, _domain = _p19_agent(attempts=32)
    try:
        names = {
            "retrieval_work": "episodic_retrieve_best_partial_cue",
            "proposal_work": "iip_propose_native_training_candidate",
            "verification_work": "iip_qualify_after_independent_goal_composition",
            "model_refinement_work": "cm_open_one_funded_refinement_request",
            "definition_decode_work": "sd_decode",
            "rollback_work": "rpi_rollback_failed_generation_to_verified_ancestor",
        }
        rules = [{"rule_index": i, "rule_name": name,
                  "metric": "term_evaluations", "count": i + 1}
                 for i, name in enumerate(names.values())]
        work = {"schema": "p22_native_rule_work_v1", "store_instance_id": 1,
            "rules": rules, "rule_identity_coverage": "COMPLETE",
            "unresolved_rule_indices": [],
            "totals_by_metric": {"term_evaluations": sum(range(1, 7))}}
        work["snapshot_sha256"] = hashlib.sha256(json.dumps(work,
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        snapshot = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 1, "native_model_calls": 0},
            native_rule_work=work)
        adapted = analyzer_resource_record(snapshot, cumulative_primitive_work=0)
        for index, name in enumerate(names):
            assert adapted["resources"][name] == index + 1
            assert adapted["resource_measurements"][name]["status"] == "MEASURED"
        assert sum(adapted["resources"][name] for name in names) == 21
        assert adapted["resources"]["approval_cost"] == 0.0
        assert adapted["resource_measurements"]["approval_cost"]["status"] == "MEASURED"
    finally:
        del agent


def test_rule_work_merge_preserves_store_namespaces_and_cumulative_totals():
    def capture(store_id, audit_id, count):
        value = {"schema": "p22_native_rule_work_v2",
            "store_instance_id": store_id,
            "rules": [{"rule_index": 4, "rule_audit_id": audit_id,
                       "rule_name": "ops_mint_verified_candidate",
                       "metric": "term_evaluations", "count": count}],
            "rule_identity_coverage": "COMPLETE",
            "unresolved_rule_indices": [],
            "totals_by_metric": {"term_evaluations": count}}
        value["snapshot_sha256"] = hashlib.sha256(json.dumps(value,
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return value

    def historical_v1():
        value = {"schema": "p22_native_rule_work_v1", "store_instance_id": 303,
            "rules": [{"rule_index": 9, "rule_name": "ops_mint_verified_candidate",
                       "metric": "term_evaluations", "count": 3}],
            "rule_identity_coverage": "COMPLETE", "unresolved_rule_indices": [],
            "totals_by_metric": {"term_evaluations": 3}}
        value["snapshot_sha256"] = hashlib.sha256(json.dumps(value,
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return value

    previous = capture(101, 1004, 7)
    current = capture(202, 2004, 11)
    merged = merge_native_rule_work_snapshots(previous, current)
    assert merged["schema"] == "p22_native_rule_work_v3"
    assert merged["store_instance_ids"] == [101, 202]
    assert {(row["store_instance_id"], row["rule_audit_id"], row["count"])
            for row in merged["rules"]} == {(101, 1004, 7), (202, 2004, 11)}
    assert merged["totals_by_metric"] == {"term_evaluations": 18}
    assert merged["rule_identity_coverage"] == "COMPLETE"
    assert native_rule_work_digest_valid(merged)
    damaged = deepcopy(merged)
    damaged["rules"][0]["count"] += 1
    assert not native_rule_work_digest_valid(damaged)
    with pytest.raises(ValueError, match="double-count"):
        merge_native_rule_work_snapshots(previous, previous)
    historic = merge_native_rule_work_snapshots(historical_v1(), current)
    assert historic["totals_by_metric"] == {"term_evaluations": 14}
    assert historic["rule_identity_coverage"] == "COMPLETE"


def test_approval_cost_requires_review_duration_for_each_approval():
    agent, _domain = _p19_agent(attempts=32)
    try:
        agent.s.add_node("OpenProcessAdoptionApproval", {
            "status": "consumed", "approval_kind": "human"})
        partial = analyzer_resource_record(snapshot_native_resources(agent),
            cumulative_primitive_work=0)
        assert partial["resources"]["approval_cost"] == 1
        assert partial["resource_measurements"]["approval_cost"]["status"] == (
            "PARTIAL_EVENT_COUNT")

        agent.s.add_node("OpenProcessAdoptionApproval", {
            "status": "consumed", "approval_kind": "human",
            "human_review_seconds": 2.5,
            "human_review_cost_source": "reviewer_self_report"})
        mixed = analyzer_resource_record(snapshot_native_resources(agent),
            cumulative_primitive_work=0)
        assert mixed["resource_measurements"]["approval_cost"]["status"] == (
            "PARTIAL_EVENT_COUNT")
    finally:
        del agent


def test_zero_and_complete_self_reported_approval_costs_are_measured():
    agent, _domain = _p19_agent(attempts=32)
    try:
        no_approval = analyzer_resource_record(snapshot_native_resources(agent),
            cumulative_primitive_work=0)
        assert no_approval["resources"]["approval_cost"] == 0.0
        assert no_approval["resource_measurements"]["approval_cost"]["status"] == (
            "MEASURED")

        agent.s.add_node("OpenProcessAdoptionApproval", {
            "status": "consumed", "approval_kind": "human",
            "human_review_seconds": 1.25,
            "human_review_cost_source": "reviewer_self_report"})
        agent.s.add_node("OpenProcessAdoptionApproval", {
            "status": "consumed", "approval_kind": "human",
            "human_review_seconds": 0.75,
            "human_review_cost_source": "reviewer_self_report"})
        measured = analyzer_resource_record(snapshot_native_resources(agent),
            cumulative_primitive_work=0)
        assert measured["resources"]["approval_cost"] == 2.0
        assert measured["resource_measurements"]["approval_cost"]["status"] == (
            "MEASURED")
        assert measured["resource_measurements"]["approval_cost"]["source"].endswith(
            "reviewer_self_report")
    finally:
        del agent


def test_isolated_native_rule_capture_attributes_work_and_cleans_global_audit():
    agent, _domain = _p19_agent(attempts=32)
    try:
        capture = NativeRuleWorkCapture(agent.native).start()
        agent.native.run_rules_report(200, False)
        interim = capture.snapshot()
        assert interim["schema"] == "p22_native_rule_work_v2"
        assert capture.active
        agent.native.run_rules_report(200, False)
        result = capture.finish()
        assert result["schema"] == "p22_native_rule_work_v2"
        assert result["store_instance_id"] is not None
        assert result["rules"]
        assert result["totals_by_metric"].get("rule_enumerations", 0) > 0
        assert result["totals_by_metric"]["term_evaluations"] >= (
            interim["totals_by_metric"]["term_evaluations"])
        assert result["snapshot_sha256"]
        assert agent.native.scale_audit_mode_snapshot() == (False, False, False)
        assert agent.native.scale_audit_per_rule_snapshot() == []
        snapshot = snapshot_native_resources(agent,
            runtime_counters={"native_rule_steps": 0, "native_model_calls": 0},
            native_rule_work=result)
        adapted = analyzer_resource_record(snapshot, cumulative_primitive_work=0)
        assert adapted["resources"]["native_rule_term_evaluations"] == (
            result["totals_by_metric"]["term_evaluations"])
        assert adapted["resource_measurements"]["native_rule_term_evaluations"][
            "status"] == "MEASURED"
        legacy_snapshot = deepcopy(snapshot)
        legacy_snapshot.pop("native_rule_work_by_class")
        legacy_snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
            {key: value for key, value in legacy_snapshot.items()
             if key != "snapshot_sha256"}, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        legacy_adapted = analyzer_resource_record(legacy_snapshot,
            cumulative_primitive_work=0)
        assert legacy_adapted["resource_measurements"]["proposal_work"][
            "status"] == ("MEASURED" if result["rule_identity_coverage"] == "COMPLETE"
                          else "UNAVAILABLE")
    finally:
        del agent


def test_repeated_native_rule_capture_resolves_namespaced_ids_to_local_indices():
    snapshots = []
    for _ in range(2):
        agent, _domain = _p19_agent(attempts=32)
        try:
            capture = NativeRuleWorkCapture(agent.native).start()
            agent.native.run_rules_report(200, False)
            snapshots.append(capture.finish())
        finally:
            del agent
    for snapshot in snapshots:
        assert snapshot["rule_identity_coverage"] == "COMPLETE"
        assert snapshot["unresolved_rule_indices"] == []
        assert snapshot["rules"]
        assert all(isinstance(row["rule_index"], int)
                   and isinstance(row["rule_audit_id"], int)
                   for row in snapshot["rules"])
    assert snapshots[0]["store_instance_id"] != snapshots[1]["store_instance_id"]
    assert [row["rule_index"] for row in snapshots[0]["rules"]] == [
        row["rule_index"] for row in snapshots[1]["rules"]]


def test_native_rule_work_is_digest_bound_and_compared_across_arms():
    def captured(total):
        value = {"schema": "p22_native_rule_work_v1", "store_instance_id": 1,
            "rules": [], "totals_by_metric": {"term_evaluations": total}}
        value["snapshot_sha256"] = hashlib.sha256(json.dumps(value,
            sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return value

    agent, _domain = _p19_agent(attempts=32)
    try:
        counters = {"native_rule_steps": 1, "native_model_calls": 0}
        low = snapshot_native_resources(agent, runtime_counters=counters,
            native_rule_work=captured(10))
        high = snapshot_native_resources(agent, runtime_counters=counters,
            native_rule_work=captured(12))
        comparison = compare_resource_snapshots({"low": low, "high": high})
        assert comparison["native_rule_work_complete"]
        assert comparison["matched"]["native_rule_work:term_evaluations"] is False
        tampered = deepcopy(low)
        tampered["native_rule_work"]["totals_by_metric"]["term_evaluations"] = 11
        tampered["snapshot_sha256"] = hashlib.sha256(json.dumps(
            {key: value for key, value in tampered.items() if key != "snapshot_sha256"},
            sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        with pytest.raises(ValueError, match="native rule-work snapshot digest"):
            compare_resource_snapshots({"low": tampered, "high": high})
    finally:
        del agent
