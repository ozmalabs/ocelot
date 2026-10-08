#!/usr/bin/env python3
"""Current-source replay for typed-population access trace events."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_NODES_OF_TYPE_TRACE_CAPTURE_V1_PREREG_20261003.md"
LOCK = ROOT / "evaluation/substrate_capability/nodes_of_type_trace_capture_v1_lock_20261003.json"
RAW = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v1_workers_raw_20261003.json.gz"
SUMMARY = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v1_20261003.json"
BASE_RUNNER = ROOT / "scripts/substrate_live_frame_rule_scope_capture_v1_1.py"
BASE_ANALYSIS = ROOT / "evaluation/reports/live_frame_rule_scope_capture_v1_1_analysis_20261003.json"
EXPECTED_GRAPH_ANALYSIS = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_analysis_20261003.json"
BASE_SUMMARY = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_1_20261003.json"
BASE_RAW = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_1_workers_raw_20261003.json.gz"
TERM_INVENTORY = ROOT / "evaluation/reports/term_access_dependency_coverage_v1_2_20261003.json"
TRACE_INVENTORY = ROOT / "evaluation/reports/substrate_runtime_access_trace_coverage_v1_3_20261003.json"
SOURCES = [ROOT / p for p in (
    "runners/dsl/src/term.rs", "runners/dsl/src/access_trace.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import assert_measuring_engine  # noqa: E402

spec = importlib.util.spec_from_file_location("rule_scope_capture_v1_1", BASE_RUNNER)
BASE = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(BASE)
V1 = BASE.V1

# The v1.1 helper refuses to proceed when its historical v1 lock differs from
# today's source. Preserve the fixture worker but give this new, versioned
# replay its own complete lock instead of rewriting that historical lock.
def current_base_inputs() -> dict:
    return {
        "capture_v1_runtime_inputs": V1.lock_inputs(),
        "capture_v1_1_protocol_sha256": sha(BASE.PROTOCOL),
        "capture_v1_1_runner_sha256": sha(BASE_RUNNER),
        "capture_v1_1_lock_sha256": sha(BASE.LOCK),
        "capture_v1_1_summary_sha256": sha(BASE_SUMMARY),
        "capture_v1_1_analysis_sha256": sha(BASE_ANALYSIS),
        "expected_graph_analysis_sha256": sha(EXPECTED_GRAPH_ANALYSIS),
        "capture_v1_1_raw_sha256": sha(BASE_RAW),
    }

BASE.lock_inputs = current_base_inputs


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def lock_inputs() -> dict:
    return {
        "protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__).resolve()),
        "base_capture_runner_sha256": sha(BASE_RUNNER),
        "base_analysis_sha256": sha(BASE_ANALYSIS), "base_summary_sha256": sha(BASE_SUMMARY),
        "base_raw_archive_sha256": sha(BASE_RAW),
        "term_inventory_sha256": sha(TERM_INVENTORY),
        "trace_inventory_sha256": sha(TRACE_INVENTORY),
        "sources_sha256": {str(p.relative_to(ROOT)): sha(p) for p in SOURCES},
        "base_runtime_inputs": BASE.lock_inputs(),
    }


def worker(rep: int) -> dict:
    assert_measuring_engine()
    started = lock_inputs()
    result = BASE.worker(rep)
    finished = lock_inputs()
    return {"replicate": rep, "source_lock_started": started,
            "source_lock_finished": finished, "base_worker": result}


def atomic_gzip(path: Path, value: dict) -> tuple[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".nodes-of-type-trace-", suffix=".json.gz", dir=path.parent)
    raw_hash = hashlib.sha256()
    try:
        with os.fdopen(fd, "wb") as target:
            with gzip.GzipFile(filename="", mode="wb", fileobj=target, compresslevel=6, mtime=0) as stream:
                for chunk in json.JSONEncoder(indent=2, sort_keys=True, default=str).iterencode(value):
                    b = chunk.encode(); raw_hash.update(b); stream.write(b)
                raw_hash.update(b"\n"); stream.write(b"\n")
            target.flush(); os.fsync(target.fileno())
        compressed_hash = sha(Path(temp))
        os.replace(temp, path)
        return raw_hash.hexdigest(), compressed_hash
    except BaseException:
        try: os.unlink(temp)
        except FileNotFoundError: pass
        raise


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".nodes-of-type-trace-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(value, f, indent=2, sort_keys=True, default=str); f.write("\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
    except BaseException:
        try: os.unlink(temp)
        except FileNotFoundError: pass
        raise


def run() -> dict:
    assert_measuring_engine()
    locked = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock; use --lock after protocol/runner final")
    env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}
    jobs = [0, 1, 2]; random.Random(20261003).shuffle(jobs)
    runs, errors = [], []
    for rep in jobs:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True)
        try: payload = json.loads(proc.stdout)
        except Exception:
            payload = {"replicate": rep, "worker_error": "invalid_worker_json",
                       "returncode": proc.returncode, "stdout_tail": proc.stdout[-3000:],
                       "stderr_tail": proc.stderr[-3000:]}
        runs.append(payload)
        if proc.returncode: errors.append({"replicate": rep, "returncode": proc.returncode,
                                            "stderr_tail": proc.stderr[-3000:]})
    # Preserve completed worker output before any analysis/gate code can fail.
    atomic_gzip(RAW, {"schema_version": 1, "stage": "captured_workers_preanalysis",
                      "locked_inputs": locked, "worker_order": jobs, "runs": runs,
                      "process_errors": errors})
    post = lock_inputs()
    valid = [r for r in runs if "base_worker" in r and "capture" in r["base_worker"]]
    expected_digest = json.loads(EXPECTED_GRAPH_ANALYSIS.read_text())["graph_semantic_sha256"]
    prompts = list(V1.BASE.PROMPTS)
    request_schedule = all([q.get("prompt") for q in r["base_worker"]["capture"]["requests"]] == prompts
                           for r in valid) and len(valid) == 3
    no_drops = all(q.get("access_dropped_events") == 0 and q.get("work_dropped_events") == 0
                   for r in valid for q in r["base_worker"]["capture"]["requests"])
    stable = post == locked and all(r.get("source_lock_started") == locked == r.get("source_lock_finished")
                                    for r in valid)
    digests = {r["base_worker"]["capture"].get("graph_semantic_sha256") for r in valid}
    digest_match = digests == {expected_digest}
    event_summary = {}
    candidate_consistency = True
    for r in valid:
        for qi, req in enumerate(r["base_worker"]["capture"]["requests"]):
            rows = req.get("access_rows", [])
            grouped = {}
            for row in rows:
                uid, kind, node, resource, peer_node, peer_resource, count = row
                key = (int(uid), str(kind), node, resource, peer_node, peer_resource)
                grouped[key] = grouped.get(key, 0) + int(count)
            type_reads = {}
            for (uid, kind, node, resource, _pn, _pr), count in grouped.items():
                if kind == "term_type_read": type_reads[(uid, node, resource)] = count
            local = {"replicate": r["replicate"], "request_index": qi, "prompt": req.get("prompt"),
                     "query_rows": [], "candidate_rows": [], "empty_candidate_query_groups": []}
            for row in rows:
                uid, kind, node, resource, peer_node, peer_resource, count = row
                if kind == "term_typed_population_query":
                    qgroup = {"rule_uid": uid, "node_type": resource or peer_resource, "count": count}
                    local["query_rows"].append(qgroup)
                elif kind == "term_typed_population_candidate":
                    local["candidate_rows"].append({"rule_uid": uid, "node_id": node,
                                                     "node_type": resource or peer_resource, "count": count})
                    if type_reads.get((uid, node, resource), 0) < int(count): candidate_consistency = False
            candidate_groups = {(row[0], row[3]) for row in rows
                                if row[1] == "term_typed_population_candidate"}
            local["empty_candidate_query_groups"] = [q for q in local["query_rows"]
                if not any(int(c["rule_uid"]) == int(q["rule_uid"]) and c["node_type"] == q["node_type"]
                           for c in local["candidate_rows"])]
            event_summary[f"rep{r['replicate']}_request{qi}"] = local
    controls, control_checks = BASE.check_controls()
    lifecycle_ok = all(
        r["base_worker"]["capture"]["task_result"]["turns"][0]["goal"]["status"] == "resolved"
        and r["base_worker"]["capture"]["task_result"]["turns"][1]["goal_count"] == 0
        for r in valid
    )
    checks = {
        "three_distinct_fresh_pids": len(valid) == 3 and len({r["base_worker"]["pid"] for r in valid}) == 3,
        "source_lock_stable": stable, "two_prompt_schedule_reproduces": request_schedule,
        "semantic_graph_matches_v1_1_and_reproduces": digest_match,
        "access_and_work_traces_have_no_dropped_rows": no_drops,
        "candidate_rows_agree_with_type_reads": candidate_consistency,
        "task_lifecycle_and_shortfall_reproduce": lifecycle_ok,
        "existing_semantic_controls_pass": all(control_checks.values()),
        "no_worker_process_failures": not errors,
    }
    raw = {"schema_version": 1, "run_id": "nodes-of-type-trace-capture-v1-20261003",
           "locked_inputs": locked, "post_run_inputs": post, "worker_order": jobs,
           "runs": runs, "controls": controls, "control_checks": control_checks,
           "process_errors": errors, "event_summary": event_summary, "checks": checks,
           "claim_boundary": "Three workers and one authored two-prompt fixture measure source-built event coverage only; no locality prevalence, exact factor scope, or scaling claim."}
    raw_sha, compressed_sha = atomic_gzip(RAW, raw)
    summary = {"schema_version": 1, "run_id": raw["run_id"], "lock_path": str(LOCK.relative_to(ROOT)),
               "lock_sha256": sha(LOCK), "raw_path": str(RAW.relative_to(ROOT)),
               "raw_sha256": raw_sha, "raw_compressed_sha256": compressed_sha,
               "raw_compression": "gzip; decompressed hash recorded", "checks": checks,
               "summary": {"workers": len(valid), "request_count": sum(len(r["base_worker"]["capture"]["requests"]) for r in valid),
                           "new_query_event_rows": sum(len(v["query_rows"]) for v in event_summary.values()),
                           "new_candidate_event_rows": sum(len(v["candidate_rows"]) for v in event_summary.values()),
                           "empty_candidate_query_groups": sum(len(v["empty_candidate_query_groups"]) for v in event_summary.values())}}
    atomic_json(SUMMARY, summary)
    print(json.dumps(summary, indent=2))
    if not all(checks.values()): raise SystemExit("one or more preregistered gates failed; raw capture retained")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", type=int, choices=(0, 1, 2))
    args = parser.parse_args()
    assert_measuring_engine()
    if args.lock:
        atomic_json(LOCK, {"locked_inputs": lock_inputs()}); print(LOCK.relative_to(ROOT))
    elif args.worker is not None:
        print(json.dumps(worker(args.worker), sort_keys=True, default=str))
    else: run()

if __name__ == "__main__": main()
