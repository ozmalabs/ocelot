#!/usr/bin/env python3
"""Current-source replay of the archived 100k predecessor fanout workload."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
BASE_PATH = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_revision_receipt_worker_v1.py"
BASE_ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_revision_receipt_validation_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_current_source_replay_v1.py"
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_CURRENT_SOURCE_REPLAY_V1_PREREG_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_current_source_replay_v1_lock_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_current_source_replay_v1_20261004.json"
OLD_CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_100k_exploratory_20261003.json"
FRAMES, TOPOLOGY, FANOUT, NOISE_NODES = 4, "independent_states", 4, 100_000
BACKENDS, REPLICATES = ("full_copy", "shared_graph_pages"), (0, 1, 2)
CONFIGS = [dict(frames=FRAMES, topology=TOPOLOGY, fanout=FANOUT,
                 noise_nodes=NOISE_NODES, backend=backend, replicate=rep)
           for backend, rep in itertools.product(BACKENDS, REPLICATES)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("fanout_revision_receipt_base", BASE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def locked_inputs():
    base = load_base()
    return {
        "base_runner_source_lock": base.source_lock(),
        "runner_sha256": sha(Path(__file__)),
        "analyzer_sha256": sha(ANALYZER),
        "protocol_sha256": sha(PREREG),
        "base_runner_sha256": sha(BASE_PATH),
        "base_analyzer_sha256": sha(BASE_ANALYZER),
        "old_exploratory_capture_sha256": sha(OLD_CAPTURE),
    }


def main():
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing lock/capture")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentPredecessorFanoutCurrentSourceReplayV1Lock",
            "locked_inputs": locked_inputs(), "configurations": CONFIGS}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        base = load_base()
        print(json.dumps(base.run_worker(CONFIGS[int(sys.argv[2])]), sort_keys=True)); return
    locked = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale pre-run source lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    rows, failures = [], []
    for index, config in enumerate(CONFIGS):
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(index)],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=600)
        except subprocess.TimeoutExpired as exc:
            failures.append({"index": index, "config": config, "error": "worker timed out after 600 seconds",
                             "stdout": str(exc.stdout)[-1000:], "stderr": str(exc.stderr)[-2000:]})
            print(f"worker {index + 1}/{len(CONFIGS)} timed out", flush=True)
            continue
        if proc.returncode == 0:
            try:
                rows.append(json.loads(proc.stdout))
            except json.JSONDecodeError as exc:
                failures.append({"index": index, "config": config, "error": f"invalid worker JSON: {exc}", "stderr": proc.stderr[-2000:]})
        else:
            failures.append({"index": index, "config": config, "returncode": proc.returncode, "stderr": proc.stderr[-4000:]})
        print(f"worker {index + 1}/{len(CONFIGS)} {'ok' if proc.returncode == 0 else 'failed'}", flush=True)
    post = locked_inputs()
    result = {"schema": "ThoughtexperimentPredecessorFanoutCurrentSourceReplayV1",
        "captured_utc": datetime.now(timezone.utc).isoformat(), "locked_inputs": locked,
        "post_run_locked_inputs": post, "source_stable": post == locked,
        "configs": CONFIGS, "runs": rows, "worker_failures": failures}
    if OUT.exists():
        raise SystemExit("refusing to overwrite existing capture")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
