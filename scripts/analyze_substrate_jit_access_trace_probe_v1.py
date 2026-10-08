#!/usr/bin/env python3
"""Independent invariant checks for the three direct JIT trace fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation/reports/substrate_jit_access_trace_probe_v1_20260925.json"
OUTPUT = ROOT / "evaluation/reports/substrate_jit_access_trace_probe_v1_analysis_20260925.json"
EXPECTED = {"jit_attr": "jit_attr_read", "jit_type": "jit_type_read",
            "jit_neighbour_count": "term_edge_read"}


def main() -> None:
    raw = json.loads(SOURCE.read_text())
    checks = {"all_three_jit_cases_present": {c["case"] for c in raw["cells"]} == set(EXPECTED),
              "runner_checks_all_pass": all(raw["checks"].values()),
              "each_case_has_one_compiled_jit_rule": True,
              "trace_kind_matches_case": True,
              "paired_outcome_equal_and_settled": True,
              "no_disabled_events_or_trace_drops": True,
              "provenance_source_hashes_current": True}
    for cell in raw["cells"]:
        checks["each_case_has_one_compiled_jit_rule"] &= cell["traced"]["compiled_jit_rules"] == 1
        checks["trace_kind_matches_case"] &= any(row[1] == EXPECTED[cell["case"]]
                                                    for row in cell["traced"]["events"])
        checks["paired_outcome_equal_and_settled"] &= (
            cell["outcome_match"] and cell["traced"]["status"] == "fixed_point"
            and cell["traced"]["terminal_progress"] == 0)
        checks["no_disabled_events_or_trace_drops"] &= (
            cell["plain"]["event_count"] == 0 and cell["traced"]["dropped"] == 0)
    for path, digest in raw["provenance"]["source_sha256"].items():
        checks["provenance_source_hashes_current"] &= hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    result = {"schema_version": 1, "source": str(SOURCE.relative_to(ROOT)),
              "checks": checks, "all_checks_pass": all(checks.values()),
              "case_event_counts": {c["case"]: c["traced"]["event_count"] for c in raw["cells"]},
              "claim_boundary": "Confirms targeted JIT hooks only; does not establish complete graph-read coverage."}
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
