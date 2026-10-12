#!/usr/bin/env python3
"""Independent checks and phase summaries for the predecessor CoW capture."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_cow_residual_v1.py"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_cow_residual_v1_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_cow_residual_v1_analysis_20261003.json"
CASES = ("retained_interface", "wrong_speaker", "intervening_topic_event",
         "topicless_chain", "missing_predecessor_edge", "omitted_target_interface")
ARMS = ("monolithic_primary", "full_copy_monolithic", "shared_pages_monolithic",
        "full_copy_scoped", "shared_pages_scoped")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(CAPTURE.read_text())
    spec = importlib.util.spec_from_file_location("predecessor_cow_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    current_lock = module.source_lock()
    runs = raw.get("runs", [])
    rows = [cell for run in runs for cell in run.get("rows", [])]
    expected = {"retained_interface": "candidate_grounded", "topicless_chain": "candidate_grounded"}
    expected.update({case: "unresolved" for case in CASES if case not in expected})
    checks = {
        "schema": raw.get("schema") == "ThoughtexperimentPredecessorCowResidualV1",
        "complete_source_lock_current": current_lock == raw.get("locked_inputs") == raw.get("post_run_inputs"),
        "runner_source_lock_matches": sha(RUNNER) == raw.get("locked_inputs", {}).get(
            "evaluation/substrate_capability/thoughtexperiment_predecessor_cow_residual_v1.py"),
        "complete_case_matrix": len(rows) == len(CASES) * 3 and {r.get("case") for r in rows} == set(CASES),
        "all_arms_present": all(set(r.get("arms", {})) == set(ARMS) for r in rows),
        "all_arms_same_canonical_graph": all(r.get("all_graph_digests_equal") for r in rows),
        "all_arms_same_grounding_evidence": all(r.get("all_grounding_equal") for r in rows),
        "branch_primary_unchanged_before_return": all(r.get("all_isolated_before_return") for r in rows),
        "returned_graph_matches_branch": all(r.get("all_branch_returns_match") for r in rows),
        "rule_store_unchanged": all(r.get("all_rules_preserved") for r in rows),
        "semantic_outcomes_match_controls": all(
            all(a["correction_status"] == expected[r["case"]] and
                (a["correction_evidence"] == "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"
                 if expected[r["case"]] == "candidate_grounded" else a["correction_evidence"] == "")
                for a in r["arms"].values()) for r in rows),
        "all_residual_returns_revision_checked": all(
            a["residual_applied"] is True and
            a["residual_application_revision"] == a["primary_revision_before_return"] and
            a["returned_branch_parity"] is True
            for r in rows for k, a in r["arms"].items() if k != "monolithic_primary"),
        "runner_gates_pass": all(raw.get("checks", {}).values()),
    }
    summary = {}
    for arm in ARMS:
        times = [r["arms"][arm]["timing_ns"] for r in rows]
        summary[arm] = {
            "cases": len(times),
            "median_closure_us": statistics.median(x["closure"] for x in times) / 1000,
            "median_branch_total_us": statistics.median(x["branch_total"] for x in times) / 1000,
            "median_fork_us": statistics.median(x["fork"] for x in times) / 1000,
            "median_residual_extract_us": statistics.median(x["residual_extract"] for x in times) / 1000,
            "median_residual_apply_us": statistics.median(x["residual_apply"] for x in times) / 1000,
            "median_work_steps": statistics.median(r["arms"][arm]["closure_work_steps"] for r in rows),
        }
        summary[arm]["by_case"] = {}
        for case in CASES:
            group = [r["arms"][arm] for r in rows if r["case"] == case]
            summary[arm]["by_case"][case] = {
                "median_closure_us": statistics.median(x["timing_ns"]["closure"] for x in group) / 1000,
                "median_branch_total_us": statistics.median(x["timing_ns"]["branch_total"] for x in group) / 1000,
                "median_work_steps": statistics.median(x["closure_work_steps"] for x in group),
                "median_residual_nodes_changed": statistics.median(
                    (x.get("residual_counts") or {}).get("nodes_changed", 0) for x in group),
            }
    output = {"schema": "ThoughtexperimentPredecessorCowResidualAnalysisV1",
        "capture_sha256": sha(CAPTURE), "checks": checks,
        "cell_count": len(rows), "summary_by_arm": summary}
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(), "checks": checks,
        "summary_by_arm": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent predecessor CoW analysis failed")


if __name__ == "__main__":
    main()
