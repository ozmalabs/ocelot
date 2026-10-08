#!/usr/bin/env python3
"""Trace the full P4 program-synthesis route on the frozen list PBE pilot suite.

This is a discovery diagnostic on a task family whose direct-search outcomes
have already been inspected; it is not confirmatory evidence.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tests/fixtures/substrate_list_pbe/tasks.json"
OUT = ROOT / "evaluation/reports/substrate_list_pbe_pipeline_instrumented_replication_20260925.json"
PROMPTS = {
    "list_001_sum": "Write a function that returns the sum of the integers in a list.",
    "list_002_length": "Write a function that returns the number of items in a list.",
    "list_003_max": "Write a function that returns the largest integer in a list.",
    "list_004_min": "Write a function that returns the smallest integer in a list.",
    "list_005_first": "Write a function that returns the first item in a list.",
    "list_006_last": "Write a function that returns the last item in a list.",
    "list_007_reverse": "Write a function that returns a list in reverse order.",
    "list_008_map_plus_one": "Write a function that adds one to every integer in a list.",
    "list_009_map_double": "Write a function that doubles every integer in a list.",
    "list_010_map_abs": "Write a function that replaces each list item with its absolute value.",
    "list_011_filter_positive": "Write a function that keeps only positive integers from a list.",
    "list_012_filter_negative": "Write a function that keeps only negative integers from a list.",
    "list_013_filter_gt_two": "Write a function that keeps list items greater than two.",
    "list_014_sum_positive": "Write a function that sums only the positive integers in a list.",
    "list_015_sum_squares": "Write a function that returns the sum of the squares of list items.",
    "list_016_count_positive": "Write a function that counts the positive integers in a list.",
    "list_017_sum_even": "Write a function that sums the even integers in a list.",
    "list_018_product": "Write a function that returns the product of the integers in a list.",
    "list_019_map_plus_three": "Write a function that adds three to every integer in a list.",
    "list_020_last_degenerate": "Write a function that returns the last item in a list.",
    "list_021_median": "Write a function that returns the median integer in a list.",
    "list_022_unique_count": "Write a function that counts the distinct integers in a list.",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    for key, value in {"OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}.items():
        os.environ.setdefault(key, value)
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts"),
                    str(ROOT / "runners/dsl/python")]
    import prog_synthesis_battery as p4
    from domains import prog_synthesis as psy
    from substrate_rs import _native

    fixture = json.loads(TASKS.read_text(encoding="utf-8"))
    start = time.perf_counter()
    cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    rows = []
    for task in fixture["tasks"]:
        task_id = task["task_id"]
        # P4 battery row shape; the task file itself is not mutated.
        p4_task = {
            "id": task_id, "stratum": task["category"],
            "request_text": PROMPTS[task_id],
            "example_rows": [dict(inputs=x["inputs"], expected=x["output"])
                             for x in task["revealed"]],
            "held_out_rows": [dict(inputs=x["inputs"], expected=x["output"])
                              for x in task["held_out"]],
        }
        row_start = time.perf_counter_ns()
        boot_start = time.perf_counter_ns()
        sub, agent = p4.boot(False)
        boot_ns = time.perf_counter_ns() - boot_start
        examples = [(x["inputs"], x["expected"]) for x in p4_task["example_rows"]]
        route_start = time.perf_counter_ns()
        result = psy.synthesize_from_request(
            sub, agent, p4_task["request_text"], examples, name=task_id)
        route_ns = time.perf_counter_ns() - route_start
        outcome = p4._build_row(sub, p4_task, result, arm="pipeline_main")
        rows.append({**outcome, "category": task["category"],
                     "request_text": p4_task["request_text"],
                     "boot_wall_ns": boot_ns, "route_wall_ns": route_ns,
                     "row_wall_ns": time.perf_counter_ns() - row_start,
                     "enumerate_detail": result.get("enumerate"),
                     "residual_tokens": result.get("residual_tokens"),
                     "descend_kind": result.get("descend_kind"),
                     "exact_detail": result.get("exact"),
                     "move_detail": result.get("moves"),
                     "repair_detail": result.get("repair"),
                     "pipeline_readback": {
                         "construction": result.get("construction"),
                         "rungs": result.get("rungs"),
                         "retrieval": result.get("retrieval"),
                         "exact": result.get("exact"),
                         "enumerate": result.get("enumerate"),
                         "descend_kind": result.get("descend_kind"),
                         "residual_tokens": result.get("residual_tokens"),
                         "gap_reason": result.get("gap_reason"),
                         "status": result.get("status"),
                     }})

    usage = resource.getrusage(resource.RUSAGE_SELF)
    counts = {}
    for row in rows:
        counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
    rung_counts = {}
    for row in rows:
        for rung, active in (row.get("rungs") or {}).items():
            if active:
                rung_counts[rung] = rung_counts.get(rung, 0) + 1
    construction_counts = {}
    for row in rows:
        construction = row.get("construction") or "none"
        construction_counts[construction] = construction_counts.get(construction, 0) + 1
    extension = Path(_native.__file__).resolve()
    paths = {
        "harness": Path(__file__).resolve(),
        "suite": TASKS,
        "pipeline_runner": ROOT / "scripts/prog_synthesis_battery.py",
        "pipeline_adapter": ROOT / "domains/prog_synthesis.py",
        "pipeline_seed": ROOT / "seeds/program_synthesis.json",
        "native_synthesizer": ROOT / "runners/dsl/src/synth_enumerate.rs",
        "benchmark_protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md",
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_LIST_PBE_PIPELINE_PILOT_NOTE_20260925.md",
        "native_extension": extension,
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
        "cargo_lock": ROOT / "runners/dsl/Cargo.lock",
    }
    payload = {
        "schema_version": 1,
        "run_id": "substrate-list-pbe-pipeline-pilot-20260925",
        "run_state": "discovery_diagnostic_previous_task_family_outcomes_known",
        "claim_boundary": "Full P4 request-to-outcome path on 22 synthetic list tasks; task family and direct-search outcomes were already inspected. Not confirmatory; no task prevalence, broad learning, mint/adoption, or transfer claim.",
        "summary": {"task_count": len(rows), "outcome_counts": counts,
                    "active_rung_counts": rung_counts,
                    "terminal_construction_counts": construction_counts,
                    "wall_seconds": time.perf_counter() - start,
                    "parent_peak_rss_kib": usage.ru_maxrss,
                    "parent_user_cpu_seconds": usage.ru_utime - cpu_start.ru_utime,
                    "parent_system_cpu_seconds": usage.ru_stime - cpu_start.ru_stime,
                    "route_wall_ms_total": sum(r["route_wall_ns"] for r in rows)/1e6,
                    "boot_wall_ms_total": sum(r["boot_wall_ns"] for r in rows)/1e6},
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "controls": {k: os.environ.get(k) for k in
                                     ("OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED", "PYTHONHASHSEED")}},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(extension),
            "sha256": {k: sha(Path(v)) for k, v in paths.items()},
            "command": "PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_list_pbe_pipeline_pilot.py",
        },
        "cases": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "summary": payload["summary"],
                      "rung_counts": rung_counts, "outcome_counts": counts}, indent=2))


if __name__ == "__main__":
    main()
