#!/usr/bin/env python3
"""Paired cache/scan closure replay on the seed-authored verdict comparator."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import assert_measuring_engine
from domains import verdict_comparator_world as vw
from substrate_rs import _native

BASELINE = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_baseline_v1.py"
SPEC = importlib.util.spec_from_file_location("shapedecode_baseline", BASELINE)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BASE)

RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SHAPEDECODE_VERDICT_COMPARATOR_CACHE_V1_PREREG_20261005.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_shapedecode_verdict_comparator_cache_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/shapedecode_verdict_comparator_cache_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/shapedecode_verdict_comparator_cache_v1_20261005.json"
SIZES = (16, 32, 64, 128)
REPLICATES = (0, 1, 2, 3, 4)
MODES = ("scan", "cached")
TRACES = (False, True)
KINDS = {"dynamic_helper_invocation", "helper_codebook_population_node",
         "helper_node_attribute_examined", "helper_codebook_part_parsed",
         "helper_search_candidate", "helper_candidate_part_scored",
         "helper_codebook_cache_hit", "helper_codebook_cache_miss"}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def manifest() -> dict:
    return {"baseline": BASE.source_manifest(),
            "world_sha256": sha(ROOT / "domains/verdict_comparator_world.py"),
            "seed_sha256": sha(ROOT / "seeds/vision_verdict_comparator.json"),
            "runner_sha256": sha(RUNNER), "protocol_sha256": sha(PROTOCOL),
            "analyzer_sha256": sha(ANALYZER)}


def cases() -> list[dict]:
    return [{"size": n, "replicate": rep, "mode": mode, "trace": trace,
             "id": f"n{n}_r{rep}_{mode}_trace{int(trace)}"}
            for n in SIZES for rep in REPLICATES for mode in MODES for trace in TRACES]


def worker(case: dict, frozen: dict) -> dict:
    before = manifest()
    if before != frozen:
        raise RuntimeError("worker source manifest differs from lock")
    assert_measuring_engine()
    _native.Substrate.runtime_shape_codebook_cache_set_enabled(case["mode"] == "cached")
    try:
        rng = vw.np.random.default_rng(205100 + case["replicate"])
        tile_arrays = [rng.integers(0, vw.K_LEVELS, size=(vw.REGION, vw.REGION), dtype=vw.np.int64)
                       for _ in range(16)]
        tiles = [(tile, tile) for tile in tile_arrays]
        order = list(range(16))
        random.Random(602100 + case["replicate"]).shuffle(order)
        world = vw.VerdictWorld("hamming")
        world.hold(tiles, order)
        for i in range(16, case["size"]):
            distractor = rng.integers(0, vw.K_LEVELS, size=(vw.REGION, vw.REGION), dtype=vw.np.int64)
            enc = vw.encode(distractor, distractor)
            world.s.add_node("VdSignature", {
                "name": f"r{i:02d}", "signature": json.dumps(enc["signature"]),
                "kind": "cache_replay_distractor", "faculty": f"r{i:02d}",
                "dim_types": vw.DIM_TYPES, "qvals": enc["qvals"], "qsq": enc["qsq"],
                "gvals": enc["gvals"], "gsq": enc["gsq"], "nvals": enc["nvals"],
                "nflat": enc["nflat"]})
        world.present([(0, tile_arrays[0], tile_arrays[0])], truth=0,
                      tag=f"n{case['size']}_r{case['replicate']}", kind="A1")
        if case["trace"]:
            _native.Substrate.runtime_access_trace_reset()
            _native.Substrate.runtime_work_trace_set_all_scopes_enabled(True)
        cpu0, wall0 = time.process_time_ns(), time.perf_counter_ns()
        try:
            work = int(world.native.run_rules())
        finally:
            wall_ns = time.perf_counter_ns() - wall0
            cpu_ns = time.process_time_ns() - cpu0
            if case["trace"]:
                _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
        if case["trace"]:
            trace_rows, dropped = _native.Substrate.runtime_work_trace_all_scopes_snapshot()
        else:
            trace_rows, dropped = [], 0
        readback = world.read()[0]
        after = manifest()
        return {"case": case, "pid": os.getpid(), "source_before": before,
                "source_after": after, "source_stable": before == after,
                "vdsignature_count": len(world.s.nodes("VdSignature")),
                "closure_work": work, "closure_wall_ns": wall_ns, "closure_cpu_ns": cpu_ns,
                "peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                "readback": readback, "trace": {"rows": [list(r) for r in trace_rows],
                                                  "dropped": int(dropped)}}
    finally:
        _native.Substrate.runtime_shape_codebook_cache_set_enabled(True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    frozen = {"manifest": manifest(), "cases": cases(), "python": sys.version,
              "platform": platform.platform(), "schedule_seed": 20261006}
    if args.worker:
        case = json.loads(sys.stdin.read())
        locked = json.loads(LOCK.read_text())
        print(json.dumps(worker(case, locked["manifest"]), sort_keys=True, default=str))
        return 0
    if args.lock:
        LOCK.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"lock": LOCK.relative_to(ROOT).as_posix(), "cases": len(cases())}))
        return 0
    if not LOCK.exists() or json.loads(LOCK.read_text()) != frozen:
        raise SystemExit("missing or stale lock; run --lock after source/protocol edits")
    schedule = list(frozen["cases"])
    random.Random(frozen["schedule_seed"]).shuffle(schedule)
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
    capture = {"schema": "ShapeDecodeVerdictComparatorCacheV1Capture",
               "run_id": "shapedecode-verdict-comparator-cache-v1-20261005",
               "lock_path": LOCK.relative_to(ROOT).as_posix(), "lock_sha256": sha(LOCK),
               "manifest": frozen["manifest"],
               "worker_order": [r.get("case", {}).get("id") for r in rows],
               "rows": rows, "process_failures": failures}
    OUT.write_text(json.dumps(capture, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"capture": OUT.relative_to(ROOT).as_posix(), "workers": len(rows),
                      "failures": len(failures)}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
