#!/usr/bin/env python3
"""Per-task fresh-process RSS and Python allocation diagnostic for P4."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/substrate_string_pbe_contrast/tasks.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_P4_ISOLATED_TASK_MEMORY_DIAGNOSTIC_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/p4_isolated_task_memory_lock_20260925.json"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    return {
        "preregistration_sha256": PREREG,
        "runner_sha256": Path(__file__).resolve(),
        "fixture_sha256": FIXTURE,
        "p4_runner_sha256": ROOT / "scripts/prog_synthesis_battery.py",
        "adapter_sha256": ROOT / "domains/prog_synthesis.py",
        "retrieval_sha256": ROOT / "domains/prog_retrieval.py",
        "seed_sha256": ROOT / "seeds/program_synthesis.json",
        "native_sha256": NATIVE,
    }


def current_rss_kib():
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except OSError:
        pass
    return None


def score(sub, ir, task, psy):
    values = []
    for group, key in (("revealed", "example_rows"), ("held_out", "held_out_rows")):
        for i, row in enumerate(task[key]):
            got, ok = psy._eval_ir_on(sub, ir, row["inputs"])
            values.append({"group": group, "index": i, "got": got,
                           "expected": row["expected"],
                           "matches": bool(ok) and got == row["expected"]})
    return values


def worker(task_id):
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
    import substrate_rs as srs
    import prog_synthesis_battery as p4
    from domains import prog_synthesis as psy

    suite = json.loads(FIXTURE.read_text())
    task = next(t for t in suite["tasks"] if t["id"] == task_id)
    rss = {"post_import_kib": current_rss_kib()}
    boot0 = time.perf_counter_ns(); cpu0 = time.process_time_ns()
    sub, agent = p4.boot(frozen=False)
    boot_wall = time.perf_counter_ns() - boot0
    boot_cpu = time.process_time_ns() - cpu0
    rss["post_boot_kib"] = current_rss_kib()
    before = {"arena_nodes": sub._inner.term_arena_len(), "graph_nodes": sub.node_count()}
    rss["pre_route_kib"] = current_rss_kib()
    tracemalloc.start()
    py_before, _ = tracemalloc.get_traced_memory()
    examples = [(r["inputs"], r["expected"]) for r in task["example_rows"]]
    route0 = time.perf_counter_ns(); route_cpu0 = time.process_time_ns()
    result = psy.synthesize_from_request(sub, agent, task["request_text"], examples, name=task_id)
    route_wall = time.perf_counter_ns() - route0
    route_cpu = time.process_time_ns() - route_cpu0
    py_after, py_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss["post_route_kib"] = current_rss_kib()
    after = {"arena_nodes": sub._inner.term_arena_len(), "graph_nodes": sub.node_count()}
    ir = result.get("ir") if isinstance(result, dict) else None
    scores = score(sub, ir, task, psy) if result.get("status") == "accepted" and isinstance(ir, dict) else []
    rss["post_score_kib"] = current_rss_kib()
    return {
        "task_id": task_id, "status": result.get("status"),
        "construction": result.get("construction"), "rungs": result.get("rungs"),
        "gap_reason": result.get("gap_reason"), "boot_wall_ns": boot_wall,
        "boot_cpu_ns": boot_cpu, "route_wall_ns": route_wall, "route_cpu_ns": route_cpu,
        "before": before, "after": after,
        "arena_node_delta": after["arena_nodes"] - before["arena_nodes"],
        "graph_node_delta": after["graph_nodes"] - before["graph_nodes"],
        "rss_stages_kib": rss,
        "route_rss_delta_kib": None if rss["pre_route_kib"] is None or rss["post_route_kib"] is None else rss["post_route_kib"] - rss["pre_route_kib"],
        "python_tracemalloc_route_current_delta_bytes": py_after - py_before,
        "python_tracemalloc_route_peak_delta_bytes": py_peak - py_before,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scores": scores,
        "all_seven_match": len(scores) == 7 and all(x["matches"] for x in scores),
        "native_sha256": sha(Path(srs._native.__file__).resolve()),
        "python": sys.version, "platform": platform.platform(),
    }


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2]), sort_keys=True))
        return 0
    if len(sys.argv) != 2:
        raise SystemExit("usage: substrate_p4_isolated_task_memory_diagnostic.py OUTPUT.json")
    lock = json.loads(LOCK.read_text())
    locked = inputs()
    if any(lock.get(k) != sha(v) for k, v in locked.items()):
        raise SystemExit("P4 isolated memory lock mismatch")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")
    suite = json.loads(FIXTURE.read_text())
    rows = []
    for task in suite["tasks"]:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", task["id"]],
                              cwd=ROOT, text=True, capture_output=True, check=True)
        record = json.loads(proc.stdout.strip().splitlines()[-1])
        if record["task_id"] != task["id"] or record["native_sha256"] != lock["native_sha256"]:
            raise RuntimeError(f"worker provenance mismatch for {task['id']}")
        rows.append(record)
    accepted = [r for r in rows if r["status"] == "accepted"]
    payload = {
        "schema_version": 1, "run_id": "p4-isolated-task-memory-20260925-v1",
        "task_count": len(rows), "accepted_count": len(accepted),
        "accepted_all_seven_match_count": sum(r["all_seven_match"] for r in accepted),
        "arena_node_delta_total": sum(r["arena_node_delta"] for r in rows),
        "graph_node_delta_total": sum(r["graph_node_delta"] for r in rows),
        "tasks": rows,
        "provenance": {"locked_inputs": {k: sha(v) for k, v in locked.items()},
                       "lock_sha256": sha(LOCK),
                       "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()},
    }
    output = Path(sys.argv[1]); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"tasks": len(rows), "accepted": len(accepted),
                      "all_seven_match": payload["accepted_all_seven_match_count"],
                      "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
