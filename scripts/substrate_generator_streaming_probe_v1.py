#!/usr/bin/env python3
"""Paired eager/streaming candidate-cohort synthesis measurement."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import tracemalloc
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

STEM = "substrate_generator_streaming_probe_v1_20261001"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
SOURCE_PATHS = (
    "domains/generator.py", "domains/engine_provenance.py",
    "scripts/substrate_generated_pool_cegis_comparison_v1.py",
    "scripts/substrate_generator_streaming_probe_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_GENERATOR_STREAMING_PROBE_V1_PREREG_20261001.md",
)
TASKS = ("triangular", "square", "euler")
MAX_SIZES = {"triangular": [5, 6, 7, 8], "square": [2, 3, 4, 5], "euler": [3, 4, 5, 6]}
PROBE_COUNTS = (0, 1, 3, 6, 10)
REPETITIONS = 2
SEED = 20261001
OPS = ("Plus", "Times", "Minus", "Div")
CONSTS = (0, 1, 2, -1)
POOL_LIMIT = 10000


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def lock_payload() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "schema_version": 1,
        "sources": {p: digest(ROOT / p) for p in SOURCE_PATHS},
        "native_extension": {"path": str(native), "sha256": digest(native)},
        "native_build_manifest_sha256": digest(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "engine_provenance": engine_provenance(),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"tasks": list(TASKS), "max_sizes": MAX_SIZES,
                   "probe_counts": list(PROBE_COUNTS), "repetitions": REPETITIONS,
                   "seed": SEED, "ops": list(OPS), "constants": list(CONSTS),
                   "solution_limit": POOL_LIMIT, "arms": ["eager", "streaming"],
                   "arm_order": "randomized within each paired worker",
                   "peak_memory_measure": "tracemalloc peak Python allocations during synthesis"},
    }


def signature_key(value):
    if isinstance(value, tuple):
        return [signature_key(item) for item in value]
    if isinstance(value, list):
        return [signature_key(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def run_cell(task_name: str, max_size: int, probe_count: int, replicate: int) -> dict:
    substrate = _native.Substrate()
    task = base.make_tasks(substrate)[task_name]
    rows = [(name, value, task["oracle"](value)) for name, value in task["knowns"]]
    examples = [(task["describe"](value), label) for _, value, label in rows]
    probes = task["candidates"][:probe_count]
    probe_envs = [task["describe"](value) for _, value in probes]
    arms = ["eager", "streaming"]
    random.Random(SEED + 100 * TASKS.index(task_name) + 10 * max_size + probe_count + replicate).shuffle(arms)
    results = {}
    for arm in arms:
        tracemalloc.start()
        tracemalloc.reset_peak()
        wall0, cpu0 = time.perf_counter(), time.process_time()
        result = synthesize(
            substrate, examples, ops=OPS, consts=CONSTS, max_size=max_size,
            timeout_s=8.0, include_output_constants=False,
            probe_envs=probe_envs, max_solutions=POOL_LIMIT, saturate_k=999999,
            stream_cohort=(arm == "streaming"),
        )
        wall, cpu = time.perf_counter() - wall0, time.process_time() - cpu0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        hypotheses = result.get("hypotheses", [])
        support_count = 0
        heldout = [(name, value, task["oracle"](value)) for name, value in task["heldout"]]
        for item in hypotheses:
            if all(base.equal(item["term"].evaluate(task["describe"](value), substrate), answer)
                   for _, value, answer in heldout):
                support_count += 1
        results[arm] = {
            "halt_reason": result.get("halt_reason"),
            "pool_size": len(hypotheses),
            "terms_explored": result.get("explored"),
            "distinct_signatures": result.get("distinct"),
            "signatures": [signature_key(item["signature"]) for item in hypotheses],
            "target_support_count": support_count,
            "wall_s": wall,
            "cpu_s": cpu,
            "python_peak_bytes": peak,
        }
    return {"task": task_name, "max_size": max_size, "probe_count": probe_count,
            "replicate": replicate, "arm_order": arms, "arms": results}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    lock = lock_payload()
    if args.lock:
        print(json.dumps(lock, indent=2, sort_keys=True))
        return
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != lock:
        raise SystemExit("source lock is absent or stale")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    schedule = [(task, size, probes, rep)
                for rep in range(REPETITIONS)
                for task in TASKS for size in MAX_SIZES[task] for probes in PROBE_COUNTS]
    random.Random(SEED).shuffle(schedule)
    rows = []
    for task, size, probes, rep in schedule:
        rows.append(run_cell(task, size, probes, rep))
    capture = {"schema": "GeneratorStreamingProbeV1", "lock": lock,
               "schedule": schedule, "comparisons": rows}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": str(RAW.relative_to(ROOT)), "workers": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
