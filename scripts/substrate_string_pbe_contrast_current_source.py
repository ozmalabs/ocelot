#!/usr/bin/env python3
"""Locked source-current replication of the prior contrast P4 pilot."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
OUT = ROOT / "evaluation/reports/substrate_string_pbe_contrast_current_source_20260925.json"
ANALYSIS = ROOT / "evaluation/reports/substrate_string_pbe_contrast_current_source_analysis_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/string_pbe_contrast_current_source_lock_20260925.json"
ORIGINAL = ROOT / "evaluation/reports/substrate_string_pbe_contrast_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths():
    dsl = ROOT / "runners/dsl"
    return {
        "preregistration_sha256": ROOT / "docs/research/engine_substrate/SUBSTRATE_STRING_PBE_CONTRAST_CURRENT_SOURCE_PREREG_20260925.md",
        "wrapper_sha256": Path(__file__).resolve(),
        "benchmark_sha256": SCRIPT_DIR / "substrate_string_pbe_contrast_benchmark.py",
        "analyzer_sha256": SCRIPT_DIR / "analyze_substrate_string_pbe_contrast.py",
        "fixture_generator_sha256": ROOT / "tests/fixtures/substrate_string_pbe_contrast/build_tasks.py",
        "fixture_sha256": ROOT / "tests/fixtures/substrate_string_pbe_contrast/tasks.json",
        "original_preregistration_sha256": ROOT / "docs/research/engine_substrate/SUBSTRATE_STRING_PBE_CONTRAST_PREREG_20260925.md",
        "protocol_sha256": ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md",
        "p4_runner_sha256": SCRIPT_DIR / "prog_synthesis_battery.py",
        "synthesis_adapter_sha256": ROOT / "domains/prog_synthesis.py",
        "retrieval_adapter_sha256": ROOT / "domains/prog_retrieval.py",
        "codebook_adapter_sha256": ROOT / "domains/code_writing.py",
        "p4_seed_sha256": ROOT / "seeds/program_synthesis.json",
        "retrieval_seed_sha256": ROOT / "seeds/mbpp_exemplars.json",
        "codebook_seed_sha256": ROOT / "seeds/code_write_constructions.json",
        "native_synthesizer_sha256": dsl / "src/synth_enumerate.rs",
        "native_extension_sha256": dsl / "python/substrate_rs/_native.abi3.so",
        "native_build_manifest_sha256": dsl / "python/substrate_rs/_native.build.json",
        "cargo_lock_sha256": dsl / "Cargo.lock",
    }


def main():
    frozen = json.loads(LOCK.read_text())
    sources = paths()
    hashes = {key: sha(path) for key, path in sources.items()}
    if frozen != hashes:
        raise SystemExit("current-source contrast lock mismatch")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(SCRIPT_DIR)]

    import substrate_string_pbe_contrast_benchmark as bench
    bench.OUT = OUT
    bench.main()

    payload = json.loads(OUT.read_text())
    previous = json.loads(ORIGINAL.read_text())
    arms = ("main", "no_retrieval", "no_retrieval_escalated", "main_replay")
    comparisons = {}
    for arm in arms:
        prior_rows = {row["task_id"]: row for row in previous["cases"][arm]}
        current_rows = {row["task_id"]: row for row in payload["cases"][arm]}
        comparisons[arm] = {
            "task_count": len(current_rows),
            "outcome_mismatches": [task_id for task_id, row in current_rows.items()
                                   if prior_rows[task_id]["outcome"] != row["outcome"]],
            "status_mismatches": [task_id for task_id, row in current_rows.items()
                                  if prior_rows[task_id]["status"] != row["status"]],
            "construction_mismatches": [task_id for task_id, row in current_rows.items()
                                        if prior_rows[task_id].get("construction") != row.get("construction")],
        }
    payload["source_current_replication"] = {
        "previous_report_sha256": sha(ORIGINAL),
        "lock_sha256": sha(LOCK),
        "locked_inputs": hashes,
        "comparison_to_original": comparisons,
        "all_arm_outcomes_match_original": all(not x["outcome_mismatches"] for x in comparisons.values()),
        "all_arm_statuses_match_original": all(not x["status_mismatches"] for x in comparisons.values()),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")

    import analyze_substrate_string_pbe_contrast as analyzer
    analyzer.RAW = OUT
    analyzer.OUT = ANALYSIS
    analyzer.main()
    print(json.dumps({"report": str(OUT), "analysis": str(ANALYSIS),
                      "all_outcomes_match_original": payload["source_current_replication"]["all_arm_outcomes_match_original"]}))


if __name__ == "__main__":
    main()
