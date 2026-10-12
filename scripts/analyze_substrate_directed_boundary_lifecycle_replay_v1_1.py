#!/usr/bin/env python3
"""Independent equation and lifecycle-history audit for v1.1."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_directed_boundary_lifecycle_replay_v1_1_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/directed_boundary_lifecycle_replay_v1_1_lock_20260925.json"
ANALYSIS = ROOT / "evaluation/reports/substrate_directed_boundary_lifecycle_replay_v1_1_analysis_20260925.json"
RUNNER = ROOT / "scripts/substrate_directed_boundary_lifecycle_replay_v1_1.py"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_DIRECTED_BOUNDARY_LIFECYCLE_REPLAY_V1_1_AMENDMENT_20260925.md"
BASE = ROOT / "scripts/substrate_can_boundary_mutation_matrix_v1_1.py"
SEED = ROOT / "seeds/can_native_reimplementation.json"
BETA = 2.0
THRESHOLD = math.atanh(0.5)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def residual(states, fields, weights) -> int:
    total = 0
    for source, state in enumerate(states):
        field = fields[source]
        if state is None or field is None:
            continue
        h = float(field)
        for src, target, weight in weights:
            if int(src) == source:
                target_state = states[int(target)]
                if target_state is None:
                    raise ValueError("active edge points to deleted target in raw record")
                h += float(weight) * float(target_state)
        scaled = BETA * h
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        total += int(expected != float(state))
    return total


def main():
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    paths = {
        "preregistration_sha256": PREREG,
        "runner_sha256": RUNNER,
        "base_runner_sha256": BASE,
        "seed_sha256": SEED,
        "rewrite_sha256": ROOT / "runners/dsl/src/rewrite.rs",
        "substrate_sha256": ROOT / "runners/dsl/src/substrate.rs",
    }
    hashes_ok = all(lock["locked_inputs"].get(k) == sha(v) for k, v in paths.items())
    if not hashes_ok:
        raise SystemExit("locked input hash mismatch")
    rows = []
    for policy in ("full", "event"):
        for step in raw[policy]["checkpoints"]:
            recomputed = residual(step["after"], step["effective_fields"], step["weights_after"])
            rows.append({"policy": policy, "index": step["index"],
                         "recomputed_residual": recomputed,
                         "runner_residual": step["residual_count"],
                         "matches": recomputed == step["residual_count"]})
    omit = raw["omission_control"]
    omitted_residual = residual(omit["state_after_omission"], omit["fields_after_omission"],
                                omit["weights_after_omission"])
    full, event = raw["full"]["checkpoints"], raw["event"]["checkpoints"]
    expected_notifications = [[2] if c["action"] in {"birth_node", "delete_node"} else [1]
                              for c in event]
    checks = {
        "locked_hashes_match": hashes_ok,
        "all_36_checkpoint_residuals_match": len(rows) == 36 and all(r["matches"] for r in rows),
        "all_recomputed_full_event_residuals_zero": all(r["recomputed_residual"] == 0 for r in rows),
        "state_and_active_parity_every_action": all(
            a["after"] == b["after"] and a["active"] == b["active"]
            for a, b in zip(full, event)),
        "mutation_effects_all_observed": all(a["changed"] and b["changed"]
                                              for a, b in zip(full, event)),
        "notifications_match_action_owners": [c["notified_frames"] for c in event] == expected_notifications,
        "omission_residual_matches_and_positive": omitted_residual == omit["residual_count"] > 0,
        "raw_gate_checks_true": all(raw["checks"].values()),
    }
    payload = {
        "schema_version": 1,
        "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK),
        "checks": checks,
        "residual_audit": rows,
        "omission_residual_recomputed": omitted_residual,
        "state_parity": [a["after"] == b["after"] and a["active"] == b["active"]
                         for a, b in zip(full, event)],
        "claim_boundary": "independent ternary update equation using raw active states, fields, and edge weights; source-workload generality not assessed",
    }
    ANALYSIS.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(ANALYSIS.relative_to(ROOT)), "checks": checks,
                      "omission_residual": omitted_residual}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent lifecycle audit failed")


if __name__ == "__main__":
    main()
