#!/usr/bin/env python3
"""Independent checks for access-trace comparison-read and tool-dispatch v2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evaluation/reports/substrate_access_trace_attr_compare_tool_v2_20260926.json"
RAW = ROOT / "evaluation/reports/substrate_access_trace_attr_compare_tool_v2_workers_raw_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_access_trace_attr_compare_tool_v2_analysis_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/access_trace_attr_compare_tool_v2_lock_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    report, raw, lock = json.loads(REPORT.read_text()), json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    runs = raw["runs"]
    checks: dict[str, bool] = {
        "three_independent_workers": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
        "raw_lock_matches_lock_file": raw["locked_inputs"] == lock["locked_inputs"] == raw["post_run_inputs"],
        "runner_and_analyzer_capture_agree_on_lock": report["locked_inputs"] == raw["locked_inputs"],
    }
    semantic_signatures = []
    cell_count = 0
    for run in runs:
        checks[f"r{run['replicate']}_worker_source_stable"] = run["before"] == raw["locked_inputs"] == run["after"]
        signature = []
        for label, expected_final in (("changed", 1), ("unchanged", 1)):
            pair = run["attribute_cases"][label]
            plain, traced = pair["plain"], pair["traced"]
            expected_compare = sum(row[5] for row in traced["events"]
                                   if row[1] == "effect_attr_compare_read")
            expected_write = sum(row[5] for row in traced["events"]
                                 if row[1] == "effect_attr_write")
            checks[f"r{run['replicate']}_{label}_expected_value"] = traced["final"] == expected_final
            checks[f"r{run['replicate']}_{label}_plain_traced_semantics_equal"] = (
                (plain["final"], plain["progress_steps"], plain["status"])
                == (traced["final"], traced["progress_steps"], traced["status"]))
            checks[f"r{run['replicate']}_{label}_actual_compare_rows_match_summary"] = (
                expected_compare == traced["compare_read_events"] == 1)
            checks[f"r{run['replicate']}_{label}_actual_write_branch"] = (
                expected_write == traced["write_events"] == (1 if label == "changed" else 0))
            checks[f"r{run['replicate']}_{label}_trace_enabled_only_when_requested"] = (
                not plain["events"] and plain["event_count"] == 0 and traced["dropped"] == 0)
            signature.append((label, plain["final"], plain["progress_steps"], plain["status"],
                              traced["events"], traced["dropped"]))
            cell_count += 1
        tool = run["tool_case"]
        plain, traced = tool["plain"], tool["traced"]
        actual_dispatch = sum(row[5] for row in traced["events"] if row[1] == "term_tool_dispatch")
        named_dispatch = sum(row[5] for row in traced["events"]
                             if row[1] == "term_tool_dispatch" and row[3] == "access_trace_tool_probe")
        checks[f"r{run['replicate']}_tool_callback_independently_observed"] = traced["handler_calls"] == 1
        checks[f"r{run['replicate']}_tool_event_matches_callback"] = (
            actual_dispatch == named_dispatch == traced["dispatch_events"] == traced["handler_calls"])
        checks[f"r{run['replicate']}_tool_plain_traced_semantics_equal"] = (
            (plain["handler_calls"], plain["progress_steps"], plain["status"])
            == (traced["handler_calls"], traced["progress_steps"], traced["status"]))
        checks[f"r{run['replicate']}_tool_trace_enabled_only_when_requested"] = (
            not plain["events"] and plain["event_count"] == 0 and traced["dropped"] == 0)
        signature.append(("tool", traced["handler_calls"], traced["dispatch_events"], traced["events"]))
        semantic_signatures.append(json.dumps(signature, sort_keys=True, separators=(",", ":")))
    checks["all_semantic_and_event_signatures_repeat"] = len(set(semantic_signatures)) == 1
    manifest = report.get("run_manifest", {})
    checks["manifest_succeeded_and_engine_current"] = (
        manifest.get("manifest_schema") == "substrate-run-manifest-v1"
        and manifest.get("exit_status") == 0
        and not manifest.get("engine", {}).get("build_is_stale", True)
        and manifest.get("engine", {}).get("native_extension_sha256")
        == raw["locked_inputs"]["native_extension_sha256"])
    log = manifest.get("stdout_stderr_capture", {})
    log_path = ROOT / log.get("path", "")
    checks["captured_log_integrity"] = (
        log_path.is_file() and sha(log_path) == log.get("sha256")
        and log_path.stat().st_size == log.get("bytes"))
    summary = {
        "workers": len(runs), "paired_fixture_cells_per_worker": 3,
        "event_kind_counts_per_worker": {
            "effect_attr_compare_read_changed": 1,
            "effect_attr_compare_read_unchanged": 1,
            "effect_attr_write_changed": 1,
            "effect_attr_write_unchanged": 0,
            "term_tool_dispatch_named": 1,
        },
        "claim_boundary": "These controlled cases establish trace visibility for one conditional attribute old-value read and one attempted UseTool dispatch per matching rule evaluation. They do not trace callback internals, scheduler/post-rule queue work, or all graph access; they do not establish locality or overhead.",
    }
    payload = {"schema_version": 1, "source_report": str(REPORT.relative_to(ROOT)),
               "raw_capture_sha256": sha(RAW), "analysis_script_sha256": sha(Path(__file__).resolve()),
               "checks": checks, "all_checks_pass": all(checks.values()), "summary": summary}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "all_checks_pass": payload["all_checks_pass"],
                      "checks_passed": sum(checks.values()), "checks_total": len(checks)}, indent=2))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
