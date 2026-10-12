#!/usr/bin/env python3
"""Locked scoped write-owner matrix against the full graph snapshot oracle."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_NATIVE_SCOPED_OWNER_EFFECT_MATRIX_PREREG_20260926.md"
LOCK = ROOT / "evaluation/substrate_capability/native_scoped_owner_effect_matrix_v1_2_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_native_scoped_owner_effect_matrix_v1_20260926.json"
CASES = ("shared_add_edge", "shared_del_edge", "shared_set_attr", "owned_node_birth", "owned_node_deletion")
SIZES = (2, 4, 8)
REPS = 2
CAP = 20_000


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def worker(case: str, size: int, rep: int, arm: str) -> dict:
    from substrate_rs import Substrate, Attr, Eq, Lit, Var
    from substrate_rs.ext import add_rule
    from substrate_rs import _native

    s = Substrate()
    controller = s.add_node("Microtheory", {"name": "controller"})
    trigger = s.add_node("Trigger", {"active": 1.0})
    s.add_edge_unchecked(controller, "has_concept", trigger)
    frames = [s.add_node("Microtheory", {"name": f"frame_{i}"}) for i in range(size)]
    src = s.add_node("Concept", {"value": 0.0})
    tgt = s.add_node("Concept", {"value": 0.0})
    s.add_edge_unchecked(frames[0], "has_concept", src)
    s.add_edge_unchecked(frames[-1], "has_concept", tgt)
    s.add_edge_unchecked(trigger, "writes", src)
    s.add_edge_unchecked(src, "targets", tgt)
    effects = []
    if case == "shared_add_edge":
        effects = [["add_edge", "src", "derived", "tgt", {}]]
    elif case == "shared_del_edge":
        s.add_edge_unchecked(src, "derived", tgt)
        effects = [["del_edge", "src", "derived", "tgt"]]
    elif case == "shared_set_attr":
        effects = [["set_attr", "src", "value", 9.0]]
    elif case == "owned_node_birth":
        effects = [["add_node", "born", "Witness", {}], ["add_edge", "controller", "has_concept", "born", {}]]
    elif case == "owned_node_deletion":
        effects = [["del_node", "src"]]
    else:
        raise ValueError(case)
    effects.append(["set_attr", "trigger", "active", 0.0])
    add_rule(s._inner, f"owner_matrix_{case}",
             [("controller", "has_concept", "trigger"), ("trigger", "writes", "src"), ("src", "targets", "tgt")],
             effects, where=Eq(Attr(Var("trigger"), "active"), Lit(1.0)))
    if case == "shared_add_edge" and s._inner.has_edge(src, "derived", tgt):
        raise RuntimeError("add-edge precondition invalid")

    method = s._inner.run_rules_scoped_delta_report if arm == "scoped" else s._inner.run_rules_snapshot_delta_report
    scope = controller if arm == "scoped" else None
    report = method(scope, CAP, False) if scope is not None else method(CAP, False)
    if arm == "scoped":
        status = "scoped"
        progress = int(report["progress_steps"])
        nodes = list(map(int, report["affected_nodes"]))
        edges = [tuple((int(e[0]), str(e[1]), int(e[2]))) for e in report["affected_edges"]]
        owners = list(map(int, report["affected_microtheories"]))
        capped = bool(report.get("hit_progress_budget", False))
        deferred = bool(report.get("deferred_effects_pending", False))
        exact = False
    else:
        status = report["status"]
        progress = int(report["progress_steps"])
        nodes = list(map(int, report["affected_nodes"]))
        edges = [tuple((int(e[0]), str(e[1]), int(e[2]))) for e in report["affected_edges"]]
        owners = list(map(int, report["affected_microtheories"]))
        capped = bool(report.get("hit_progress_budget", False))
        deferred = bool(report.get("deferred_effects_pending", False))
        exact = bool(report.get("exact_graph_state_diff", False))
    id_names = {int(controller.value): "controller", **{int(x.value): f"frame_{i}" for i, x in enumerate(frames)}}
    owner_names = sorted(id_names[x] for x in owners if x in id_names)
    if arm == "scoped":
        terminal = s._inner.run_rules_scoped_delta_report(controller, CAP, False)
        terminal_progress = int(terminal["progress_steps"])
        terminal_deferred = bool(terminal["deferred_effects_pending"])
    else:
        terminal = s._inner.run_rules_report(CAP, False)
        terminal_progress = int(terminal["progress_steps"])
        terminal_deferred = False
    state = {
        "src_live": s._inner.has_node(src), "tgt_live": s._inner.has_node(tgt),
        "derived_edge": s._inner.has_edge(src, "derived", tgt),
        "src_value": s.node(src)["attrs"].get("value") if s._inner.has_node(src) else None,
        "trigger_active": s.node(trigger)["attrs"].get("active"),
        "witness_count": sum(s.node(x)["type"] == "Witness" for x in s.nodes()),
    }
    return {"case": case, "size": size, "replicate": rep, "arm": arm,
            "pid": os.getpid(), "status": status, "progress_steps": progress,
            "hit_progress_budget": capped, "deferred_effects_pending": deferred,
            "affected_nodes": nodes, "affected_edges": [list(x) for x in edges],
            "affected_microtheories": owners, "owner_names": owner_names,
            "exact_graph_state_diff": exact, "terminal_progress_steps": terminal_progress,
            "terminal_deferred_effects_pending": terminal_deferred,
            "state": state, "native_extension_sha256": sha(Path(_native.__file__).resolve())}


def locked_inputs() -> dict:
    paths = {
        "protocol": PROTOCOL,
        "runner": Path(__file__).resolve(),
        "analyzer": ROOT / "scripts/analyze_substrate_native_scoped_owner_effect_matrix_v1.py",
        "rewrite": ROOT / "runners/dsl/src/rewrite.rs",
        "substrate": ROOT / "runners/dsl/src/substrate.rs",
        "py_binding": ROOT / "runners/dsl/src/py.rs",
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
    }
    return {k: sha(p) for k, p in paths.items()}


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps(locked_inputs(), indent=2, sort_keys=True)); return
    if len(sys.argv) == 6 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]), sort_keys=True)); return
    lock = locked_inputs()
    if json.loads(LOCK.read_text()) != lock:
        raise SystemExit("locked input mismatch; do not run")
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    jobs = [(c, n, r, a) for c in CASES for n in SIZES for r in range(REPS) for a in ("scoped", "oracle")]
    runs = []
    for case, size, rep, arm in jobs:
        cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", case, str(size), str(rep), arm]
        row = json.loads(subprocess.check_output(cmd, cwd=ROOT, env=env, text=True))
        runs.append(row)
        print(f"{case} n={size} rep={rep} arm={arm} owners={row['owner_names']}", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "run_id": "native-scoped-owner-effect-matrix-v1-20260926",
               "claim_boundary": "five synthetic direct effect shapes; scoped write-owner coverage only",
               "locked_inputs": lock, "matrix": {"cases": CASES, "sizes": SIZES, "repeats": REPS}, "runs": runs}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"raw report: {OUT.relative_to(ROOT)} ({len(runs)} workers)")


if __name__ == "__main__":
    main()
