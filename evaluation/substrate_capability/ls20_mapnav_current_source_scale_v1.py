#!/usr/bin/env python3
"""Source-locked held-out scale panel for the ls20 map-navigation task."""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LS20_MAPNAV_CURRENT_SOURCE_SCALE_V1_PREREG_20260928.md"
RUNNER = Path(__file__).resolve()
BENCH_PATH = ROOT / "scripts/arc_ls20_mapnav_measure.py"
SCENARIO_PATH = ROOT / "worlds/arc_ls20_scenario.py"
LOCK_PATH = ROOT / "evaluation/substrate_capability/ls20_mapnav_current_source_scale_v1_lock_20260928.json"
OUT_DIR = ROOT / "evaluation/reports/ls20_mapnav_current_source_scale_v1"
PARTIAL_PATH = OUT_DIR / "partial.json"
CAPTURE_PATH = OUT_DIR / "capture.json"

SPEC = importlib.util.spec_from_file_location("arc_ls20_mapnav_benchmark", BENCH_PATH)
BENCH = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BENCH)

CELLS = [
    {"name": "walled_16_1", "h": 16, "w": 16, "stations": 1, "walls": True, "density": 0.20, "seed": 220200},
    {"name": "walled_16_3", "h": 16, "w": 16, "stations": 3, "walls": True, "density": 0.20, "seed": 220201},
    {"name": "walled_32_1", "h": 32, "w": 32, "stations": 1, "walls": True, "density": 0.20, "seed": 220202},
    {"name": "walled_32_3", "h": 32, "w": 32, "stations": 3, "walls": True, "density": 0.20, "seed": 220203},
    {"name": "open_16_1", "h": 16, "w": 16, "stations": 1, "walls": False, "density": 0.20, "seed": 220204},
]
N_PER_CELL = 30


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_record(path: Path) -> dict:
    b = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(b), "sha256": sha(b)}


def tree_record(path: Path, suffixes: tuple[str, ...]) -> dict:
    h = hashlib.sha256(); n = total = 0
    for f in sorted(p for p in path.rglob("*") if p.is_file() and p.suffix in suffixes):
        raw = f.read_bytes(); rel = f.relative_to(path).as_posix()
        h.update(rel.encode()); h.update(b"\0"); h.update(len(raw).to_bytes(8, "big")); h.update(raw)
        n += 1; total += len(raw)
    return {"path": path.relative_to(ROOT).as_posix(), "suffixes": list(suffixes), "files": n, "bytes": total, "sha256": h.hexdigest()}


def pkg(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def input_lock() -> dict:
    from domains.engine_provenance import build_is_stale
    from substrate.boot_core import CORE_SEEDS
    from substrate.seed_loader import SEED_DIR
    rust_root = ROOT / "runners/dsl/src"
    py_facade = ROOT / "runners/dsl/python/substrate_rs"
    native = py_facade / "_native.abi3.so"
    manifest = py_facade / "_native.build.json"
    current_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    stale = build_is_stale(str(ROOT))
    pending = list(CORE_SEEDS) + ["math_capability_shapes", "self_design_axis", "shape_decode_loop",
                                  "minting_recurrence_ledger", "navigation_modes", "affordance_basis",
                                  "quanta_navigation"]
    seed_ids = set()
    while pending:
        sid = pending.pop()
        if sid in seed_ids:
            continue
        seed_ids.add(sid)
        manifest_path = SEED_DIR / f"{sid}.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"missing seed dependency {sid!r}: {manifest_path}")
        manifest_data = json.loads(manifest_path.read_text())
        pending.extend(str(dep) for dep in manifest_data.get("depends_on", []))
    return {
        "protocol": file_record(PROTOCOL), "runner": file_record(RUNNER),
        "benchmark": file_record(BENCH_PATH), "scenario": file_record(SCENARIO_PATH),
        "source_trees": {
            "domains_python": tree_record(ROOT / "domains", (".py",)),
            "worlds_python": tree_record(ROOT / "worlds", (".py",)),
            "substrate_python": tree_record(ROOT / "substrate", (".py",)),
            "scripts_python": tree_record(ROOT / "scripts", (".py",)),
            "rust_source_and_manifests": tree_record(rust_root, (".rs", ".toml", ".lock")),
            "python_facade": tree_record(py_facade, (".py", ".json")),
        },
        "native_extension": file_record(native), "native_build_manifest": file_record(manifest),
        "native_build_stale_reasons": stale,
        "seed_dependency_closure": {sid: file_record(SEED_DIR / f"{sid}.json") for sid in sorted(seed_ids)},
        "git_head": current_head,
        "runtime": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
                    "numpy": pkg("numpy"), "scipy": pkg("scipy"), "cpu_model": cpu_model()},
        "parameters": {"cells": CELLS, "n_per_cell": N_PER_CELL, "router_order": "quanta first on even index, greedy first on odd index", "budget_steps": 200},
    }


def cpu_model() -> str | None:
    p = Path("/proc/cpuinfo")
    if not p.exists(): return None
    for line in p.read_text(errors="replace").splitlines():
        if line.lower().startswith("model name") and ":" in line:
            return line.split(":", 1)[1].strip()
    return None


def atomic_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    temp.replace(path)


def run_pair(scn: dict, index: int) -> dict:
    order = ("quanta", "greedy") if index % 2 == 0 else ("greedy", "quanta")
    outcomes = {}
    for router in order:
        wall0 = time.perf_counter(); cpu0 = time.process_time()
        result = BENCH.run_episode(scn, "curious", router=router)
        outcomes[router] = {"result": result, "wall_seconds": time.perf_counter() - wall0,
                            "cpu_seconds": time.process_time() - cpu0}
    return {"order": list(order), "outcomes": outcomes}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK_PATH.exists() or PARTIAL_PATH.exists() or CAPTURE_PATH.exists():
            raise SystemExit("refusing to overwrite existing lock or capture")
        lock = input_lock()
        if lock["native_build_stale_reasons"]:
            raise SystemExit(f"native extension stale for locked source: {lock['native_build_stale_reasons'][:8]}")
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(LOCK_PATH, lock)
        print(LOCK_PATH.relative_to(ROOT))
        return

    lock = json.loads(LOCK_PATH.read_text())
    if input_lock() != lock:
        raise SystemExit("source/input lock drift; retain partial capture and do not resume")
    state = json.loads(PARTIAL_PATH.read_text()) if PARTIAL_PATH.exists() else {"next_cell": 0, "cells": []}
    import numpy as np
    import resource
    started_wall = time.perf_counter(); started_cpu = time.process_time()
    for cell_index in range(state["next_cell"], len(CELLS)):
        cell = CELLS[cell_index]
        rng = np.random.default_rng(cell["seed"])
        rows = []
        for episode_index in range(N_PER_CELL):
            scn = BENCH.make_scenario(rng, H=cell["h"], W=cell["w"], n_stations=cell["stations"],
                                      walls=cell["walls"], wall_density=cell["density"])
            pair = run_pair(scn, episode_index)
            row = {"cell": cell["name"], "episode_index": episode_index,
                   "scenario": scn, "pair": pair}
            rows.append(row)
            if (episode_index + 1) % 5 == 0:
                print(f"{cell['name']}: {episode_index + 1}/{N_PER_CELL}", flush=True)
        state["cells"].append({"parameters": cell, "records": rows})
        state["next_cell"] = cell_index + 1
        atomic_json(PARTIAL_PATH, state)
    after = input_lock()
    if after != lock:
        raise SystemExit("post-run source/input lock drift; preserve partial as censored")
    usage = resource.getrusage(resource.RUSAGE_SELF)
    capture = {
        "schema_version": 1, "run_id": "ls20-mapnav-current-source-scale-v1-20260928",
        "capture_status": "complete", "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "locked_inputs": lock, "post_run_inputs": after, "cells": state["cells"],
        "process": {"wall_seconds": time.perf_counter() - started_wall, "cpu_seconds": time.process_time() - started_cpu,
                    "max_rss_kib": usage.ru_maxrss},
        "claim_boundary": "Synthetic offline ls20-shaped planning/navigation task, not natural task prevalence or general planning capability.",
    }
    atomic_json(CAPTURE_PATH, capture)
    PARTIAL_PATH.unlink(missing_ok=True)
    print(json.dumps({"capture": str(CAPTURE_PATH.relative_to(ROOT)), "status": "complete",
                      "paired_scenarios": sum(len(c["records"]) for c in state["cells"]),
                      "source_lock_stable": True}, indent=2))


if __name__ == "__main__":
    main()
