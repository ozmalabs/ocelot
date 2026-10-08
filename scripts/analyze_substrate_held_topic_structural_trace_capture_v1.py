#!/usr/bin/env python3
"""Independent gates for the held-topic structural/access/work capture."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/held_topic_structural_trace_capture_v1_20260928.json"
OUT = ROOT / "evaluation/reports/held_topic_structural_trace_capture_v1_analysis_20260928.json"
BASE_OUT = ROOT / "evaluation/reports/substrate_live_held_topic_evidence_v1_6_20260926.json"
BASE_RAW = ROOT / "evaluation/reports/substrate_live_held_topic_evidence_v1_6_workers_raw_20260926.json"
SCHEDULER = {
    "scheduler_pass": "scheduler_passes",
    "scheduler_external_poll_slots": "scheduler_external_poll_slots",
    "scheduler_fixedpoint_probe_slots": "scheduler_fixedpoint_probe_slots",
    "scheduler_dirty_vector_slots": "scheduler_dirty_vector_slots",
    "scheduler_selected_rules": "scheduler_selected_rules",
}
FAMILIES = {"rule_edits": 1, "rule_patches": 2, "fb_samples": 3, "track_identity": 4, "net_collapses": 5}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def work_metric(kind: str, subject) -> str | None:
    if kind in SCHEDULER:
        return SCHEDULER[kind]
    if kind.startswith("deferred_queue_"):
        family = next((name for name, code in FAMILIES.items() if code == subject), None)
        suffix = {"deferred_queue_enqueue_items": "enqueued_items",
                  "deferred_queue_drain_batches": "drain_batches",
                  "deferred_queue_drained_items": "drained_items"}.get(kind)
        return f"deferred_queue:{family}:{suffix}" if family and suffix else None
    return None


def reconcile_work(work: dict) -> dict:
    trace: Counter[tuple[int, str]] = Counter()
    operation_kinds = {}
    op_ids = set()
    scopes = set()
    valid = True
    unknown = Counter()
    for row in work["all_scope_work_rows"]:
        if len(row) != 6:
            valid = False
            continue
        scope, operation, uid, kind, subject, units = row
        scope, operation, uid, units = int(scope), int(operation), int(uid), int(units)
        subject = None if subject is None else int(subject)
        scopes.add(scope)
        op_ids.add(operation)
        valid &= scope > 0 and operation > 0 and units > 0
        if kind == "operation_kind":
            valid &= subject in (1, 2, 3) and units == 1 and operation not in operation_kinds
            operation_kinds[operation] = subject
            continue
        metric = work_metric(str(kind), subject)
        if metric is None:
            unknown[str(kind)] += units
            valid = False
        else:
            trace[(scope, metric)] += units
    counters: Counter[tuple[int, str]] = Counter()
    for scope, metric, units in work["all_scope_scale_counters"]:
        metric = str(metric)
        if metric in set(SCHEDULER.values()) or metric.startswith("deferred_queue:"):
            counters[(int(scope), metric)] += int(units)
    keys = set(trace) | set(counters)
    deltas = {f"{scope}:{metric}": counters[(scope, metric)] - trace[(scope, metric)]
              for scope, metric in sorted(keys)}
    global_deltas = {}
    global_counts = work["scale_counters"]
    metrics = list(SCHEDULER.values()) + [
        f"deferred_queue:{family}:{suffix}" for family in FAMILIES
        for suffix in ("enqueued_items", "drain_batches", "drained_items")]
    for metric in metrics:
        scoped = sum(value for (scope, key), value in counters.items() if key == metric)
        global_deltas[metric] = {"global": int(global_counts.get(metric, 0)), "scoped_sum": scoped,
                                 "delta": int(global_counts.get(metric, 0)) - scoped}
    return {
        "valid_rows": valid, "dropped_rows": int(work["all_scope_work_dropped"]),
        "scope_count": len(scopes), "operation_count": len(op_ids),
        "operation_kind_marker_count": len(operation_kinds),
        "every_operation_has_exactly_one_kind_marker": op_ids == set(operation_kinds),
        "scope_counter_deltas": deltas,
        "all_scope_counters_reconcile": all(value == 0 for value in deltas.values()),
        "process_global_deltas": global_deltas,
        "all_global_work_assigned_to_scopes": all(row["delta"] == 0 for row in global_deltas.values()),
        "unknown_work_kinds": dict(unknown),
    }


def access_summary(work: dict) -> dict:
    rules = {int(row["rule_uid"]): row for row in work["static_rule_accesses"]}
    categories = Counter()
    mismatches = Counter()
    unresolved = set(map(int, work["unresolved_access_rule_uids"]))
    try:
        from scripts.analyze_rooted_frame_access_scope_reconciliation_v1_2 import static_match
        for row in work["access_rows"]:
            uid = int(row["rule_uid"])
            if uid not in rules:
                unresolved.add(uid)
                categories["uid_unresolved"] += int(row["count"])
                continue
            category = static_match(row, rules[uid])
            categories[category] += int(row["count"])
            if category in ("static_key_mismatch", "implicit_read_not_declared"):
                mismatches[category] += int(row["count"])
    except ImportError:
        unresolved.add(-1)
    total = sum(int(row["count"]) for row in work["access_rows"])
    return {
        "weighted_access_events": total,
        "row_count": len(work["access_rows"]),
        "dropped_events": int(work["access_dropped"]),
        "recorded_weight_conserves": total == int(work["weighted_access_events"]),
        "static_rule_uids": len(rules),
        "unresolved_rule_uids": sorted(unresolved),
        "static_event_categories": dict(sorted(categories.items())),
        "static_mismatch_event_weights": dict(sorted(mismatches.items())),
    }


def verify_schema(frame: dict) -> dict:
    members = set(map(int, frame["node_ids"]))
    external = {int(edge[2]) if int(edge[0]) in members else int(edge[0]) for edge in frame["boundary_edges"]}
    member_schema = frame["owned_task_attribute_schema"]
    external_schema = frame["external_boundary_attribute_schema"]

    def check(schema: dict, expected: set[int]) -> bool:
        nodes = schema.get("nodes", [])
        if {int(row["node_id"]) for row in nodes} != expected or len(nodes) != len(expected):
            return False
        by_type_attr = defaultdict(lambda: {"count": 0, "kinds": set(), "categories": set()})
        for row in nodes:
            typ = str(row["node_type"])
            kinds = row["attribute_value_kinds"]
            for key in row["attribute_keys"]:
                slot = by_type_attr[f"{typ}.{key}"]
                slot["count"] += 1
                slot["kinds"].add(kinds[key])
                if key in row["observed_categorical_values"]:
                    slot["categories"].add(row["observed_categorical_values"][key])
        saved = schema.get("by_type_attribute", {})
        if set(saved) != set(by_type_attr):
            return False
        for key, slot in by_type_attr.items():
            row = saved[key]
            if int(row["node_attribute_observations"]) != slot["count"] or set(row["python_value_kinds"]) != slot["kinds"]:
                return False
            if row["field_designated_categorical"] and int(row["observed_categorical_value_count_lower_bound"]) != len(slot["categories"]):
                return False
            if row["field_designated_categorical"] and row["observed_categorical_values"] is not None and set(row["observed_categorical_values"]) != slot["categories"]:
                return False
        return True

    expected_member_types = Counter(str(row["node_type"]) for row in member_schema["nodes"])
    expected_external_types = Counter(str(row["node_type"]) for row in external_schema["nodes"])
    return {
        "member_node_metadata_exact": check(member_schema, members),
        "external_node_metadata_exact": check(external_schema, external),
        "member_type_counts_match": dict(sorted(expected_member_types.items())) == frame["member_node_type_counts"],
        "external_type_counts_match": dict(sorted(expected_external_types.items())) == frame["external_node_type_counts_recomputed"],
        "edge_cut_recomputes": len(frame["boundary_edges"]) == int(frame["boundary_incidence_count"])
            and len(frame["internal_edges"]) == int(frame["internal_edge_count"]),
    }


def independent_task_oracle(turn: dict) -> dict:
    topic = turn["expected_topic"]
    expected_path = turn["expected_path"]
    dispatch = (turn.get("comprehension") or {}).get("dispatch", {})
    if topic not in {"unobtainium", "localhitium"}:
        held = turn["held_answers"]
        goal_ok = (len(turn["answer_topic_goal_ids"]) == 1 and len(turn["goals"]) == 1
                   and turn["goals"][0]["attrs"].get("concept") == topic)
        receipt_ok = any(receipt["attrs"].get("status") == "released"
                         and receipt["attrs"].get("surface") == turn["reply"]
                         and any(node_id in receipt["released_ids"]
                                 for node_id in turn["answer_topic_goal_ids"] + turn["held_answer_ids"])
                         for receipt in turn["receipts"])
        return {"expected": "exact supported answer with grounded held evidence and released receipt",
                "passed": turn["reply"] == {"copper": "Copper conducts electricity and heat.",
                                            "basalt": "Basalt is a fine-grained igneous rock formed when lava cools quickly.",
                                            "hexagon": "A hexagon has six straight sides and six angles."}[topic]
                    and len(held) == 1 and held[0]["attrs"].get("text") == turn["reply"]
                    and held[0]["attrs"].get("grounding_referent") == topic
                    and held[0]["attrs"].get("grounding_status") == "supported"
                    and len(turn["evidence"]) >= 1 and goal_ok and receipt_ok
                    and dispatch.get("path") == expected_path}
    if topic == "unobtainium":
        return {"expected": "unknown topic remains unresolved without unrelated answer leakage",
                "passed": len(turn["answer_topic_goal_ids"]) == 1 and len(turn["grounder_calls"]) >= 1
                    and turn["grounder_calls"][0]["phrase"].lower() == "unobtainium"
                    and turn["goals"][0]["attrs"].get("outcome") == "unresolved"
                    and "copper conducts electricity" not in turn["reply"].lower()
                    and "unobtainium" in turn["reply"].lower() and dispatch.get("path") == expected_path}
    expected_answer = "Localhitium is a controlled local-source fixture for this evaluation."
    request_statuses = {request["type"]: request["attrs"].get("status") for request in turn["matching_requests_after"]}
    return {"expected": "injected local hit is returned, grounded, and released; stale requests superseded",
            "passed": turn["reply"] == expected_answer and len(turn["grounder_calls"]) == 1
                and turn["grounder_calls"][0].get("injected_local_hit") is True
                and len(turn["held_answers"]) == 1 and turn["held_answers"][0]["attrs"].get("text") == expected_answer
                and turn["held_answers"][0]["attrs"].get("grounding_status") == "supported"
                and len(turn["evidence"]) >= 1 and turn["goals"][0]["attrs"].get("outcome") == "resolved"
                and any(receipt["attrs"].get("status") == "released" and receipt["attrs"].get("surface") == expected_answer
                        for receipt in turn["receipts"])
                and request_statuses.get("GroundRequest") == "superseded"
                and request_statuses.get("SearchRequest") == "superseded"
                and dispatch.get("path") == expected_path}


def main() -> None:
    raw, baseline = json.loads(RAW.read_text()), json.loads(BASE_OUT.read_text())
    base_raw = json.loads(BASE_RAW.read_text())
    checks = {
        "three_workers": len(raw["runs"]) == 3,
        "three_fresh_pids": len({run["pid"] for run in raw["runs"]}) == 3,
        "replicates_0_1_2": sorted(run["replicate"] for run in raw["runs"]) == [0, 1, 2],
        "source_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"]
            and all(run["driver_started_inputs"] == raw["locked_inputs"] == run["driver_finished_inputs"] for run in raw["runs"]),
        "base_report_gates_pass": all(bool(value) for value in baseline.get("checks", {}).values()),
        "base_raw_lock_stable": baseline["locked_inputs"] == baseline["post_run_inputs"]
            and baseline["locked_inputs"] == json.loads((ROOT / "evaluation/substrate_capability/live_held_topic_evidence_v1_6_lock_20260926.json").read_text())["locked_inputs"],
    }
    base_by_rep = {int(run["replicate"]): run for run in base_raw["runs"]}
    analyses = []
    outcome_assessments = []
    baseline_comparisons = []
    core_fields = ("prompt", "expected_topic", "expected_path", "reply", "message", "comprehension",
                   "goals", "answer_topic_goal_ids", "held_answers", "evidence", "receipts", "matching_requests_after")
    structural_fields = ("node_ids", "node_count", "internal_edge_count", "boundary_incidence_count",
                         "boundary_unique_external_node_count", "boundary_edge_type_counts",
                         "boundary_external_node_type_counts")
    for run in raw["runs"]:
        rep = int(run["replicate"])
        old = base_by_rep[rep]
        check_by_call = []
        calls = list(run["teaching"]) + list(run["turns"])
        checks[f"replicate_{rep}_fixed_schedule"] = len(run["teaching"]) == 3 and len(run["turns"]) == 7
        checks[f"replicate_{rep}_base_worker_lock_stable"] = run["worker_started_inputs"] == run["worker_finished_inputs"]
        task_baseline_match = all(
            all(new.get(field) == previous.get(field) for field in core_fields)
            for new, previous in zip(run["turns"], old["turns"])) and all(
                new["returned_answer"] == previous["returned_answer"] and new["expected_answer"] == previous["expected_answer"]
                for new, previous in zip(run["teaching"], old["teaching"]))
        boundary_baseline_match = all(
            all(new["task_frame"].get(field) == previous["task_frame"].get(field) for field in structural_fields)
            for new, previous in zip(run["turns"], old["turns"]))
        baseline_comparisons.append({"replicate": rep, "task_outputs_match_historical_v1_6": task_baseline_match,
                                     "boundary_summaries_match_historical_v1_6": boundary_baseline_match})
        for teach in run["teaching"]:
            outcome_assessments.append({"replicate": rep, "operation": "teaching", "topic": teach["topic"],
                                        "expected": teach["expected_answer"],
                                        "passed": teach["returned_answer"] == teach["expected_answer"]})
        for turn in run["turns"]:
            oracle = independent_task_oracle(turn)
            outcome_assessments.append({"replicate": rep, "operation": "query", "prompt": turn["prompt"],
                                        "topic": turn["expected_topic"], **oracle})
        for call_index, call in enumerate(calls):
            work = call["work"]
            access = access_summary(work)
            reconciliation = reconcile_work(work)
            prefix = f"rep{rep}_call{call_index}"
            call_checks = {
                "access_count_conserves": access["recorded_weight_conserves"],
                "access_zero_drops": access["dropped_events"] == 0,
                "all_access_uids_resolve": not access["unresolved_rule_uids"],
                "work_rows_valid": reconciliation["valid_rows"],
                "work_zero_drops": reconciliation["dropped_rows"] == 0,
                "operation_markers_complete": reconciliation["every_operation_has_exactly_one_kind_marker"],
                "scope_work_reconciles": reconciliation["all_scope_counters_reconcile"],
                "process_global_work_assigned": reconciliation["all_global_work_assigned_to_scopes"],
            }
            for key, value in call_checks.items():
                checks[prefix + "_" + key] = bool(value)
            check_by_call.append({"call_index": call_index, "access": access,
                                  "work_reconciliation": reconciliation, "checks": call_checks})
        frame_checks = []
        for turn_index, turn in enumerate(run["turns"]):
            frame_check = verify_schema(turn["task_frame"])
            frame_checks.append(frame_check)
            for key, value in frame_check.items():
                checks[f"rep{rep}_turn{turn_index}_{key}"] = value
        analyses.append({"replicate": rep, "pid": run["pid"], "calls": check_by_call,
                         "task_frame_checks": frame_checks,
                         "weighted_access_events_by_call": [row["access"]["weighted_access_events"] for row in check_by_call],
                         "static_mismatch_weights_by_call": [row["access"]["static_mismatch_event_weights"] for row in check_by_call]})
    result = {
        "schema_version": 1,
        "run_id": "held-topic-structural-trace-capture-v1-analysis-20260928",
        "input_sha256": {"raw": sha(RAW), "base_output": sha(BASE_OUT), "base_raw": sha(BASE_RAW),
                         "base_lock": sha(ROOT / "evaluation/substrate_capability/live_held_topic_evidence_v1_6_lock_20260926.json"),
                         "analyzer": sha(Path(__file__))},
        "checks": checks, "all_capture_integrity_checks_pass": all(checks.values()),
        "capability_oracle_pass": all(row["passed"] for row in outcome_assessments),
        "outcome_assessments": outcome_assessments,
        "historical_baseline_comparisons": baseline_comparisons,
        "worker_analyses": analyses,
        "claim_boundary": "Fresh instrumented replay of a fixed seven-case authored held-topic suite. Access traces remain partial, static concordance does not prove completeness, and categorical observations do not define full domains.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_capture_integrity_checks_pass": result["all_capture_integrity_checks_pass"],
                      "capability_oracle_pass": result["capability_oracle_pass"], "check_count": len(checks),
                      "failed_checks": [key for key, value in checks.items() if not value],
                      "output": str(OUT.relative_to(ROOT))}, indent=2))
    if not result["all_capture_integrity_checks_pass"]:
        raise SystemExit("held-topic structural trace analysis failed")


if __name__ == "__main__":
    main()
