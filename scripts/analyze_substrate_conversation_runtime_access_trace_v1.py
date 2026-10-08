#!/usr/bin/env python3
"""Independent consistency checks for the conversation runtime trace capture."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation/reports/substrate_conversation_runtime_access_trace_v1_20260925.json"
OUTPUT = ROOT / "evaluation/reports/substrate_conversation_runtime_access_trace_v1_analysis_20260925.json"


def main() -> None:
    source = json.loads(SOURCE.read_text())
    cells = source["cells"]
    checks = {
        "four_paired_cells": len(cells) == 4,
        "runner_checks_all_pass": all(source["checks"].values()),
        "all_trace_site_counts_reconcile": True,
        "all_trace_events_match_static_access": True,
        "all_dynamic_pairs_within_static_projection": True,
        "disabled_arms_have_no_events": True,
        "enabled_arms_have_events_without_drops": True,
    }
    summaries = []
    totals = {"event_occurrences": 0, "static_possible_pairs": 0,
              "dynamic_concrete_pairs": 0, "static_pairs_unobserved": 0}
    for cell in cells:
        plain, traced = cell["plain"], cell["traced"]
        checks["disabled_arms_have_no_events"] &= plain["event_total"] == 0
        checks["enabled_arms_have_events_without_drops"] &= (
            traced["event_total"] > 0 and traced["dropped_events"] == 0)
        checks["all_trace_events_match_static_access"] &= not traced["static_resource_mismatches"]
        checks["all_dynamic_pairs_within_static_projection"] &= not traced["dynamic_pairs_outside_static"]
        checks["all_trace_site_counts_reconcile"] &= all(
            all(row[key] for key in ("pattern_edge_exact", "attr_read_exact", "attr_write_exact",
                                     "edge_upsert_exact", "node_mint_exact"))
            for row in traced["instrumented_site_coverage"])
        for key in totals:
            totals[key] += traced[{
                "event_occurrences": "event_total",
                "static_possible_pairs": "static_possible_pairs",
                "dynamic_concrete_pairs": "dynamic_concrete_pairs",
                "static_pairs_unobserved": "static_pairs_unobserved",
            }[key]]
        summaries.append({"size": cell["size"], "replicate": cell["replicate"],
                          "events": traced["event_total"],
                          "observed_rules": traced["observed_rule_count"],
                          "static_pairs": traced["static_possible_pairs"],
                          "dynamic_pairs": traced["dynamic_concrete_pairs"],
                          "unobserved_static_pairs": traced["static_pairs_unobserved"],
                          "site_rows": len(traced["instrumented_site_coverage"])})
    result = {"schema_version": 1, "source": str(SOURCE.relative_to(ROOT)),
              "checks": checks, "all_checks_pass": all(checks.values()),
              "aggregate": totals, "cells": summaries,
              "claim_boundary": "Consistency analysis only; observed accesses do not prove trace completeness or safe frame partitioning."}
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
