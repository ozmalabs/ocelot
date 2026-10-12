#!/usr/bin/env python3
"""Re-run the frozen P6 battery on the installed engine with provenance."""
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
OUT = ROOT / "evaluation/reports/substrate_p6_current_recheck_20260925.json"
sys.path.insert(0, str(ROOT / "scripts"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_arm(current: list[dict], previous: list[dict]) -> dict:
    old = {r["task_id"]: r for r in previous}
    new = {r["task_id"]: r for r in current}
    changes = [{"task_id": tid, "prior": old[tid]["outcome"], "current": new[tid]["outcome"]}
               for tid in sorted(set(old) & set(new)) if old[tid]["outcome"] != new[tid]["outcome"]]
    return {
        "prior_rows": len(old), "current_rows": len(new),
        "prior_passes": sum(r["outcome"] == "accepted_holdout_ok" for r in old.values()),
        "current_passes": sum(r["outcome"] == "accepted_holdout_ok" for r in new.values()),
        "changed_outcome_rows": changes,
        "outcome_signature_identical": not changes and set(old) == set(new),
    }


def main() -> None:
    import prog_synthesis_battery as p6
    from substrate_rs import _native

    p6.OUT_PATH = str(OUT)
    wall_start = time.perf_counter()
    p6.main()
    wall = time.perf_counter() - wall_start
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    data = json.loads(OUT.read_text(encoding="utf-8"))
    data["current_recheck"] = {
        "run_state": "replication_current_source_recheck",
        "wall_seconds_including_children": round(wall, 6),
        "parent_process_peak_rss_kib": self_usage.ru_maxrss,
        "parent_user_cpu_seconds": round(self_usage.ru_utime, 6),
        "parent_system_cpu_seconds": round(self_usage.ru_stime, 6),
        "child_process_max_rss_kib_linux_ru_maxrss": child_usage.ru_maxrss,
        "child_user_cpu_seconds": round(child_usage.ru_utime, 6),
        "child_system_cpu_seconds": round(child_usage.ru_stime, 6),
        "resource_scope": "Parent RSS/CPU include Python setup, fresh-substrate runs, and report generation. Child CPU/RSS aggregate subprocess activity (including selected toolchain checks); child ru_maxrss is the maximum child, not a sum. Wall time includes children.",
    }
    prior_path = ROOT / "results/prog_synthesis_battery.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    data["prior_artifact_comparison"] = {
        "prior_artifact_sha256": sha(prior_path),
        "interpretation": "The earlier known-outcome artifact is used only for an identity-level current-source recheck; this is not a new confirmatory split or an independent custody replication.",
        "arms": {
            name: compare_arm(data["arms"][name]["rows"], prior["arms"][name]["rows"])
            for name in ("main", "frozen")
        },
    }
    extension = Path(_native.__file__).resolve()
    source_paths = {
        "harness": Path(__file__).resolve(),
        "p6_runner": ROOT / "scripts/prog_synthesis_battery.py",
        "task_fixture": ROOT / "tests/fixtures/prog_synthesis_battery/tasks.json",
        "task_generator": ROOT / "tests/fixtures/prog_synthesis_battery/build_tasks.py",
        "synthesis_orchestrator": ROOT / "domains/prog_synthesis.py",
        "program_eval": ROOT / "runners/dsl/src/prog_eval.rs",
        "program_seed": ROOT / "seeds/program_synthesis.json",
        "native_extension": extension,
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
        "cargo_lock": ROOT / "runners/dsl/Cargo.lock",
        "p6_preregistration": ROOT / "docs/research/program_synthesis/PROGRAM_SYNTHESIS_PREREG.md",
        "p6_battery_protocol": ROOT / "docs/research/program_synthesis/PROGRAM_SYNTHESIS_P6_BATTERY.md",
    }
    data["provenance_current_recheck"] = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "python": sys.version, "platform": platform.platform(),
        "native_extension_path": str(extension),
        "native_extension_sha256": sha(extension),
        "source_sha256": {name: sha(path) for name, path in source_paths.items()},
        "environment_controls": {key: os.environ.get(key) for key in
                                  ("OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED", "PYTHONHASHSEED")},
        "command": "PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_p6_current_recheck.py",
        "original_results_path_unchanged_by_wrapper": str(prior_path),
    }
    OUT.write_text(json.dumps(data, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT), "wall_seconds": round(wall, 3),
        "parent_peak_rss_kib": self_usage.ru_maxrss,
        "child_max_rss_kib": child_usage.ru_maxrss,
        "main": data["prior_artifact_comparison"]["arms"]["main"],
        "frozen": data["prior_artifact_comparison"]["arms"]["frozen"],
        "native_extension_sha256": data["provenance_current_recheck"]["native_extension_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
