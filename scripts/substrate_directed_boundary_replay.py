#!/usr/bin/env python3
"""Repeat directed boundary mutations against full CAN rule rescans."""
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
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_DIRECTED_BOUNDARY_REPLAY_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/directed_boundary_replay_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_directed_boundary_replay_20260925.json"
BASE = ROOT / "scripts/substrate_can_boundary_mutation_matrix_v1_1.py"
SEED = ROOT / "seeds/can_native_reimplementation.json"
N = 12
BOUNDARY_SRC, BOUNDARY_TGT = 7, 8
SEQUENCE = ("delete", "insert_075", "replace_m075", "replace_075") * 3
POLICIES = ("full", "event", "omission")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("directed_boundary_base", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the locked mutation reference helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fresh_graph(sr, manifest, base):
    fields = [0.0] * N
    fields[-1] = 1.0
    weights = {(i, i + 1): 0.75 for i in range(N - 1)}
    return base.build(sr, manifest, N, fields, weights), fields, weights


def apply_action(outer, nodes, weights, action):
    key = (BOUNDARY_SRC, BOUNDARY_TGT)
    src, tgt = nodes[key[0]], nodes[key[1]]
    if action == "delete":
        removed = outer.remove_edge(src, "causal_influence", tgt)
        if not removed:
            raise RuntimeError("directed boundary edge absent at deletion")
        weights.pop(key)
    else:
        value = {"insert_075": 0.75, "replace_m075": -0.75,
                 "replace_075": 0.75}[action]
        if key in weights:
            outer.remove_edge(src, "causal_influence", tgt)
        outer.add_edge_unchecked(src, "causal_influence", tgt, {"weight": value})
        weights[key] = value
    return {BOUNDARY_SRC // 4}


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
        raise RuntimeError("expected exactly one 3-state update rule")
    graph, fields, weights = fresh_graph(sr, manifest, base)
    outer, inner, mts, nodes, frames, active = graph
    initial_steps, initial_complete, initial_rounds = base.settle_all(inner, mts)
    if not initial_complete:
        raise RuntimeError("starting full graph failed to settle")
    initial_state = base.state_vector(inner, nodes, active)
    steps = []
    if policy == "omission":
        action = "delete"
        apply_action(outer, nodes, weights, action)
        state = base.state_vector(inner, nodes, active)
        residual = sum(base.residuals(inner, nodes, active, weights))
        return {"policy": policy, "initial_state": initial_state,
                "action": action, "state_after_omission": state,
                "residual_count": residual,
                "provenance": _provenance(_native, engine_provenance)}

    for index, action in enumerate(SEQUENCE):
        before = base.state_vector(inner, nodes, active)
        seed_frames = apply_action(outer, nodes, weights, action)
        if policy == "event":
            moved, complete, turns = base.settle_event(
                inner, mts, nodes, frames, active, weights, seed_frames)
        else:
            moved, complete, turns = base.settle_all(inner, mts)
        state = base.state_vector(inner, nodes, active)
        residual = sum(base.residuals(inner, nodes, active, weights))
        steps.append({"sequence_index": index, "action": action,
                      "directly_notified_frames": sorted(seed_frames),
                      "steps": moved, "turns": turns, "complete": complete,
                      "before": before, "after": state,
                      "changed": before != state, "residual_count": residual,
                      "weights_after": [[a, b, w] for (a, b), w in sorted(weights.items())]})
    return {"policy": policy,
            "initial_settlement": {"steps": initial_steps, "complete": initial_complete,
                                   "rounds": initial_rounds},
            "initial_state": initial_state, "sequence": steps,
            "all_complete": all(x["complete"] for x in steps),
            "all_residuals_zero": all(x["residual_count"] == 0 for x in steps),
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
        print(f"{policy}: " + ("residuals=" + str([s["residual_count"] for s in records[policy].get("sequence", [])])
                               if policy != "omission" else "omission_residual=" + str(records[policy]["residual_count"])),
              flush=True)
    full, event = records["full"]["sequence"], records["event"]["sequence"]
    checks = {
        "sequence_has_12_actions": len(full) == len(event) == len(SEQUENCE) == 12,
        "full_event_action_parity": all(a["action"] == b["action"] and a["after"] == b["after"]
                                         for a, b in zip(full, event)),
        "all_full_event_checkpoints_complete": records["full"]["all_complete"] and records["event"]["all_complete"],
        "all_full_event_residuals_zero": records["full"]["all_residuals_zero"] and records["event"]["all_residuals_zero"],
        "mutation_effects_observed": all(a["changed"] for a in full),
        "omission_control_sensitive": records["omission"]["residual_count"] > 0,
    }
    payload = {"schema_version": 1, "run_id": "directed-boundary-replay-20260925-v1",
               "claim_boundary": "12 repeated directed edge mutations on a synthetic 12-node path; not natural prevalence or native notifications",
               "locked_inputs": locked, "lock_sha256": sha(LOCK),
               "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "configuration": {"nodes": N, "frame_size": 4, "boundary": [BOUNDARY_SRC, BOUNDARY_TGT],
                                 "sequence": SEQUENCE},
               "checks": checks, "omission_control": records["omission"],
               "full": records["full"], "event": records["event"]}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("directed boundary replay gate failed; preserve raw record")


if __name__ == "__main__":
    main()
