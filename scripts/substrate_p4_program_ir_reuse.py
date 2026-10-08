#!/usr/bin/env python3
"""Measure P4 accepted-IR verification, retention, and repeated ProgEval use."""
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

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_P4_PROGRAM_IR_REUSE_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/p4_program_ir_reuse_lock_20260925.json"
FIXTURE = ROOT / "tests/fixtures/substrate_string_pbe_contrast/tasks.json"
NATIVE = Path(srs._native.__file__).resolve()
TASK_ID = "contrast_reverse_string_01"
ACQUISITION_REPEATS = 3
APPLICATION_COUNTS = (100, 1000, 10000)
REMOVE_CYCLES = (1, 10, 100)
ROWS = ("revealed", "held_out")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate_rows(sub, root, task):
    term = psy._prog_eval_term("e", "p")
    results = []
    start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    for group in ROWS:
        key = "example_rows" if group == "revealed" else "held_out_rows"
        for i, row in enumerate(task[key]):
            out = sub._inner.evaluate(term, {"e": dict(row["inputs"]), "p": root})
            got = out.get("result")
            ok = out.get("halted") is True and out.get("trap") is None and got == row["expected"]
            results.append({"group": group, "row": i, "expected": row["expected"],
                            "got": got, "halted": out.get("halted"),
                            "trap": out.get("trap"), "ok": bool(ok)})
    return results, time.perf_counter_ns() - start, time.process_time_ns() - cpu_start


def application_batch(sub, root, task, count):
    rows = task["held_out_rows"]
    term = psy._prog_eval_term("e", "p")
    started = time.perf_counter_ns()
    cpu_started = time.process_time_ns()
    for i in range(count):
        row = rows[i % len(rows)]
        out = sub._inner.evaluate(term, {"e": dict(row["inputs"]), "p": root})
        if out.get("halted") is not True or out.get("trap") is not None or out.get("result") != row["expected"]:
            raise RuntimeError(f"ProgEval mismatch at repeated-use call {i}")
    return {"calls": count, "wall_ns": time.perf_counter_ns() - started,
            "cpu_ns": time.process_time_ns() - cpu_started}


def current_rss_kib():
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return None


def graph_size_bytes(sub):
    return len(json.dumps(sub.graph_to_dict(), separators=(",", ":")).encode("utf-8"))


def retention_growth_probe(sub, ir):
    start_nodes = sub.node_count()
    start_bytes = graph_size_bytes(sub)
    start_rss = current_rss_kib()
    points = []
    done = 0
    for target in (1, 10, 100):
        wall0 = time.perf_counter_ns(); cpu0 = time.process_time_ns()
        for _ in range(target - done):
            root = sub._inner.add_term_subgraph(ir)
            sub._inner.remove_node(root)
        cycle_wall = time.perf_counter_ns() - wall0
        cycle_cpu = time.process_time_ns() - cpu0
        done = target
        after_nodes = sub.node_count()
        rss = current_rss_kib()
        export0 = time.perf_counter_ns()
        after_bytes = graph_size_bytes(sub)
        export_wall = time.perf_counter_ns() - export0
        points.append({"cycles_total": target, "cycle_wall_ns": cycle_wall,
                       "cycle_cpu_ns": cycle_cpu, "graph_nodes": after_nodes,
                       "node_growth": after_nodes - start_nodes,
                       "graph_json_bytes": after_bytes,
                       "graph_json_growth_bytes": after_bytes - start_bytes,
                       "graph_export_wall_ns": export_wall,
                       "current_rss_kib": rss,
                       "rss_growth_kib": None if rss is None or start_rss is None else rss - start_rss})
    return {"baseline_nodes": start_nodes, "baseline_graph_json_bytes": start_bytes,
            "baseline_current_rss_kib": start_rss, "points": points}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: substrate_p4_program_ir_reuse.py OUTPUT.json")
    output = Path(sys.argv[1])
    lock = json.loads(LOCK.read_text())
    source_files = {
        "preregistration_sha256": PREREG,
        "runner_sha256": Path(__file__).resolve(),
        "fixture_sha256": FIXTURE,
        "p4_runner_sha256": ROOT / "scripts/prog_synthesis_battery.py",
        "adapter_sha256": ROOT / "domains/prog_synthesis.py",
        "retrieval_sha256": ROOT / "domains/prog_retrieval.py",
        "seed_sha256": ROOT / "seeds/program_synthesis.json",
        "native_sha256": NATIVE,
    }
    if any(lock.get(k) != sha(v) for k, v in source_files.items()):
        raise SystemExit("P4 Program IR reuse lock mismatch")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")
    suite = json.loads(FIXTURE.read_text())
    task = next(t for t in suite["tasks"] if t["id"] == TASK_ID)
    runs = []
    for _ in range(ACQUISITION_REPEATS):
        boot0 = time.perf_counter_ns(); boot_cpu0 = time.process_time_ns()
        sub, agent = p4.boot(frozen=False)
        boot_ns = time.perf_counter_ns() - boot0
        boot_cpu_ns = time.process_time_ns() - boot_cpu0
        examples = [(r["inputs"], r["expected"]) for r in task["example_rows"]]
        route0 = time.perf_counter_ns(); route_cpu0 = time.process_time_ns()
        result = psy.synthesize_from_request(sub, agent, task["request_text"], examples,
                                             name=task["id"])
        route_ns = time.perf_counter_ns() - route0
        route_cpu_ns = time.process_time_ns() - route_cpu0
        if result.get("status") != "accepted" or not isinstance(result.get("ir"), dict):
            raise RuntimeError(f"registered task did not yield accepted IR: {result.get('status')} / {result.get('gap_reason')}")
        ir = result["ir"]
        fp = hashlib.sha256(json.dumps(ir, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        nodes_before_ir = sub.node_count()
        root = sub._inner.add_term_subgraph(ir)
        nodes_with_ir = sub.node_count()
        verified, verify_ns, verify_cpu_ns = evaluate_rows(sub, root, task)
        if not all(x["ok"] for x in verified):
            raise RuntimeError("accepted IR failed independent ProgEval verification")
        export0 = time.perf_counter_ns(); export_cpu0 = time.process_time_ns()
        serialized = sub._inner.term_subgraph_json(root)
        export_ns = time.perf_counter_ns() - export0
        export_cpu_ns = time.process_time_ns() - export_cpu0
        serialized_bytes = len(serialized.encode("utf-8"))
        sub._inner.remove_node(root)
        nodes_after_remove = sub.node_count()
        restore0 = time.perf_counter_ns(); restore_cpu0 = time.process_time_ns()
        restored_root = sub._inner.add_term_subgraph(json.loads(serialized))
        restore_ns = time.perf_counter_ns() - restore0
        restore_cpu_ns = time.process_time_ns() - restore_cpu0
        stable = sub._inner.term_subgraph_json(restored_root) == serialized
        restored_verify, restored_verify_ns, restored_verify_cpu_ns = evaluate_rows(sub, restored_root, task)
        if not stable or not all(x["ok"] for x in restored_verify):
            raise RuntimeError("IR graph export/restore parity failed")
        app0 = application_batch(sub, restored_root, task, 100)
        batches = [application_batch(sub, restored_root, task, n)
                   for n in APPLICATION_COUNTS]
        removals = retention_growth_probe(sub, ir)
        runs.append({
            "status": result.get("status"), "construction": result.get("construction"),
            "route_rungs": result.get("rungs"), "ir_sha256": fp,
            "boot_wall_ns": boot_ns, "boot_cpu_ns": boot_cpu_ns,
            "route_wall_ns": route_ns, "route_cpu_ns": route_cpu_ns,
            "acquisition_total_wall_ns": boot_ns + route_ns,
            "acquisition_total_cpu_ns": boot_cpu_ns + route_cpu_ns,
            "verification_wall_ns": verify_ns, "verification_cpu_ns": verify_cpu_ns,
            "verification_rows": verified,
            "ir_serialized_bytes": serialized_bytes, "ir_export_wall_ns": export_ns,
            "ir_export_cpu_ns": export_cpu_ns,
            "ir_restore_wall_ns": restore_ns, "ir_restore_cpu_ns": restore_cpu_ns,
            "native_node_count_before_ir": nodes_before_ir,
            "native_node_count_with_ir": nodes_with_ir,
            "ir_native_node_delta": nodes_with_ir - nodes_before_ir,
            "native_node_count_after_remove": nodes_after_remove,
            "ir_remove_node_delta": nodes_after_remove - nodes_before_ir,
            "ir_roundtrip_stable": stable,
            "restored_verification_wall_ns": restored_verify_ns,
            "restored_verification_cpu_ns": restored_verify_cpu_ns,
            "restored_verification_rows": restored_verify,
            "warmup": app0, "application_batches": batches,
            "remove_cycle_batches": removals,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        })
    fingerprints = {r["ir_sha256"] for r in runs}
    payload = {
        "schema_version": 1,
        "run_id": "substrate-p4-program-ir-reuse-20260925-v1",
        "design": {"task_id": TASK_ID, "acquisition_repeats": ACQUISITION_REPEATS,
                   "application_counts": list(APPLICATION_COUNTS),
                   "root_remove_cycle_counts": list(REMOVE_CYCLES),
                   "application_path": "P4 accepted ps_ir reflected into native term graph and evaluated via ProgEval",
                   "boot_and_seed_setup_timed_separately": True},
        "runs": runs,
        "all_gates_pass": len(fingerprints) == 1 and all(
            r["status"] == "accepted" and r["ir_roundtrip_stable"] and
            all(x["ok"] for x in r["verification_rows"] + r["restored_verification_rows"])
            for r in runs),
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "native_path": str(NATIVE), "native_sha256": sha(NATIVE)},
        "provenance": {"preregistration_sha256": sha(PREREG), "lock_sha256": sha(LOCK),
                       "locked_inputs": {k: sha(v) for k, v in source_files.items()},
                       "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                       "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": payload["all_gates_pass"], "output": str(output)}))
    return 0 if payload["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
