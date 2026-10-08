#!/usr/bin/env python3
"""Run uninstrumented global parity workers under one fixed Python hash seed."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_AREA_SETTLEMENT_FIXED_SEED_REPEATABILITY_V1_PREREG_20261006.md"
RUNNER = Path(__file__).resolve()
PARITY_RUNNER = ROOT / "scripts/substrate_held_topic_area_settlement_parity_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/area_settlement_fixed_seed_repeatability_v1_20261006_lock.json"
OUTDIR = ROOT / "evaluation/reports/area_settlement_fixed_seed_repeatability_v1_20261006"
CAPTURE = OUTDIR / "capture.json.gz"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parity_module():
    spec = importlib.util.spec_from_file_location("area_settlement_parity_v11", PARITY_RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lock_payload():
    parity = parity_module()
    return {"schema_version": 1, "protocol_sha256": sha(PROTOCOL),
            "runner_sha256": sha(RUNNER), "parity_runner_sha256": sha(PARITY_RUNNER),
            "parity_lock": parity.lock_payload(), "worker_environment": {"PYTHONHASHSEED": "0"},
            "workers": 3, "arm": "global", "turns": 7}


def main():
    if sys.argv[1:] == ["--lock"]:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    expected = lock_payload()
    if not LOCK.exists() or json.loads(LOCK.read_text()) != expected:
        raise SystemExit("source lock absent or stale")
    if CAPTURE.exists():
        raise SystemExit(f"refusing to overwrite {CAPTURE}")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / "runners/dsl/python"),
                                         str(ROOT / "scripts"), env.get("PYTHONPATH", "")])
    runs = []
    for rep in range(3):
        proc = subprocess.run([sys.executable, str(PARITY_RUNNER), "--worker", "global", str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        result = json.loads(proc.stdout)
        turns = []
        for index, row in enumerate(result["turns"]):
            parity = row.get("settlement_parity", {})
            turns.append({"prompt": row.get("prompt"), "reply": row.get("reply"),
                          "graph_sha256": parity.get("graph_sha256"),
                          "graph_wl_sha256": parity.get("graph_wl_sha256"),
                          "node_count": parity.get("node_count"), "edge_count": parity.get("edge_count"),
                          "final_snapshot_zlib_b64": parity.get("graph_snapshot_zlib_b64") if index == 6 else None})
        runs.append({"arm": result["arm"], "replicate": result["replicate"], "pid": result["pid"],
                     "worker_source_stable": result["worker_source_stable"],
                     "worker_input_sha256": result["worker_input_sha256"], "turns": turns,
                     "final_graph": result["final_graph"]})
    ended = lock_payload()
    payload = {"schema": "AreaSettlementFixedSeedRepeatabilityV1", "locked_inputs": expected,
               "post_run_inputs": ended, "environment": {"PYTHONHASHSEED": "0",
                   "python": sys.version, "platform": platform.platform()}, "runs": runs}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    CAPTURE.write_bytes(gzip.compress(json.dumps(payload, sort_keys=True,
        separators=(",", ":"), default=str).encode(), compresslevel=6, mtime=0))
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)), "workers": len(runs),
                      "source_stable": ended == expected}, indent=2))
    if ended != expected:
        raise SystemExit("source changed during capture")


if __name__ == "__main__":
    main()
