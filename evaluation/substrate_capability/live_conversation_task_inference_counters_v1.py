#!/usr/bin/env python3
"""Capture per-request native inference counters on the task-diverse live panel."""
from __future__ import annotations

import gzip
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
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/LIVE_CONVERSATION_TASK_INFERENCE_COUNTERS_V1_PREREG_20261006.md"
BASE_RUNNER = ROOT / "evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py"
BASE_PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_CONVERSATION_TASK_GRAPH_HARVEST_V2_PREREG_20261004.md"
BASE_LOCK = ROOT / "evaluation/substrate_capability/live_conversation_task_graph_harvest_v2_lock_20261004.json"
BASE_ANALYZER = ROOT / "evaluation/substrate_capability/analyze_live_conversation_task_graph_harvest_v2.py"
BASE_ANALYSIS = ROOT / "evaluation/reports/live_conversation_task_graph_harvest_v2_analysis_20261004.json"
BASE_RAW = ROOT / "evaluation/reports/live_conversation_task_graph_harvest_v2_20261004.jsonl.gz"
LOCK = ROOT / "evaluation/substrate_capability/live_conversation_task_inference_counters_v1_lock_20261006.json"
OUT = ROOT / "evaluation/reports/live_conversation_task_inference_counters_v1_20261006.json"
COUNTERS = ("dim_infer_arg_calls", "term_eval:DimInfer", "term_eval:GenInfer",
            "term_eval:ShapeDecode", "term_eval:TransformDecode",
            "term_unit:ShapeDecode", "term_unit:TransformDecode")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def base_module():
    spec = importlib.util.spec_from_file_location("live_conversation_task_graph_harvest_v2", BASE_RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def inputs() -> dict:
    from substrate_rs import _native
    from domains.engine_provenance import provenance_line
    module = base_module()
    paths = (RUNNER, PROTOCOL, BASE_RUNNER, BASE_PROTOCOL, BASE_LOCK, BASE_ANALYZER, BASE_ANALYSIS, BASE_RAW,
             ROOT / "runners/dsl/Cargo.toml", ROOT / "runners/dsl/Cargo.lock",
             ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
             ROOT / "scripts/substrate_seed_rule_provenance_live_capture_v1.py")
    return {"files": {str(path.relative_to(ROOT)): sha(path) for path in paths},
            "base_runtime_inputs": module.inputs(),
            "native_sha256": sha(Path(_native.__file__).resolve()),
            "native_provenance": provenance_line()}


def worker(condition: str, replicate: int) -> dict:
    from substrate_rs import _native
    from domains.engine_provenance import assert_measuring_engine
    from substrate.world_adapter import WorldAdapter
    assert_measuring_engine()
    locked = inputs()
    base = base_module()
    native = _native.Substrate
    original = WorldAdapter.converse
    observations = []

    def counted(agent, *args, **kwargs):
        native.scale_audit_set_enabled(False)
        native.scale_audit_set_per_rule_enabled(False)
        native.scale_audit_reset()
        native.scale_audit_per_rule_reset()
        native.scale_audit_set_enabled(True)
        prompt = str(args[0]) if args else None
        started = time.perf_counter_ns()
        try:
            return original(agent, *args, **kwargs)
        finally:
            elapsed = time.perf_counter_ns() - started
            rows = native.scale_audit_snapshot()
            counter_map = {str(row[0]): int(row[1]) for row in rows if len(row) >= 2}
            observations.append({"prompt": prompt, "instrumented_call_elapsed_ns": elapsed,
                                 "counters": {key: counter_map.get(key, 0) for key in COUNTERS}})
            native.scale_audit_set_enabled(False)
            native.scale_audit_set_per_rule_enabled(False)

    WorldAdapter.converse = counted
    try:
        result = base.worker(condition, replicate)
    finally:
        WorldAdapter.converse = original
        native.scale_audit_set_enabled(False)
        native.scale_audit_set_per_rule_enabled(False)
    analyzer = importlib.util.spec_from_file_location("live_task_graph_harvest_analyzer", BASE_ANALYZER)
    analyzer_module = importlib.util.module_from_spec(analyzer)
    assert analyzer and analyzer.loader
    analyzer.loader.exec_module(analyzer_module)
    task_contract = analyzer_module.task_oracle(result)
    return {"condition": condition, "replicate": replicate,
            "source_stable": result.get("source_stable", False),
            "locked_inputs": locked, "post_run_inputs": inputs(),
            "boot_loaded": result.get("boot_loaded"), "boot_failures": result.get("boot_failures"),
            "task_contract_pass": task_contract, "reply": result.get("reply"),
            "action_results": result.get("action_results", []),
            "task_wall_ns_instrumented": result.get("task_wall_ns"),
            "task_process_cpu_ns_instrumented": result.get("task_process_cpu_ns"),
            "request_observations": observations}


def validate(rows: list[dict], locked: dict, post: dict) -> None:
    module = base_module()
    expected = list(module.SCHEDULE)
    actual = [(row["condition"], row["replicate"]) for row in rows]
    if actual != expected or len(rows) != 10:
        raise RuntimeError("task schedule mismatch")
    if locked != post or any(row["locked_inputs"] != locked or row["post_run_inputs"] != locked or
                             not row["source_stable"] or not row["boot_loaded"] or
                             len(row["request_observations"]) != 1
                             for row in rows):
        raise RuntimeError("source/boot/request integrity failure")
    by_condition = {}
    for row in rows:
        by_condition.setdefault(row["condition"], []).append(row)
    for condition, pair in by_condition.items():
        if len(pair) != 2 or pair[0]["task_contract_pass"] != pair[1]["task_contract_pass"] or \
                pair[0]["reply"] != pair[1]["reply"] or pair[0]["action_results"] != pair[1]["action_results"]:
            raise RuntimeError(f"task repeat parity failed: {condition}")


def main() -> int:
    args = sys.argv[1:]
    if args == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing task counter artifacts")
        LOCK.write_text(json.dumps({"schema": "LiveConversationTaskInferenceCountersV1Lock",
                                    "locked_inputs": inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if len(args) == 3 and args[0] == "--worker":
        print(json.dumps(worker(args[1], int(args[2])), sort_keys=True, separators=(",", ":")))
        return 0
    if args:
        raise SystemExit("usage: live_conversation_task_inference_counters_v1.py [--lock|--worker CONDITION REP]")
    locked = json.loads(LOCK.read_text()).get("locked_inputs")
    if locked != inputs():
        raise SystemExit("missing or stale source lock")
    base = base_module()
    rows = []
    for condition, replicate in base.SCHEDULE:
        env = dict(os.environ, OZMA_NO_LLM="1", OZMA_SEED_PERSIST_DISABLED="1",
                   OCEL0_TASK_CONDITION=condition, OCEL0_TASK_REP=str(replicate))
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", condition, str(replicate)],
                              cwd=ROOT, env=env, text=True, capture_output=True, timeout=300)
        if proc.returncode:
            raise RuntimeError(f"worker failed {condition}/{replicate}: {proc.stderr[-1800:]}")
        rows.append(json.loads(proc.stdout))
        print(f"completed={condition}/{replicate}", file=sys.stderr, flush=True)
    post = inputs()
    validate(rows, locked, post)
    passed = sum(bool(row["task_contract_pass"]) for row in rows)
    by_condition = {}
    for row in rows:
        by_condition.setdefault(row["condition"], []).append(row)
    summary = {}
    for condition, pair in by_condition.items():
        one = pair[0]["request_observations"][0]["counters"]
        summary[condition] = {"replicate_task_contract_pass": [x["task_contract_pass"] for x in pair],
                              "replicate_counters": [x["request_observations"][0]["counters"] for x in pair],
                              "median_counters": {key: sorted(x["request_observations"][0]["counters"][key]
                                                                for x in pair)[len(pair)//2] for key in COUNTERS}}
    payload = {"schema": "LiveConversationTaskInferenceCountersV1",
               "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "host": platform.platform(), "locked_inputs": locked, "post_run_inputs": post,
               "source_stable": locked == post, "task_schedule": base.SCHEDULE,
               "worker_count": len(rows), "task_contract_passes": passed,
               "task_contract_pass_count_by_condition": {k: v[0]["task_contract_pass"] for k,v in by_condition.items()},
               "instrumented_counts_only": True, "task_diversity_claim": "five authored production-route conditions, not sampled natural traffic",
               "counter_names": list(COUNTERS), "per_condition": summary, "workers": rows}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "workers": len(rows),
                      "task_contract_passes": passed, "source_stable": locked == post}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
