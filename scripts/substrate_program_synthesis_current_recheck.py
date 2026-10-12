#!/usr/bin/env python3
"""Run the fixed PBE battery on the installed engine with full provenance."""
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
OUT = ROOT / "evaluation/reports/substrate_program_synthesis_pbe_recheck_20260925.json"
sys.path.insert(0, str(ROOT / "scripts"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows: list[dict]) -> dict:
    elapsed_ms = sorted(round(row["elapsed_seconds"] * 1000, 3) for row in rows)
    tested = [row.get("tested") or 0 for row in rows]
    passed = [row["task_id"] for row in rows if row.get("outcome") == "pass"]
    return {
        "rows": len(rows), "passed": len(passed), "pass_task_ids": sorted(passed),
        "found_count": sum(bool(row.get("found")) for row in rows),
        "found_but_holdout_fail_count": sum(row.get("outcome") == "found_but_holdout_fail" for row in rows),
        "budget_or_search_fail_count": sum(str(row.get("outcome", "")).startswith("not_found:") for row in rows),
        "tested_candidates_total": sum(tested), "tested_candidates_median": sorted(tested)[len(tested)//2],
        "elapsed_ms_total_rounded_rows": round(sum(elapsed_ms), 3),
        "elapsed_ms_median": elapsed_ms[len(elapsed_ms)//2],
        "elapsed_ms_p90": elapsed_ms[min(len(elapsed_ms)-1, int(0.9 * len(elapsed_ms)))],
        "elapsed_ms_max": max(elapsed_ms),
    }


def main() -> None:
    import pbe_string_battery as pbe
    from substrate_rs import _native

    pbe.OUT_PATH = str(OUT)
    start = time.perf_counter()
    pbe.main()
    wall = time.perf_counter() - start
    usage = resource.getrusage(resource.RUSAGE_SELF)
    data = json.loads(OUT.read_text(encoding="utf-8"))
    data["measurement"] = {
        "run_state": "pilot_current_source_recheck",
        "current_run_wall_seconds": round(wall, 6),
        "process_peak_rss_kib": usage.ru_maxrss,
        "process_user_cpu_seconds": round(usage.ru_utime, 6),
        "process_system_cpu_seconds": round(usage.ru_stime, 6),
        "arm_summaries": {
            name: summarize(arm["rows"])
            for name, arm in data["arms"].items()
        },
        "tier_summaries": {
            arm_name: {
                tier: summarize([row for row in arm["rows"] if row.get("tier") == tier])
                for tier in sorted({row.get("tier", "unknown") for row in arm["rows"]})
            }
            for arm_name, arm in data["arms"].items()
        },
        "resource_scope": "Process-wide peak RSS and CPU include Python imports, fixture handling, every task arm, and report generation; row wall timings cover each native SynthEnumerate call plus its holdout check.",
    }
    extension = Path(_native.__file__).resolve()
    prior_path = ROOT / "evaluation/reports/substrate_program_synthesis_pbe_recheck_20260924.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    data["prior_recheck_comparison"] = {}
    for arm_name, current_arm in data["arms"].items():
        if arm_name not in prior.get("arms", {}):
            continue
        old_arm = prior["arms"][arm_name]
        new_arm = current_arm
        old_ids = set(old_arm.get("pass_task_ids", old_arm.get("newly_pass_task_ids", [])))
        new_ids = set(new_arm.get("pass_task_ids", new_arm.get("newly_pass_task_ids", [])))
        data["prior_recheck_comparison"][arm_name] = {
            "prior_pass_count": len(old_ids), "current_pass_count": len(new_ids),
            "gained_task_ids": sorted(new_ids - old_ids), "lost_task_ids": sorted(old_ids - new_ids),
            "interpretation": "same fixed fixture and arm settings; repeated checkout measurement, not a pre-pricing baseline or independent task-family replication",
        }
    data["provenance"] = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "python": sys.version, "platform": platform.platform(),
        "native_extension_path": str(extension), "native_extension_sha256": sha(extension),
        "source_sha256": {
            "harness": sha(Path(__file__).resolve()),
            "pbe_runner": sha(ROOT / "scripts/pbe_string_battery.py"),
            "fixture": sha(ROOT / "tests/fixtures/pbe_string/pbe_string_tasks.json"),
            "synthesis_engine": sha(ROOT / "runners/dsl/src/synth_enumerate.rs"),
            "native_build_manifest": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "cargo_lock": sha(ROOT / "runners/dsl/Cargo.lock"),
            "benchmark_protocol": sha(ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md"),
        },
        "environment_controls": {key: os.environ.get(key) for key in
                                  ("OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED", "PYTHONHASHSEED")},
        "command": "PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_program_synthesis_current_recheck.py",
    }
    OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "run_wall_seconds": data["measurement"]["current_run_wall_seconds"],
                      "process_peak_rss_kib": usage.ru_maxrss,
                      "arm_summaries": data["measurement"]["arm_summaries"],
                      "prior_recheck_comparison": data["prior_recheck_comparison"],
                      "native_extension_sha256": data["provenance"]["native_extension_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
