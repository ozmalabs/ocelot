#!/usr/bin/env python3
"""Compare source-matched lifecycle helper work for live describe/self-report routes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE_RAW = ROOT / "evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_5_20260926.json"
SCENE_LOCK = ROOT / "evaluation/substrate_capability/live_describe_scene_threaded_interleaving_v1_5_lock_20260926.json"
SCENE_ANALYSIS = ROOT / "evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_5_analysis_20260926.json"
SELF_RAW = ROOT / "evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_7_20260926.json"
SELF_LOCK = ROOT / "evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_7_lock_20260926.json"
SELF_ANALYSIS = ROOT / "evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_7_analysis_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_live_action_route_work_comparison_v1_20260926.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


scene_raw, self_raw = json.loads(SCENE_RAW.read_text()), json.loads(SELF_RAW.read_text())
scene_lock = json.loads(SCENE_LOCK.read_text())["locked_inputs"]
self_lock = json.loads(SELF_LOCK.read_text())["locked_inputs"]
scene_analysis, self_analysis = json.loads(SCENE_ANALYSIS.read_text()), json.loads(SELF_ANALYSIS.read_text())
checks = {
    "scene_analysis_all_checks_pass": all(scene_analysis["checks"].values()),
    "self_report_analysis_all_checks_pass": all(self_analysis["checks"].values()),
    "same_full_source_closure": scene_lock["source_closure_sha256"] == self_lock["source_closure_sha256"],
    "same_native_extension": scene_lock["native_extension_sha256"] == self_lock["native_extension_sha256"],
    "same_native_build_manifest": scene_lock["native_build_manifest_sha256"] == self_lock["native_build_manifest_sha256"],
    "same_python_platform": scene_raw["environment"] == self_raw["environment"],
    "same_two_request_six_helper_schedule": all(len(r["producer_work"]) == 6 for r in scene_raw["runs"])
        and all(sum(len(t["producer_work"]) for t in r["turns"]) == 6 for r in self_raw["runs"]),
    "three_worker_replicates_each": len(scene_raw["runs"]) == len(self_raw["runs"]) == 3,
}

scene_kinds = scene_analysis["producer_work_summary"]
self_kinds = self_analysis["production_helper_work_summary"]
routes = {}
for route, kind_data in (("describe_scene", scene_kinds), ("self_report", self_kinds)):
    routes[route] = {
        "requests_per_run": 2,
        "helper_calls_per_run": 6,
        "candidate_pairs_per_run": sum(x["candidate_pairs_per_run"] for x in kind_data.values()),
        "term_evaluations_per_run": sum(x["term_evaluations_per_run"] for x in kind_data.values()),
        "by_event_kind": kind_data,
    }
candidate_ratio = routes["describe_scene"]["candidate_pairs_per_run"] / routes["self_report"]["candidate_pairs_per_run"]
term_ratio = routes["describe_scene"]["term_evaluations_per_run"] / routes["self_report"]["term_evaluations_per_run"]
checks["source_match_claim_is_not_empty"] = bool(scene_lock["source_closure_sha256"])
result = {
    "schema": "substrate_live_action_route_work_comparison_v1",
    "input_sha256": {"scene_raw": sha(SCENE_RAW), "scene_lock": sha(SCENE_LOCK),
                     "scene_analysis": sha(SCENE_ANALYSIS), "self_report_raw": sha(SELF_RAW),
                     "self_report_lock": sha(SELF_LOCK), "self_report_analysis": sha(SELF_ANALYSIS)},
    "checks": checks, "check_count": len(checks), "all_checks_pass": all(checks.values()),
    "matched_execution_context": {"source_closure_files": len(scene_lock["source_closure_sha256"]),
                                  "native_extension_sha256": scene_lock["native_extension_sha256"],
                                  "native_build_manifest_sha256": scene_lock["native_build_manifest_sha256"],
                                  "environment": scene_raw["environment"]},
    "routes": routes,
    "descriptive_ratios": {"describe_scene_over_self_report_candidate_pairs": candidate_ratio,
                           "describe_scene_over_self_report_term_evaluations": term_ratio},
    "claim_boundary": "Retrospective same-source comparison of two different task contents and schedules. Route, scene/organization content, evolving graph state, and threaded-vs-sequential schedule are confounded. The ratios describe these two captured fixtures; they are not causal route effects or natural workload averages.",
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"all_checks_pass": result["all_checks_pass"], "check_count": len(checks),
                  "descriptive_ratios": result["descriptive_ratios"], "output": str(OUT)}, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
