#!/usr/bin/env python3
"""Measure complete generated-hypothesis-pool scaling across size and probes."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains.engine_provenance import engine_preamble, engine_provenance, rust_source_fingerprint
engine_preamble()
from domains.generator import synthesize
from substrate_rs import _native
import substrate_generated_pool_cegis_comparison_v1 as base

STEM = "substrate_generated_pool_scale_v1_20261001"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_SCALE_V1_PREREG_20261001.md"
SOURCE_PATHS = (
    "domains/generator.py", "domains/engine_provenance.py",
    "domains/reason.py", "domains/compute_grounding.py",
    "scripts/substrate_generated_pool_cegis_comparison_v1.py",
    "scripts/substrate_generated_pool_scale_v1.py",
    "scripts/analyze_substrate_generated_pool_scale_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_SCALE_V1_PREREG_20261001.md",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_PREREG_20261001.md",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_5_AMENDMENT_20261001.md",
)
SOURCE_PATHS = tuple(dict.fromkeys(SOURCE_PATHS + tuple(base.SOURCE_PATHS)))
TASKS = ("triangular", "square", "euler")
MAX_SIZES = {"triangular": [5, 6, 7, 8], "square": [2, 3, 4, 5], "euler": [3, 4, 5, 6]}
PROBE_COUNTS = (0, 1, 3, 6, 10)
REPETITIONS = 2
SEED = 20261001
TIMEOUT_S = 8.0
PARENT_TIMEOUT_S = 15.0
POOL_LIMIT = 10000
OPS = ("Plus", "Times", "Minus", "Div")
CONSTS = (0, 1, 2, -1)


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def rss_high_water() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def lock_payload() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "schema_version": 1,
        "sources": {name: digest(ROOT / name) for name in SOURCE_PATHS},
        "native_extension": {"path": str(native), "sha256": digest(native)},
        "native_build_manifest_sha256": digest(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "engine_provenance": engine_provenance(),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {
            "tasks": list(TASKS), "max_sizes": MAX_SIZES, "probe_counts": list(PROBE_COUNTS),
            "repetitions": REPETITIONS, "seed": SEED, "pool_limit": POOL_LIMIT,
            "internal_timeout_s": TIMEOUT_S, "parent_timeout_s": PARENT_TIMEOUT_S,
            "ops": list(OPS), "constants": list(CONSTS),
            "include_output_constants": False, "saturation_disabled": True,
            "worker_order": "randomized sequential workers within each repetition",
        },
    }


def worker(task_name: str, max_size: int, probe_count: int, replicate: int) -> dict:
    setup_start, setup_cpu = time.perf_counter(), time.process_time()
    substrate = _native.Substrate()
    task = base.make_tasks(substrate)[task_name]
    setup_wall, setup_cpu_s = time.perf_counter() - setup_start, time.process_time() - setup_cpu

    train_start, train_cpu = time.perf_counter(), time.process_time()
    rows = [(name, value, task["oracle"](value)) for name, value in task["knowns"]]
    training_oracle_wall = time.perf_counter() - train_start
    training_oracle_cpu = time.process_time() - train_cpu
    examples = [(task["describe"](value), label) for _, value, label in rows]
    probes = task["candidates"][:probe_count]
    probe_envs = [task["describe"](value) for _, value in probes]
    rss_before = rss_high_water()

    synth_wall_start, synth_cpu_start = time.perf_counter(), time.process_time()
    result = synthesize(
        substrate, examples, ops=OPS, consts=CONSTS, max_size=max_size,
        timeout_s=TIMEOUT_S, include_output_constants=False,
        probe_envs=probe_envs, max_solutions=POOL_LIMIT, saturate_k=999999,
    )
    synth_wall = time.perf_counter() - synth_wall_start
    synth_cpu = time.process_time() - synth_cpu_start
    rss_after = rss_high_water()
    hypotheses = result.get("hypotheses", [])

    eval_start, eval_cpu = time.perf_counter(), time.process_time()
    target_support_count = 0
    heldout_labels = [(name, value, task["oracle"](value)) for name, value in task["heldout"]]
    target_support_count = sum(
        1 for item in hypotheses
        if all(base.equal(item["term"].evaluate(task["describe"](value), substrate), answer)
               for _, value, answer in heldout_labels)
    )
    evaluation_wall = time.perf_counter() - eval_start
    evaluation_cpu = time.process_time() - eval_cpu

    return {
        "task": task_name, "max_size": max_size, "probe_count": probe_count,
        "replicate": replicate, "train_count": len(rows),
        "probe_names": [name for name, _ in probes],
        "heldout_count": len(heldout_labels),
        "pool_halt_reason": result.get("halt_reason"),
        "pool_complete": result.get("halt_reason") == "max_size",
        "pool_size": len(hypotheses), "solution_limit": POOL_LIMIT,
        "terms_explored": result.get("explored"),
        "distinct_signatures": result.get("distinct"),
        "target_support_count": target_support_count,
        "target_supported": target_support_count > 0,
        "setup_wall_s": setup_wall, "setup_cpu_s": setup_cpu_s,
        "training_oracle_wall_s": training_oracle_wall,
        "training_oracle_cpu_s": training_oracle_cpu,
        "synthesis_wall_s": synth_wall, "synthesis_cpu_s": synth_cpu,
        "evaluation_wall_s": evaluation_wall, "evaluation_cpu_s": evaluation_cpu,
        "rss_high_water_before_kib": rss_before,
        "rss_high_water_after_kib": rss_after,
        "rss_high_water_delta_kib": max(0, rss_after - rss_before),
        "rss_units": "KiB on Linux; ru_maxrss platform-specific",
        "worker_host": {"machine": platform.machine(), "platform": platform.platform(),
                        "python": sys.version.split()[0]},
        "source_lock_sha256": digest(LOCK),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", nargs=4, metavar=("TASK", "SIZE", "PROBES", "REPLICATE"))
    args = parser.parse_args()
    lock = lock_payload()
    if args.lock:
        print(json.dumps(lock, indent=2, sort_keys=True))
        return
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != lock:
        raise SystemExit("source lock is absent or stale")
    if args.worker:
        task_name, size, probes, replicate = args.worker
        print(json.dumps(worker(task_name, int(size), int(probes), int(replicate)), sort_keys=True))
        return
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")

    schedule = []
    for replicate in range(REPETITIONS):
        block = [(task, size, probes, replicate)
                 for task in TASKS for size in MAX_SIZES[task] for probes in PROBE_COUNTS]
        random.Random(SEED + replicate).shuffle(block)
        schedule.extend(block)

    rows = []
    for task_name, max_size, probe_count, replicate in schedule:
        cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", task_name,
               str(max_size), str(probe_count), str(replicate)]
        start = time.perf_counter()
        try:
            proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True,
                                  timeout=PARENT_TIMEOUT_S)
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            rows.append({"task": task_name, "max_size": max_size, "probe_count": probe_count,
                         "replicate": replicate, "worker_error": "parent_timeout",
                         "parent_wall_s": time.perf_counter() - start,
                         "stdout_tail": stdout[-1200:]})
            continue
        parent_wall = time.perf_counter() - start
        if proc.returncode != 0:
            rows.append({"task": task_name, "max_size": max_size, "probe_count": probe_count,
                         "replicate": replicate, "worker_error": proc.stderr[-3000:],
                         "returncode": proc.returncode, "parent_wall_s": parent_wall})
            continue
        json_lines = [line for line in proc.stdout.splitlines() if line.strip().startswith("{")]
        if not json_lines:
            rows.append({"task": task_name, "max_size": max_size, "probe_count": probe_count,
                         "replicate": replicate, "worker_error": "missing_json_output",
                         "stdout_tail": proc.stdout[-1200:], "parent_wall_s": parent_wall})
            continue
        row = json.loads(json_lines[-1])
        row["parent_wall_s"] = parent_wall
        rows.append(row)

    capture = {"schema": "GeneratedPoolScaleV1", "lock": lock,
               "schedule": schedule, "comparisons": rows,
               "capture_complete": len(rows) == len(schedule)}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": str(RAW.relative_to(ROOT)), "workers": len(rows),
                      "capture_complete": capture["capture_complete"],
                      "worker_errors": sum("worker_error" in row for row in rows)}, indent=2))


if __name__ == "__main__":
    main()
