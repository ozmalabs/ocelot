#!/usr/bin/env python3
"""Matched instrumentation on/off capture for the 100k fanout workload."""
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
REPLAY_PATH = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_current_source_replay_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1.py"
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_INSTRUMENTATION_OVERHEAD_V1_PREREG_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_lock_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_20261004.json"
COST_LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1_lock_20261004.json"
COST_CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_cost_breakdown_v1_20261004.json"
COST_ANALYSIS = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_cost_breakdown_v1_analysis_20261004.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fixed_pairs():
    return [(backend, replicate, arm) for backend, replicate in itertools.product(
        ("full_copy", "shared_graph_pages"), range(3)) for arm in ("off", "on")]


def schedule():
    pairs = [(backend, rep) for backend, rep in itertools.product(
        ("full_copy", "shared_graph_pages"), range(3))]
    random.Random(20261004).shuffle(pairs)
    return [{"backend": backend, "replicate": rep, "arm_order": ["off", "on"] if i % 2 == 0 else ["on", "off"]}
            for i, (backend, rep) in enumerate(pairs)]


def configurations():
    configs = []
    for pair in schedule():
        for arm in pair["arm_order"]:
            configs.append({"frames": 4, "topology": "independent_states", "fanout": 4,
                "noise_nodes": 100_000, "backend": pair["backend"], "replicate": pair["replicate"],
                "instrumentation": arm})
    return configs


def locked_inputs():
    cost = load_module("fanout_cost_breakdown", COST_PATH)
    return {"cost_breakdown_locked_inputs": cost.locked_inputs(),
        "runner_sha256": sha(Path(__file__)), "analyzer_sha256": sha(ANALYZER),
        "protocol_sha256": sha(PREREG), "cost_lock_sha256": sha(COST_LOCK),
        "cost_capture_sha256": sha(COST_CAPTURE), "cost_analysis_sha256": sha(COST_ANALYSIS)}


def run_config(cfg):
    replay = load_module("fanout_replay_worker", REPLAY_PATH)
    base = replay.load_base()
    base_cfg = {key: value for key, value in cfg.items() if key != "instrumentation"}
    index = replay.CONFIGS.index(base_cfg)
    if cfg["instrumentation"] == "on":
        cost = load_module("fanout_cost_worker", COST_PATH)
        return cost.worker(index)
    row = base.run_worker(base_cfg)
    row["cost_breakdown_in_lifecycle"] = {"graph_export_calls": 0, "graph_export_ns": 0,
        "canonical_digest_calls": 0, "canonical_digest_ns": 0, "instrumentation_arm": "off"}
    return row


def main():
    configs = configurations()
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing lock/capture")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentFanoutInstrumentationOverheadV1Lock",
            "locked_inputs": locked_inputs(), "schedule": schedule(), "configurations": configs},
            indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(run_config(configs[int(sys.argv[2])]), sort_keys=True)); return
    locked = locked_inputs()
    lock_data = json.loads(LOCK.read_text()) if LOCK.exists() else {}
    if lock_data.get("locked_inputs") != locked or lock_data.get("configurations") != configs:
        raise SystemExit("missing or stale pre-run source lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    rows, failures = [], []
    for index, cfg in enumerate(configs):
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(index)],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=600)
        except subprocess.TimeoutExpired as exc:
            failures.append({"index": index, "config": cfg, "error": "worker timeout", "stderr": str(exc.stderr)[-2000:]})
            continue
        if proc.returncode == 0:
            try:
                row = json.loads(proc.stdout); row["instrumentation_arm"] = cfg["instrumentation"]; rows.append(row)
            except json.JSONDecodeError as exc:
                failures.append({"index": index, "config": cfg, "error": str(exc), "stderr": proc.stderr[-2000:]})
        else:
            failures.append({"index": index, "config": cfg, "returncode": proc.returncode, "stderr": proc.stderr[-4000:]})
        print(f"worker {index + 1}/{len(configs)} {'ok' if proc.returncode == 0 else 'failed'}", flush=True)
    post = locked_inputs()
    result = {"schema": "ThoughtexperimentFanoutInstrumentationOverheadV1",
        "captured_utc": datetime.now(timezone.utc).isoformat(), "locked_inputs": locked,
        "post_run_locked_inputs": post, "source_stable": post == locked,
        "schedule": schedule(), "configs": configs, "runs": rows, "worker_failures": failures}
    if OUT.exists(): raise SystemExit("refusing to overwrite existing capture")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__": main()
