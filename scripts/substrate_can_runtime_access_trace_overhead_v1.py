#!/usr/bin/env python3
"""Four-arm CAN timing/correctness measurement for trace instrumentation."""
from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
import sys
from pathlib import Path

from substrate_can_runtime_access_trace_v1 import ROOT, make_input, run_arm, sha

OUT = ROOT / "evaluation/reports/substrate_can_runtime_access_trace_overhead_v1_1_20260925.json"
SIZES = (8, 16)
TOPOLOGIES = ("path", "complete")
MODES = ("2state", "3state")
REPLICATES = 6
ARMS = ("plain", "scale_only", "trace_only", "both")


def summarize(cells: list[dict]) -> list[dict]:
    summaries = []
    for n in SIZES:
        for topology in TOPOLOGIES:
            for mode in MODES:
                group = [cell for cell in cells if
                         (cell["n"], cell["topology"], cell["mode"]) == (n, topology, mode)]
                per_arm = {}
                for arm in ARMS:
                    wall = [cell["arms"][arm]["wall_time_ns"] for cell in group]
                    cpu = [cell["arms"][arm]["cpu_time_ns"] for cell in group]
                    per_arm[arm] = {
                        "wall_median_ns": int(statistics.median(wall)),
                        "wall_range_ns": [min(wall), max(wall)], "wall_replicates_ns": wall,
                        "cpu_median_ns": int(statistics.median(cpu)),
                        "cpu_range_ns": [min(cpu), max(cpu)], "cpu_replicates_ns": cpu,
                    }
                ratios = {}
                for name, numerator, denominator in (
                    ("trace_only_over_plain", "trace_only", "plain"),
                    ("scale_only_over_plain", "scale_only", "plain"),
                    ("both_over_scale_only", "both", "scale_only"),
                    ("both_over_trace_only", "both", "trace_only"),
                ):
                    wall_pair_ratios = [cell["arms"][numerator]["wall_time_ns"] /
                                        max(1, cell["arms"][denominator]["wall_time_ns"])
                                        for cell in group]
                    cpu_pair_ratios = [cell["arms"][numerator]["cpu_time_ns"] /
                                       max(1, cell["arms"][denominator]["cpu_time_ns"])
                                       for cell in group]
                    wall_pair_diffs = [cell["arms"][numerator]["wall_time_ns"] -
                                       cell["arms"][denominator]["wall_time_ns"]
                                       for cell in group]
                    cpu_pair_diffs = [cell["arms"][numerator]["cpu_time_ns"] -
                                      cell["arms"][denominator]["cpu_time_ns"]
                                      for cell in group]
                    ratios[name] = {
                        "wall_paired_ratio_median": statistics.median(wall_pair_ratios),
                        "wall_paired_ratio_range": [min(wall_pair_ratios), max(wall_pair_ratios)],
                        "wall_paired_difference_median_ns": int(statistics.median(wall_pair_diffs)),
                        "wall_paired_difference_range_ns": [min(wall_pair_diffs), max(wall_pair_diffs)],
                        "wall_paired_ratios": wall_pair_ratios,
                        "wall_paired_differences_ns": wall_pair_diffs,
                        "cpu_paired_ratio_median": statistics.median(cpu_pair_ratios),
                        "cpu_paired_ratio_range": [min(cpu_pair_ratios), max(cpu_pair_ratios)],
                        "cpu_paired_difference_median_ns": int(statistics.median(cpu_pair_diffs)),
                        "cpu_paired_difference_range_ns": [min(cpu_pair_diffs), max(cpu_pair_diffs)],
                        "cpu_paired_ratios": cpu_pair_ratios,
                        "cpu_paired_differences_ns": cpu_pair_diffs,
                    }
                summaries.append({"n": n, "topology": topology, "mode": mode,
                                  "replicates": len(group), "arms": per_arm, "ratios": ratios})
    return summaries


def main() -> None:
    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only
    import substrate_can_structure_envelope as can

    seed_doc = json.loads(can.SEED_FILE.read_text())
    cells = []
    for n in SIZES:
        for topology in TOPOLOGIES:
            for mode in MODES:
                for replicate in range(REPLICATES):
                    seed = 20260924 + n * 1000 + replicate
                    fields, weights = make_input(can, n, topology, seed)
                    arm_order = list(ARMS[replicate % len(ARMS):] + ARMS[:replicate % len(ARMS)])
                    arms = {}
                    for arm in arm_order:
                        trace_on = arm in ("trace_only", "both")
                        scale_on = arm in ("scale_only", "both")
                        arms[arm] = run_arm(can, sr, engine_rules_only, seed_doc, n, topology,
                                            mode, seed, trace_on, scale_on)
                    plain = arms["plain"]
                    parity = all(arm["states"] == plain["states"] and arm["progress"] == plain["progress"]
                                 for arm in arms.values())
                    settled = all(arm["terminal_progress"] == 0 and arm["fixed_point_residuals"] == 0
                                  for arm in arms.values())
                    trace_clean = all(
                        arms[name]["dropped_events"] == 0
                        and not arms[name]["static_resource_mismatches"]
                        for name in ("trace_only", "both")
                    )
                    cells.append({"n": n, "topology": topology, "mode": mode,
                                  "replicate": replicate, "seed": seed, "arm_order": arm_order,
                                  "outcome_parity": parity, "all_settled_and_independently_fixed": settled,
                                  "traces_clean": trace_clean, "arms": arms})
    checks = {
        "all_four_arm_outcomes_match": all(cell["outcome_parity"] for cell in cells),
        "all_arms_settle_and_pass_independent_oracle": all(cell["all_settled_and_independently_fixed"] for cell in cells),
        "trace_arms_have_no_dropped_or_unexplained_events": all(cell["traces_clean"] for cell in cells),
        "disabled_trace_arm_emits_no_events": all(
            cell["arms"]["plain"]["event_total"] == 0
            and cell["arms"]["scale_only"]["event_total"] == 0 for cell in cells),
        "trace_only_arm_has_trace_and_no_scale_counters": all(
            cell["arms"]["trace_only"]["event_total"] > 0
            and not cell["arms"]["trace_only"]["scale_audit_counters"] for cell in cells),
        "scale_only_arm_has_scale_counters_and_no_trace": all(
            cell["arms"]["scale_only"]["scale_audit_counters"].get("leaf_visits", 0) > 0
            and cell["arms"]["scale_only"]["event_total"] == 0 for cell in cells),
    }
    extension_path = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    summaries = summarize(cells)
    report = {
        "schema_version": 1,
        "run_id": "substrate-can-runtime-access-trace-overhead-v1.1-20260925",
        "protocol": "SUBSTRATE_CAN_RUNTIME_ACCESS_TRACE_OVERHEAD_PREREG_20260925.md",
        "scope": "48 deterministic CAN instances × four instrumentation arms = 192 runs; N=8/16, path/complete, two-/three-state, six replicates",
        "claim_boundary": "Single-host descriptive overhead estimate for this authored CAN envelope. No extrapolation to larger graphs, frame-locality claim, or complete trace coverage.",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(extension_path), "native_extension_sha256": sha(extension_path),
            "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "source_sha256": {path: sha(ROOT / path) for path in (
                "runners/dsl/src/access_trace.rs", "runners/dsl/src/lib.rs", "runners/dsl/src/rewrite.rs",
                "runners/dsl/src/term.rs", "runners/dsl/src/py.rs", "scripts/substrate_can_runtime_access_trace_v1.py",
                "scripts/substrate_can_runtime_access_trace_overhead_v1.py",
                "scripts/substrate_can_structure_envelope.py", "seeds/can_native_reimplementation.json",
                "docs/research/engine_substrate/SUBSTRATE_CAN_RUNTIME_ACCESS_TRACE_OVERHEAD_PREREG_20260925.md")},
        },
        "checks": checks, "summaries": summaries, "cells": cells,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "cells": len(cells), "runs": len(cells) * len(ARMS),
                      "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("CAN trace-overhead measurement failed semantic/instrumentation gates")


if __name__ == "__main__":
    main()
