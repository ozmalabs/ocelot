#!/usr/bin/env python3
"""Independent state-equation and action-history audit."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_directed_boundary_replay_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/directed_boundary_replay_lock_20260925.json"
ANALYSIS = ROOT / "evaluation/reports/substrate_directed_boundary_replay_analysis_20260925.json"
RUNNER = ROOT / "scripts/substrate_directed_boundary_replay.py"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_DIRECTED_BOUNDARY_REPLAY_PREREG_20260925.md"
BASE = ROOT / "scripts/substrate_can_boundary_mutation_matrix_v1_1.py"
SEED = ROOT / "seeds/can_native_reimplementation.json"
THRESHOLD = math.atanh(0.5)
BETA = 2.0
N = 12


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recompute(states, weights) -> int:
    residual = 0
    fields = [0.0] * N
    fields[-1] = 1.0
    for source in range(N):
        h = fields[source] + sum(float(weight) * float(states[int(target)])
                                 for src, target, weight in weights
                                 if int(src) == source)
        scaled = BETA * h
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        residual += int(expected != float(states[source]))
    return residual


def main() -> None:
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
    hash_ok = all(lock["locked_inputs"].get(k) == sha(v) for k, v in paths.items())
    if not hash_ok:
        raise SystemExit("locked source hashes mismatch")
    rows = []
    for policy in ("full", "event"):
        for step in raw[policy]["sequence"]:
            value = recompute(step["after"], step["weights_after"])
            rows.append({"policy": policy, "sequence_index": step["sequence_index"],
                         "recomputed_residual": value,
                         "runner_residual": step["residual_count"],
                         "matches": value == step["residual_count"]})
    omission = raw["omission_control"]
    omission_weights = [[i, i + 1, 0.75] for i in range(N - 1)
                        if (i, i + 1) != (7, 8)]
    omission_residual = recompute(omission["state_after_omission"], omission_weights)
    step_parity = [a["after"] == b["after"]
                   for a, b in zip(raw["full"]["sequence"], raw["event"]["sequence"])]
    checks = {
        "locked_hashes_match": hash_ok,
        "all_24_action_residuals_recompute": len(rows) == 24 and all(r["matches"] for r in rows),
        "all_recomputed_terminal_residuals_zero": all(r["recomputed_residual"] == 0 for r in rows),
        "state_parity_at_every_action": len(step_parity) == 12 and all(step_parity),
        "all_action_effects_observed": all(s["changed"] for p in ("full", "event")
                                           for s in raw[p]["sequence"]),
        "omission_residual_recomputes_positive": omission_residual > 0 and
            omission_residual == omission["residual_count"],
        "raw_preregistered_checks_true": all(raw["checks"].values()),
    }
    result = {
        "schema_version": 1,
        "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK),
        "checks": checks,
        "recomputed_residuals": rows,
        "omission_control_recomputed_residual": omission_residual,
        "action_state_parity": step_parity,
        "audit_boundary": "independent ternary update equation over recorded states and directed weights; fixed initial fields from preregistration",
    }
    ANALYSIS.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(ANALYSIS.relative_to(ROOT)), "checks": checks,
                      "omission_control_residual": omission_residual}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent analysis failed")


if __name__ == "__main__":
    main()
