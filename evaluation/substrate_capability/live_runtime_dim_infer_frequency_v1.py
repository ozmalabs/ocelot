#!/usr/bin/env python3
"""Compact source-locked analysis of DimInfer counters in a live-runtime pilot."""
from __future__ import annotations

import gzip
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/LIVE_RUNTIME_DIM_INFER_FREQUENCY_V1_PREREG_20261006.md"
RAW = ROOT / "evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz"
RAW_LOCK = ROOT / "evaluation/substrate_capability/live_runtime_closure_counters_v1_6_lock_20261004.json"
RAW_ANALYSIS = ROOT / "evaluation/reports/live_runtime_closure_counters_v1_6_analysis_20261004.json"
LOCK = ROOT / "evaluation/substrate_capability/live_runtime_dim_infer_frequency_v1_lock_20261006.json"
OUT = ROOT / "evaluation/reports/live_runtime_dim_infer_frequency_v1_20261006.json"
PROMPTS = ("report your organisation", "describe who you are")
COUNTERS = ("dim_infer_arg_calls", "term_eval:DimInfer", "term_eval:GenInfer",
            "term_eval:ShapeDecode", "term_eval:TransformDecode",
            "term_unit:ShapeDecode", "term_unit:TransformDecode")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs() -> dict:
    paths = (RUNNER, PROTOCOL, RAW, RAW_LOCK, RAW_ANALYSIS)
    return {str(path.relative_to(ROOT)): sha(path) for path in paths}


def extract() -> dict:
    integrity = json.loads(RAW_ANALYSIS.read_text())
    if not integrity.get("passed"):
        raise RuntimeError("existing v1.6 independent analysis did not pass")
    with gzip.open(RAW, "rt", encoding="utf-8") as stream:
        capture = json.load(stream)
    if not capture.get("source_stable") or not capture.get("all_checks_pass"):
        raise RuntimeError("existing v1.6 capture integrity failed")
    runs = [run for run in capture.get("runs", []) if run.get("audit_mode") == "on"]
    if {int(run.get("replicate", -1)) for run in runs} != {0, 1, 2}:
        raise RuntimeError("expected three audit-on replicates")
    observations = []
    for run in runs:
        if run.get("worker_returncode") != 0:
            raise RuntimeError("nonzero worker return code in source capture")
        by_prompt = {}
        for obs in run.get("native_counter_observations", []):
            prompt = obs.get("prompt")
            if prompt not in PROMPTS or prompt in by_prompt:
                raise RuntimeError("unexpected or repeated prompt observation")
            rows = obs.get("counter_rows", {}).get("global")
            if not isinstance(rows, list):
                raise RuntimeError("missing global counter schema")
            counter_map = {str(row[0]): int(row[1]) for row in rows if isinstance(row, list) and len(row) >= 2}
            by_prompt[prompt] = {name: counter_map.get(name, 0) for name in COUNTERS}
        if set(by_prompt) != set(PROMPTS):
            raise RuntimeError("prompt pair incomplete in replicate")
        for prompt in PROMPTS:
            observations.append({"replicate": int(run["replicate"]), "prompt": prompt,
                                 "counters": by_prompt[prompt]})
    if len(observations) != 6:
        raise RuntimeError("expected exactly six prompt executions")
    summary = {}
    for prompt in PROMPTS:
        rows = [obs["counters"] for obs in observations if obs["prompt"] == prompt]
        summary[prompt] = {
            name: {"values": [row[name] for row in rows],
                   "median": statistics.median(row[name] for row in rows),
                   "min": min(row[name] for row in rows),
                   "max": max(row[name] for row in rows)}
            for name in COUNTERS
        }
    return {"schema": "LiveRuntimeDimInferFrequencyV1",
            "population": "two repeated live-runtime self-report prompt routes; three audit-on replicates",
            "sample_count": len(observations), "prompt_routes": list(PROMPTS),
            "observations": observations, "summary": summary,
            "scope_limit": "not representative natural-task prevalence; instrumented counters are not timing",
            "source_capture_sha256": sha(RAW), "source_analysis_sha256": sha(RAW_ANALYSIS)}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing pilot artifacts")
        LOCK.write_text(json.dumps({"schema": "LiveRuntimeDimInferFrequencyV1Lock",
                                    "inputs": inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if sys.argv[1:]:
        raise SystemExit("usage: live_runtime_dim_infer_frequency_v1.py [--lock]")
    locked = json.loads(LOCK.read_text())
    if locked.get("inputs") != inputs():
        raise SystemExit("missing or stale source lock")
    result = extract()
    result["inputs"] = inputs()
    result["lock_sha256"] = sha(LOCK)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    positives = sum(obs["counters"]["dim_infer_arg_calls"] > 0 for obs in result["observations"])
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "sample_count": result["sample_count"],
                      "prompt_executions_with_dim_infer_args": positives,
                      "source_stable": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
