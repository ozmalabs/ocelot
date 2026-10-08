#!/usr/bin/env python3
"""Source-locked 10k/100k/200k node scale sweep for thoughtexperiment fanout."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
COST_PATH = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_node_scale_v1.py"
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_NODE_SCALE_V1_PREREG_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_node_scale_v1_lock_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_20261004.json"
BACKENDS, SIZES, REPLICATES = ("full_copy", "shared_graph_pages"), (10_000, 100_000, 200_000), range(3)
SEED = 20261006


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module; spec.loader.exec_module(module); return module


def configurations():
    rows = [dict(frames=4, topology="independent_states", fanout=4, noise_nodes=size, backend=backend, replicate=rep)
            for size, backend, rep in itertools.product(SIZES, BACKENDS, REPLICATES)]
    random.Random(SEED).shuffle(rows)
    return rows


def locked_inputs():
    cost = load_module("fanout_cost_for_scaling", COST_PATH)
    return {"cost_breakdown_locked_inputs": cost.locked_inputs(), "runner_sha256": sha(Path(__file__)),
        "analyzer_sha256": sha(ANALYZER), "protocol_sha256": sha(PREREG)}


def run_config(cfg):
    cost = load_module("fanout_cost_worker_scale", COST_PATH)
    replay = cost.load_replay()
    replay.CONFIGS = [cfg]
    original_load = cost.load_replay
    cost.load_replay = lambda: replay
    try:
        return cost.worker(0)
    finally:
        cost.load_replay = original_load


def main():
    configs = configurations()
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists(): raise SystemExit("refusing to overwrite existing lock/capture")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentFanoutNodeScaleV1Lock", "locked_inputs": locked_inputs(),
            "random_seed": SEED, "configurations": configs}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(run_config(configs[int(sys.argv[2])]), sort_keys=True)); return
    locked = locked_inputs(); lock = json.loads(LOCK.read_text()) if LOCK.exists() else {}
    if lock.get("locked_inputs") != locked or lock.get("configurations") != configs:
        raise SystemExit("missing or stale pre-run source lock")
    env = dict(os.environ); env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    rows, failures = [], []
    for i, cfg in enumerate(configs):
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(i)],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=900)
        except subprocess.TimeoutExpired as exc:
            failures.append({"index": i, "config": cfg, "error": "worker timeout", "stderr": str(exc.stderr)[-2000:]}); continue
        if proc.returncode == 0:
            try: rows.append(json.loads(proc.stdout))
            except json.JSONDecodeError as exc: failures.append({"index": i, "config": cfg, "error": str(exc), "stderr": proc.stderr[-2000:]})
        else: failures.append({"index": i, "config": cfg, "returncode": proc.returncode, "stderr": proc.stderr[-4000:]})
        print(f"worker {i + 1}/{len(configs)} {'ok' if proc.returncode == 0 else 'failed'}", flush=True)
    post = locked_inputs()
    result = {"schema": "ThoughtexperimentFanoutNodeScaleV1", "captured_utc": datetime.now(timezone.utc).isoformat(),
        "locked_inputs": locked, "post_run_locked_inputs": post, "source_stable": post == locked,
        "random_seed": SEED, "configs": configs, "runs": rows, "worker_failures": failures}
    if OUT.exists(): raise SystemExit("refusing to overwrite existing capture")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); print(OUT.relative_to(ROOT))


if __name__ == "__main__": main()
