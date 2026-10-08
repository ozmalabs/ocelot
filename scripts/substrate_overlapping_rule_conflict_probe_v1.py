#!/usr/bin/env python3
"""Conflict, insertion-order, and cycle-detection probe for overlapping rules."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_OVERLAPPING_RULE_CONFLICT_PROBE_V1_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_overlapping_rule_conflict_probe_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/overlapping_rule_conflict_probe_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/overlapping_rule_conflict_probe_v1_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_overlapping_rule_conflict_probe_v1.py",
    "scripts/analyze_overlapping_rule_conflict_probe_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_OVERLAPPING_RULE_CONFLICT_PROBE_V1_PREREG_20260928.md",
)
ORDERS = ("A_then_B", "B_then_A")
DETECTION = (False, True)
MAX_STEPS = 12


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    ext = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_PATHS},
        "native_extension_path": str(ext), "native_extension_sha256": sha(ext),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
    }


def cell(order: str, detect_cycles: bool) -> dict:
    from substrate_rs import Lit, Substrate, Term, _native
    _native.clear_tool_handlers()
    calls = []

    def handler(arg):
        calls.append(str(arg))
        return "yes"

    _native.register_tool_handler("always_true", handler)
    sub = Substrate(); inner = sub._inner
    x = inner.add_node("ConflictProbe", {})
    y = inner.add_node("ConflictProbe", {})
    inner.add_edge_unchecked(x, "trigger", y, {})
    where = Term("Eq", a=Term("UseTool", tool="always_true", args=[Lit("same")]), b=Lit("yes")).to_dict()
    rules = {
        "A": {"name": "conflict_A", "match": [["x", "trigger", "y"]], "where": where,
              "effects": [["set_attr_if_different", "y", "accepted", 1]]},
        "B": {"name": "conflict_B", "match": [["x", "trigger", "y"]], "where": where,
              "effects": [["set_attr_if_different", "y", "accepted", 2]]},
    }
    sequence = ("A", "B") if order == "A_then_B" else ("B", "A")
    for label in sequence:
        inner.add_rule(rules[label])
    report = inner.run_rules_report(MAX_STEPS, detect_cycles)
    graph = inner.graph_to_dict()
    node_attrs = {int(n["id"]): n.get("attrs", {}) for n in graph.get("nodes", [])}
    _native.clear_tool_handlers()
    return {"order": order, "detect_cycles": detect_cycles, "rule_sequence": sequence,
            "termination": dict(report), "callback_count": len(calls), "callback_arguments": calls,
            "final_accepted": node_attrs.get(y.value, {}).get("accepted"), "graph": graph}


def worker(worker_id: int) -> dict:
    started = lock_inputs()
    if json.loads(LOCK.read_text())["locked_inputs"] != started:
        raise RuntimeError("worker source/native lock mismatch")
    cells = [cell(order, detect) for order in ORDERS for detect in DETECTION]
    return {"worker_id": worker_id, "pid": os.getpid(), "python": sys.version,
            "platform": platform.platform(), "started_inputs": started, "cells": cells}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int)
    ap.add_argument("--write-lock", action="store_true")
    args = ap.parse_args()
    if args.write_lock:
        if LOCK.exists(): raise SystemExit(f"refusing to overwrite lock {LOCK}")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"lock_id": "overlapping_rule_conflict_probe_v1_20260928",
                                    "locked_inputs": lock_inputs(), "workers": 3,
                                    "orders": ORDERS, "detect_cycles": DETECTION,
                                    "max_steps": MAX_STEPS}, indent=2, sort_keys=True) + "\n")
        print(str(LOCK.relative_to(ROOT))); return
    if args.worker is not None:
        print(json.dumps(worker(args.worker), sort_keys=True)); return
    if RAW.exists(): raise SystemExit(f"refusing to overwrite capture {RAW}")
    lock = json.loads(LOCK.read_text())
    if lock_inputs() != lock["locked_inputs"]: raise SystemExit("source/native lock mismatch")
    runs = []
    for wid in range(1, 4):
        argv = [sys.executable, str(Path(__file__).resolve()), "--worker", str(wid)]
        cp = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
        if cp.returncode: raise SystemExit(f"worker {wid} failed: {cp.stderr[-2000:]}")
        runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
    raw = {"run_id": "overlapping_rule_conflict_probe_v1_20260928",
           "locked_inputs": lock["locked_inputs"], "protocol_sha256": sha(PROTOCOL),
           "analyzer_sha256": sha(ANALYZER), "lock_sha256": sha(LOCK),
           "max_steps": MAX_STEPS, "runs": runs,
           "claim_boundary": "One binding, two identical predicates, opposing attribute effects. Measures insertion order and structured cycle/budget termination only for this deterministic fixture."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("x", encoding="utf-8") as f: f.write(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "cells_per_worker": len(runs[0]["cells"]), "raw": str(RAW.relative_to(ROOT))}))


if __name__ == "__main__": main()
