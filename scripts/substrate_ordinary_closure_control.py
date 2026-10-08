#!/usr/bin/env python3
"""Paired same-build audit control for closure rules without term-edge reads.

Uses the established isolated closure worker and exact closure oracle. Audit
instrumentation-on and instrumentation-off workers use identical generated
instances in alternating process order. The run measures instrumentation cost
on the unaffected match-edge-only path.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/substrate_capability_closure_pilot.py"
OUT = ROOT / "evaluation/reports/substrate_ordinary_closure_control_20260924.json"
SIZES = (16, 32, 64, 96)
TOPOLOGIES = ("path", "banded_dag")
REPEATS = 20
AUDIT_MODES = ("off", "on")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    from substrate_rs import _native

    inherited_paths = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
    worker_paths = inherited_paths + [str(ROOT / "runners/dsl/python"), str(ROOT)]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(worker_paths)}
    extension_path = Path(_native.__file__).resolve()
    spec = importlib.util.spec_from_file_location("closure_control_worker", HARNESS)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load shared closure workload constructor")
    closure_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(closure_module)
    static_access_audit = []
    for topology in TOPOLOGIES:
        for n in SIZES:
            audit_substrate, _ = closure_module.make_substrate(n, topology, "transitive_closure")
            access = audit_substrate.rule_access_sets()
            if any(row[4] for row in access):
                raise RuntimeError(f"closure control unexpectedly has typed term-edge reads: {topology} n={n}")
            static_access_audit.append({
                "topology": topology,
                "nodes": n,
                "rule_access_sets": [list(row) for row in access],
                "term_edge_reads_empty": True,
            })
    records = []
    started = time.time_ns()
    for topology in TOPOLOGIES:
        for n in SIZES:
            for replicate in range(REPEATS):
                mode_order = AUDIT_MODES if replicate % 2 == 0 else tuple(reversed(AUDIT_MODES))
                for audit_mode in mode_order:
                    proc = subprocess.run(
                        [sys.executable, str(HARNESS),
                         "--worker-size", str(n),
                         "--worker-topology", topology,
                         "--worker-family", "transitive_closure",
                         "--worker-run-id", "ordinary-closure-control-20260924",
                         "--worker-audit-mode", audit_mode,
                         "--worker-replicate", str(replicate),
                         "--max-steps", "100000"],
                        cwd=ROOT, env=env, text=True, capture_output=True, check=True,
                    )
                    row = json.loads(proc.stdout)
                    row["worker_stderr"] = proc.stderr
                    row["replicate"] = replicate
                    row["audit_mode"] = audit_mode
                    if audit_mode == "on" and not all(row["pilot_detail"]["counter_invariants"].values()):
                        raise RuntimeError(f"native counter reconciliation failed: {topology} n={n}")
                    records.append(row)
    summaries = []
    for topology in TOPOLOGIES:
        for n in SIZES:
            group = [r for r in records if r["pilot_detail"]["topology"] == topology
                     and r["input_structure"]["nodes"] == n]
            per_mode = {}
            for mode in AUDIT_MODES:
                mode_rows = [r for r in group if r["audit_mode"] == mode]
                per_mode[mode] = {
                    "median_wall_time_ns": int(statistics.median(r["cost"]["wall_time_ns"] for r in mode_rows)),
                    "median_cpu_time_ns": int(statistics.median(r["cost"]["cpu_time_ns"] for r in mode_rows)),
                    "median_progress_steps": int(statistics.median(r["cost"]["rule_firings"] for r in mode_rows)),
                    "median_candidate_pairs": (
                        int(statistics.median(r["pilot_detail"]["candidate_pairs_enumerated"] for r in mode_rows))
                        if mode == "on" else None),
                    "all_exact_and_settled": all(r["outcome"]["exact"] and
                                                  r["outcome"]["reason"] == "settled" for r in mode_rows),
                }
            ratios = []
            cpu_ratios = []
            for replicate in range(REPEATS):
                off = next(r for r in group if r["audit_mode"] == "off" and r["replicate"] == replicate)
                on = next(r for r in group if r["audit_mode"] == "on" and r["replicate"] == replicate)
                ratios.append(on["cost"]["wall_time_ns"] / off["cost"]["wall_time_ns"])
                cpu_ratios.append(on["cost"]["cpu_time_ns"] / off["cost"]["cpu_time_ns"])
            summaries.append({
                "topology": topology,
                "nodes": n,
                "repeats_per_mode": REPEATS,
                "paired_wall_ratio_audit_on_over_off_median": statistics.median(ratios),
                "paired_cpu_ratio_audit_on_over_off_median": statistics.median(cpu_ratios),
                "modes": per_mode,
                "all_exact_and_settled": all(m["all_exact_and_settled"] for m in per_mode.values()),
            })
    output = {
        "run_state": "exploratory_paired_instrumentation_pilot",
        "protocol": "ordinary closure audit-on/off control v2",
        "command": "PYTHONPATH=<fresh-native-package>:.: python3 scripts/substrate_ordinary_closure_control.py",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip() != "",
        "started_unix_ns": started,
        "finished_unix_ns": time.time_ns(),
        "python": sys.version,
        "platform": platform.platform(),
        "native_extension_path": str(extension_path),
        "native_extension_sha256": sha(extension_path),
        "source_sha256": {
            "harness": sha(Path(__file__)),
            "closure_worker": sha(HARNESS),
            "rewrite": sha(ROOT / "runners/dsl/src/rewrite.rs"),
            "substrate": sha(ROOT / "runners/dsl/src/substrate.rs"),
        },
        "static_access_audit": static_access_audit,
        "workload": {
            "family": "two-rule transitive closure",
            "topologies": list(TOPOLOGIES),
            "sizes": list(SIZES),
            "repeats_per_point": REPEATS,
            "audit_modes": list(AUDIT_MODES),
            "term_edge_reads": [],
            "reference": "independent expected closure formula plus terminal no-work probe in the shared worker",
        },
        "summary": summaries,
        "records": records,
        "claim_boundary": [
            "Eighty isolated workers on two sparse graph families through n=96; exploratory only.",
            "The measurements show the term-edge cursor path is absent for these typed match-edge-only rules.",
            "Paired ratios estimate scale-audit overhead on this path only; no general complexity/hardware-scale claim follows.",
        ],
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "summary": summaries,
                      "all_exact_and_settled": all(x["all_exact_and_settled"] for x in summaries)}, indent=2))
    if not all(x["all_exact_and_settled"] for x in summaries):
        raise SystemExit("an ordinary closure control worker failed its exact-state or settle check")


if __name__ == "__main__":
    main()
