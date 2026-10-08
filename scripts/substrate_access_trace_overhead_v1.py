#!/usr/bin/env python3
"""Matched access-trace on/off request-time capture for a fixed live fixture."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import random
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ACCESS_TRACE_OVERHEAD_V1_PREREG_20261003.md"
LOCK = ROOT / "evaluation/substrate_capability/access_trace_overhead_v1_lock_20261003.json"
RAW = ROOT / "evaluation/reports/access_trace_overhead_v1_workers_raw_20261003.json.gz"
SUMMARY = ROOT / "evaluation/reports/access_trace_overhead_v1_20261003.json"
BASE_RUNNER = ROOT / "scripts/substrate_nodes_of_type_trace_capture_v2.py"
BASE_LOCK = ROOT / "evaluation/substrate_capability/nodes_of_type_trace_capture_v2_lock_20261003.json"
BASE_SUMMARY = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v2_20261003.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v2_analysis_20261003.json"
BASE_RAW = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v2_workers_raw_20261003.json.gz"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


spec = importlib.util.spec_from_file_location("nodes_type_capture_v2", BASE_RUNNER)
BASE = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(BASE)


def lock_inputs() -> dict:
    return {"protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__).resolve()),
            "base_runner_sha256": sha(BASE_RUNNER), "base_lock_sha256": sha(BASE_LOCK),
            "base_summary_sha256": sha(BASE_SUMMARY), "base_analysis_sha256": sha(BASE_ANALYSIS),
            "base_raw_sha256": sha(BASE_RAW), "base_runtime_inputs": BASE.lock_inputs()}


def worker(rep: int, mode: str) -> dict:
    os.environ["OZMA_ACCESS_TRACE"] = "1" if mode == "on" else "0"
    started = lock_inputs()
    result = BASE.worker(rep)
    finished = lock_inputs()
    return {"replicate": rep, "mode": mode, "locked_inputs_started": started,
            "locked_inputs_finished": finished, "worker_result": result}


def atomic_gzip(path: Path, data: dict) -> tuple[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".access-trace-overhead-", suffix=".json.gz", dir=path.parent)
    raw_hash = hashlib.sha256()
    try:
        with os.fdopen(fd, "wb") as out:
            with gzip.GzipFile(filename="", mode="wb", fileobj=out, compresslevel=6, mtime=0) as stream:
                for chunk in json.JSONEncoder(indent=2, sort_keys=True, default=str).iterencode(data):
                    b = chunk.encode(); raw_hash.update(b); stream.write(b)
                raw_hash.update(b"\n"); stream.write(b"\n")
            out.flush(); os.fsync(out.fileno())
        compressed_hash = sha(Path(temp)); os.replace(temp, path)
        return raw_hash.hexdigest(), compressed_hash
    except BaseException:
        try: os.unlink(temp)
        except FileNotFoundError: pass
        raise


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".access-trace-overhead-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True, default=str); f.write("\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
    except BaseException:
        try: os.unlink(temp)
        except FileNotFoundError: pass
        raise


def run() -> dict:
    from domains.engine_provenance import assert_measuring_engine
    assert_measuring_engine()
    locked = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale overhead source lock")
    jobs = [(rep, mode) for rep in range(3) for mode in ("on", "off")]
    random.Random(20261004).shuffle(jobs)
    env_base = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}
    runs, failures = [], []
    for rep, mode in jobs:
        env = {**env_base, "OZMA_ACCESS_TRACE": "1" if mode == "on" else "0"}
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep), "--mode", mode],
                              cwd=ROOT, env=env, text=True, capture_output=True)
        try: row = json.loads(proc.stdout)
        except Exception:
            row = {"replicate": rep, "mode": mode, "worker_error": "invalid_worker_json",
                   "returncode": proc.returncode, "stdout_tail": proc.stdout[-3000:],
                   "stderr_tail": proc.stderr[-3000:]}
        runs.append(row)
        if proc.returncode: failures.append({"replicate": rep, "mode": mode,
                                              "returncode": proc.returncode, "stderr_tail": proc.stderr[-3000:]})
    atomic_gzip(RAW, {"schema_version": 1, "stage": "captured_workers_preanalysis",
                      "locked_inputs": locked, "worker_order": jobs, "runs": runs,
                      "process_failures": failures})
    post = lock_inputs()
    valid = [r for r in runs if "worker_result" in r and "base_worker" in r["worker_result"]]
    by_pair = {}
    latency_rows = []
    on_event_rows = off_event_rows = work_drops = access_drops = 0
    for r in valid:
        w = r["worker_result"]["base_worker"]; capture = w["capture"]
        digests = capture.get("graph_semantic_sha256")
        pair = by_pair.setdefault(r["replicate"], {})
        pair[r["mode"]] = digests
        for qi, req in enumerate(capture["requests"]):
            access_rows = req.get("access_rows", [])
            direct = [x for x in access_rows if x[1] in ("term_nodes_of_type_query", "term_nodes_of_type_candidate")]
            if r["mode"] == "on": on_event_rows += len(access_rows)
            else: off_event_rows += len(access_rows)
            work_drops += int(req.get("work_dropped_events", 0)); access_drops += int(req.get("access_dropped_events", 0))
            latency_rows.append({"replicate": r["replicate"], "mode": r["mode"], "prompt": req["prompt"],
                                 "elapsed_ns": int(req["elapsed_ns"]),
                                 "direct_nodes_of_type_event_rows": len(direct)})
    prompts = list(BASE.V1.BASE.PROMPTS)
    shape_ok = len(valid) == 6 and all(
        [q["prompt"] for q in r["worker_result"]["base_worker"]["capture"]["requests"]] == prompts for r in valid)
    pids = [r["worker_result"]["base_worker"]["pid"] for r in valid]
    stable = post == locked and all(
        r.get("locked_inputs_started") == locked == r.get("locked_inputs_finished")
        and r["worker_result"].get("source_lock_started") == BASE.lock_inputs()
        == r["worker_result"].get("source_lock_finished")
        for r in valid)
    pair_semantics = len(by_pair) == 3 and all(set(v) == {"on", "off"} and v["on"] == v["off"] for v in by_pair.values())
    expected = json.loads(BASE.EXPECTED_GRAPH_ANALYSIS.read_text())["graph_semantic_sha256"]
    graph_match = all(v.get("on") == expected == v.get("off") for v in by_pair.values())
    on_rows = sum(x["direct_nodes_of_type_event_rows"] for x in latency_rows if x["mode"] == "on")
    lifecycle_ok = all(
        r["worker_result"]["base_worker"]["capture"]["task_result"]["turns"][0]["goal"]["status"] == "resolved"
        and r["worker_result"]["base_worker"]["capture"]["task_result"]["turns"][1]["goal_count"] == 0
        for r in valid)
    controls, control_checks = BASE.BASE.check_controls()
    checks = {
        "six_distinct_fresh_processes": len(valid) == 6 and len(set(pids)) == 6,
        "source_lock_stable": stable, "three_matched_replicate_pairs": pair_semantics,
        "semantic_digest_matches_v2_and_pairs": graph_match, "two_prompt_schedule_reproduces": shape_ok,
        "access_trace_on_events_present_and_off_events_absent": on_rows > 0 and off_event_rows == 0,
        "all_trace_drop_counters_zero": access_drops == 0 and work_drops == 0,
        "lifecycle_and_shortfall_reproduce": lifecycle_ok,
        "existing_semantic_controls_pass": all(control_checks.values()),
        "no_worker_failures": not failures,
    }
    timing = {}
    for prompt in prompts:
        obs = {(r["replicate"], r["mode"]): r["elapsed_ns"] for r in latency_rows if r["prompt"] == prompt}
        pairs = [{"replicate": rep, "on_ns": obs[(rep, "on")], "off_ns": obs[(rep, "off")],
                  "on_over_off": obs[(rep, "on")] / obs[(rep, "off")]} for rep in range(3)]
        timing[prompt] = {"pairs": pairs,
                          "on_median_ns": statistics.median(p["on_ns"] for p in pairs),
                          "off_median_ns": statistics.median(p["off_ns"] for p in pairs),
                          "median_paired_on_over_off": statistics.median(p["on_over_off"] for p in pairs),
                          "paired_ratio_min": min(p["on_over_off"] for p in pairs),
                          "paired_ratio_max": max(p["on_over_off"] for p in pairs)}
    raw = {"schema_version": 1, "run_id": "access-trace-overhead-v1-20261003",
           "locked_inputs": locked, "post_run_inputs": post, "worker_order": jobs,
           "runs": runs, "latency_rows": latency_rows, "timing_summary": timing,
           "controls": controls, "control_checks": control_checks, "process_failures": failures,
           "checks": checks, "claim_boundary": "Three paired replicates on one authored fixture; timing is descriptive and includes Python/native worker overhead, not a general engine cost model."}
    raw_sha, compressed_sha = atomic_gzip(RAW, raw)
    summary = {"schema_version": 1, "run_id": raw["run_id"], "lock_path": str(LOCK.relative_to(ROOT)),
               "lock_sha256": sha(LOCK), "raw_path": str(RAW.relative_to(ROOT)),
               "raw_sha256": raw_sha, "raw_compressed_sha256": compressed_sha,
               "checks": checks, "timing_summary": timing,
               "summary": {"workers": len(valid), "matched_pairs": len(by_pair),
                           "on_access_event_rows": on_event_rows, "off_access_event_rows": off_event_rows,
                           "latency_rows": len(latency_rows)}}
    atomic_json(SUMMARY, summary)
    print(json.dumps(summary, indent=2))
    if not all(checks.values()): raise SystemExit("paired trace overhead gates failed; raw retained")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", type=int, choices=(0, 1, 2))
    parser.add_argument("--mode", choices=("on", "off"))
    args = parser.parse_args()
    if args.lock:
        atomic_json(LOCK, {"locked_inputs": lock_inputs()}); print(LOCK.relative_to(ROOT))
    elif args.worker is not None and args.mode:
        print(json.dumps(worker(args.worker, args.mode), sort_keys=True, default=str))
    else: run()

if __name__ == "__main__": main()
