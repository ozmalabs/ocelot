#!/usr/bin/env python3
"""Measure directed frame wakeups and a notification-omission control."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_BIGVILLE_DIRECTED_FRAME_WAKEUP_V1_1_AMENDMENT_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/bigville_directed_frame_wakeup_v1_1_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_bigville_directed_frame_wakeup_v1_1_20260925.json"
BASE = ROOT / "scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py"
CAST = ROOT / "seeds/bigville_cast100.json"
SEED = ROOT / "seeds/can_native_reimplementation.json"
TOPOLOGIES = ("chain", "leaves_to_hub", "hub_to_leaves")
POLICIES = ("full", "event", "omission")
TARGETS = {"chain": 11, "leaves_to_hub": 0, "hub_to_leaves": 11}
N_FRAMES = 12
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("bigville_directed_base", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the locked runtime replay helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def directed_pairs(topology: str) -> list[tuple[int, int]]:
    if topology == "chain":
        return [(i, i + 1) for i in range(N_FRAMES - 1)]
    if topology == "leaves_to_hub":
        return [(i, 0) for i in range(1, N_FRAMES)]
    if topology == "hub_to_leaves":
        return [(0, i) for i in range(1, N_FRAMES)]
    raise ValueError(topology)


def worker(topology: str, policy: str) -> dict:
    import substrate_rs as sr
    from domains.engine_provenance import engine_provenance
    from substrate_rs import _native
    from worlds import bigville_can_beliefs as bigville

    base = load_base()
    cast = json.loads(CAST.read_text())["residents"][:N_FRAMES]
    seed_doc = json.loads(SEED.read_text())
    outer, inner, residents, mts, concepts, frame_nodes, node_frame, edges, cross, refs, node_flat = base.build(
        sr, cast, seed_doc, bigville)
    # Isolate the cross-frame read relation while retaining live rule and frame APIs.
    for topic_map in concepts:
        for node in topic_map.values():
            for neighbor in list(inner.neighbours(node, "causal_influence")):
                inner.remove_edge(node, "causal_influence", neighbor)
            inner.set_attr(node, "external_field", 0.0)
            inner.set_attr(node, "identity_field", 0.0)
            inner.set_attr(node, "state", 0.0)

    injected = []
    for source, target in directed_pairs(topology):
        src = concepts[source]["world_safe"]
        dst = concepts[target]["world_safe"]
        src_id, dst_id = base.nid(src), base.nid(dst)
        inner.add_edge_unchecked(src, "causal_influence", dst, {"weight": 1.0})
        edges.append((src_id, dst_id))
        cross.append((src_id, dst_id))
        injected.append((node_flat[src_id], node_flat[dst_id], 1.0))

    # All intra-frame edges were removed; the independent residual oracle uses
    # only the injected directed links.
    weights = injected
    initial = base.settle_full(inner, mts)
    if not initial["complete"]:
        raise RuntimeError("full-graph baseline did not settle")
    initial_states = base.states(inner, concepts)
    target = TARGETS[topology]
    inner.set_attr(concepts[target]["world_safe"], "external_field", 1.0)
    before = base.states(inner, concepts)

    start = time.perf_counter_ns()
    if policy == "full":
        settlement = base.settle_full(inner, mts, audit=True)
    elif policy == "event":
        settlement = base.settle_event(inner, mts, frame_nodes, node_frame, edges, refs,
                                       {target}, audit=True)
    elif policy == "omission":
        inner.scale_audit_reset(); inner.scale_audit_set_enabled(True)
        steps = inner.run_rules_scoped(CAP, False, mts[target])
        audit = base.snap(inner); inner.scale_audit_set_enabled(False)
        settlement = {"steps": steps, "turns": 1, "rounds": 1, "enqueues": 0,
                      "changed_frames": int(before != base.states(inner, concepts)),
                      "complete": True, "audit": audit}
    else:
        raise ValueError(policy)
    wall_ns = time.perf_counter_ns() - start
    final_states = base.states(inner, concepts)
    field_rows = base.fields(inner, concepts)
    residual_count = sum(base.residuals(final_states, field_rows, weights))
    return {
        "topology": topology,
        "policy": policy,
        "target_frame": target,
        "directed_edge_count": len(directed_pairs(topology)),
        "directed_edges": [[a, b, w] for a, b, w in injected],
        "initial_settlement": initial,
        "initial_states": initial_states,
        "pre_settlement_states": before,
        "final_states": final_states,
        "fields": field_rows,
        "residual_count": residual_count,
        "settlement": settlement,
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
        "base_runner_sha256": sha(BASE),
        "cast_sha256": sha(CAST),
        "seed_sha256": sha(SEED),
        "builder_sha256": sha(ROOT / "worlds/bigville_can_beliefs.py"),
        "rewrite_sha256": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        "substrate_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
    }
    if len(sys.argv) == 2 and sys.argv[1] == "--lock":
        print(json.dumps(locked, indent=2, sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing lock or locked inputs changed")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],
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
            row = records[-1]
            print(f"{topology}/{policy}: residual={row['residual_count']} "
                  f"turns={row['settlement']['turns']}", flush=True)
    summaries = {}
    for topology in TOPOLOGIES:
        arms = {r["policy"]: r for r in records if r["topology"] == topology}
        summaries[topology] = {
            "full_event_state_equal": arms["full"]["final_states"] == arms["event"]["final_states"],
            "full_residual": arms["full"]["residual_count"],
            "event_residual": arms["event"]["residual_count"],
            "omission_residual": arms["omission"]["residual_count"],
            "event_turns": arms["event"]["settlement"]["turns"],
            "event_enqueues": arms["event"]["settlement"].get("enqueues", 0),
            "omission_state_changed": arms["omission"]["pre_settlement_states"] != arms["omission"]["final_states"],
        }
    checks = {
        "all_full_and_event_settled": all(
            r["settlement"]["complete"] for r in records if r["policy"] in ("full", "event")),
        "full_and_event_residual_zero": all(
            summaries[t][key] == 0 for t in TOPOLOGIES for key in ("full_residual", "event_residual")),
        "all_expected_topology_edges": all(
            next(r for r in records if r["topology"] == t)["directed_edge_count"] == len(directed_pairs(t))
            for t in TOPOLOGIES),
        "omission_control_sensitive": all(
            summaries[t]["omission_state_changed"] and summaries[t]["omission_residual"] > 0
            for t in TOPOLOGIES),
    }
    payload = {
        "schema_version": 1,
        "run_id": "bigville-directed-frame-wakeup-20260925-v1.1",
        "claim_boundary": "controlled state-flip wakeup fixture on 12 Bigville-constructed frames with injected directed links; not authored resident dynamics, natural prevalence, dynamic edge mutation, or native GALS",
        "locked_inputs": locked,
        "lock_sha256": sha(LOCK),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "checks": checks,
        "summaries": summaries,
        "runs": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "summaries": summaries}, indent=2))
    if not all(checks.values()):
        raise SystemExit("registered directed wakeup criteria failed; preserve raw record")


if __name__ == "__main__":
    main()
