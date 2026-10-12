#!/usr/bin/env python3
"""Independent outcome checks for adapter-path v1 capture."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_adapter_path_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_adapter_path_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_adapter_path_v1_analysis_20261002.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lock = json.loads(LOCK.read_text()); capture = json.loads(RAW.read_text())
    workers = capture["workers"]
    checks = []
    checks.append(("capture_lock_matches", capture["lock"] == lock))
    checks.append(("source_stable", capture["source_stable"] and capture["post_lock"] == lock["active"]))
    checks.append(("processes_are_fresh", len({row["pid"] for row in workers}) == 6))
    checks.append(("complete_factorial", len(workers) == 6 and
        {(row["case"], row["repetition"]) for row in workers} ==
        {(case, rep) for case in ("valid_signature", "tampered_signature")
         for rep in (1, 2, 3)}))
    valid = [row for row in workers if row["case"] == "valid_signature"]
    tampered = [row for row in workers if row["case"] == "tampered_signature"]
    checks.append(("valid_evidence_adopted", len(valid) == 3 and all(
        row["receipt_status"] == "accepted" and row["shape_delta"] > 0 and
        "learned the shape" in row["reply"] for row in valid)))
    checks.append(("tampered_signature_refused_after_accepted_receipt", len(tampered) == 3 and all(
        row["receipt_status"] == "accepted" and row["shape_delta"] == 0 and
        "could not take it as a lesson" in row["reply"] for row in tampered)))
    result = {"schema": "SubstrateAdequacyAdapterPathV1Analysis",
        "checks": [{"name": name, "pass": passed} for name, passed in checks],
        "passed": sum(ok for _, ok in checks), "total": len(checks),
        "valid_median_elapsed_ms": sorted(row["elapsed_ns"] for row in valid)[1] / 1e6,
        "tampered_median_elapsed_ms": sorted(row["elapsed_ns"] for row in tampered)[1] / 1e6,
        "limits": ["one authored scalar function family", "one host",
                   "test-only process-local key", "does not establish signer truthfulness",
                   "does not audit direct or alternate legacy teaching entrypoints"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(ok for _, ok in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
