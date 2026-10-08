#!/usr/bin/env python3
"""Bounded paired eager/streaming generator probe with a conditional grammar."""
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

STEM = "substrate_generator_streaming_grammar_v1_20261001"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
SOURCES = (
    "domains/generator.py", "domains/engine_provenance.py",
    "scripts/substrate_generated_pool_cegis_comparison_v1.py",
    "scripts/substrate_generator_streaming_grammar_v1.py",
    "scripts/analyze_substrate_generator_streaming_grammar_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_GENERATOR_STREAMING_GRAMMAR_V1_PREREG_20261001.md",
)
OPS = ("Plus", "Times", "Minus", "Div", "Lt", "Gt", "Eq", "IfThenElse")
SIZES = {"triangular": (5, 6), "square": (5, 6), "euler": (4, 5)}
PROBE_COUNT = 5
REPETITIONS = 2
SEED = 20261001
PARENT_TIMEOUT_S = 25.0


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def lock_payload() -> dict:
    native = Path(_native.__file__).resolve()
    return {"schema_version": 1, "sources": {name: digest(ROOT / name) for name in SOURCES},
            "native_extension": {"path": str(native), "sha256": digest(native)},
            "native_build_manifest_sha256": digest(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "engine_provenance": engine_provenance(),
            "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"ops": list(OPS), "sizes": {k: list(v) for k, v in SIZES.items()},
                       "probe_count": PROBE_COUNT, "repetitions": REPETITIONS, "seed": SEED,
                       "timeout_s": 8.0, "parent_timeout_s": PARENT_TIMEOUT_S,
                       "solution_limit": 10000, "arms": ["eager", "streaming"]}}


def canon(v):
    if isinstance(v, tuple): return [canon(x) for x in v]
    if isinstance(v, list): return [canon(x) for x in v]
    return v if isinstance(v, (str, int, float, bool)) or v is None else repr(v)


def worker(task_name: str, size: int, rep: int) -> dict:
    sub = _native.Substrate()
    task = base.make_tasks(sub)[task_name]
    rows = [(n, x, task["oracle"](x)) for n, x in task["knowns"]]
    examples = [(task["describe"](x), y) for _, x, y in rows]
    probes = task["candidates"][:PROBE_COUNT]
    probe_envs = [task["describe"](x) for _, x in probes]
    arms = ["eager", "streaming"]
    random.Random(SEED + 100 * (0 if task_name == "triangular" else 1 if task_name == "square" else 2) + size + rep).shuffle(arms)
    out = {}
    for arm in arms:
        tracemalloc.start(); tracemalloc.reset_peak()
        wall0, cpu0 = time.perf_counter(), time.process_time()
        result = synthesize(sub, examples, ops=OPS, consts=(0, 1, 2, -1), max_size=size,
                            timeout_s=8.0, include_output_constants=False, probe_envs=probe_envs,
                            max_solutions=10000, saturate_k=999999, stream_cohort=arm == "streaming")
        wall, cpu = time.perf_counter() - wall0, time.process_time() - cpu0
        _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
        hypotheses = result.get("hypotheses", [])
        held = [(x, task["oracle"](x)) for _, x in task["heldout"]]
        support = sum(all(base.equal(h["term"].evaluate(task["describe"](x), sub), y) for x, y in held)
                      for h in hypotheses)
        out[arm] = {"halt_reason": result.get("halt_reason"), "pool_size": len(hypotheses),
                    "explored": result.get("explored"), "distinct": result.get("distinct"),
                    "signatures": [canon(h["signature"]) for h in hypotheses],
                    "target_support": support, "wall_s": wall, "cpu_s": cpu, "python_peak_bytes": peak}
    return {"task": task_name, "max_size": size, "replicate": rep, "arm_order": arms, "arms": out}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", nargs=3); args = parser.parse_args()
    lock = lock_payload()
    if args.lock:
        print(json.dumps(lock, indent=2, sort_keys=True)); return
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != lock: raise SystemExit("source lock is absent or stale")
    if args.worker:
        task, size, rep = args.worker
        print(json.dumps(worker(task, int(size), int(rep)), sort_keys=True)); return
    if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
    schedule = [(task, size, rep) for task in SIZES for size in SIZES[task] for rep in range(REPETITIONS)]
    random.Random(SEED).shuffle(schedule)
    rows = []
    for task, size, rep in schedule:
        cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", task, str(size), str(rep)]
        try:
            proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=PARENT_TIMEOUT_S)
            if proc.returncode:
                rows.append({"task": task, "max_size": size, "replicate": rep, "worker_error": proc.stderr[-2000:]})
            else:
                lines = [line for line in proc.stdout.splitlines() if line.strip().startswith("{")]
                rows.append(json.loads(lines[-1]) if lines else {"task": task, "max_size": size,
                                                                  "replicate": rep, "worker_error": "missing_json"})
        except subprocess.TimeoutExpired:
            rows.append({"task": task, "max_size": size, "replicate": rep, "worker_error": "parent_timeout"})
    capture = {"schema": "GeneratorStreamingGrammarV1", "lock": lock, "schedule": schedule, "comparisons": rows}
    RAW.parent.mkdir(parents=True, exist_ok=True); RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": str(RAW.relative_to(ROOT)), "workers": len(rows),
                      "worker_errors": sum("worker_error" in r for r in rows)}, indent=2))


if __name__ == "__main__": main()
