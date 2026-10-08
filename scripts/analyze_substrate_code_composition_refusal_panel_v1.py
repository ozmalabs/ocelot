#!/usr/bin/env python3
"""Independent scorer for code-composition refusal panel v1."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/code_composition_refusal_panel_v1_20260928.json"
OUT = ROOT / "evaluation/reports/code_composition_refusal_panel_v1_analysis_20260928.json"
FRAME = ROOT / "evaluation/substrate_capability/code_composition_refusal_panel_v1_frame_20260928.json"
EXPECTED = {
    "unique_constant_positive": {"kind": "value", "type": "bool", "value": True},
    "pure_helper_positive": {"kind": "value", "type": "bool", "value": True},
    "duplicate_global": {"kind": "error", "type": "EmitError"},
    "dynamic_global": {"kind": "error", "type": "EmitError"},
    "wildcard_import": {"kind": "error", "type": "EmitError"},
    "recursive_helper": {"kind": "error", "type": "EmitError"},
    "depth_overflow": {"kind": "error", "type": "EmitError"},
    "keyword_helper_argument": {"kind": "error", "type": "EmitError"},
    "effectful_helper_refusal": {"kind": "error", "type": "EmitError"},
    "bitwise_bool_refusal": {"kind": "error", "type": "EmitError"},
    "bitwise_string_refusal": {"kind": "error", "type": "EmitError"},
    "bitwise_i64_overflow_refusal": {"kind": "error", "type": "EmitError"},
}
SENTINEL = Path("/tmp/ocelot_code_composition_refusal_sentinel_20260928")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    frame = json.loads(FRAME.read_text())
    raw = json.loads(RAW.read_text())
    manifest = raw.get("run_manifest", {})
    cap = manifest.get("stdout_stderr_capture") or {}
    log_path = ROOT / cap.get("path", "__missing__")
    log = log_path.read_bytes() if log_path.is_file() else b""
    frame_ids = [c["id"] for c in frame.get("cases", [])]
    runs = raw.get("runs", [])
    outcome_map = []
    for run in runs:
        by_id = {x.get("id"): x for x in run.get("outcomes", [])}
        outcome_map.append(by_id)
    checks = {
        "frozen_frame_case_ids": frame_ids == list(EXPECTED),
        "two_fresh_workers": len(runs) == 2 and len({r.get("pid") for r in runs}) == 2,
        "stable_parent_and_worker_source_locks": raw.get("post_run_inputs") == raw.get("locked_inputs") and all(r.get("source_stable") and r.get("locked_inputs_before") == raw.get("locked_inputs") == r.get("locked_inputs_after") for r in runs),
        "complete_exact_schedules": len(outcome_map) == 2 and all(list(x) == frame_ids for x in outcome_map),
        "manifest_console_capture_valid": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and bool(log) and len(log) == cap.get("bytes") and hashlib.sha256(log).hexdigest() == cap.get("sha256") and all(f"completed=worker{i} rc=0".encode() in log for i in (0, 1)),
        "workers_succeeded": all(r.get("worker_returncode") == 0 and r.get("boot", {}).get("loaded", 0) > 0 for r in runs),
        "all_declared_outcomes_match": all(outcome_map and all(
            ("error" if o.get("error_type") else "value") == EXPECTED[cid]["kind"]
            and (o.get("error_type") == EXPECTED[cid]["type"] if EXPECTED[cid]["kind"] == "error"
                 else o.get("value") == {"type": EXPECTED[cid]["type"], "value": EXPECTED[cid]["value"]})
            for cid, o in mapping.items() for _ in [0]) for mapping in outcome_map),
        "no_effect_sentinel_created": all(not o.get("sentinel_created") for mapping in outcome_map for o in mapping.values()) and not SENTINEL.exists(),
        "worker_outcome_parity": len(outcome_map) == 2 and all(
            (outcome_map[0][cid].get("value"), outcome_map[0][cid].get("error_type"), outcome_map[0][cid].get("sentinel_created"))
            == (outcome_map[1][cid].get("value"), outcome_map[1][cid].get("error_type"), outcome_map[1][cid].get("sentinel_created"))
            for cid in frame_ids),
        "integrity_gate_passed": raw.get("integrity_pass") and all(raw.get("integrity_checks", {}).values()),
    }
    result = {"schema": "code-composition-refusal-analysis-v1", "checks": checks,
              "pass": all(checks.values()), "case_count_per_worker": len(frame_ids),
              "workers": [{"replicate": r.get("replicate"), "pid": r.get("pid"),
                           "boot_loaded": r.get("boot", {}).get("loaded"),
                           "boot_total": r.get("boot", {}).get("total"),
                           "boot_failures": len(r.get("boot", {}).get("failed", [])),
                           "peak_rss_bytes": r.get("runtime", {}).get("peak_rss_bytes"),
                           "outcomes": r.get("outcomes", [])} for r in runs],
              "claim_boundary": raw.get("claim_boundary")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(), "pass": result["pass"], "checks": checks}, indent=2, sort_keys=True))
    if not result["pass"]:
        raise SystemExit("refusal panel analysis failed")


if __name__ == "__main__":
    main()
