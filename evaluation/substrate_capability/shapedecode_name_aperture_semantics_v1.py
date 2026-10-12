#!/usr/bin/env python3
"""Locked paired semantic controls for the ShapeDecode name cache."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.crossframe_world import CrossFrameWorld
from substrate_rs import Attr, Lit, MaxOver, SetT, Term, Var
from substrate_rs import _native

BASE_RUNNER = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_baseline_v1.py"
SPEC = importlib.util.spec_from_file_location("shape_baseline", BASE_RUNNER)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BASE)

RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SHAPEDECODE_NAME_APERTURE_SEMANTICS_V1_PREREG_20261005.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_shapedecode_name_aperture_semantics_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_semantics_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/shapedecode_name_aperture_semantics_v1_20261005.json"
CONTROLS = ("unique", "case_varied", "exact_duplicate", "casefold_duplicate",
            "scope_none_value", "scope_empty", "scope_order")
MODES = ("scan", "cached")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def manifest() -> dict:
    return {"baseline_sources": BASE.source_manifest(),
            "runner_sha256": sha(RUNNER), "protocol_sha256": sha(PROTOCOL),
            "analyzer_sha256": sha(ANALYZER)}


def cases() -> list[dict]:
    return [{"control": control, "mode": mode, "id": f"{control}_{mode}"}
            for control in CONTROLS for mode in MODES]


def worker(case: dict, locked_manifest: dict) -> dict:
    before = manifest()
    if before != locked_manifest:
        raise RuntimeError("worker source manifest differs from lock")
    _native.Substrate.runtime_shape_codebook_cache_set_enabled(case["mode"] == "cached")
    try:
        world = CrossFrameWorld(arm=False)
        tiles = [BASE.np.random.default_rng(7123 + i).integers(0, 4, size=(6, 6), dtype=BASE.np.int64)
                 for i in range(16)]
        world.hold_codebook(tiles, list(range(16)))
        held = []
        for nid in world.s.nodes("ShapeSignature"):
            node = world.s.node(nid)
            name = node["attrs"].get("name")
            if isinstance(name, str) and name.startswith("r"):
                held.append((nid, name))
        if case["control"] == "case_varied":
            for nid, name in held:
                if name == "r00":
                    world.s.set_attr(nid, "name", "R00")
        elif case["control"] == "exact_duplicate":
            world.s.add_node("ShapeSignature", {
                "name": "r00", "signature": json.dumps(BASE.sig_of(tiles[1])),
                "kind": "duplicate", "faculty": "duplicate"})
        elif case["control"] == "casefold_duplicate":
            for nid, name in held:
                if name == "r00":
                    world.s.set_attr(nid, "name", "R00")
                    break
            world.s.add_node("ShapeSignature", {
                "name": "r00", "signature": json.dumps(BASE.sig_of(tiles[1])),
                "kind": "duplicate", "faculty": "duplicate"})
        elif case["control"] == "scope_order":
            for nid, name in held:
                if name == "r01":
                    world.s.set_attr(nid, "signature", json.dumps(BASE.sig_of(tiles[0])))

        obs = world.present(tiles[0], truth=0, tag=case["id"])
        if case["control"] in ("scope_none_value", "scope_empty", "scope_order"):
            scope = (Attr(Var("obs"), "missing_scope") if case["control"] == "scope_none_value"
                     else SetT([Lit("r01"), Lit("r00")]) if case["control"] == "scope_order"
                     else SetT([]))
            term = Term("ShapeDecode", goal=Attr(Var("obs"), "signature"),
                        codebook_type="ShapeSignature", codebook_scope=scope,
                        field="ordered_parts" if case["control"] == "scope_order" else "covered_count",
                        beam=1, max_steps=1, cand_k=1)
            result = world.s.evaluate(term, {"obs": obs})
        else:
            scoped_decode = Term("ShapeDecode", goal=Attr(Var("obs"), "signature"),
                                 codebook_type="ShapeSignature",
                                 codebook_scope=SetT([Attr(Var("sig"), "name")]),
                                 field="covered_count", beam=1, max_steps=1, cand_k=1)
            term = MaxOver(Term("NodesOfType", node_type="ShapeSignature"), "sig",
                           scoped_decode, default=Lit(-1))
            result = world.s.evaluate(term, {"obs": obs})
        after = manifest()
        return {"case": case, "pid": os.getpid(), "source_before": before,
                "source_after": after, "source_stable": before == after,
                "result": result, "held_name_count": len(held)}
    finally:
        _native.Substrate.runtime_shape_codebook_cache_set_enabled(True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    locked = {"manifest": manifest(), "cases": cases(), "python": sys.version,
              "platform": platform.platform(), "schedule_seed": 20261005}
    if args.worker:
        incoming = json.loads(sys.stdin.read())
        lock = json.loads(LOCK.read_text())
        print(json.dumps(worker(incoming, lock["manifest"]), sort_keys=True, default=str))
        return 0
    if args.lock:
        LOCK.write_text(json.dumps(locked, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"lock": str(LOCK.relative_to(ROOT)), "cases": len(cases())}))
        return 0
    if not LOCK.exists() or json.loads(LOCK.read_text()) != locked:
        raise SystemExit("missing or stale lock; run --lock after source/protocol edits")
    schedule = list(locked["cases"])
    random.Random(locked["schedule_seed"]).shuffle(schedule)
    env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}
    rows, failures = [], []
    for case in schedule:
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker"],
                              input=json.dumps(case), cwd=ROOT, env=env,
                              text=True, capture_output=True)
        try:
            rows.append(json.loads(proc.stdout))
        except Exception:
            rows.append({"case": case, "worker_error": "invalid_json",
                         "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]})
        if proc.returncode:
            failures.append({"case": case, "returncode": proc.returncode,
                             "stderr_tail": proc.stderr[-2000:]})
    capture = {"schema": "ShapeDecodeNameApertureSemanticsV1Capture",
               "run_id": "shapedecode-name-aperture-semantics-v1-20261005",
               "lock_path": str(LOCK.relative_to(ROOT)), "lock_sha256": sha(LOCK),
               "manifest": locked["manifest"], "rows": rows, "process_failures": failures}
    OUT.write_text(json.dumps(capture, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"capture": str(OUT.relative_to(ROOT)), "workers": len(rows),
                      "failures": len(failures)}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
