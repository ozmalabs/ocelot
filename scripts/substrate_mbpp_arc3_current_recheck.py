#!/usr/bin/env python3
"""Current-source recheck of the registered MBPP Arc 3 R3 battery."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_mbpp_arc3_current_recheck_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/mbpp_arc3_current_recheck_lock_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
    import mbpp_arc3_battery as battery
    from substrate_rs import _native

    battery.OUT_PATH = str(OUT)
    started = datetime.now(timezone.utc).isoformat()
    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    wall_start = time.perf_counter()
    battery.main()
    wall = time.perf_counter() - wall_start
    usage_after = resource.getrusage(resource.RUSAGE_SELF)
    data = json.loads(OUT.read_text(encoding="utf-8"))
    extension = Path(_native.__file__).resolve()
    lock_hash = sha(LOCK)
    data["current_source_recheck"] = {
        "run_state": "current_source_replication_known_mbpp_test_split",
        "started_utc": started,
        "wrapper_wall_seconds": wall,
        "parent_peak_rss_kib": usage_after.ru_maxrss,
        "parent_user_cpu_seconds": usage_after.ru_utime - usage_before.ru_utime,
        "parent_system_cpu_seconds": usage_after.ru_stime - usage_before.ru_stime,
        "native_extension_path": str(extension),
        "native_extension_sha256": sha(extension),
        "lock_path": str(LOCK.relative_to(ROOT)),
        "lock_sha256": lock_hash,
        "source_sha256": {
            "wrapper": sha(Path(__file__).resolve()),
            "runner": sha(ROOT / "scripts/mbpp_arc3_battery.py"),
            "splitter": sha(ROOT / "scripts/mbpp_zero_shot_baseline.py"),
            "spec_parser": sha(ROOT / "domains/mbpp_spec.py"),
            "synthesis_adapter": sha(ROOT / "domains/prog_synthesis.py"),
            "chunk_adapter": sha(ROOT / "domains/prog_chunk_growth.py"),
            "synthesis_seed": sha(ROOT / "seeds/program_synthesis.json"),
            "training_diet_seed": sha(ROOT / "seeds/mbpp_train_diet.json"),
            "chunk_artifact": sha(ROOT / "results/prog_chunk_mine.json"),
            "fixture": sha(ROOT / "tests/fixtures/mbpp/sanitized-mbpp.json"),
            "fixture_provenance": sha(ROOT / "tests/fixtures/mbpp/provenance.json"),
            "arc3_preregistration": sha(ROOT / "docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC3_PREREG.md"),
            "benchmark_protocol": sha(ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md"),
            "arc2_continuity_artifact": sha(ROOT / "results/mbpp_endgame.json"),
            "r0_ceiling_artifact": sha(ROOT / "results/retrieval_oracle_ceiling.json"),
            "native_synthesizer": sha(ROOT / "runners/dsl/src/synth_enumerate.rs"),
            "native_build_manifest": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "cargo_lock": sha(ROOT / "runners/dsl/Cargo.lock"),
        },
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "controls": {k: os.environ.get(k) for k in
                                     ("OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED", "PYTHONHASHSEED")}},
        "command": "PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_mbpp_arc3_current_recheck.py",
    }
    OUT.write_text(json.dumps(data, indent=1, sort_keys=False, default=battery._json_default) + "\n",
                   encoding="utf-8")
    print(json.dumps({"output": str(OUT), "wall_seconds": wall,
                      "peak_rss_kib": usage_after.ru_maxrss,
                      "arms": {name: {
                          "pass_over_runnable": arm["aggregates"]["pass_over_runnable"],
                          "pass_over_all_test_257": arm["aggregates"]["pass_over_all_test_257"],
                          "deterministic": arm["determinism"]["identical"],
                          "prefix_cut": arm["prefix_cut"],
                      } for name, arm in data["arms"].items()}}, indent=2))


if __name__ == "__main__":
    main()
