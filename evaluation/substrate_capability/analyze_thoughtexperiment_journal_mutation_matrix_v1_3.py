#!/usr/bin/env python3
"""Independently recompute journal/oracle equality from v1.3 raw diffs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_journal_mutation_matrix_v1_3_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_3_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_3_analysis_20261004.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    lock = json.loads(LOCK.read_text())
    capture = json.loads(CAPTURE.read_text())
    current = {name: sha(ROOT / name) for name in lock["locked_inputs"]}
    lock_sha = sha(LOCK)
    result = capture["result"]
    rows = result.get("rows", [])
    case_names = [row.get("case") for row in rows]
    checks = {
        "capture_lock_hash_matches": capture.get("lock_sha256") == lock_sha,
        "current_sources_match_lock": current == lock["locked_inputs"] == capture.get("locked_inputs"),
        "seventeen_unique_cases": len(rows) == 17 and len(set(case_names)) == 17,
        "journal_diffs_recompute_equal_oracle": all(row.get("journal_delta") == row.get("whole_graph_diff") for row in rows),
        "phase_diff_payloads_are_well_formed": all(
            (row.get("phase_journal_delta") == row.get("phase_whole_graph_diff"))
            if row.get("case") == "phase checkpoint and derived writes"
            else row.get("phase_journal_delta") is None and row.get("phase_whole_graph_diff") is None
            for row in rows),
        "post_capture_divergence_is_explicit": all(
            (row.get("post_capture_whole_graph_diff") is not None and
             row.get("post_capture_whole_graph_diff") != row.get("journal_delta"))
            if row.get("case") == "post-capture untracked divergence control"
            else row.get("post_capture_whole_graph_diff") is None
            for row in rows),
        "evaluator_flags_agree_with_recomputed_diffs": all(
            row.get("journal_equals_whole_graph_diff_at_capture") is
            (row.get("journal_delta") == row.get("whole_graph_diff")) and
            row.get("phase_journal_equals_phase_diff") is
            (row.get("phase_journal_delta") == row.get("phase_whole_graph_diff")
             if row.get("phase_journal_delta") is not None else True)
            for row in rows),
    }
    expected_cases = {
        "node attribute set", "direct mutable node access", "node attribute removal",
        "node type change", "live identity restoration", "fresh identity restoration",
        "tombstoned identity restoration", "node deletion with incident edges", "node insertion",
        "edge insertion", "existing edge replacement", "mutable edge attributes",
        "single edge deletion", "batch edge deletion with duplicate index",
        "repeated writes to one identity", "phase checkpoint and derived writes",
        "post-capture untracked divergence control",
    }
    checks["registered_case_set_matches"] = set(case_names) == expected_cases
    analysis = {
        "schema": "ThoughtexperimentJournalMutationMatrixV1_3Analysis",
        "capture_sha256": sha(CAPTURE), "lock_sha256": lock_sha,
        "checks": checks, "passed": all(checks.values()),
        "case_count": len(rows), "case_names": case_names,
        "journal_oracle_equal_count": sum(row.get("journal_delta") == row.get("whole_graph_diff") for row in rows),
        "phase_case_equal": next((row.get("phase_journal_delta") == row.get("phase_whole_graph_diff")
                                  for row in rows if row.get("case") == "phase checkpoint and derived writes"), False),
    }
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": analysis["passed"], "checks": checks,
                      "analysis_sha256": sha(OUT)}, sort_keys=True))
    return 0 if analysis["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
