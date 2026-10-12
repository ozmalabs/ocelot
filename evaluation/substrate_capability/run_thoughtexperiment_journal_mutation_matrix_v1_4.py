#!/usr/bin/env python3
"""Run the locked current-source Thoughtexperiment journal mutation matrix v1.4."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_journal_mutation_matrix_v1_4_lock_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_4_20261004.json"
INPUTS = [
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_JOURNAL_MUTATION_MATRIX_V1_4_PREREG_20261004.md",
    "runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_4.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/persist.rs",
    "runners/dsl/src/value.rs", "runners/dsl/src/sym.rs", "runners/dsl/src/lib.rs",
    "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
    "evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_4.py",
    "evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_4.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if not LOCK.is_file() or not OUT.parent.is_dir():
        raise SystemExit("locked inputs or report directory missing")
    lock = json.loads(LOCK.read_text())
    actual = {name: sha(ROOT / name) for name in INPUTS}
    if lock.get("locked_inputs") != actual:
        raise SystemExit("locked source/protocol mismatch; refusing to run")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    argv = ["cargo", "run", "-j", "2", "--bin", "thoughtexperiment_journal_mutation_matrix_v1_4",
            "--manifest-path", "runners/dsl/Cargo.toml"]
    completed = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise SystemExit(f"Cargo/evaluator failed ({completed.returncode}); stderr follows:\n{completed.stderr[-12000:]}")
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise SystemExit(f"evaluator did not emit one JSON result: {exc}\n{completed.stdout[-4000:]}")
    rows = result.get("rows", [])
    if len(rows) != 20 or result.get("all_matrix_cases_match") is not True or result.get("divergence_control_works") is not True:
        raise SystemExit("evaluator gates failed or row count differs from preregistered 20")
    if any(row.get("journal_equals_whole_graph_diff_at_capture") is not True or
           row.get("phase_journal_equals_phase_diff") is not True for row in rows):
        raise SystemExit("one or more journal/oracle parity checks failed")
    if result.get("all_revision_expectations_match") is not True:
        raise SystemExit("revision behavior differed from the preregistered method class")
    binary = ROOT / "runners/dsl/target/debug/thoughtexperiment_journal_mutation_matrix_v1_4"
    rustc = subprocess.run(["rustc", "-V"], text=True, capture_output=True, check=True).stdout.strip()
    capture = {
        "schema": "ThoughtexperimentJournalMutationMatrixV1_4Capture",
        "execution": {"argv": argv, "profile": "dev", "returncode": completed.returncode,
                      "rustc": rustc, "cargo_stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
                      "cargo_warning_count": completed.stderr.count("warning:")},
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "lock_sha256": sha(LOCK), "locked_inputs": actual,
        "runner_binary": {"path": str(binary.relative_to(ROOT)), "sha256": sha(binary)},
        "result": result,
    }
    OUT.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    analyzer = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_4.py"
    reviewed = subprocess.run(["python3", str(analyzer)], cwd=ROOT, text=True,
                              capture_output=True, check=False)
    if reviewed.returncode:
        raise SystemExit(f"independent analysis failed ({reviewed.returncode}):\n{reviewed.stderr}\n{reviewed.stdout}")
    print(json.dumps({"capture": str(OUT.relative_to(ROOT)), "rows": len(rows),
                      "all_matrix_cases_match": True, "divergence_control_works": True,
                      "lock_sha256": capture["lock_sha256"],
                      "result_sha256": sha(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
