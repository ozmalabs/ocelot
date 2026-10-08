#!/usr/bin/env python3
"""Independent post-run audit for the preregistered CAN boundary scale pilot."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_can_dynamic_boundary_scale_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/can_dynamic_boundary_scale_v1_1_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_can_dynamic_boundary_scale_analysis_20260925.json"
FRAME_SIZE = 4
BETA = 2.0
THRESHOLD = math.atanh(0.5)
MUTATIONS = ("insert_boundary_edge", "delete_boundary_edge",
             "replace_boundary_weight", "external_field_change")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconstruct(n: int, mutation: str):
    fields = [0.0] * n
    fields[3], fields[4] = 1.0, -0.1
    weights = {}
    for a in range(n - 1):
        if a == 3 and mutation == "insert_boundary_edge":
            continue
        w = 0.75 if a == 3 else (0.25 if a % 2 == 0 else -0.25)
        weights[a, a + 1] = weights[a + 1, a] = w
    if mutation == "insert_boundary_edge":
        weights[3, 4] = weights[4, 3] = 0.75
    elif mutation == "delete_boundary_edge":
        weights.pop((3, 4), None)
        weights.pop((4, 3), None)
    elif mutation == "replace_boundary_weight":
        weights[3, 4] = weights[4, 3] = -0.75
    elif mutation == "external_field_change":
        fields[0] = 1.0
    else:
        raise ValueError(mutation)
    return fields, weights


def local_residuals(state: list[float], fields: list[float], weights: dict) -> list[bool]:
    residual = []
    for node, current in enumerate(state):
        h = fields[node] + sum(weight * state[target]
                                for (source, target), weight in weights.items()
                                if source == node)
        scaled = BETA * h
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        residual.append(expected != current)
    return residual


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    rows = raw["cases"]
    expected = {(n, mutation) for n in (8, 16, 32, 64) for mutation in MUTATIONS}
    observed = {(row["n"], row["case"]) for row in rows}
    checks = {
        "locked_runner_matches_raw": lock["runner_sha256"] == raw["environment"]["harness_sha256"],
        "seed_matches_lock": lock["seed_sha256"] == raw["environment"]["seed_manifest_sha256"],
        "extension_matches_lock": lock["native_extension_sha256"] == raw["environment"]["native_extension_sha256"],
        "engine_source_matches": raw["environment"]["engine_provenance"]["source_match"] in ("own", "shared")
        and not raw["environment"]["engine_provenance"]["stale_rust"],
        "exact_locked_cell_set": observed == expected and len(rows) == len(expected),
        "case_count_matches": raw["case_count"] == len(expected),
    }
    analyzed = []
    for row in rows:
        fields, weights = reconstruct(row["n"], row["case"])
        event_state = row["event"]["states"]
        full_state = row["full_rescan"]["states"]
        event_residuals = local_residuals(event_state, fields, weights)
        full_residuals = local_residuals(full_state, fields, weights)
        missed = row["missed_notification_control"]
        missed_residuals = (local_residuals(missed["states"], fields, weights)
                            if missed is not None else [])
        row_checks = {
            "equal_states": event_state == full_state,
            "event_independent_residual_zero": not any(event_residuals),
            "full_scan_independent_residual_zero": not any(full_residuals),
            "reported_event_residual_reconciles": sum(event_residuals) == row["event"]["residual_count"],
            "reported_full_residual_reconciles": sum(full_residuals) == row["full_rescan"]["residual_count"],
            "mutation_changes_state": event_state != row["pre_mutation_states"],
            "both_arms_complete": row["event"]["complete"] and row["full_rescan"]["complete"],
        }
        if row["case"] == "insert_boundary_edge":
            row_checks["missed_notification_is_detectably_stale"] = (
                missed is not None and missed["detects_stale_frame"]
                and bool(any(missed_residuals))
                and sum(missed_residuals) == missed["residual_count"]
            )
        else:
            row_checks["no_unregistered_negative_control"] = missed is None
        analyzed.append({
            "n": row["n"], "frame_count": row["frame_count"], "case": row["case"],
            "checks": row_checks,
            "event_progress_steps": row["event"]["steps"],
            "full_rescan_progress_steps": row["full_rescan"]["steps"],
            "event_frame_turns": row["event"]["turns"],
            "event_residual_count_recomputed": sum(event_residuals),
            "full_residual_count_recomputed": sum(full_residuals),
        })
    all_case_checks = all(all(row["checks"].values()) for row in analyzed)
    checks["all_case_level_checks_pass"] = all_case_checks
    payload = {
        "run_id": raw["source_engine_id"] + ":can-dynamic-boundary-scale-v1.1",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "analyzer_sha256": sha(Path(__file__)),
        "checks": checks,
        "pass": all(checks.values()),
        "case_count": len(analyzed),
        "progress_counts_equal_event_and_full_scan_all_cells": all(
            row["event_progress_steps"] == row["full_rescan_progress_steps"] for row in analyzed
        ),
        "cases": analyzed,
        "claim_boundary": [
            "Independent reconstruction confirms registered local residuals and exact event/full-scan state parity on the recorded path cases.",
            "Progress-application counts are equal across the two arms in this fixed fixture; event turns are not compared to an independently counted full-scan turn measure.",
            "The analyzer independently reconstructs the authored path/field model from the frozen case definition; it is not a second native execution implementation.",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "pass": payload["pass"],
                      "checks": checks,
                      "event_and_full_progress_counts_equal": payload["progress_counts_equal_event_and_full_scan_all_cells"]}, indent=2))
    if not payload["pass"]:
        raise SystemExit("independent pilot audit failed")


if __name__ == "__main__":
    main()
