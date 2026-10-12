#!/usr/bin/env python3
"""Independent arithmetic/provenance audit for the multi-sheet probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_vision_settle_multi_sheet_probe_v1_2_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/vision_settle_multi_sheet_probe_v1_2_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_vision_settle_multi_sheet_probe_v1_2_analysis_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    p = raw["provenance"]
    arms = raw["arms"]
    expected = []
    for b in (0.0, 1.0):
        # Two A and two B units. Both A units have one A neighbor, aff=0.
        mean_sheet = (2.0 + 2.0 * b) / 4.0
        expected.append(max(1.0 - mean_sheet, 0.0))
    checks = {
        "runner_hash_matches_lock": lock["hashes"]["runner"] == p["runner_sha256"],
        "analyzer_hash_matches_lock": lock["hashes"]["analyzer"] == sha(Path(__file__)),
        "protocol_hash_matches_lock": lock["hashes"]["protocol"] == p["protocol_sha256"],
        "seed_hash_matches_lock": lock["hashes"]["seed"] == p["seed_sha256"],
        "extension_hash_matches_lock": lock["native_extension_sha256"] == p["native_extension_sha256"],
        "engine_matches_current_source": p["engine_provenance"]["source_match"] in ("own", "shared")
        and not p["engine_provenance"]["stale_rust"],
        "two_registered_arms": [a["b_initial_act"] for a in arms] == [0.0, 1.0] and len(arms) == 2,
        "rules_progressed_under_cap": all(a["progress"] > 0 and a["complete"] for a in arms),
        "A_matches_independent_global_fold": all(
            all(abs(x - expect) <= 1e-7 for x in arm["a_act_next"])
            for arm, expect in zip(arms, expected)),
        "B_intervention_changes_A": arms[0]["a_act_next"] != arms[1]["a_act_next"],
    }
    result = {
        "run_id": "vision-settle-multi-sheet-coupling-independent-analysis",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK), "analyzer_sha256": sha(Path(__file__)),
        "independently_expected_a_act_next": expected,
        "checks": checks, "pass": all(checks.values()),
        "claim_boundary": [
            "This verifies two tiny world-rooted pairs under the single native st_settle rule.",
            "It does not test full cortical-sheet construction, st_commit, multiple SettleParams nodes, or performance.",
            "Observed cross-world coupling occurs because the rule reads NodesOfType(SUnit) globally in this substrate graph.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "pass": result["pass"], "checks": checks}, indent=2))
    if not result["pass"]:
        raise SystemExit("independent multi-sheet probe audit failed")


if __name__ == "__main__":
    main()
