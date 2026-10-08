#!/usr/bin/env python3
"""Recheck P4 temporary Term cleanup after native API integration."""
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
from domains import prog_retrieval as pr

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_P4_TERM_ARENA_RETENTION_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/p4_term_arena_retention_lock_20260925.json"
FIXTURE = ROOT / "tests/fixtures/substrate_string_pbe_contrast/tasks.json"
NATIVE = Path(srs._native.__file__).resolve()
TASK_ID = "contrast_reverse_string_01"
CYCLE_COUNTS = (1, 10, 100)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph_bytes(sub):
    return len(json.dumps(sub.graph_to_dict(), separators=(",", ":")).encode())


def current_rss_kib():
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return None


def run_eval_rows(sub, root, task):
    term = psy._prog_eval_term("e", "p")
    rows = []
    for group, key in (("revealed", "example_rows"), ("held_out", "held_out_rows")):
        for i, row in enumerate(task[key]):
            out = sub._inner.evaluate(term, {"e": dict(row["inputs"]), "p": root})
            rows.append({"group": group, "index": i, "got": out.get("result"),
                         "halted": out.get("halted"), "trap": out.get("trap"),
                         "expected": row["expected"],
                         "ok": out.get("halted") is True and out.get("trap") is None
                               and out.get("result") == row["expected"]})
    return rows


def cleanup_cycles(sub, ir, count, native):
    base_nodes = sub.node_count(); base_bytes = graph_bytes(sub); base_arena = sub._inner.term_arena_len()
    wall0 = time.perf_counter_ns(); cpu0 = time.process_time_ns()
    per_root_nodes = None
    removed_counts = []
    for _ in range(count):
        before = sub.node_count()
        root = sub._inner.add_term_subgraph(ir)
        if per_root_nodes is None:
            per_root_nodes = sub.node_count() - before
        if native:
            report = sub._inner.remove_term_subgraph(root)
            removed_counts.append(len(report["removed_node_ids"]))
            if report["protected_node_ids"]:
                raise RuntimeError("unexpected protected nodes in unshared IR cleanup")
        else:
            sub._inner.remove_node(root)
            removed_counts.append(1)
    wall_ns = time.perf_counter_ns() - wall0
    cpu_ns = time.process_time_ns() - cpu0
    rss = current_rss_kib()
    final_nodes = sub.node_count(); final_bytes = graph_bytes(sub); final_arena = sub._inner.term_arena_len()
    return {"cycles": count, "native_cleanup": native,
            "nodes_added_by_one_root": per_root_nodes,
            "removed_nodes_per_cycle": sorted(set(removed_counts)),
            "baseline_nodes": base_nodes, "final_nodes": final_nodes,
            "node_growth": final_nodes - base_nodes,
            "baseline_graph_json_bytes": base_bytes,
            "final_graph_json_bytes": final_bytes,
            "graph_json_growth_bytes": final_bytes - base_bytes,
            "baseline_arena_nodes": base_arena, "final_arena_nodes": final_arena,
            "arena_node_growth": final_arena - base_arena,
            "wall_ns": wall_ns, "cpu_ns": cpu_ns,
            "current_rss_kib": rss}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: substrate_p4_term_cleanup_recheck.py OUTPUT.json")
    output = Path(sys.argv[1])
    lock = json.loads(LOCK.read_text())
    locked = {
        "preregistration_sha256": PREREG,
        "runner_sha256": Path(__file__).resolve(),
        "fixture_sha256": FIXTURE,
        "p4_runner_sha256": ROOT / "scripts/prog_synthesis_battery.py",
        "prog_synthesis_sha256": ROOT / "domains/prog_synthesis.py",
        "prog_retrieval_sha256": ROOT / "domains/prog_retrieval.py",
        "seed_sha256": ROOT / "seeds/program_synthesis.json",
        "native_sha256": NATIVE,
    }
    if any(lock.get(k) != sha(v) for k, v in locked.items()):
        raise SystemExit("P4 cleanup recheck lock mismatch")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")
    task = next(t for t in json.loads(FIXTURE.read_text())["tasks"] if t["id"] == TASK_ID)
    boot0 = time.perf_counter_ns(); sub, agent = p4.boot(frozen=False)
    boot_wall = time.perf_counter_ns() - boot0
    examples = [(r["inputs"], r["expected"]) for r in task["example_rows"]]
    route0 = time.perf_counter_ns()
    result = psy.synthesize_from_request(sub, agent, task["request_text"], examples, name=TASK_ID)
    route_wall = time.perf_counter_ns() - route0
    if result.get("status") != "accepted" or not isinstance(result.get("ir"), dict):
        raise RuntimeError(f"P4 task failed: {result.get('status')} {result.get('gap_reason')}")
    ir = result["ir"]
    helper_checks = []
    row = task["held_out_rows"][0]
    for name, call in (("prog_synthesis._eval_ir_on", lambda: psy._eval_ir_on(sub, ir, row["inputs"])),
                       ("prog_retrieval._eval_ir", lambda: pr._eval_ir(sub, ir, row["inputs"]))):
        before = sub.node_count(); arena_before = sub._inner.term_arena_len(); value, ok = call(); after = sub.node_count(); arena_after = sub._inner.term_arena_len()
        helper_checks.append({"helper": name, "value": value, "ok": bool(ok),
                              "expected": row["expected"], "node_count_before": before,
                              "node_count_after": after, "no_graph_node_growth": before == after,
                              "arena_nodes_before": arena_before, "arena_nodes_after": arena_after,
                              "no_arena_node_growth": arena_before == arena_after,
                              "output_matches": value == row["expected"]})
    start_nodes = sub.node_count(); start_bytes = graph_bytes(sub)
    legacy = [cleanup_cycles(sub, ir, n, native=False) for n in CYCLE_COUNTS]
    safe = [cleanup_cycles(sub, ir, n, native=True) for n in CYCLE_COUNTS]
    final_root = sub._inner.add_term_subgraph(ir)
    final_rows = run_eval_rows(sub, final_root, task)
    payload = {
        "schema_version": 1, "run_id": "p4-term-arena-retention-20260925-v2",
        "task_id": TASK_ID, "status": result.get("status"),
        "construction": result.get("construction"),
        "ir_sha256": hashlib.sha256(json.dumps(ir, sort_keys=True,
                                      separators=(",", ":")).encode()).hexdigest(),
        "boot_wall_ns": boot_wall, "route_wall_ns": route_wall,
        "initial_node_count": start_nodes, "initial_graph_json_bytes": start_bytes,
        "temporary_helper_checks": helper_checks,
        "legacy_root_only_cycles": legacy,
        "native_cleanup_cycles": safe,
        "final_all_seven_rows_pass": len(final_rows) == 7 and all(r["ok"] for r in final_rows),
        "final_rows": final_rows,
        "all_gates_pass": all(x["ok"] and x["no_graph_node_growth"] and x["no_arena_node_growth"] and x["output_matches"]
                               for x in helper_checks) and
                          all(x["node_growth"] > 0 and x["graph_json_growth_bytes"] > 0 and x["arena_node_growth"] == 0 for x in legacy) and
                          all(x["node_growth"] == 0 and x["graph_json_growth_bytes"] == 0 and x["arena_node_growth"] == 0 for x in safe) and
                          len(final_rows) == 7 and all(r["ok"] for r in final_rows),
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "native_path": str(NATIVE), "native_sha256": sha(NATIVE),
                        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        "provenance": {"locked_inputs": {k: sha(v) for k, v in locked.items()},
                       "lock_sha256": sha(LOCK),
                       "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": payload["all_gates_pass"], "output": str(output)}))
    return 0 if payload["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
