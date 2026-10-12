#!/usr/bin/env python3
"""Instrument graph export and digest costs in the 100k thoughtexperiment."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
REPLAY_PATH = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_revision_receipt_replay_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_revision_receipt_validation_v1.py"
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_REVISION_RECEIPT_VALIDATION_V1_PREREG_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_revision_receipt_v1_lock_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_revision_receipt_v1_20261004.json"
REPLAY_LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_current_source_replay_v1_lock_20261004.json"
REPLAY_CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_current_source_replay_v1_20261004.json"
REPLAY_ANALYSIS = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_current_source_replay_v1_analysis_20261004.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_replay():
    spec = importlib.util.spec_from_file_location("fanout_current_replay", REPLAY_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def locked_inputs():
    replay = load_replay()
    return {
        "replay_locked_inputs": replay.locked_inputs(),
        "runner_sha256": sha(Path(__file__)),
        "analyzer_sha256": sha(ANALYZER),
        "protocol_sha256": sha(PREREG),
        "replay_lock_sha256": sha(REPLAY_LOCK),
        "replay_capture_sha256": sha(REPLAY_CAPTURE),
        "replay_analysis_sha256": sha(REPLAY_ANALYSIS),
    }


class Instrumentation:
    def __init__(self):
        self.active = False
        self.graph_export_ns = 0
        self.graph_export_calls = 0
        self.canonical_digest_ns = 0
        self.canonical_digest_calls = 0


def worker(index: int) -> dict:
    from substrate_rs import Substrate
    replay = load_replay()
    base = replay.load_base()
    cfg = replay.CONFIGS[index]
    tracker = Instrumentation()
    clock = time.perf_counter_ns
    source_lines, first_line = inspect.getsourcelines(base.run_worker)
    tree = ast.parse("".join(source_lines))
    start_line = end_line = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = {t.id for t in node.targets if isinstance(t, ast.Name)}
            if "lifecycle_start" in names:
                start_line = first_line + node.lineno - 1
            elif "lifecycle_ns" in names:
                end_line = first_line + node.lineno - 1
    if start_line is None or end_line is None:
        raise RuntimeError("could not identify lifecycle timer boundaries")

    class ClockProxy:
        @staticmethod
        def perf_counter_ns():
            caller = inspect.currentframe().f_back
            now = clock()
            if caller.f_code is base.run_worker.__code__:
                if caller.f_lineno == start_line:
                    tracker.active = True
                elif caller.f_lineno == end_line:
                    tracker.active = False
            return now

    original_graph_export = Substrate.graph_to_dict
    original_graph_digest = base.canonical_graph_digest

    def graph_export(self):
        started = clock()
        result = original_graph_export(self)
        elapsed = clock() - started
        if tracker.active:
            tracker.graph_export_calls += 1
            tracker.graph_export_ns += elapsed
        return result

    def graph_digest(graph):
        started = clock()
        result = original_graph_digest(graph)
        elapsed = clock() - started
        if tracker.active:
            tracker.canonical_digest_calls += 1
            tracker.canonical_digest_ns += elapsed
        return result

    Substrate.graph_to_dict = graph_export
    base.canonical_graph_digest = graph_digest
    base.time = ClockProxy
    try:
        row = base.run_worker(cfg)
    finally:
        Substrate.graph_to_dict = original_graph_export
        base.canonical_graph_digest = original_graph_digest
    row["cost_breakdown_in_lifecycle"] = {
        "graph_export_calls": tracker.graph_export_calls,
        "graph_export_ns": tracker.graph_export_ns,
        "canonical_digest_calls": tracker.canonical_digest_calls,
        "canonical_digest_ns": tracker.canonical_digest_ns,
        "timer_boundary_source_lines": {"lifecycle_start": start_line, "lifecycle_ns": end_line},
    }
    return row


def main():
    replay = load_replay()
    configs = replay.CONFIGS
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing lock/capture")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentPredecessorFanoutCostBreakdownV1Lock",
            "locked_inputs": locked_inputs(), "configurations": configs}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True)); return
    locked = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale pre-run source lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    rows, failures = [], []
    for index, config in enumerate(configs):
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(index)],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=600)
        except subprocess.TimeoutExpired as exc:
            failures.append({"index": index, "config": config, "error": "worker timed out after 600 seconds",
                             "stderr": str(exc.stderr)[-2000:]})
            continue
        if proc.returncode == 0:
            try:
                rows.append(json.loads(proc.stdout))
            except json.JSONDecodeError as exc:
                failures.append({"index": index, "config": config, "error": f"invalid JSON: {exc}", "stderr": proc.stderr[-2000:]})
        else:
            failures.append({"index": index, "config": config, "returncode": proc.returncode, "stderr": proc.stderr[-4000:]})
        print(f"worker {index + 1}/{len(configs)} {'ok' if proc.returncode == 0 else 'failed'}", flush=True)
    post = locked_inputs()
    result = {"schema": "ThoughtexperimentPredecessorFanoutCostBreakdownV1",
        "captured_utc": datetime.now(timezone.utc).isoformat(), "locked_inputs": locked,
        "post_run_locked_inputs": post, "source_stable": post == locked,
        "configs": configs, "runs": rows, "worker_failures": failures}
    if OUT.exists():
        raise SystemExit("refusing to overwrite existing capture")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
