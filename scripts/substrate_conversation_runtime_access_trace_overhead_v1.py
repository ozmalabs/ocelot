#!/usr/bin/env python3
"""Four-arm conversation trace instrumentation overhead capture."""
from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
import sys
from pathlib import Path

from substrate_conversation_runtime_access_trace_v1 import ROOT, run_arm

OUT = ROOT / "evaluation/reports/substrate_conversation_runtime_access_trace_overhead_v1_20260925.json"
SIZES = (1, 2)
REPLICATES = 6
ARMS = ("plain", "scale_only", "trace_only", "both")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    cells = []
    for size in SIZES:
        for replicate in range(REPLICATES):
            order = list(ARMS[replicate % 4:] + ARMS[:replicate % 4])
            arms = {}
            for arm in order:
                trace = arm in ("trace_only", "both")
                scale = arm in ("scale_only", "both")
                arms[arm] = run_arm(size, replicate, trace_enabled=trace, scale_enabled=scale)
            base = arms["plain"]
            parity = all((a["progress"], a["runner_status"], a["terminal_progress"], a["projections"])
                         == (base["progress"], base["runner_status"], base["terminal_progress"], base["projections"])
                         for a in arms.values())
            sites = arms["both"]["instrumented_site_coverage"]
            coverage = all(all(row[k] for k in ("pattern_edge_exact", "attr_read_exact", "attr_write_exact",
                                                "edge_upsert_exact", "node_mint_exact")) for row in sites)
            clean = all(not arms[a]["dropped_events"] and not arms[a]["static_resource_mismatches"]
                        for a in ("trace_only", "both"))
            cells.append({"size": size, "replicate": replicate, "arm_order": order, "arms": arms,
                          "outcome_parity": parity, "coverage_reconciles": coverage, "traces_clean": clean})

    checks = {
        "all_arms_match_outcome_progress_and_fixed_point": all(c["outcome_parity"] for c in cells),
        "both_arm_coverage_counts_reconcile": all(c["coverage_reconciles"] for c in cells),
        "traces_have_no_overflow_or_static_mismatch": all(c["traces_clean"] for c in cells),
        "trace_disabled_arms_emit_no_events": all(
            c["arms"][a]["event_total"] == 0 for c in cells for a in ("plain", "scale_only")),
        "trace_enabled_arms_emit_events": all(
            c["arms"][a]["event_total"] > 0 for c in cells for a in ("trace_only", "both")),
        "scale_counter_arms_have_counters": all(
            bool(c["arms"][a]["scale_audit"]) for c in cells for a in ("scale_only", "both")),
        "non_scale_arms_have_no_counters": all(
            not c["arms"][a]["scale_audit"] for c in cells for a in ("plain", "trace_only")),
    }
    summaries = []
    for size in SIZES:
        group = [c for c in cells if c["size"] == size]
        times = {a: [c["arms"][a]["wall_time_ns"] for c in group] for a in ARMS}
        cpu = {a: [c["arms"][a]["cpu_time_ns"] for c in group] for a in ARMS}
        contrasts = {}
        for numerator, denominator in (("trace_only", "plain"), ("scale_only", "plain"),
                                       ("both", "scale_only"), ("both", "trace_only")):
            wr = [c["arms"][numerator]["wall_time_ns"] / max(1, c["arms"][denominator]["wall_time_ns"])
                  for c in group]
            cr = [c["arms"][numerator]["cpu_time_ns"] / max(1, c["arms"][denominator]["cpu_time_ns"])
                  for c in group]
            contrasts[f"{numerator}_over_{denominator}"] = {
                "wall_paired_ratio_median": statistics.median(wr), "wall_paired_ratio_range": [min(wr), max(wr)],
                "cpu_paired_ratio_median": statistics.median(cr), "cpu_paired_ratio_range": [min(cr), max(cr)],
                "wall_paired_ratios": wr, "cpu_paired_ratios": cr,
            }
        summaries.append({"size": size, "replicates": len(group), "arms": {
            a: {"wall_median_ns": int(statistics.median(times[a])), "wall_range_ns": [min(times[a]), max(times[a])],
                "wall_replicates_ns": times[a], "cpu_median_ns": int(statistics.median(cpu[a])),
                "cpu_range_ns": [min(cpu[a]), max(cpu[a])], "cpu_replicates_ns": cpu[a]} for a in ARMS},
            "contrasts": contrasts})

    ext = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    report = {
        "schema_version": 1,
        "run_id": "substrate-conversation-runtime-access-trace-overhead-v1-20260925",
        "protocol": "SUBSTRATE_CONVERSATION_RUNTIME_ACCESS_TRACE_OVERHEAD_PREREG_20260925.md",
        "scope": "12 deterministic one/two-deliberation fixtures × four instrumentation arms = 48 closure runs; six replicates per size",
        "claim_boundary": "One-host descriptive instrumentation cost on one small authored conversation workload; no scaling, representativeness, or complete-trace claim.",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                       "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
                       "native_extension_sha256": sha(ext),
                       "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
                       "source_sha256": {p: sha(ROOT / p) for p in (
                           "runners/dsl/src/access_trace.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/term.rs",
                           "runners/dsl/src/py.rs", "scripts/substrate_conversation_runtime_access_trace_v1.py",
                           "scripts/substrate_conversation_runtime_access_trace_overhead_v1.py",
                           "docs/research/engine_substrate/SUBSTRATE_CONVERSATION_RUNTIME_ACCESS_TRACE_OVERHEAD_PREREG_20260925.md",
                           "domains/conversation_deliberation.py", "substrate/world_adapter.py")}},
        "checks": checks, "summaries": summaries, "cells": cells,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "cells": len(cells), "runs": len(cells) * len(ARMS), "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("conversation overhead gate failed; timing is not interpretable")


if __name__ == "__main__":
    main()
