#!/usr/bin/env python3
"""Independent equation, sensitivity, topology, and provenance audit."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners/dsl/python"))
sys.path.insert(1, str(ROOT))
RAW = ROOT / "evaluation/reports/substrate_bigville_directed_frame_wakeup_v1_1_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/bigville_directed_frame_wakeup_v1_1_lock_20260925.json"
ANALYSIS = ROOT / "evaluation/reports/substrate_bigville_directed_frame_wakeup_v1_1_analysis_20260925.json"
RUNNER = ROOT / "scripts/substrate_bigville_directed_frame_wakeup_v1_1.py"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_BIGVILLE_DIRECTED_FRAME_WAKEUP_V1_1_AMENDMENT_20260925.md"
BASE = ROOT / "scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py"
CAST = ROOT / "seeds/bigville_cast100.json"
SEED = ROOT / "seeds/can_native_reimplementation.json"
TOPICS = ("trust_mayor", "claim_credible", "world_safe", "self_worth", "debtor_trustworthy")
THRESHOLD = 0.5493061443340548


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def residual_count(run: dict) -> int:
    flat = [float(frame[topic]) for frame in run["final_states"] for topic in TOPICS]
    count = 0
    for source, state in enumerate(flat):
        external, identity = run["fields"][source]
        h = float(external) + float(identity)
        for src, target, weight in run["directed_edges"]:
            if int(src) == source:
                h += float(weight) * flat[int(target)]
        scaled = 1.5 * h
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        count += int(expected != state)
    return count


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    paths = {
        "preregistration_sha256": PREREG,
        "runner_sha256": RUNNER,
        "base_runner_sha256": BASE,
        "cast_sha256": CAST,
        "seed_sha256": SEED,
        "builder_sha256": ROOT / "worlds/bigville_can_beliefs.py",
        "rewrite_sha256": ROOT / "runners/dsl/src/rewrite.rs",
        "substrate_sha256": ROOT / "runners/dsl/src/substrate.rs",
    }
    hashes_match = all(lock["locked_inputs"].get(k) == sha(v) for k, v in paths.items())
    if not hashes_match:
        raise SystemExit("locked input hash mismatch")
    rows = []
    for run in raw["runs"]:
        measured = residual_count(run)
        rows.append({"topology": run["topology"], "policy": run["policy"],
                     "recomputed_residual_count": measured,
                     "runner_residual_count": run["residual_count"],
                     "residual_matches": measured == run["residual_count"],
                     "edge_count": len(run["directed_edges"])})
    paired = {}
    for topology in ("chain", "leaves_to_hub", "hub_to_leaves"):
        arms = {r["policy"]: r for r in raw["runs"] if r["topology"] == topology}
        paired[topology] = {
            "full_event_states_equal": arms["full"]["final_states"] == arms["event"]["final_states"],
            "omission_has_positive_residual": residual_count(arms["omission"]) > 0,
            "event_turns": arms["event"]["settlement"]["turns"],
            "event_enqueues": arms["event"]["settlement"]["enqueues"],
        }
    checks = {
        "locked_hashes_match": hashes_match,
        "nine_arms_present": len(rows) == 9,
        "all_residuals_recompute": all(r["residual_matches"] for r in rows),
        "full_and_event_residuals_zero": all(
            r["recomputed_residual_count"] == 0 for r in rows if r["policy"] in ("full", "event")),
        "omission_positive_in_all_topologies": all(
            v["omission_has_positive_residual"] for v in paired.values()),
        "full_event_state_parity_all_topologies": all(
            v["full_event_states_equal"] for v in paired.values()),
        "raw_gate_checks_true": all(raw["checks"].values()),
    }
    payload = {
        "schema_version": 1,
        "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK),
        "checks": checks,
        "per_arm_residual_audit": rows,
        "topology_comparisons": paired,
        "equation": "state_i = sign(1.5 * (external_i + identity_i + sum_j weight_ij * state_j)) with strict +/- 0.5493061443340548 thresholds",
        "claim_boundary": "equation and provenance audit on an isolated directed-link fixture; no natural prevalence claim",
    }
    ANALYSIS.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(ANALYSIS.relative_to(ROOT)), "checks": checks,
                      "topology_comparisons": paired}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent analysis failed")


if __name__ == "__main__":
    main()
