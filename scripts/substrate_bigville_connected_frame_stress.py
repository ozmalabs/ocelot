#!/usr/bin/env python3
"""Controlled cross-frame CAN stress experiment on the Bigville runtime path."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_BIGVILLE_CONNECTED_FRAME_STRESS_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/bigville_connected_frame_stress_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_bigville_connected_frame_stress_20260925.json"
BASE_RUNNER = ROOT / "scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py"
CAST = ROOT / "seeds/bigville_cast100.json"
SEED = ROOT / "seeds/can_native_reimplementation.json"
TOPOLOGIES = ("disconnected", "ring", "star")
POLICIES = ("full", "event")
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("bigville_partition_base", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the pinned partition replay implementation")
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


def worker(topology: str, policy: str) -> dict:
    import substrate_rs as sr
    from domains.engine_provenance import engine_provenance
    from substrate_rs import _native
    from worlds import bigville_can_beliefs as bigville

    base = load_base()
    original_build = base.build
    original_weights = base.weights_by_id
    added_weights: list[tuple[int, int, float]] = []
    injection = {"topology": topology}

    def connected_build(sr_module, cast, seed_doc, builder):
        result = list(original_build(sr_module, cast, seed_doc, builder))
        (outer, inner, residents, mts, concepts, frame_nodes, node_frame,
         edges, cross, ref_by_id, node_flat) = result
        pairs = frame_pairs(topology, len(mts))
        # Fixed index-independent topic lookup; all links join world_safe.
        for left, right in pairs:
            a = concepts[left]["world_safe"]
            b = concepts[right]["world_safe"]
            aid, bid = base.nid(a), base.nid(b)
            inner.add_edge_unchecked(a, "causal_influence", b, {"weight": 0.2})
            inner.add_edge_unchecked(b, "causal_influence", a, {"weight": 0.2})
            edges.extend(((aid, bid), (bid, aid)))
            cross.extend(((aid, bid), (bid, aid)))
            added_weights.extend(((node_flat[aid], node_flat[bid], 0.2),
                                  (node_flat[bid], node_flat[aid], 0.2)))
        injection["pair_count"] = len(pairs)
        injection["directed_cross_edge_count"] = 2 * len(pairs)
        injection["frame_degree"] = [0] * len(mts)
        for left, right in pairs:
            injection["frame_degree"][left] += 1
            injection["frame_degree"][right] += 1
        return tuple(result)

    def connected_weights(*args, **kwargs):
        return original_weights(*args, **kwargs) + list(added_weights)

    base.build = connected_build
    base.weights_by_id = connected_weights
    base.CAP = CAP
    cast_doc, seed_doc = json.loads(CAST.read_text()), json.loads(SEED.read_text())
    start = time.perf_counter_ns()
    arm = base.run_arm(sr, cast_doc["residents"], seed_doc, bigville, policy)
    wall_ns = time.perf_counter_ns() - start
    checkpoints = arm["checkpoints"]
    return {
        "topology": topology,
        "policy": policy,
        "injected": injection,
        "initial": arm["initial"],
        "initial_states": arm["initial_states"],
        "checkpoints": checkpoints,
        "complete": arm["initial"]["complete"] and all(
            c["settlement"]["complete"] for c in checkpoints),
        "all_full_graph_residuals_zero": all(c["residual_count"] == 0 for c in checkpoints),
        "wall_ns": wall_ns,
        "provenance": {
            "python": sys.version,
            "platform": platform.platform(),
            "native_extension_path": str(Path(_native.__file__).resolve()),
            "native_extension_sha256": sha(Path(_native.__file__).resolve()),
            "engine_provenance": engine_provenance(),
        },
    }


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], sys.argv[3]), sort_keys=True))
        return
    locked = {
        "preregistration_sha256": sha(PREREG),
        "runner_sha256": sha(Path(__file__).resolve()),
        "base_runner_sha256": sha(BASE_RUNNER),
        "cast_sha256": sha(CAST),
        "seed_sha256": sha(SEED),
        "builder_sha256": sha(ROOT / "worlds/bigville_can_beliefs.py"),
        "rewrite_sha256": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        "substrate_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
    }
    if len(sys.argv) == 2 and sys.argv[1] == "--lock":
        print(json.dumps(locked, indent=2, sort_keys=True))
        return
    if not LOCK.exists():
        raise SystemExit("missing preregistered lock; create it from the reviewed protocol before execution")
    lock = json.loads(LOCK.read_text())
    if lock.get("locked_inputs") != locked:
        raise SystemExit("locked inputs changed; preserve this lock and issue a disclosed amendment")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')) )"],
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit("native build stale:\n" + stale)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    records = []
    for topology in TOPOLOGIES:
        for policy in POLICIES:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                   "--worker", topology, policy], cwd=ROOT, env=env,
                                  text=True, capture_output=True, check=True)
            records.append(json.loads(proc.stdout.strip()))
            print(f"{topology}/{policy} complete={records[-1]['complete']} "
                  f"residuals_zero={records[-1]['all_full_graph_residuals_zero']}", flush=True)
    pairs = {}
    for topology in TOPOLOGIES:
        full = next(r for r in records if r["topology"] == topology and r["policy"] == "full")
        event = next(r for r in records if r["topology"] == topology and r["policy"] == "event")
        pairs[topology] = {
            "baseline_states_equal": full["initial_states"] == event["initial_states"],
            "checkpoint_state_equal": [a["states"] == b["states"] for a, b in
                                        zip(full["checkpoints"], event["checkpoints"])],
            "full_turns": [c["settlement"]["turns"] for c in full["checkpoints"]],
            "event_turns": [c["settlement"]["turns"] for c in event["checkpoints"]],
            "full_candidates": [c["settlement"]["audit"]["cand_enum"] for c in full["checkpoints"]],
            "event_candidates": [c["settlement"]["audit"]["cand_enum"] for c in event["checkpoints"]],
            "full_term_units": [c["settlement"]["audit"]["term_units_total"] for c in full["checkpoints"]],
            "event_term_units": [c["settlement"]["audit"]["term_units_total"] for c in event["checkpoints"]],
        }
    checks = {
        "all_arms_complete": all(r["complete"] for r in records),
        "all_full_graph_residuals_zero": all(r["all_full_graph_residuals_zero"] for r in records),
        "one_record_per_topology_policy": len(records) == len(TOPOLOGIES) * len(POLICIES),
        "ring_pairs_100": next(r for r in records if r["topology"] == "ring")["injected"]["pair_count"] == 100,
        "star_pairs_99": next(r for r in records if r["topology"] == "star")["injected"]["pair_count"] == 99,
    }
    payload = {
        "schema_version": 1,
        "run_id": "bigville-connected-frame-stress-20260925-v1",
        "claim_boundary": "controlled cross-resident CAN edge stress; not authored Bigville semantics, natural locality prevalence, or generic GALS",
        "locked_inputs": locked,
        "lock_sha256": sha(LOCK),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "checks": checks,
        "comparisons": pairs,
        "runs": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "comparisons": pairs}, indent=2))
    if not all(checks.values()):
        raise SystemExit("semantic gate failed; inspect and preserve raw result")


if __name__ == "__main__":
    main()
