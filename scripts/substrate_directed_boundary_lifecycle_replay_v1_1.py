#!/usr/bin/env python3
"""Combine repeated directed boundary changes with node birth/deletion."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_DIRECTED_BOUNDARY_LIFECYCLE_REPLAY_V1_1_AMENDMENT_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/directed_boundary_lifecycle_replay_v1_1_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_directed_boundary_lifecycle_replay_v1_1_20260925.json"
BASE = ROOT / "scripts/substrate_can_boundary_mutation_matrix_v1_1.py"
SEED = ROOT / "seeds/can_native_reimplementation.json"
N = 12
FRAME_SIZE = 4
BOUNDARY = (7, 8)
POLICIES = ("full", "event", "omission")
SEQUENCE = ("delete_edge", "insert_positive", "replace_negative", "replace_positive",
            "birth_node", "delete_node") * 3
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("directed_lifecycle_base", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load locked CAN mutation helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fresh_graph(sr, manifest, base):
    fields = [0.0] * N
    fields[-1] = 1.0
    weights = {(i, i + 1): 0.75 for i in range(N - 1)}
    return base.build(sr, manifest, N, fields, weights), fields, weights


def apply_action(outer, inner, mts, nodes, frames, active, fields, weights, action):
    src, tgt = BOUNDARY
    owner = src // FRAME_SIZE
    key = (src, tgt)
    if action == "delete_edge":
        if not outer.remove_edge(nodes[src], "causal_influence", nodes[tgt]):
            raise RuntimeError("expected directed boundary edge to exist")
        weights.pop(key)
    elif action in ("insert_positive", "replace_negative", "replace_positive"):
        if key in weights:
            outer.remove_edge(nodes[src], "causal_influence", nodes[tgt])
        value = -0.75 if action == "replace_negative" else 0.75
        outer.add_edge_unchecked(nodes[src], "causal_influence", nodes[tgt], {"weight": value})
        weights[key] = value
    elif action == "birth_node":
        new_index = len(nodes)
        node = inner.add_node("Concept", {
            "name": f"lifecycle_{new_index}", "state": 0.0,
            "external_field": -1.0, "identity_field": 0.0,
        })
        outer.add_edge_unchecked(mts[2], "has_concept", node, {})
        nodes.append(node)
        frames.append(2)
        active.append(True)
        fields.append(-1.0)
        weights[(11, new_index)] = 0.75
        outer.add_edge_unchecked(nodes[11], "causal_influence", node, {"weight": 0.75})
    elif action == "delete_node":
        doomed = len(nodes) - 1
        if not active[doomed]:
            raise RuntimeError("last lifecycle node is already inactive")
        if not inner.remove_node(nodes[doomed]):
            raise RuntimeError("expected lifecycle node to be removed")
        active[doomed] = False
        fields[doomed] = None
        for edge in [edge for edge in weights if doomed in edge]:
            weights.pop(edge)
    else:
        raise ValueError(action)
    # Boundary edge updates directly affect their source reader frame;
    # node lifecycle updates directly affect the frame that owns that node.
    return {2 if action in {"birth_node", "delete_node"} else owner}


def run_worker(policy: str) -> dict:
    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only
    from substrate_rs import _native
    from domains.engine_provenance import engine_provenance

    base = load_base()
    seed_doc = json.loads(SEED.read_text())
    manifest = dict(engine_rules_only(seed_doc))
    manifest["rules"] = [r for r in manifest.get("rules", [])
                         if r.get("name") == "can_native_update_3state"]
    if len(manifest["rules"]) != 1:
        raise RuntimeError("expected only the native 3-state CAN update rule")
    graph, fields, weights = fresh_graph(sr, manifest, base)
    outer, inner, mts, nodes, frames, active = graph
    initial_steps, initial_complete, initial_rounds = base.settle_all(inner, mts, CAP)
    if not initial_complete:
        raise RuntimeError("initial graph failed to settle")
    initial_state = base.state_vector(inner, nodes, active)
    initial_fields = base.effective_fields(inner, nodes, active)
    if policy == "omission":
        apply_action(outer, inner, mts, nodes, frames, active, fields, weights, "delete_edge")
        state = base.state_vector(inner, nodes, active)
        residual = sum(base.residuals(inner, nodes, active, weights))
        return {"policy": policy, "initial_state": initial_state,
                "initial_fields": initial_fields, "state_after_omission": state,
                "fields_after_omission": base.effective_fields(inner, nodes, active),
                "weights_after_omission": [[a, b, w] for (a, b), w in sorted(weights.items())],
                "residual_count": residual,
                "provenance": _provenance(_native, engine_provenance)}
    checkpoints = []
    for index, action in enumerate(SEQUENCE):
        before = base.state_vector(inner, nodes, active)
        before_active = list(active)
        seed_frames = apply_action(outer, inner, mts, nodes, frames, active, fields, weights, action)
        if policy == "event":
            steps, complete, turns = base.settle_event(
                inner, mts, nodes, frames, active, weights, seed_frames, CAP)
        else:
            steps, complete, turns = base.settle_all(inner, mts, CAP)
        after = base.state_vector(inner, nodes, active)
        effective = base.effective_fields(inner, nodes, active)
        residual = sum(base.residuals(inner, nodes, active, weights))
        checkpoints.append({
            "index": index, "action": action, "notified_frames": sorted(seed_frames),
            "steps": steps, "turns": turns, "complete": complete,
            "before": before, "before_active": before_active,
            "after": after, "active": list(active),
            "effective_fields": effective,
            "weights_after": [[a, b, w] for (a, b), w in sorted(weights.items())],
            "changed": before != after or before_active != active,
            "residual_count": residual,
        })
    return {"policy": policy,
            "initial_settlement": {"steps": initial_steps, "complete": initial_complete,
                                   "rounds": initial_rounds},
            "initial_state": initial_state, "initial_fields": initial_fields,
            "checkpoints": checkpoints,
            "all_complete": all(c["complete"] for c in checkpoints),
            "all_residuals_zero": all(c["residual_count"] == 0 for c in checkpoints),
            "all_mutations_effective": all(c["changed"] for c in checkpoints),
            "provenance": _provenance(_native, engine_provenance)}


def _provenance(native, engine_provenance):
    path = Path(native.__file__).resolve()
    return {"python": sys.version, "platform": platform.platform(),
            "native_extension_path": str(path), "native_extension_sha256": sha(path),
            "engine_provenance": engine_provenance()}


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(run_worker(sys.argv[2]), sort_keys=True)); return
    locked = {
        "preregistration_sha256": sha(PREREG), "runner_sha256": sha(Path(__file__).resolve()),
        "base_runner_sha256": sha(BASE), "seed_sha256": sha(SEED),
        "rewrite_sha256": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        "substrate_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
    }
    if len(sys.argv) == 2 and sys.argv[1] == "--lock":
        print(json.dumps(locked, indent=2, sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing lock or locked source inputs changed")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit("native build stale:\n" + stale)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    records = {}
    for policy in POLICIES:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                               "--worker", policy], cwd=ROOT, env=env,
                              text=True, capture_output=True, check=True)
        records[policy] = json.loads(proc.stdout.strip())
        if policy != "omission":
            print(f"{policy}: checkpoints={len(records[policy]['checkpoints'])} "
                  f"zero_residual={records[policy]['all_residuals_zero']}", flush=True)
        else:
            print(f"omission: residual={records[policy]['residual_count']}", flush=True)
    full = records["full"]["checkpoints"]
    event = records["event"]["checkpoints"]
    expected_notifications = [
        [2] if action in {"birth_node", "delete_node"} else [1]
        for action in SEQUENCE
    ]
    checks = {
        "sequence_has_18_actions": len(full) == len(event) == len(SEQUENCE) == 18,
        "action_and_state_parity_every_checkpoint": all(
            a["action"] == b["action"] and a["after"] == b["after"] and a["active"] == b["active"]
            for a, b in zip(full, event)),
        "all_full_event_arms_complete": records["full"]["all_complete"] and records["event"]["all_complete"],
        "all_full_event_residuals_zero": records["full"]["all_residuals_zero"] and records["event"]["all_residuals_zero"],
        "all_mutations_change_state_or_active_set": records["full"]["all_mutations_effective"] and records["event"]["all_mutations_effective"],
        "event_notification_frames_match_mutation_owners": [c["notified_frames"] for c in event] == expected_notifications,
        "omission_control_sensitive": records["omission"]["residual_count"] > 0,
    }
    payload = {
        "schema_version": 1,
        "run_id": "directed-boundary-lifecycle-replay-20260925-v1.1",
        "claim_boundary": "18 repeated directed edge/lifecycle mutations on a synthetic 12-node path; not natural prevalence or native notifications",
        "locked_inputs": locked, "lock_sha256": sha(LOCK),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "configuration": {"nodes_initial": N, "frame_size": FRAME_SIZE,
                          "boundary_edge": BOUNDARY, "sequence": SEQUENCE},
        "checks": checks, "omission_control": records["omission"],
        "full": records["full"], "event": records["event"],
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("directed lifecycle replay gate failed; preserve raw record")


if __name__ == "__main__":
    main()
