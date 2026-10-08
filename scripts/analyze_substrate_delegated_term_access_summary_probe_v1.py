#!/usr/bin/env python3
"""Independent checks for the delegated Term static access-summary probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_delegated_term_access_summary_probe_v1_20260926.json"
EXPECTED = {
    "motor_compose", "future_manifold_projection", "future_manifold_selection",
    "transform_decode", "dim_infer", "gen_infer", "net_forward", "enigma_crib",
    "enigma_bombe", "enigma_bombe_witness", "track_identity_correspondence",
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    raw = json.loads(RAW.read_text())
    names = {row["case"] for row in raw["cases"]}
    checks = {
        "exact_expected_family_set": names == EXPECTED,
        "all_cases_report_reads_any": len(raw["cases"]) == 11 and all(row["reads_any"] for row in raw["cases"]),
        "runner_checks_pass": all(raw["checks"].values()),
        "source_hash_current": raw["provenance"]["source_sha256"] == sha(ROOT / "runners/dsl/src/rewrite.rs"),
        "runner_hash_current": raw["provenance"]["runner_sha256"] == sha(ROOT / "scripts/substrate_delegated_term_access_summary_probe_v1.py"),
        "native_hash_current": raw["provenance"]["native_extension_sha256"] == sha(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"),
    }
    result = {"source": str(RAW.relative_to(ROOT)), "claim_boundary": raw["claim_boundary"], "checks": checks, "all_checks_pass": all(checks.values())}
    output = ROOT / "evaluation/reports/substrate_delegated_term_access_summary_probe_v1_analysis_20260926.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("delegated Term summary analysis failed")

if __name__ == "__main__":
    main()
