#!/usr/bin/env python3
"""Independent outcome checks for the adequacy receipt adoption panel."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/substrate_adequacy_receipt_adoption_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_receipt_adoption_v1_analysis_20261002.json"


def analyze() -> dict:
    capture = json.loads(RAW.read_text())
    checks = []
    expected = {"rejected": "rejected", "ambiguous": "ambiguous",
                "incomplete": "incomplete", "invalid": "invalid"}
    for worker in capture["workers"]:
        cells = worker["cases"]
        for name, status in expected.items():
            cell = cells[name]
            checks.append({"rep": worker["repetition"], "case": name,
                           "pass": cell["receipt_status"] == status and cell["teach_ok"] is False
                           and cell["candidate_id_matches"] is True
                           and cell["no_adoption_state_preserved"] is True})
        cell = cells["missing"]
        checks.append({"rep": worker["repetition"], "case": "missing",
                       "pass": cell["receipt_status"] is None and cell["teach_ok"] is False
                       and cell["no_adoption_state_preserved"] is True})
        cell = cells["accepted_adoption"]
        checks.append({"rep": worker["repetition"], "case": "accepted_adoption",
                       "pass": cell["receipt_status"] == "accepted" and cell["teach_ok"] is True
                       and cell["candidate_id_matches"] is True and cell["epoch_increment"] == 1
                       and len(cell["state_after"]["shapes"]) == len(cell["state_before"]["shapes"]) + 1})
    result = {"schema": "SubstrateAdequacyReceiptAdoptionV1Analysis",
              "capture_pass": capture["passes"], "checks": checks,
              "passed": all(row["pass"] for row in checks),
              "repetitions": len(capture["workers"]),
              "median_boot_ms": sorted(w["boot_ns"] / 1e6 for w in capture["workers"])[len(capture["workers"])//2],
              "median_refusal_ms": {case: sorted(w["cases"][case]["wall_ns"] / 1e6
                                                  for w in capture["workers"])[len(capture["workers"])//2]
                                    for case in [*expected, "missing"]},
              "median_accepted_adoption_ms": sorted(w["cases"]["accepted_adoption"]["wall_ns"] / 1e6
                                                     for w in capture["workers"])[len(capture["workers"])//2]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    result = analyze()
    print(json.dumps({"passed": result["passed"], "checks": len(result["checks"]),
                      "analysis": str(OUT)}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
