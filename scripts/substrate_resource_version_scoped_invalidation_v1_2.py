#!/usr/bin/env python3
"""Paired global/scoped resource-version invalidation scale panel."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_RESOURCE_VERSION_SCOPED_INVALIDATION_V1_2_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_resource_version_scoped_invalidation_v1_2.py"
LOCK = ROOT / "evaluation/substrate_capability/resource_version_scoped_invalidation_v1_2_lock_20260928.json"
RAW = ROOT / "evaluation/reports/resource_version_scoped_invalidation_v1_2_20260928.json"
SIZES = (4, 16, 64)
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "substrate/seed_loader.py", "seeds/can_native_reimplementation.json",
    "scripts/substrate_resource_version_scoped_invalidation_v1_2.py",
    "scripts/analyze_resource_version_scoped_invalidation_v1_2.py",
    "docs/research/engine_substrate/SUBSTRATE_RESOURCE_VERSION_SCOPED_INVALIDATION_V1_2_PREREG_20260928.md",
)


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


def build_fixture(n_frames: int, scoped: bool) -> dict:
    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only
    from substrate_rs import Lit, Substrate, Term, _native

    _native.clear_tool_handlers()
    s = Substrate()
    inner = s._inner
    seed = json.loads((ROOT / "seeds/can_native_reimplementation.json").read_text())
    boot = inner.load_seed_manifest(engine_rules_only(seed))
    if boot.get("rules_skipped"):
        raise RuntimeError(f"CAN vocabulary seed rejected rules: {boot['rules_skipped']}")

    callback_log: list[dict] = []
    temp = tempfile.TemporaryDirectory(prefix="resource-version-scope-")
    resource_dir = Path(temp.name)
    revisions = []
    for i in range(n_frames):
        rev0, rev1 = f"r{i}_v0", f"r{i}_v1"
        (resource_dir / f"{rev0}.txt").write_text("0", encoding="utf-8")
        (resource_dir / f"{rev1}.txt").write_text("0", encoding="utf-8")
        revisions.append((rev0, rev1))

    def handler(revision):
        rev = str(revision)
        content = (resource_dir / f"{rev}.txt").read_text(encoding="utf-8")
        callback_log.append({"revision": rev, "value": content})
        return content

    _native.register_tool_handler("resource_revision_value", handler)
    mts, sources, targets = [], [], []
    for i in range(n_frames):
        mt = inner.add_node("Microtheory", {"name": f"mt_{i}"})
        x = inner.add_node("Concept", {"name": f"source_{i}", "resource_rev": revisions[i][0], "state": 0.0})
        y = inner.add_node("Concept", {"name": f"target_{i}", "state": 0.0})
        inner.add_edge_unchecked(mt, "has_concept", x, {})
        inner.add_edge_unchecked(mt, "has_concept", y, {})
        inner.add_edge_unchecked(x, "trigger", y, {})
        mts.append(mt); sources.append(x); targets.append(y)

    tool = Term("UseTool", tool="resource_revision_value", args=[
        Term("Attr", node=Term("Var", name="x"), key="resource_rev")
    ])
    predicate = Term("Eq", a=tool, b=Lit("1"))
    custom_idx = inner.add_rule({
        "name": "resource_revision_guard", "match": [["x", "trigger", "y"]],
        "where": predicate.to_dict(), "effects": [["set_attr", "y", "accepted", 1]],
    })
    access = inner.rule_access_sets()[custom_idx]

    def settle(label: str, fn) -> dict:
        callback_log.clear()
        before = int(_native.tool_fire_count())
        started = time.perf_counter_ns()
        progress = int(fn())
        elapsed = time.perf_counter_ns() - started
        fire_delta = int(_native.tool_fire_count()) - before
        graph_now = inner.graph_to_dict()
        attrs_now = {int(n["id"]): n.get("attrs", {}) for n in graph_now.get("nodes", [])}
        phase_frames = [
            {"frame": j, "revision": attrs_now.get(src.value, {}).get("resource_rev"),
             "accepted": attrs_now.get(dst.value, {}).get("accepted") == 1}
            for j, (src, dst) in enumerate(zip(sources, targets))
        ]
        return {"label": label, "progress": progress, "elapsed_ns": elapsed,
                "callback_count": len(callback_log), "native_fire_delta": fire_delta,
                "callback_log": list(callback_log), "frames": phase_frames}

    initial = settle("initial_full_closure", lambda: inner.run_rules(100_000))
    # Change the currently referenced resource for frame 0 without changing graph state.
    (resource_dir / f"{revisions[0][0]}.txt").write_text("1", encoding="utf-8")
    external_only = settle("resource_changed_no_graph_change", lambda: inner.run_rules(100_000))
    # Publish revision 1, then explicitly update only frame 0's graph revision fact.
    (resource_dir / f"{revisions[0][1]}.txt").write_text("1", encoding="utf-8")
    inner.set_attr(sources[0], "resource_rev", revisions[0][1])
    if scoped:
        update = settle("revision_fact_scoped_settle", lambda: inner.run_rules_scoped(100_000, False, mts[0]))
    else:
        update = settle("revision_fact_global_settle", lambda: inner.run_rules(100_000))

    graph = inner.graph_to_dict()
    attr_by_id = {int(n["id"]): n.get("attrs", {}) for n in graph.get("nodes", [])}
    frame_projection = [
        {"frame": j, "revision": attr_by_id.get(src.value, {}).get("resource_rev"),
         "accepted": attr_by_id.get(dst.value, {}).get("accepted") == 1}
        for j, (src, dst) in enumerate(zip(sources, targets))
    ]
    static = {"reads": sorted(map(str, access[3])), "reads_any": bool(access[6])}
    _native.clear_tool_handlers()
    temp.cleanup()
    return {"n_frames": n_frames, "arm": "scoped" if scoped else "global",
            "initial": initial, "external_only": external_only, "revision_update": update,
            "frames": frame_projection, "static_access": static,
            "resource_revisions": revisions}


def worker(worker_id: int) -> dict:
    started = lock_inputs()
    if json.loads(LOCK.read_text())["locked_inputs"] != started:
        raise RuntimeError("worker source/native lock mismatch")
    cells = []
    for size in SIZES:
        # Fresh independently built paired graph per execution arm.
        cells.append(build_fixture(size, scoped=False))
        cells.append(build_fixture(size, scoped=True))
    return {"worker_id": worker_id, "pid": os.getpid(), "python": sys.version,
            "platform": platform.platform(), "started_inputs": started, "cells": cells}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int)
    ap.add_argument("--write-lock", action="store_true")
    args = ap.parse_args()
    if args.write_lock:
        if LOCK.exists():
            raise SystemExit(f"refusing to overwrite lock {LOCK}")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"lock_id": "resource_version_scoped_invalidation_v1_2_20260928",
                                    "locked_inputs": lock_inputs(), "sizes": SIZES, "workers": 3}, indent=2, sort_keys=True) + "\n")
        print(str(LOCK.relative_to(ROOT))); return
    if args.worker is not None:
        print(json.dumps(worker(args.worker), sort_keys=True)); return
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite capture {RAW}")
    lock = json.loads(LOCK.read_text())
    if lock_inputs() != lock["locked_inputs"]:
        raise SystemExit("source/native lock mismatch")
    runs = []
    for worker_id in range(1, 4):
        argv = [sys.executable, str(Path(__file__).resolve()), "--worker", str(worker_id)]
        proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(f"worker {worker_id} failed: {proc.stderr[-2000:]}")
        runs.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    payload = {"run_id": "resource_version_scoped_invalidation_v1_2_20260928",
               "protocol_sha256": sha(PROTOCOL), "analyzer_sha256": sha(ANALYZER),
               "lock_sha256": sha(LOCK), "locked_inputs": lock["locked_inputs"],
               "sizes": list(SIZES), "runs": runs,
               "claim_boundary": "Three fresh workers, N=4/16/64, paired global and caller-selected per-Microtheory closure. Measures callback work, result parity, and descriptive timing for one authored rule family. No automatic resource watcher or natural frame distribution is tested."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("x", encoding="utf-8") as f:
        f.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "cells_per_worker": len(runs[0]["cells"]), "raw": str(RAW.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
