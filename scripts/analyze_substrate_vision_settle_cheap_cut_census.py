#!/usr/bin/env python3
"""Independent arithmetic and source-signature check for the vision census."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_vision_settle_cheap_cut_census_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/vision_settle_cheap_cut_census_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_vision_settle_cheap_cut_census_analysis_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    p, sig = raw["provenance"], raw["source_signature"]
    expected = []
    for n in (16, 64, 256, 1024):
        for k in (4, 16, 64):
            if n % k == 0:
                expected.append({
                    "units": n, "frame_units": k, "frame_count": n // k,
                    "global_input_incidences": n * n,
                    "cross_frame_input_incidences": n * (n - k),
                    "cross_frame_incidence_share": (n - k) / n,
                    "external_state_per_frame": n - k,
                    "complete_dependency_graph_treewidth": n - 1,
                })
    checks = {
        "runner_hash_matches_lock": lock["hashes"]["runner"] == p["runner_sha256"],
        "protocol_hash_matches_lock": lock["hashes"]["protocol"] == p["protocol_sha256"],
        "seed_hash_matches_lock": lock["hashes"]["seed"] == p["seed_sha256"],
        "substrate_source_hash_matches_lock": lock["hashes"]["substrate"] == p["substrate_rs_sha256"],
        "rewrite_source_hash_matches_lock": lock["hashes"]["rewrite"] == p["rewrite_rs_sha256"],
        "required_rule_signature_present": all(sig[k] for k in (
            "settle_batch", "commit_batch", "one_sunit_membership_match", "settle_writes_act_next",
            "commit_copies_act_next_to_act", "local_neighbor_act_fold", "global_all_sunit_act_fold")),
        "exact_case_matrix_and_arithmetic": raw["cases"] == expected,
        "global_complete_graph_claim_reconciles": "K_N" in raw["inference"] and
            all(c["complete_dependency_graph_treewidth"] == c["units"] - 1 for c in raw["cases"]),
        "scoped_api_is_microtheory_specific": raw["scope_api_source"]["run_rules_scoped_argument"] == "scope_mt: Option<NodeID>"
            and "has_concept" in raw["scope_api_source"]["owned_nodes"]
            and raw["scope_api_source"]["arbitrary_sunit_frame_api_found"] is False,
    }
    result = {
        "run_id": "vision-settle-cheap-cut-static-census-independent-analysis",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "analyzer_sha256": sha(Path(__file__)), "checks": checks,
        "pass": all(checks.values()), "case_count": len(expected),
        "claim_boundary": [
            "This verifies the seed's declared source dependency shape and exact symbolic cut arithmetic, not runtime execution cost.",
            "The global term may also couple distinct SUnit sheets sharing one substrate; that runtime behavior was not tested.",
            "The result refutes cheap-cut factorization for this specific rule signature only.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "pass": result["pass"],
                      "case_count": len(expected), "checks": checks}, indent=2))
    if not result["pass"]:
        raise SystemExit("independent vision dependency census audit failed")


if __name__ == "__main__":
    main()
