#!/usr/bin/env python3
"""Measure direct SynthEnumerate acquisition versus repeated ProgEval use."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs
from domains.prog_synthesis import _wire_rows
import pbe_string_battery as pbe

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SYNTHESIS_ACQUISITION_APPLICATION_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/synthesis_acquisition_application_lock_20260925.json"
FIXTURE = ROOT / "tests/fixtures/pbe_string/pbe_string_tasks.json"
NATIVE = Path(srs._native.__file__).resolve()
TASK_IDS = ("pbe_001", "pbe_010", "pbe_024")
ACQUISITION_REPEATS = 3
REUSE_COUNTS = (1, 2, 5, 100, 1000, 10000)
REPEATED_SEARCH_COUNTS = (2, 5)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synth(task, sub=None):
    sub = sub or srs.Substrate()
    rows = _wire_rows([{"inputs": dict(r["inputs"]), "output": r["output"]}
                       for r in task["revealed"]])
    term = pbe.SYNTH(rows, ops=pbe.PBE_OPS, consts=pbe.PBE_CONSTS,
                     max_size=15, max_candidates=0)
    cpu0 = time.process_time_ns()
    t0 = time.perf_counter_ns()
    out = sub._inner.evaluate(term, {})
    wall_ns = time.perf_counter_ns() - t0
    cpu_ns = time.process_time_ns() - cpu0
    ir = json.loads(out["term"]) if out.get("found") else None
    return sub, out, ir, wall_ns, cpu_ns


def apply_batch(sub, ir, task, count):
    held = task["held_out"]
    t0 = time.perf_counter_ns()
    checksum = 0
    for i in range(count):
        row = held[i % len(held)]
        got = sub._inner.evaluate(ir, dict(row["inputs"]))
        if got != row["output"]:
            raise RuntimeError(f"held-out mismatch {task['task_id']} iteration {i}: {got!r}")
        checksum += len(repr(got))
    return {"calls": count, "wall_ns": time.perf_counter_ns() - t0,
            "checksum": checksum}


def repeated_acquisition(task, count):
    sub = srs.Substrate()
    t0 = time.perf_counter_ns()
    tested = []
    search_ns = 0
    application_ns = 0
    for i in range(count):
        _, out, ir, elapsed, _ = synth(task, sub)
        search_ns += elapsed
        if not out.get("found") or ir is None:
            raise RuntimeError(f"repeated acquisition failed for {task['task_id']}")
        held = task["held_out"][i % len(task["held_out"])]
        apply0 = time.perf_counter_ns()
        got = sub._inner.evaluate(ir, dict(held["inputs"]))
        application_ns += time.perf_counter_ns() - apply0
        if got != held["output"]:
            raise RuntimeError(f"repeated-search application mismatch for {task['task_id']}")
        tested.append(int(out.get("tested") or 0))
    return {"searches": count, "wall_ns": time.perf_counter_ns() - t0,
            "search_wall_ns": search_ns, "application_wall_ns": application_ns,
            "tested_candidates": tested}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: substrate_synthesis_acquisition_application.py OUTPUT.json")
    output = Path(sys.argv[1])
    lock = json.loads(LOCK.read_text())
    expected = {
        "preregistration_sha256": sha(PREREG),
        "runner_sha256": sha(Path(__file__).resolve()),
        "fixture_sha256": sha(FIXTURE),
        "pbe_runner_sha256": sha(ROOT / "scripts/pbe_string_battery.py"),
        "prog_synthesis_adapter_sha256": sha(ROOT / "domains/prog_synthesis.py"),
        "native_sha256": sha(NATIVE),
    }
    if any(lock.get(k) != v for k, v in expected.items()):
        raise SystemExit("acquisition/application input lock mismatch")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")
    fixture = json.loads(FIXTURE.read_text())
    tasks = {t["task_id"]: t for t in fixture}
    cpu_start = time.process_time_ns()
    results = []
    for task_id in TASK_IDS:
        task = tasks[task_id]
        acquisitions = []
        retained = None
        for _ in range(ACQUISITION_REPEATS):
            sub, out, ir, wall_ns, cpu_ns = synth(task)
            row = {"found": bool(out.get("found")), "halt_reason": out.get("halt_reason"),
                   "tested": out.get("tested"), "distinct": out.get("distinct"),
                   "wall_ns": wall_ns, "cpu_ns": cpu_ns,
                   "term": ir, "term_str": out.get("term_str")}
            acquisitions.append(row)
            if out.get("found") and retained is None:
                retained = (sub, ir)
        if retained is None:
            raise RuntimeError(f"no acquisition found for {task_id}")
        sub, ir = retained
        canonical = json.dumps(ir, sort_keys=True, separators=(",", ":"))
        consistent = all(x["found"] and json.dumps(x["term"], sort_keys=True,
                          separators=(",", ":")) == canonical for x in acquisitions)
        holdout = pbe.holdout_check(sub, ir, task["held_out"])
        warm = apply_batch(sub, ir, task, 100)
        applications = [apply_batch(sub, ir, task, n) for n in REUSE_COUNTS]
        repeated = [repeated_acquisition(task, n) for n in REPEATED_SEARCH_COUNTS]
        med_acq = int(statistics.median(x["wall_ns"] for x in acquisitions))
        app_per_call = {str(x["calls"]): x["wall_ns"] / x["calls"] for x in applications}
        economic = []
        rep_by_n = {x["searches"]: x for x in repeated}
        for app in applications:
            n = app["calls"]
            reused_cost = med_acq + app["wall_ns"]
            # Project repeated acquire-and-use from measured median acquisition
            # plus the measured application batch; directly measured 2/5 use
            # batches are retained separately.
            modeled_repeated = n * med_acq + app["wall_ns"]
            economic.append({"uses": n, "one_acquisition_plus_applications_ns": reused_cost,
                             "modeled_repeated_search_ns": modeled_repeated,
                             "measured_repeated_search_batch": rep_by_n.get(n),
                             "application_cost_per_use_ns": app_per_call[str(n)]})
        results.append({"task_id": task_id, "name": task["name"], "tier": task["tier"],
                        "acquisitions": acquisitions, "acquisition_median_wall_ns": med_acq,
                        "acquisition_median_cpu_ns": int(statistics.median(x["cpu_ns"] for x in acquisitions)),
                        "canonical_term_consistent": consistent,
                        "held_out": holdout, "warmup": warm,
                        "application_batches": applications,
                        "repeated_acquisition_batches": repeated,
                        "reuse_economics": economic})
    payload = {
        "schema_version": 1,
        "run_id": "substrate-synthesis-acquisition-application-20260925-v1",
        "design": {"task_ids": list(TASK_IDS), "acquisition_repeats": ACQUISITION_REPEATS,
                   "reuse_counts": list(REUSE_COUNTS),
                   "direct_repeated_search_counts": list(REPEATED_SEARCH_COUNTS),
                   "application_path": "native Substrate._inner.evaluate over exact SynthEnumerate-returned Term; not reflected Program IR / ProgEval",
                   "operator_pool": pbe.PBE_OPS, "constant_pool": pbe.PBE_CONSTS,
                   "budget": {"max_size": 15, "max_candidates": 0}},
        "results": results,
        "all_gates_pass": all(r["canonical_term_consistent"] and r["held_out"]["all_ok"]
                               for r in results),
        "process_cpu_ns": time.process_time_ns() - cpu_start,
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "native_path": str(NATIVE), "native_sha256": sha(NATIVE)},
        "provenance": {"preregistration_sha256": sha(PREREG),
                       "runner_sha256": sha(Path(__file__).resolve()),
                       "lock_sha256": sha(LOCK), "fixture_sha256": sha(FIXTURE),
                       "pbe_runner_sha256": sha(ROOT / "scripts/pbe_string_battery.py"),
                       "adapter_sha256": sha(ROOT / "domains/prog_synthesis.py"),
                       "native_sha256": sha(NATIVE),
                       "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                       "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": payload["all_gates_pass"],
                      "tasks": len(results), "output": str(output)}))
    return 0 if payload["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
