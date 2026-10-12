#!/usr/bin/env python3
"""Paired scan/cache experiment for ShapeDecode name apertures."""
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
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native

BASE_RUNNER = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_baseline_v1.py"
SPEC = importlib.util.spec_from_file_location("shapedecode_name_aperture_baseline_v1", BASE_RUNNER)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BASE)

RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SHAPEDECODE_NAME_APERTURE_CACHE_V1_PREREG_20261005.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_shapedecode_name_aperture_cache_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_cache_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/shapedecode_name_aperture_cache_v1_20261005.json"
SIZES = (16, 32, 64, 128)
REPLICATES = (0, 1, 2, 3, 4)
MODES = ("scan", "cached")
TRACE_STATES = (False, True)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def manifest() -> dict:
    return {
        "baseline_inputs": BASE.source_manifest(),
        "runner_sha256": sha(RUNNER),
        "protocol_sha256": sha(PROTOCOL),
        "analyzer_sha256": sha(ANALYZER),
    }


def cases() -> list[dict]:
    return [{"size": size, "replicate": rep, "trace": trace, "cache_mode": mode,
             "id": f"n{size}_r{rep}_{mode}_trace{int(trace)}"}
            for size in SIZES for rep in REPLICATES for mode in MODES for trace in TRACE_STATES]


def run_worker(case: dict, locked_manifest: dict) -> dict:
    before = manifest()
    if before != locked_manifest:
        raise RuntimeError("worker sources differ from frozen source manifest")
    _native.Substrate.runtime_shape_codebook_cache_set_enabled(case["cache_mode"] == "cached")
    try:
        result = BASE.worker(case)
    finally:
        _native.Substrate.runtime_shape_codebook_cache_set_enabled(True)
    after = manifest()
    return {"case": case, "pid": os.getpid(), "source_before": before,
            "source_after": after, "source_stable": before == after,
            "result": result}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    assert_measuring_engine()
    frozen = {"manifest": manifest(), "cases": cases(), "python": sys.version,
              "platform": platform.platform(), "schedule_seed": 20261005}
    if args.worker:
        incoming = json.loads(sys.stdin.read())
        locked = json.loads(LOCK.read_text())
        print(json.dumps(run_worker(incoming, locked["manifest"]), sort_keys=True, default=str))
        return 0
    if args.lock:
        LOCK.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"lock": str(LOCK.relative_to(ROOT)), "cases": len(frozen["cases"])}))
        return 0
    if not LOCK.exists() or json.loads(LOCK.read_text()) != frozen:
        raise SystemExit("missing or stale lock; run with --lock after protocol/source edits")
    schedule = list(frozen["cases"])
    random.Random(frozen["schedule_seed"]).shuffle(schedule)
    env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}
    rows, failures = [], []
    for case in schedule:
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker"],
                              input=json.dumps(case), cwd=ROOT, env=env,
                              text=True, capture_output=True)
        try:
            row = json.loads(proc.stdout)
        except Exception:
            row = {"case": case, "worker_error": "invalid_json",
                   "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]}
        rows.append(row)
        if proc.returncode:
            failures.append({"case": case, "returncode": proc.returncode,
                             "stderr_tail": proc.stderr[-2000:]})
    capture = {"schema": "ShapeDecodeNameApertureCacheV1Capture",
               "run_id": "shapedecode-name-aperture-cache-v1-20261005",
               "lock_path": str(LOCK.relative_to(ROOT)), "lock_sha256": sha(LOCK),
               "manifest": frozen["manifest"],
               "worker_order": [r.get("case", {}).get("id") for r in rows],
               "rows": rows, "process_failures": failures}
    OUT.write_text(json.dumps(capture, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"capture": str(OUT.relative_to(ROOT)), "workers": len(rows),
                      "failures": len(failures)}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
