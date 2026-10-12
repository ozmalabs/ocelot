#!/usr/bin/env python3
"""Independent outcome checks for strict adoption-surface capture."""
import hashlib
import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_adoption_surface_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_adoption_surface_v1_analysis_20261002.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lock = json.loads(LOCK.read_text()); capture = json.loads(RAW.read_text())
    spec = importlib.util.spec_from_file_location(
        "adoption_surface_runner", ROOT / "evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1.py")
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    current_lock = runner.frozen_payload()
    workers = capture["workers"]
    checks = []
    checks.append(("capture_lock_matches", capture["lock"] == lock))
    checks.append(("current_lock_matches", current_lock == lock))
    checks.append(("source_stable", capture["source_stable"] and
        capture["post_lock"] == lock and
        all(row["active_after"] == lock["active"] for row in workers)))
    cases = ("valid_signature", "tampered_signature", "direct_legacy_call", "curriculum_legacy_call")
    checks.append(("processes_are_fresh", len({row["pid"] for row in workers}) == 12))
    checks.append(("complete_factorial", len(workers) == 12 and
        {(row["case"], row["repetition"]) for row in workers} ==
        {(case, rep) for case in cases
         for rep in (1, 2, 3)}))
    valid = [row for row in workers if row["case"] == "valid_signature"]
    tampered = [row for row in workers if row["case"] == "tampered_signature"]
    checks.append(("valid_evidence_adopted", len(valid) == 3 and all(
        row["receipt_status"] == "accepted" and row["shape_delta"] == 1 and
        "learned the shape" in row["reply"] for row in valid)))
    checks.append(("tampered_signature_refused_after_accepted_receipt", len(tampered) == 3 and all(
        row["receipt_status"] == "accepted" and row["shape_delta"] == 0 and not row["adopted_code_shape_ids"] and
        "could not take it as a lesson" in row["reply"] for row in tampered)))
    direct = [row for row in workers if row["case"] == "direct_legacy_call"]
    checks.append(("direct_legacy_function_respects_strict_policy", len(direct) == 3 and all(
        row["shape_delta"] == 0 and row["outcomes"] == [{
            "ok": False, "reason": "provider-authenticated adequacy evidence required"}]
        for row in direct)))
    curriculum = [row for row in workers if row["case"] == "curriculum_legacy_call"]
    checks.append(("published_curriculum_route_respects_strict_policy", len(curriculum) == 3 and all(
        row["shape_delta"] == 0 and row["outcomes"] and all(
            not outcome["ok"] and outcome["reason"] ==
            "provider-authenticated adequacy evidence required"
            for outcome in row["outcomes"])
        for row in curriculum)))
    result = {"schema": "SubstrateAdequacyAdoptionSurfaceV1Analysis",
        "checks": [{"name": name, "pass": passed} for name, passed in checks],
        "passed": sum(ok for _, ok in checks), "total": len(checks),
        "valid_median_elapsed_ms": sorted(row["elapsed_ns"] for row in valid)[1] / 1e6,
        "tampered_median_elapsed_ms": sorted(row["elapsed_ns"] for row in tampered)[1] / 1e6,
        "limits": ["one authored scalar function family", "one host",
                   "test-only process-local key", "does not establish signer truthfulness",
                   "direct calls through the audited code_write_growth and code_curriculum routes refuse under strict adapter policy",
                   "does not establish global policy for non-strict agents or direct teach() calls"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(ok for _, ok in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
