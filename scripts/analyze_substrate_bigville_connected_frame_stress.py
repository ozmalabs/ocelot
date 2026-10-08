#!/usr/bin/env python3
"""Independent raw-record checks for connected-frame CAN stress run."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners/dsl/python"))
sys.path.insert(1, str(ROOT))
RAW = ROOT / "evaluation/reports/substrate_bigville_connected_frame_stress_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/bigville_connected_frame_stress_lock_20260925.json"
ANALYSIS = ROOT / "evaluation/reports/substrate_bigville_connected_frame_stress_analysis_20260925.json"
RUNNER = ROOT / "scripts/substrate_bigville_connected_frame_stress.py"
BASE = ROOT / "scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_BIGVILLE_CONNECTED_FRAME_STRESS_PREREG_20260925.md"
CAST = ROOT / "seeds/bigville_cast100.json"
SEED = ROOT / "seeds/can_native_reimplementation.json"
THRESHOLD = 0.5493061443340548


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("bigville_stress_audit_base", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load runtime graph builder for independent weight reconstruction")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frame_pairs(topology: str, count: int) -> list[tuple[int, int]]:
    if topology == "disconnected":
        return []
    if topology == "ring":
        return [(i, (i + 1) % count) for i in range(count)]
    if topology == "star":
        return [(0, i) for i in range(1, count)]
    raise ValueError(topology)


def audit_residual(states, fields, weights, topic_order) -> int:
    # The runner prints JSON with sort_keys=True, so rebuild the builder's
    # canonical topic order rather than relying on serialized object order.
    flat = [float(frame[topic]) for frame in states for topic in topic_order]
    residuals = 0
    for source, value in enumerate(flat):
        external, identity = fields[source]
        local_field = float(external) + float(identity)
        for a, b, weight in weights:
            if int(a) == source:
                local_field += float(weight) * flat[int(b)]
        scaled = 1.5 * local_field
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        residuals += int(expected != value)
    return residuals


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    locked_paths = {
        "preregistration_sha256": PREREG,
        "runner_sha256": RUNNER,
        "base_runner_sha256": BASE,
        "cast_sha256": CAST,
        "seed_sha256": SEED,
        "builder_sha256": ROOT / "worlds/bigville_can_beliefs.py",
        "rewrite_sha256": ROOT / "runners/dsl/src/rewrite.rs",
        "substrate_sha256": ROOT / "runners/dsl/src/substrate.rs",
    }
    hash_match = all(lock["locked_inputs"].get(key) == sha(path)
                     for key, path in locked_paths.items())
    if not hash_match:
        raise SystemExit("locked source hash mismatch")

    import substrate_rs as sr
    from worlds import bigville_can_beliefs as bigville
    base = load_base()
    cast = json.loads(CAST.read_text())["residents"]
    seed_doc = json.loads(SEED.read_text())
    checks = {"locked_input_hashes_match": hash_match,
              "arm_count_is_six": len(raw["runs"]) == 6,
              "all_raw_gate_checks_true": all(raw["checks"].values())}
    rows = []
    for topology in ("disconnected", "ring", "star"):
        for policy in ("full", "event"):
            run = next(r for r in raw["runs"]
                       if r["topology"] == topology and r["policy"] == policy)
            (outer, inner, residents, mts, concepts, frame_nodes, node_frame,
             edges, cross, ref_by_id, node_flat) = base.build(sr, cast, seed_doc, bigville)
            pairs = frame_pairs(topology, len(mts))
            weights = base.weights_by_id(concepts, residents, bigville, node_flat)
            for left, right in pairs:
                a = node_flat[base.nid(concepts[left]["world_safe"])]
                b = node_flat[base.nid(concepts[right]["world_safe"])]
                weights.extend(((a, b, 0.2), (b, a, 0.2)))
            recorded_pairs = run["injected"]["pair_count"]
            topology_ok = recorded_pairs == len(pairs)
            checkpoint_rows = []
            for index, checkpoint in enumerate(run["checkpoints"]):
                observed = audit_residual(checkpoint["states"], checkpoint["fields"],
                                          weights, bigville.TOPIC_NAMES)
                reported = int(checkpoint["residual_count"])
                checkpoint_rows.append({"checkpoint": index,
                                        "recomputed_residual_count": observed,
                                        "runner_residual_count": reported,
                                        "residual_matches": observed == reported})
            rows.append({"topology": topology, "policy": policy,
                         "topology_pair_count_matches": topology_ok,
                         "checkpoint_count": len(checkpoint_rows),
                         "checkpoints": checkpoint_rows})
    checks["topology_counts_match"] = all(r["topology_pair_count_matches"] for r in rows)
    checks["all_checkpoint_residuals_recompute"] = all(
        c["residual_matches"] for r in rows for c in r["checkpoints"])
    checks["all_recomputed_residuals_zero"] = all(
        c["recomputed_residual_count"] == 0 for r in rows for c in r["checkpoints"])
    paired = {}
    for topology in ("disconnected", "ring", "star"):
        full = next(r for r in raw["runs"] if r["topology"] == topology and r["policy"] == "full")
        event = next(r for r in raw["runs"] if r["topology"] == topology and r["policy"] == "event")
        paired[topology] = {
            "baseline_exact_state_match": full["initial_states"] == event["initial_states"],
            "checkpoint_exact_state_matches": [a["states"] == b["states"] for a, b in
                                                zip(full["checkpoints"], event["checkpoints"])],
        }
    checks["paired_checkpoint_counts_match"] = all(
        len(v["checkpoint_exact_state_matches"]) == 10 for v in paired.values())
    result = {
        "schema_version": 1,
        "raw_sha256": sha(RAW),
        "lock_sha256": sha(LOCK),
        "checks": checks,
        "paired_state_audit": paired,
        "residual_audit": rows,
        "audit_boundary": "independent residual equation and topology arithmetic; uses source runtime builder and authored weights to reconstruct the measured model",
    }
    ANALYSIS.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(ANALYSIS.relative_to(ROOT)), "checks": checks,
                      "paired_state_audit": paired}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent raw-record audit failed")


if __name__ == "__main__":
    main()
