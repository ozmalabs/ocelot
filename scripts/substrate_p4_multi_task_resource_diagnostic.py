#!/usr/bin/env python3
"""Measure repeated P4 acquisition outcomes/resources over a locked task family."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
import substrate_rs as srs
import prog_synthesis_battery as p4
from domains import prog_synthesis as psy

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_P4_MULTI_TASK_RESOURCE_DIAGNOSTIC_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/p4_multi_task_resource_diagnostic_lock_20260925.json"
FIXTURE = ROOT / "tests/fixtures/substrate_string_pbe_contrast/tasks.json"
NATIVE = Path(srs._native.__file__).resolve()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rss_kib():
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except OSError:
        pass
    return None


def score(sub, ir, task):
    rows = []
    for group, key in (("revealed", "example_rows"), ("held_out", "held_out_rows")):
        for i, row in enumerate(task[key]):
            start = time.perf_counter_ns()
            got, ok = psy._eval_ir_on(sub, ir, row["inputs"])
            rows.append({"group": group, "index": i, "expected": row["expected"],
                         "got": got, "helper_ok": bool(ok),
                         "matches": bool(ok) and got == row["expected"],
                         "wall_ns": time.perf_counter_ns() - start})
    return rows


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: substrate_p4_multi_task_resource_diagnostic.py OUTPUT.json")
    output = Path(sys.argv[1])
    lock = json.loads(LOCK.read_text())
    locked = {
        "preregistration_sha256": PREREG,
        "runner_sha256": Path(__file__).resolve(),
        "fixture_sha256": FIXTURE,
        "p4_runner_sha256": ROOT / "scripts/prog_synthesis_battery.py",
        "adapter_sha256": ROOT / "domains/prog_synthesis.py",
        "retrieval_sha256": ROOT / "domains/prog_retrieval.py",
        "seed_sha256": ROOT / "seeds/program_synthesis.json",
        "native_sha256": NATIVE,
    }
    if any(lock.get(k) != sha(v) for k, v in locked.items()):
        raise SystemExit("P4 multi-task diagnostic lock mismatch")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")

    suite = json.loads(FIXTURE.read_text())
    task_records = []
    for index, task in enumerate(suite["tasks"]):
        boot_wall0 = time.perf_counter_ns(); boot_cpu0 = time.process_time_ns()
        sub, agent = p4.boot(frozen=False)
        boot_wall = time.perf_counter_ns() - boot_wall0
        boot_cpu = time.process_time_ns() - boot_cpu0
        before = {"arena_nodes": sub._inner.term_arena_len(), "graph_nodes": sub.node_count(), "rss_kib": rss_kib()}
        examples = [(r["inputs"], r["expected"]) for r in task["example_rows"]]
        route_wall0 = time.perf_counter_ns(); route_cpu0 = time.process_time_ns()
        result = psy.synthesize_from_request(sub, agent, task["request_text"], examples, name=task["id"])
        route_wall = time.perf_counter_ns() - route_wall0
        route_cpu = time.process_time_ns() - route_cpu0
        after = {"arena_nodes": sub._inner.term_arena_len(), "graph_nodes": sub.node_count(), "rss_kib": rss_kib()}
        ir = result.get("ir") if isinstance(result, dict) else None
        scored = score(sub, ir, task) if result.get("status") == "accepted" and isinstance(ir, dict) else []
        task_records.append({
            "fixture_index": index, "task_id": task["id"],
            "status": result.get("status"), "construction": result.get("construction"),
            "rungs": result.get("rungs"), "gap_reason": result.get("gap_reason"),
            "ir_sha256": hashlib.sha256(json.dumps(ir, sort_keys=True, separators=(",", ":")).encode()).hexdigest() if isinstance(ir, dict) else None,
            "boot_wall_ns": boot_wall, "boot_cpu_ns": boot_cpu,
            "route_wall_ns": route_wall, "route_cpu_ns": route_cpu,
            "before": before, "after": after,
            "arena_node_delta": after["arena_nodes"] - before["arena_nodes"],
            "graph_node_delta": after["graph_nodes"] - before["graph_nodes"],
            "rss_delta_kib": None if before["rss_kib"] is None or after["rss_kib"] is None else after["rss_kib"] - before["rss_kib"],
            "scores": scored,
            "all_seven_match": len(scored) == 7 and all(x["matches"] for x in scored),
        })
    accepted = [r for r in task_records if r["status"] == "accepted"]
    payload = {
        "schema_version": 1, "run_id": "p4-multi-task-resource-diagnostic-20260925-v1",
        "fixture_task_count": len(task_records), "accepted_count": len(accepted),
        "accepted_all_seven_match_count": sum(r["all_seven_match"] for r in accepted),
        "arena_node_delta_total": sum(r["arena_node_delta"] for r in task_records),
        "graph_node_delta_total": sum(r["graph_node_delta"] for r in task_records),
        "tasks": task_records,
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "native_path": str(NATIVE), "native_sha256": sha(NATIVE),
                        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        "provenance": {"locked_inputs": {k: sha(v) for k, v in locked.items()},
                       "lock_sha256": sha(LOCK),
                       "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"tasks": len(task_records), "accepted": len(accepted),
                      "all_seven_match": payload["accepted_all_seven_match_count"],
                      "output": str(output)}))


if __name__ == "__main__":
    main()
