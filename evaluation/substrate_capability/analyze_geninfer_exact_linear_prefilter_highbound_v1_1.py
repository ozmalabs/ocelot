#!/usr/bin/env python3
"""Admission checks for the isolated v1.1 high-bound smoke pair."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_highbound_v1_1_20261006.json"
OUT = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_highbound_v1_1_analysis_20261006.json"


def main() -> int:
    raw = json.loads(RAW.read_text())
    by_audit = {worker["audit"]: worker for worker in raw["workers"]}
    if set(by_audit) != {False, True}:
        raise SystemExit("missing audit-on/off worker")
    checks = {}
    checks["both_workers_complete"] = all(by_audit[a]["exit_code"] == 0 and by_audit[a]["worker"] for a in (False, True))
    checks["source_and_binary_stable"] = len(raw["sources_sha256"]) >= 10 and all(len(v) == 64 for v in raw["sources_sha256"].values()) and len(raw["native_binary"]["sha256"]) == 64
    checks["both_finish_under_300s"] = all(by_audit[a]["elapsed_ns"] < raw["timeout_seconds_per_worker"] * 1e9 for a in (False, True))
    summaries = {}
    for audit, item in by_audit.items():
        row = item["worker"]
        if row is None:
            summaries[str(audit)] = {"complete": False}
            continue
        training = row["training"]
        counters = training["counters"]
        summaries[str(audit)] = {
            "worker_elapsed_ns": item["elapsed_ns"],
            "closure_ns": training["closure_ns"],
            "training_status": training["status"],
            "training_generator_payloads": training["generator_payloads"],
            "heldout_generator_payloads": row["heldout"]["generator_payloads"],
            "prefilter_attempts": counters.get("gen_infer_prefilter_attempts"),
            "prefilter_solved": counters.get("gen_infer_prefilter_solved"),
            "prefilter_proven_no_fit": counters.get("gen_infer_prefilter_proven_no_fit"),
            "prefilter_fallback": counters.get("gen_infer_prefilter_fallback"),
            "matrix_attempts": counters.get("gen_infer_matrix_attempts"),
            "quadratic_attempts": counters.get("gen_infer_quadratic_attempts"),
            "quadratic_survivors": counters.get("gen_infer_quadratic_survivors"),
        }
    audited = summaries["True"]
    checks["audit_confirms_no_fit_on_each_geninfer_call"] = audited.get("prefilter_attempts") == audited.get("prefilter_proven_no_fit") == audited.get("quadratic_attempts") == 2 and audited.get("prefilter_solved") == audited.get("prefilter_fallback") == 0
    checks["no_matrix_enumeration"] = audited.get("matrix_attempts") == 0
    checks["quadratic_learner_refuses"] = audited.get("quadratic_survivors") == 0
    checks["no_generator_minted_or_transferred"] = not audited.get("training_generator_payloads") and not audited.get("heldout_generator_payloads")
    report = {
        "schema": "GenInferExactLinearPrefilterHighBoundV1_1Analysis",
        "status": "pass" if all(checks.values()) else "fail",
        "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "checks": checks,
        "workers": summaries,
        "interpretation": "The updated relation-count proof handles this one high-bound cubic control. It does not establish general tractability or admission across the v1 main panel.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "checks": checks}, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
