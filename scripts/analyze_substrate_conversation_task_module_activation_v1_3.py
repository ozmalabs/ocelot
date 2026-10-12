#!/usr/bin/env python3
"""Independent integrity, task-oracle, and call-footprint analysis."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/conversation_task_module_activation_v1_3_20260928.json"
OUT = ROOT / "evaluation/reports/conversation_task_module_activation_v1_3_analysis_20260928.json"
CONDITIONS = ("scene_description", "held_self_knowledge_answer", "self_report_action",
              "unknown_word_clarification", "concern_authoring")


def task_ok(run: dict, locked_base_inputs: dict) -> bool:
    if not (run.get("source_stable") and run.get("locked_inputs") == locked_base_inputs
            == run.get("post_run_inputs") and run.get("boot_loaded", 0) > 0
            and run.get("error") is None and len(run.get("turns", [])) == 1):
        return False
    turn = run["turns"][0]
    routes = [item.get("route") for item in run.get("action_results", [])]
    if run["condition"] == "scene_description":
        return (run["reply"] == "I see the grey thing stays, the yellow counter, and the blue thing moves."
                and any(g.get("kind") == "describe_scene" and g.get("status") == "resolved"
                        and g.get("events") == ["selection", "execution", "action_result"]
                        for g in turn["goals"])
                and len(run["faculty_build_calls"]) == 1
                and run["faculty_build_calls"][0]["rule_delta"] == 18)
    if run["condition"] == "held_self_knowledge_answer":
        return "organis" in run["reply"].lower() and not run["reply"].rstrip().endswith("?")
    if run["condition"] == "self_report_action":
        return ("self_report" in routes
                and any(g.get("kind") == "report_self" and g.get("status") == "resolved"
                        and g.get("events") == ["selection", "execution", "action_result"]
                        for g in turn["goals"])
                and bool(run["reply"].strip()))
    if run["condition"] == "unknown_word_clarification":
        return ("quorplezap" in run["reply"].lower() and run["reply"].rstrip().endswith("?")
                and any("quorplezap" in str(m.get("trouble_source", "")).lower()
                        and m.get("expects_response") is True
                        and "clarification" in m.get("speech_acts", [])
                        for m in turn["outbound_messages"]))
    if run["condition"] == "concern_authoring":
        return (any(a.get("route") == "concern_authored" and a.get("concern") is not None
                    for a in run.get("action_results", []))
                and bool(run["reply"].strip())
                and "no attached world/faculty" not in run["reply"].lower()
                and run["teacher_calls"] == 0)
    return False


def footprint(run: dict) -> dict:
    trace = run["module_activation"]
    return {"modules": trace["module_call_counts"],
            "functions": trace["function_call_counts"],
            "edges": trace["domain_call_edges"]}


def main() -> None:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    locked_base = raw["locked_inputs"]["base_panel_inputs"]
    counts = {condition: [r for r in runs if r["condition"] == condition] for condition in CONDITIONS}
    outcomes = {condition: [task_ok(r, locked_base) for r in rows]
                for condition, rows in counts.items()}
    checks = {
        "capture_status_complete": raw.get("capture_status") == "complete",
        "parent_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "ten_unique_worker_processes": len(runs) == 10 and len({r["pid"] for r in runs}) == 10,
        "two_workers_per_condition": all(len(rows) == 2 for rows in counts.values()),
        "worker_inputs_stable": all(r["module_activation_inputs_stable"]
                                     and r["module_activation_inputs_before"]
                                     == raw["locked_inputs"]
                                     == r["module_activation_inputs_after"] for r in runs),
        "wordnet_corpus_and_cache_stable": all(
            r["module_activation_inputs_before"]["wordnet_external_inputs"]
            == raw["locked_inputs"]["wordnet_external_inputs"]
            == r["module_activation_inputs_after"]["wordnet_external_inputs"] for r in runs),
        "wordnet_cache_metadata_valid": (
            raw["locked_inputs"]["wordnet_external_inputs"]["cache_metadata"]
            == [1, raw["locked_inputs"]["wordnet_external_inputs"]["corpus_source_digest"]]),
        "no_wordnet_database_build_in_worker_calls": all(
            r["module_activation"]["function_call_counts"].get(
                "domains.wordnet_membership:_build_database", 0) == 0 for r in runs),
        "base_worker_inputs_stable": all(r.get("source_stable")
                                         and r.get("locked_inputs") == locked_base == r.get("post_run_inputs")
                                         for r in runs),
        "one_conversation_extent_each": all(r["module_activation"]["conversation_extent_count"] == 1
                                             for r in runs),
        "nonempty_domain_trace_each": all(r["module_activation"]["domain_call_event_count"] > 0
                                           and bool(r["module_activation"]["module_call_counts"])
                                           for r in runs),
        "conditions_match_preregistered_schedule": sorted((r["condition"], r["replicate"]) for r in runs)
            == sorted((str(c), int(rep)) for c, rep in raw["schedule"]),
    }
    by_condition = {}
    for condition, rows in counts.items():
        fps = [footprint(r) for r in rows]
        module_sets = [set(fp["modules"]) for fp in fps]
        function_sets = [set(fp["functions"]) for fp in fps]
        edge_sets = [{(e["caller"], e["callee"]) for e in fp["edges"]} for fp in fps]
        wall = [r["task_wall_ns"] / 1e6 for r in rows]
        cpu = [r["task_process_cpu_ns"] / 1e6 for r in rows]
        by_condition[condition] = {
            "task_oracle_passes": sum(outcomes[condition]),
            "task_oracle_trials": len(rows),
            "workers": [{"replicate": r["replicate"], "pid": r["pid"],
                         "module_count": len(fps[i]["modules"]),
                         "domain_function_count": len(fps[i]["functions"]),
                         "domain_call_events": r["module_activation"]["domain_call_event_count"],
                         "modules": sorted(fps[i]["modules"]),
                         "top_functions": sorted(fps[i]["functions"].items(), key=lambda x: (-x[1], x[0]))[:20],
                         "top_call_edges": sorted(((e["caller"], e["callee"], e["calls"])
                                                    for e in fps[i]["edges"]), key=lambda x: (-x[2], x[0], x[1]))[:30]}
                        for i, r in enumerate(rows)],
            "module_intersection": sorted(set.intersection(*module_sets)) if module_sets else [],
            "module_union": sorted(set.union(*module_sets)) if module_sets else [],
            "module_footprints_exactly_equal": len(module_sets) == 2 and module_sets[0] == module_sets[1],
            "function_intersection_count": len(set.intersection(*function_sets)) if function_sets else 0,
            "function_union_count": len(set.union(*function_sets)) if function_sets else 0,
            "call_edge_intersection_count": len(set.intersection(*edge_sets)) if edge_sets else 0,
            "call_edge_union_count": len(set.union(*edge_sets)) if edge_sets else 0,
            "task_wall_ms": {"median": statistics.median(wall) if wall else None, "values": wall},
            "task_cpu_ms": {"median": statistics.median(cpu) if cpu else None, "values": cpu},
        }
    report = {
        "schema_version": 1, "run_id": raw.get("run_id"),
        "all_capture_integrity_checks_pass": all(checks.values()),
        "checks": checks, "task_oracle_outcomes_by_condition": outcomes,
        "task_oracle_pass_count": sum(sum(x) for x in outcomes.values()),
        "task_oracle_trial_count": sum(len(x) for x in outcomes.values()),
        "activation_by_condition": by_condition,
        "claim_boundary": "Two profiled fresh-process replicates per authored route. Function calls identify activated Python paths in this source snapshot; they do not establish causal necessity, Rust/native operation execution, natural prevalence, or profiler overhead.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_capture_integrity_checks_pass": report["all_capture_integrity_checks_pass"],
                      "checks": checks, "task_oracle_outcomes_by_condition": outcomes,
                      "analysis": str(OUT.relative_to(ROOT))}, indent=2))
    if not report["all_capture_integrity_checks_pass"]:
        raise SystemExit("capture integrity gate failed")


if __name__ == "__main__":
    main()
