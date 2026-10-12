#!/usr/bin/env python3
"""Replay the authored CAN discrete relaxation on the current native engine.

This is an envelope probe, not a replacement for the registered CAN tests:
it records per-draw convergence, terminal fixed-point check, state vocabulary,
frustration, and runtime with exact source/build provenance.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "tests/test_can_native_reimplementation.py"
OUT = ROOT / "evaluation/reports/substrate_can_authored_workload_20260924.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    from substrate_rs import _native

    spec = importlib.util.spec_from_file_location("can_authored_helpers", TEST)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    rows = []
    for mode in ("2state", "3state"):
        for coarse in (True, False):
            for replicate in range(20):
                s = module._loaded_substrate()
                inner = s._inner
                mt, concepts = module._build_draw(s, 1000 + replicate, coarse, mode)
                cpu0, wall0 = time.process_time_ns(), time.perf_counter_ns()
                converged, steps = module._discrete_async_converges(inner, 3000)
                wall, cpu = time.perf_counter_ns() - wall0, time.process_time_ns() - cpu0
                states = module._read_states(inner, concepts)
                # A zero-progress follow-up verifies that the settled state is fixed.
                terminal = inner.run_rules(1)
                values = sorted({float(v) for v in states.values()})
                expected_vocab = [-1.0, 1.0] if mode == "2state" else [-1.0, 0.0, 1.0]
                exact_vocab = all(v in expected_vocab for v in values)
                rows.append({
                    "mode": mode, "weight_granularity": 1.0 if coarse else 0.25,
                    "seed": 1000 + replicate, "concepts": len(concepts),
                    "directed_coupling_edges": len(concepts) * (len(concepts) - 1),
                    "converged_under_3000": converged, "progress_steps": steps,
                    "terminal_probe_steps": terminal, "state_vocab_valid": exact_vocab,
                    "state_histogram": {str(v): sum(1 for x in states.values() if float(x) == v)
                                         for v in expected_vocab},
                    "frustration": float(module._frustration(inner, mt, concepts)),
                    "wall_time_ns": wall, "cpu_time_ns": cpu,
                })
    summaries = []
    for mode in ("2state", "3state"):
        for granularity in (1.0, 0.25):
            group = [r for r in rows if r["mode"] == mode and r["weight_granularity"] == granularity]
            summaries.append({
                "mode": mode, "weight_granularity": granularity, "n": len(group),
                "all_converged": all(r["converged_under_3000"] for r in group),
                "all_terminal_probes_zero": all(r["terminal_probe_steps"] == 0 for r in group),
                "all_vocab_valid": all(r["state_vocab_valid"] for r in group),
                "median_progress_steps": statistics.median(r["progress_steps"] for r in group),
                "median_wall_time_ns": int(statistics.median(r["wall_time_ns"] for r in group)),
                "median_cpu_time_ns": int(statistics.median(r["cpu_time_ns"] for r in group)),
                "median_frustration": statistics.median(r["frustration"] for r in group),
            })
    payload = {
        "run_id": "substrate-can-authored-workload-20260924",
        "scope": "authored CAN discrete asynchronous relaxation; N=8 complete symmetric coupling graph",
        "limits": ["single graph size", "not independent replication", "frustration is native metric"],
        "provenance": {
            "seed_manifest_sha256": sha(ROOT / "seeds/can_native_reimplementation.json"),
            "authored_test_sha256": sha(TEST),
            "native_extension": str(Path(_native.__file__).resolve()),
            "native_extension_sha256": sha(Path(_native.__file__).resolve()),
            "python": platform.python_version(), "platform": platform.platform(),
            "cwd": str(ROOT), "pythonpath": os.environ.get("PYTHONPATH", ""),
            "command": "PYTHONPATH=/tmp/ocelot-native-access.ErnBQ0:$PWD python scripts/substrate_can_authored_workload.py",
        },
        "summaries": summaries, "draws": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summaries, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
