#!/usr/bin/env python3
"""Assemble independently captured, current-lock held-topic workers."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKERS = ROOT / "evaluation/reports/held_topic_structural_trace_capture_v1_workers"
LOCK = ROOT / "evaluation/substrate_capability/held_topic_structural_trace_capture_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/held_topic_structural_trace_capture_v1_20260928.json"
DRIVER = ROOT / "scripts/substrate_held_topic_structural_trace_capture_v1.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    from scripts.substrate_held_topic_structural_trace_capture_v1 import lock_inputs
    locked = json.loads(LOCK.read_text())
    if lock_inputs() != locked:
        raise SystemExit("current sources differ from held-topic structural capture lock")
    runs = []
    for replicate in range(3):
        path = WORKERS / f"replicate_{replicate}.json"
        run = json.loads(path.read_text())
        if int(run.get("replicate", -1)) != replicate:
            raise SystemExit(f"worker file has wrong replicate id: {path}")
        if run.get("driver_started_inputs") != locked or run.get("driver_finished_inputs") != locked:
            raise SystemExit(f"worker source/native fingerprint mismatch: {path}")
        runs.append(run)
    post = lock_inputs()
    RAW.write_text(json.dumps({
        "schema_version": 1,
        "run_id": "held-topic-structural-trace-capture-v1-20260928",
        "locked_inputs": locked, "post_run_inputs": post,
        "environment": {"python": sys.version, "platform": platform.platform()},
        "worker_files": [{"path": str((WORKERS / f"replicate_{i}.json").relative_to(ROOT)),
                          "sha256": sha(WORKERS / f"replicate_{i}.json")} for i in range(3)],
        "aggregator_sha256": sha(Path(__file__)), "runs": runs,
    }, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"workers": len(runs), "source_stable": post == locked,
                      "raw": str(RAW.relative_to(ROOT)), "bytes": RAW.stat().st_size}, indent=2))
    if post != locked:
        raise SystemExit("source changed during worker aggregation")


if __name__ == "__main__":
    main()
