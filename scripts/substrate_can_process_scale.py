#!/usr/bin/env python3
"""Fresh-process CAN size/resource sweep using the shared workload constructor."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKLOAD = ROOT / "scripts/substrate_can_structure_envelope.py"
OUT = ROOT / "evaluation/reports/substrate_can_process_scale_20260924.json"
REPLICATES = 3
MODES = ("2state", "3state")
GRANULARITY = 0.25
CELLS = [
    (n, topology)
    for topology, sizes in (("path", (32, 64, 128, 256)),
                            ("banded2", (32, 64, 128, 256)),
                            ("complete", (32, 64, 128)))
    for n in sizes
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inherited = os.environ.copy()
    rows = []
    start = time.perf_counter()
    for n, topology in CELLS:
        for mode in MODES:
            for replicate in range(REPLICATES):
                fd, tmp_name = tempfile.mkstemp(prefix="can-scale-", suffix=".json")
                os.close(fd)
                tmp_path = Path(tmp_name)
                env = {
                    **inherited,
                    "SUBSTRATE_CAN_OUT": str(tmp_path),
                    "SUBSTRATE_CAN_SIZES": str(n),
                    "SUBSTRATE_CAN_TOPOLOGIES": topology,
                    "SUBSTRATE_CAN_MODES": mode,
                    "SUBSTRATE_CAN_GRANULARITIES": str(GRANULARITY),
                    "SUBSTRATE_CAN_REPLICATES": "1",
                    "SUBSTRATE_CAN_SKIP_AUDIT": "1",
                }
                command = [sys.executable, str(WORKLOAD)]
                t0 = time.perf_counter_ns()
                proc = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                      capture_output=True, timeout=120)
                elapsed = time.perf_counter_ns() - t0
                if proc.returncode != 0:
                    raise RuntimeError(
                        f"worker failed n={n} {topology} {mode} rep={replicate}:\n"
                        f"stdout={proc.stdout}\nstderr={proc.stderr}"
                    )
                payload = json.loads(tmp_path.read_text())
                tmp_path.unlink(missing_ok=True)
                draw = payload["draws"][0]
                rows.append({
                    **draw,
                    "worker_elapsed_ns": elapsed,
                    "worker_command": command,
                    "worker_stdout": proc.stdout.strip(),
                    "rss_baseline_highwater_kib": draw["rss_after_import_highwater_kib"],
                    "rss_after_setup_highwater_kib": draw["rss_after_setup_highwater_kib"],
                    "rss_after_run_highwater_kib": draw["rss_after_run_highwater_kib"],
                    "worker_seed_manifest_sha256": payload["provenance"]["seed_manifest_sha256"],
                    "worker_native_extension_sha256": payload["provenance"]["native_extension_sha256"],
                })
                print(f"finished n={n} {topology} {mode} rep={replicate + 1}/{REPLICATES} "
                      f"wall_ms={draw['wall_time_ns']/1e6:.2f} rss_kib={draw['rss_after_run_highwater_kib']}",
                      flush=True)

    summaries = []
    for n, topology in CELLS:
        for mode in MODES:
            group = [r for r in rows if (r["n"], r["topology"], r["mode"]) == (n, topology, mode)]
            summaries.append({
                "n": n, "topology": topology, "mode": mode,
                "replicates": len(group),
                "all_complete": all(r["budget_not_reached"] and r["terminal_probe_count"] == 0
                                     and r["independent_fixed_point_residuals"] == 0 for r in group),
                "median_progress_count": statistics.median(r["progress_count"] for r in group),
                "median_wall_time_ns": int(statistics.median(r["wall_time_ns"] for r in group)),
                "median_cpu_time_ns": int(statistics.median(r["cpu_time_ns"] for r in group)),
                "median_rss_baseline_highwater_kib": int(statistics.median(r["rss_baseline_highwater_kib"] for r in group)),
                "median_rss_after_setup_highwater_kib": int(statistics.median(r["rss_after_setup_highwater_kib"] for r in group)),
                "median_rss_after_run_highwater_kib": int(statistics.median(r["rss_after_run_highwater_kib"] for r in group)),
                "median_edges": int(statistics.median(r["directed_coupling_edges"] for r in group)),
            })
    payload = {
        "run_id": "substrate-can-process-scale-20260924",
        "scope": "fresh-process native CAN scaling and process high-water RSS; no audit twin",
        "configuration": {"cells": CELLS, "modes": MODES, "weight_granularity": GRANULARITY,
                          "replicates_per_cell": REPLICATES, "audit": "disabled",
                          "graph_setup": "included in RSS, excluded from run_rules timing"},
        "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                    "total_elapsed_seconds": time.perf_counter() - start},
        "provenance": {"orchestrator_sha256": sha(Path(__file__).resolve()),
                       "workload_sha256": sha(WORKLOAD),
                       "seed_manifest_sha256": sha(ROOT / "seeds/can_native_reimplementation.json"),
                       "command": "PYTHONPATH=<native-extension-parent>:$PWD python3 scripts/substrate_can_process_scale.py",
                       "pythonpath": inherited.get("PYTHONPATH", ""), "cwd": str(ROOT)},
        "summaries": summaries, "workers": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(rows), "groups": len(summaries),
                      "all_complete": all(x["all_complete"] for x in summaries),
                      "output": str(OUT)}, indent=2))
    if not all(x["all_complete"] for x in summaries):
        raise SystemExit("incomplete or unstable scale worker recorded")


if __name__ == "__main__":
    main()
