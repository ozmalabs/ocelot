#!/usr/bin/env python3
"""Factorial relation-count × matrix-bound GenInfer work capture."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
BASE_PROFILE = ROOT / "evaluation/substrate_capability/substrate_geninfer_training_work_profile_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_geninfer_training_work_profile_v2.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_TRAINING_WORK_PROFILE_V2_PREREG_20261006.md"
V1 = ROOT / "evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py"
OUT = ROOT / "evaluation/reports/substrate_geninfer_training_work_profile_v2_20261006.json"
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def base_module():
    spec = importlib.util.spec_from_file_location("geninfer_work_profile_v1", BASE_PROFILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cases():
    return [
        {"id": f"positive_n{n}_b{bound}_r{rep}", "kind": "positive", "n": n,
         "bound": bound, "repeat": rep}
        for n in (4, 16, 64) for bound in (3, 5, 7) for rep in (1, 2, 3)
    ]


def worker(case):
    base_module().worker(case)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--prepare":
        base_module().prepare(sys.argv[2])
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(json.loads(sys.argv[2]))
        return
    if sys.argv[1:] != ["--run"]:
        raise SystemExit("usage: --prepare 64_SHARD_SO | --run | --worker CASE_JSON")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    base = base_module()
    native = base.TREE / "runners/dsl/python/substrate_rs/_native.abi3.so"
    record = base.TREE / "runners/dsl/python/substrate_rs/_native.build.json"
    if not native.is_file() or not record.is_file():
        raise SystemExit("prepare the current-source 64-shard overlay first")
    locked = {"runner_sha256": sha(RUNNER), "protocol_sha256": sha(PROTOCOL),
              "analyzer_sha256": sha(ANALYZER), "base_profile_sha256": sha(BASE_PROFILE),
              "v1_runner_sha256": sha(V1)}
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    rows = []
    for case in cases():
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", json.dumps(case)], cwd=ROOT,
                              env=env, text=True, capture_output=True, timeout=600)
        if proc.returncode:
            raise RuntimeError(f"worker {case['id']} failed: {proc.stderr}")
        rows.append(json.loads(proc.stdout))
    if locked != {"runner_sha256": sha(RUNNER), "protocol_sha256": sha(PROTOCOL),
                  "analyzer_sha256": sha(ANALYZER), "base_profile_sha256": sha(BASE_PROFILE),
                  "v1_runner_sha256": sha(V1)}:
        raise RuntimeError("source drift during factorial capture")
    payload = {
        "schema": "GenInferTrainingWorkProfileV2Results",
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.platform(), **locked, "case_spec": cases(), "worker_count": len(rows),
        "source_stable": all(row.get("source_stable") for row in rows),
        "source_sha256_by_worker": [row["source_before"]["source_sha256"] for row in rows],
        "cases": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "worker_count": len(rows),
                      "source_stable": payload["source_stable"]}))


if __name__ == "__main__":
    main()
