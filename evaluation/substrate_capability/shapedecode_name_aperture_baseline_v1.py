#!/usr/bin/env python3
"""Current-source scan baseline for singleton ShapeDecode name apertures."""
from __future__ import annotations

import argparse
import hashlib
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
from domains.engine_provenance import assert_measuring_engine, build_is_stale, provenance_line
from domains.crossframe_world import CrossFrameWorld, sig_of
from substrate_rs import _native
import numpy as np

RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SHAPEDECODE_NAME_APERTURE_BASELINE_V1_PREREG_20261005.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_shapedecode_name_aperture_baseline_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_baseline_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/shapedecode_name_aperture_baseline_v1_20261005.json"
SIZES = (16, 32, 64, 128)
REPLICATES = (0, 1, 2)
TRACE_STATES = (False, True)
TRACE_HELPER = 1
HELPER_KINDS = {
    "dynamic_helper_invocation", "helper_codebook_population_node",
    "helper_node_attribute_examined", "helper_codebook_part_parsed",
    "helper_search_candidate", "helper_candidate_part_scored",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_manifest() -> dict:
    paths = [
        "domains/crossframe_world.py", "domains/engine_provenance.py",
        "substrate/boot_core.py", "substrate/seed_loader.py",
        "runners/dsl/src/shape_decode.rs", "runners/dsl/src/term.rs",
        "runners/dsl/src/graph.rs", "runners/dsl/src/access_trace.rs",
        "runners/dsl/src/rewrite.rs", "runners/dsl/src/substrate.rs",
        "runners/dsl/src/py.rs", "runners/dsl/src/jsonio.rs",
        "runners/dsl/src/reflect.rs", "runners/dsl/src/lib.rs",
        "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
        "runners/dsl/python/substrate_rs/__init__.py",
        "runners/dsl/python/substrate_rs/_native.build.json",
        str(RUNNER.relative_to(ROOT)), str(PROTOCOL.relative_to(ROOT)),
        str(ANALYZER.relative_to(ROOT)), "seeds/shape_decode_loop.json",
        "seeds/vision_crossframe_identity.json",
    ]
    native = Path(_native.__file__).resolve()
    return {
        "source_sha256": {p: sha(ROOT / p) for p in paths},
        "native_path": str(native), "native_sha256": sha(native),
        "engine": provenance_line(),
    }


def cases() -> list[dict]:
    return [{"size": size, "replicate": rep, "trace": trace,
             "id": f"n{size}_r{rep}_trace{int(trace)}"}
            for size in SIZES for rep in REPLICATES for trace in TRACE_STATES]


def worker(case: dict) -> dict:
    assert_measuring_engine()
    if build_is_stale(str(ROOT)):
        raise RuntimeError("native extension is stale")
    before = source_manifest()
    world = CrossFrameWorld(arm=True)
    rng = np.random.default_rng(205100 + case["replicate"])
    tiles = [rng.integers(0, 4, size=(6, 6), dtype=np.int64) for _ in range(16)]
    world.hold_codebook(tiles, list(range(16)))
    for i in range(16, case["size"]):
        world.s.add_node("ShapeSignature", {
            "name": f"r{i:02d}",
            "signature": json.dumps([["noise", i, "unmatched"]]),
            "kind": "aperture_baseline_distractor",
            "faculty": "aperture_baseline",
        })
    observation = world.present(tiles[0], truth=0, tag=case["id"])
    world.s.add_node("NativeCrossFrameReceipt", {
        "schema": "native_crossframe_receipt_v1",
        "cluster": "crossframe_world.identity_settlement",
        "provenance": "native_rule_readback:crossframe_identity",
        "native_rule": "crossframe_identity_native_rules",
        "native_steps": ["present_observations", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    if case["trace"]:
        _native.Substrate.runtime_access_trace_reset()
        _native.Substrate.runtime_work_trace_set_all_scopes_enabled(True)
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    try:
        closure_work = int(world.native.run_rules())
    finally:
        wall_ns = time.perf_counter_ns() - wall_start
        cpu_ns = time.process_time_ns() - cpu_start
        if case["trace"]:
            _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
    if case["trace"]:
        trace_rows, dropped = _native.Substrate.runtime_work_trace_all_scopes_snapshot()
    else:
        trace_rows, dropped = [], 0
    attrs = world.s.node(observation)["attrs"]
    result = world.read()[0]
    after = source_manifest()
    counts: dict[str, int] = {}
    for row in trace_rows:
        if len(row) == 6 and str(row[3]) in HELPER_KINDS and int(row[4] or 0) == TRACE_HELPER:
            key = str(row[3])
            counts[key] = counts.get(key, 0) + int(row[5])
    return {
        "case": case, "pid": os.getpid(), "source_before": before,
        "source_after": after, "source_stable": before == after,
        "engine_stale": False, "graph_nodes": len(list(world.s.nodes())),
        "shape_signature_count": len(list(world.s.nodes("ShapeSignature"))),
        "closure_work": closure_work, "closure_wall_ns": wall_ns,
        "closure_cpu_ns": cpu_ns,
        "peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "identified_as": attrs.get("identified_as"), "readback": result,
        "expected_name": "r00", "runtime_work_trace": {
            "rows": [list(r) for r in trace_rows], "dropped": int(dropped),
            "shape_decode_counts": counts,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        case = json.loads(sys.stdin.read())
        print(json.dumps(worker(case), sort_keys=True, default=str))
        return 0
    assert_measuring_engine()
    locked = {"source_manifest": source_manifest(), "cases": cases(),
              "python": sys.version, "platform": platform.platform(),
              "seed": 20261005, "trace_helper_subject": TRACE_HELPER}
    if args.lock:
        LOCK.write_text(json.dumps(locked, indent=2, sort_keys=True) + "\n")
        print(f"locked {len(locked['cases'])} cases at {LOCK.relative_to(ROOT)}")
        return 0
    if not LOCK.exists() or json.loads(LOCK.read_text()) != locked:
        raise SystemExit("missing or stale baseline lock; run with --lock after final edits")
    jobs = list(locked["cases"])
    random.Random(20261005).shuffle(jobs)
    rows, failures = [], []
    env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}
    for case in jobs:
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker"], input=json.dumps(case),
                              cwd=ROOT, env=env, text=True, capture_output=True)
        try:
            row = json.loads(proc.stdout)
        except Exception:
            row = {"case": case, "worker_error": "invalid_json", "stdout_tail": proc.stdout[-2000:],
                   "stderr_tail": proc.stderr[-2000:]}
        rows.append(row)
        if proc.returncode:
            failures.append({"case": case, "returncode": proc.returncode,
                             "stderr_tail": proc.stderr[-2000:]})
    capture = {
        "schema": "ShapeDecodeNameApertureBaselineV1Capture",
        "run_id": "shapedecode-name-aperture-baseline-v1-20261005",
        "lock_path": str(LOCK.relative_to(ROOT)),
        "lock_sha256": sha(LOCK), "source_manifest": locked["source_manifest"],
        "worker_order": [r.get("case", {}).get("id") for r in rows],
        "rows": rows, "process_failures": failures,
    }
    OUT.write_text(json.dumps(capture, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"capture": str(OUT.relative_to(ROOT)), "workers": len(rows),
                      "failures": len(failures)}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
