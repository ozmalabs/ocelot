#!/usr/bin/env python3
"""Independent residual and provenance audit for mutation-matrix v1.1."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_can_boundary_mutation_matrix_v1_1_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/can_boundary_mutation_matrix_v1_1_discovery_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_can_boundary_mutation_matrix_v1_1_analysis_20260925.json"
THRESHOLD = math.atanh(0.5)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def residuals(states, fields, active, directed_weights):
    weights = {(int(src), int(tgt)): float(weight)
               for src, tgt, weight in directed_weights}
    out = []
    for source, live in enumerate(active):
        if not live:
            out.append(False)
            continue
        field = float(fields[source])
        h = field + sum(weight * float(states[target])
                        for (src, target), weight in weights.items() if src == source)
        scaled = 2.0 * h
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        out.append(expected != float(states[source]))
    return out


def main():
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    expected = {(n, mutation) for n in (8, 16, 32) for mutation in (
        "insert_boundary_edge", "delete_boundary_edge", "replace_boundary_weight",
        "external_field_change", "identity_field_change", "node_birth",
        "node_deletion", "mixed_weight_and_field_change")}
    cases = raw["cases"]
    observed = {(case["n"], case["case"]) for case in cases}
    checks = {
        "runner_hash_matches_lock": lock["hashes"]["runner"] == raw["provenance"]["harness_sha256"],
        "seed_hash_matches_lock": lock["hashes"]["seed"] == raw["provenance"]["seed_manifest_sha256"],
        "extension_hash_matches_lock": lock["native_extension_sha256"] == raw["provenance"]["native_extension_sha256"],
        "engine_matches_current_source": raw["provenance"]["engine_provenance"]["source_match"] in ("own", "shared")
        and not raw["provenance"]["engine_provenance"]["stale_rust"],
        "exact_locked_case_set": observed == expected and len(cases) == len(expected),
    }
    analyzed = []
    for case in cases:
        active = case["active_mask"]
        fields = case["final_effective_fields"]
        weights = case["final_directed_weights"]
        event = case["event"]["states"]
        reference = case["full_rescan"]["states"]
        event_residual = residuals(event, fields, active, weights)
        reference_residual = residuals(reference, fields, active, weights)
        per_case = {
            "event_state_equals_reference": event == reference,
            "event_residual_zero": not any(event_residual),
            "reference_residual_zero": not any(reference_residual),
            "event_residual_count_reconciles": sum(event_residual) == case["event"]["residual_count"],
            "reference_residual_count_reconciles": sum(reference_residual) == case["full_rescan"]["residual_count"],
            "both_settled_under_cap": case["event"]["complete"] and case["full_rescan"]["complete"],
            "mutation_changes_projection": event != case["pre_mutation_state"],
            "active_mask_length_matches_state": len(active) == len(event) == len(reference),
        }
        neg = case["negative_control"]
        if neg is not None:
            nr = residuals(neg["states"], fields, active, weights)
            per_case["negative_control_recomputed_stale"] = (
                neg["states"] != reference and any(nr)
                and sum(nr) == neg["residual_count"] and neg["detects_stale"]
            )
        analyzed.append({
            "n": case["n"], "mutation": case["case"],
            "checks": per_case,
            "event_steps": case["event"]["steps"],
            "full_scan_steps": case["full_rescan"]["steps"],
            "event_turns": case["event"]["turns"],
            "full_scan_rounds": case["full_rescan"]["rounds"],
        })
    checks["all_event_residual_and_parity_checks_pass"] = all(
        all(item["checks"][key] for key in (
            "event_state_equals_reference", "event_residual_zero", "reference_residual_zero",
            "event_residual_count_reconciles", "reference_residual_count_reconciles",
            "both_settled_under_cap", "mutation_changes_projection", "active_mask_length_matches_state"))
        for item in analyzed)
    negative_rows = [item for item in analyzed if "negative_control_recomputed_stale" in item["checks"]]
    checks["all_registered_negative_controls_detect_staleness"] = bool(negative_rows) and all(
        item["checks"]["negative_control_recomputed_stale"] for item in negative_rows)
    payload = {
        "run_id": "substrate-can-boundary-mutation-matrix-v1.1-independent-analysis",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK), "analyzer_sha256": sha(Path(__file__)),
        "checks": checks, "pass": all(checks.values()),
        "case_count": len(analyzed),
        "progress_counts_equal_all_cells": all(
            item["event_steps"] == item["full_scan_steps"] for item in analyzed),
        "cases": analyzed,
        "claim_boundary": [
            "Residuals are recomputed from saved final fields, active mask, states, and directed weights.",
            "This analyzer checks the authored CAN one-rule local update, not a second substrate execution.",
            "v1.1 is discovery evidence after a failed v1 fixture; it is not confirmatory evidence.",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "pass": payload["pass"],
                      "checks": checks, "case_count": len(analyzed),
                      "progress_counts_equal_all_cells": payload["progress_counts_equal_all_cells"]}, indent=2))
    if not payload["pass"]:
        raise SystemExit("independent v1.1 mutation-matrix audit failed")


if __name__ == "__main__":
    main()
