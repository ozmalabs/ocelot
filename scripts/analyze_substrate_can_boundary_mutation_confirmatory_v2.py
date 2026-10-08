#!/usr/bin/env python3
"""Independent fixed-point/parity audit for CAN boundary confirmation v2."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_can_boundary_mutation_confirmatory_v2_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/can_boundary_mutation_confirmatory_v2_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_can_boundary_mutation_confirmatory_v2_analysis_20260925.json"
THRESHOLD = math.atanh(0.5)
SEEDS, SIZES = (20260925, 8675309, 104729), (8, 16, 32)
MUTATIONS = (
    "insert_boundary_edge", "delete_boundary_edge", "replace_boundary_weight",
    "external_field_change", "identity_field_change", "node_birth",
    "node_deletion", "mixed_weight_and_field_change",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def residuals(states, fields, active, directed_weights):
    weights = {(int(src), int(tgt)): float(weight)
               for src, tgt, weight in directed_weights}
    result = []
    for src, live in enumerate(active):
        if not live:
            result.append(False)
            continue
        h = float(fields[src]) + sum(w * float(states[tgt])
                                     for (source, tgt), w in weights.items()
                                     if source == src)
        scaled = 2.0 * h
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        result.append(expected != float(states[src]))
    return result


def main():
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    prov = raw["provenance"]
    cases = raw["cases"]
    expected = {(seed, n, mut) for seed in SEEDS for n in SIZES for mut in MUTATIONS}
    observed = {(c["fixture_seed"], c["n"], c["case"]) for c in cases}
    lock_checks = {
        "runner_hash_matches_lock": lock["hashes"]["runner"] == prov["runner_sha256"],
        "base_runner_hash_matches_lock": lock["hashes"]["base_mechanism_runner"] == prov["base_mechanism_runner_sha256"],
        "analyzer_hash_matches_lock": lock["hashes"]["analyzer"] == sha(Path(__file__)),
        "protocol_hash_matches_lock": lock["hashes"]["protocol"] == prov["protocol_sha256"],
        "seed_hash_matches_lock": lock["hashes"]["seed"] == prov["seed_manifest_sha256"],
        "extension_hash_matches_lock": lock["native_extension_sha256"] == prov["native_extension_sha256"],
        "engine_matches_current_source": prov["engine_provenance"]["source_match"] in ("own", "shared")
        and not prov["engine_provenance"]["stale_rust"],
        "exact_case_set": observed == expected and len(cases) == len(expected),
    }
    per_case, negative_checks = [], []
    for c in cases:
        active, fields = c["active_mask"], c["final_effective_fields"]
        weights = c["final_directed_weights"]
        ev, ref = c["event"]["states"], c["full_rescan"]["states"]
        er, rr = residuals(ev, fields, active, weights), residuals(ref, fields, active, weights)
        checks = {
            "equal_projection": ev == ref,
            "event_zero_residual": not any(er),
            "reference_zero_residual": not any(rr),
            "settled_under_cap": c["event"]["complete"] and c["full_rescan"]["complete"],
            "mutation_changes_projection": ev != c["pre_mutation_state"],
            "projection_lengths_valid": len(active) == len(fields) == len(ev) == len(ref),
            "event_residual_count_reconciles": sum(er) == c["event"]["residual_count"],
            "reference_residual_count_reconciles": sum(rr) == c["full_rescan"]["residual_count"],
        }
        neg = c["negative_control"]
        if neg is not None:
            nr = residuals(neg["states"], fields, active, weights)
            ncheck = neg["states"] != ref and any(nr) and sum(nr) == neg["residual_count"]
            checks["omitted_notification_detects_stale"] = bool(ncheck)
            negative_checks.append(bool(ncheck))
        per_case.append({"seed": c["fixture_seed"], "n": c["n"], "mutation": c["case"],
                         "checks": checks,
                         "event_progress": c["event"]["steps"],
                         "reference_progress": c["full_rescan"]["steps"]})
    checks = {
        **lock_checks,
        "all_case_checks_pass": all(all(c["checks"].values()) for c in per_case),
        "exact_negative_control_set": len(negative_checks) == 9,
        "all_negative_controls_pass": len(negative_checks) == 9 and all(negative_checks),
    }
    result = {
        "run_id": "can-boundary-mutation-confirmatory-v2-independent-analysis",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK), "analyzer_sha256": sha(Path(__file__)),
        "checks": checks, "pass": all(checks.values()), "case_count": len(per_case),
        "negative_control_count": len(negative_checks),
        "progress_counts_equal_all_cases": all(c["event_progress"] == c["reference_progress"]
                                                for c in per_case),
        "cases": per_case,
        "claim_boundary": [
            "Independent residuals recomputed from saved terminal fields, active mask, states and directed weights.",
            "The analysis validates the authored 3-state local equation, not an independent substrate implementation.",
            "Caller-supplied notifications and synthetic seeded path fixtures only; no natural locality or cost claim.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "pass": result["pass"],
                      "case_count": len(per_case), "negative_control_count": len(negative_checks),
                      "progress_counts_equal_all_cases": result["progress_counts_equal_all_cases"],
                      "checks": checks}, indent=2))
    if not result["pass"]:
        raise SystemExit("independent confirmation audit failed")


if __name__ == "__main__":
    main()
