#!/usr/bin/env python3
"""Rule-order and simultaneous external transition probe for explicit compensation."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_COMPENSATION_ORDER_SIMULTANEOUS_TRANSITIONS_V1_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_compensation_order_simultaneous_transitions_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/compensation_order_simultaneous_transitions_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/compensation_order_simultaneous_transitions_v1_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_compensation_order_simultaneous_transitions_v1.py",
    "scripts/analyze_compensation_order_simultaneous_transitions_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_COMPENSATION_ORDER_SIMULTANEOUS_TRANSITIONS_V1_PREREG_20260928.md",
)
MODES = ("compensating_attr", "retractable_edge")
ORDERS = ("positive_first", "compensator_first")


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


def run_cell(mode: str, order: str) -> dict:
    from substrate_rs import Lit, Substrate, Term, _native
    _native.clear_tool_handlers()
    calls: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="compensation-order-") as td:
        root = Path(td)
        for frame in range(3):
            for rev, value in (("r0", "0"), ("r1", "1"), ("r2", "0")):
                (root / f"{frame}_{rev}.txt").write_text(value, encoding="utf-8")

        def handler(revision):
            frame_s, rev = str(revision).split(":", 1)
            value = (root / f"{frame_s}_{rev}.txt").read_text(encoding="utf-8")
            calls.append({"frame": int(frame_s), "revision": rev, "value": value})
            return value

        _native.register_tool_handler("transition_value", handler)
        sub = Substrate(); inner = sub._inner
        sources, targets = [], []
        for frame in range(3):
            x = inner.add_node("ReplayProbe", {"frame": frame, "resource_rev": f"{frame}:r0"})
            y = inner.add_node("ReplayProbe", {"frame": frame})
            inner.add_edge_unchecked(x, "trigger", y, {})
            sources.append(x); targets.append(y)
        tool = Term("UseTool", tool="transition_value", args=[
            Term("Attr", node=Term("Var", name="x"), key="resource_rev")
        ])
        positive_where = Term("Eq", a=tool, b=Lit("1")).to_dict()
        negative_where = Term("Eq", a=tool, b=Lit("0")).to_dict()
        if mode == "compensating_attr":
            positive_effect = [["set_attr_if_different", "y", "accepted", 1]]
            negative_effect = [["set_attr_if_different", "y", "accepted", 0]]
        else:
            positive_effect = [["add_edge", "x", "accepted", "y", {}]]
            negative_effect = [["del_edge", "x", "accepted", "y"]]
        specs = [
            ("positive", positive_where, positive_effect),
            ("compensator", negative_where, negative_effect),
        ]
        if order == "compensator_first":
            specs.reverse()
        for name, where, effects in specs:
            inner.add_rule({"name": name, "match": [["x", "trigger", "y"]],
                            "where": where, "effects": effects})

        def projection() -> list[dict]:
            g = inner.graph_to_dict()
            attrs = {int(n["id"]): n.get("attrs", {}) for n in g.get("nodes", [])}
            edges = {(int(e["src"]), str(e["type"]), int(e["tgt"])) for e in g.get("edges", [])}
            return [{"frame": i, "revision": attrs[sources[i].value].get("resource_rev"),
                     "accepted_attr": attrs[targets[i].value].get("accepted"),
                     "accepted_edge": (sources[i].value, "accepted", targets[i].value) in edges}
                    for i in range(3)]

        phases = []

        def settle(name: str):
            calls.clear()
            before = int(_native.tool_fire_count())
            progress = int(inner.run_rules(100))
            fire_delta = int(_native.tool_fire_count()) - before
            phases.append({"phase": name, "progress": progress,
                           "callback_count": len(calls), "native_fire_delta": fire_delta,
                           "callback_log": list(calls), "frames": projection()})

        settle("A_initial_all_negative")
        inner.set_attr(sources[0], "resource_rev", "0:r1")
        settle("B_establish_frame0_positive")
        # Simultaneous graph transition: frame 0 positive->negative, frame 1 negative->positive.
        inner.set_attr(sources[0], "resource_rev", "0:r2")
        inner.set_attr(sources[1], "resource_rev", "1:r1")
        settle("C_simultaneous_opposite_transitions")
        _native.clear_tool_handlers()
        return {"mode": mode, "rule_order": order, "phases": phases}


def worker(worker_id: int) -> dict:
    started = lock_inputs()
    if json.loads(LOCK.read_text())["locked_inputs"] != started:
        raise RuntimeError("worker source/native lock mismatch")
    cells = [run_cell(m, o) for m in MODES for o in ORDERS]
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
        LOCK.write_text(json.dumps({"lock_id": "compensation_order_simultaneous_transitions_v1_20260928",
                                    "locked_inputs": lock_inputs(), "workers": 3,
                                    "modes": MODES, "orders": ORDERS}, indent=2, sort_keys=True) + "\n")
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
    raw = {"run_id": "compensation_order_simultaneous_transitions_v1_20260928",
           "locked_inputs": lock["locked_inputs"], "protocol_sha256": sha(PROTOCOL),
           "analyzer_sha256": sha(ANALYZER), "lock_sha256": sha(LOCK), "runs": runs,
           "claim_boundary": "Three fresh workers × two compensation representations × two insertion orders. Measures authored independent transition rules, not arbitrary overlapping effects or automatic truth maintenance."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("x", encoding="utf-8") as f: f.write(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "cells_per_worker": len(runs[0]["cells"]), "raw": str(RAW.relative_to(ROOT))}))


if __name__ == "__main__": main()
