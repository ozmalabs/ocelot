#!/usr/bin/env python3
"""Independent state, residual, work and provenance audit for Bigville replay."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_bigville_can_runtime_partition_replay_v3_1_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/bigville_can_runtime_partition_replay_v3_1_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_bigville_can_runtime_partition_replay_v3_1_analysis_20260925.json"
TOPICS = ("trust_mayor", "claim_credible", "world_safe", "self_worth", "debtor_trustworthy")
TARGETS = tuple(range(0, 100, 10))
THRESHOLD = 0.5493061443340548


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_residual(states, fields, edges):
    flat_states = [float(row[topic]) for row in states for topic in TOPICS]
    residuals = []
    for i, state in enumerate(flat_states):
        external, identity = fields[i]
        h = float(external) + float(identity)
        h += sum(float(weight) * flat_states[int(target)]
                 for source, target, weight in edges if int(source) == i)
        scaled = 1.5 * h
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        residuals.append(expected != state)
    return residuals


def main():
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    p = raw["provenance"]
    checks = {
        "runner_hash_matches_lock": lock["hashes"]["runner"] == p["runner_sha256"],
        "analyzer_hash_matches_lock": lock["hashes"]["analyzer"] == sha(Path(__file__)),
        "protocol_hash_matches_lock": lock["hashes"]["protocol"] == p["protocol_sha256"],
        "cast_hash_matches_lock": lock["hashes"]["cast"] == p["cast_sha256"],
        "can_seed_hash_matches_lock": lock["hashes"]["can_seed"] == p["can_seed_sha256"],
        "builder_hash_matches_lock": lock["hashes"]["builder"] == p["bigville_builder_sha256"],
        "extension_hash_matches_lock": lock["native_extension_sha256"] == p["native_extension_sha256"],
        "engine_matches_current_source": p["engine_provenance"]["source_match"] in ("own", "shared")
        and not p["engine_provenance"]["stale_rust"],
        "exact_target_sequence": [c["target_resident_position"] for c in raw["checkpoints"]] == list(TARGETS),
        "exact_cast_and_component_size": raw["resident_count"] == 100 and raw["component_count"] == 100
        and raw["component_sizes"] == [5] * 100,
        "no_cross_component_edges": raw["cross_frame_edge_count"] == 0,
        "baseline_state_parity": raw["baseline_states_equal"],
    }
    per_checkpoint = []
    for c in raw["checkpoints"]:
        er = local_residual(c["event_states"], c["event_fields"], raw["directed_weights_by_flat_index"])
        rr = local_residual(c["full_states"], c["full_fields"], raw["directed_weights_by_flat_index"])
        row = {
            "target_resident_position": c["target_resident_position"],
            "states_equal": c["event_states"] == c["full_states"],
            "event_residual_zero": not any(er), "full_residual_zero": not any(rr),
            "saved_residuals_reconcile": sum(er) == c["event_residual_count"]
            and sum(rr) == c["full_residual_count"],
            "both_settled": c["event_settlement"]["complete"] and c["full_settlement"]["complete"],
            "event_turns": c["event_settlement"]["turns"],
            "full_turns": c["full_settlement"]["turns"],
            "event_progress": c["event_settlement"]["steps"],
            "full_progress": c["full_settlement"]["steps"],
            "event_audit": c["event_settlement"]["audit"],
            "full_audit": c["full_settlement"]["audit"],
        }
        per_checkpoint.append(row)
    checks["all_checkpoint_checks_pass"] = all(
        row[k] for row in per_checkpoint for k in
        ("states_equal", "event_residual_zero", "full_residual_zero", "saved_residuals_reconcile", "both_settled"))
    control = raw["omitted_notification_control"]
    checks["omitted_notification_control_sensitive"] = (
        control["baseline_settled"] and control["notified_sequence_changes_state"]
        and control["detects_stale"] and control["residual_count"] > 0
    )
    event_candidates = sum(r["event_audit"].get("cand_enum", 0) for r in per_checkpoint)
    full_candidates = sum(r["full_audit"].get("cand_enum", 0) for r in per_checkpoint)
    event_turns = sum(r["event_turns"] for r in per_checkpoint)
    full_turns = sum(r["full_turns"] for r in per_checkpoint)
    event_units = {key: sum(r["event_audit"].get(key, 0) for r in per_checkpoint)
                   for key in ("cand_enum", "cand_tested", "where_evals", "leaf_visits", "term_evals_total", "term_units_total")}
    full_units = {key: sum(r["full_audit"].get(key, 0) for r in per_checkpoint)
                  for key in event_units}
    result = {
        "run_id": "bigville-can-runtime-partition-replay-independent-analysis",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK), "analyzer_sha256": sha(Path(__file__)),
        "checks": checks, "pass": all(checks.values()),
        "checkpoint_count": len(per_checkpoint), "checkpoints": per_checkpoint,
        "work_totals": {"event_frame_turns": event_turns, "full_frame_turns": full_turns,
                        "event_candidate_pairs": event_candidates, "full_candidate_pairs": full_candidates,
                        "event_units": event_units, "full_units": full_units,
                        "full_over_event_candidate_ratio": full_candidates / event_candidates if event_candidates else None,
                        "progress_counts_equal_each_update": all(r["event_progress"] == r["full_progress"]
                                                                  for r in per_checkpoint)},
        "claim_boundary": [
            "This is a project-authored deterministic Bigville cast replay, not natural-world prevalence evidence.",
            "Partitions are connected components of live causal-influence adjacency and are mapped to live has_concept owners.",
            "Evidence updates use caller-supplied frame notification; no native effect-to-frame producer is tested.",
            "No cross-frame edges exist in these authored per-resident CANs; connected-frame correctness is not established.",
            "Candidate counters are operation counts for the registered update path; they are not time or allocation measurements.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "pass": result["pass"],
                      "checks": checks, "work_totals": result["work_totals"]}, indent=2))
    if not result["pass"]:
        raise SystemExit("Bigville replay independent audit failed")


if __name__ == "__main__":
    main()
