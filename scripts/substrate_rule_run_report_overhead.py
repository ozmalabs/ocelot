#!/usr/bin/env python3
"""Paired microbenchmark for legacy vs typed rule-run APIs.

Measures caller-visible cost on identical deterministic rule cycles. Both APIs
share the same Rust runner; the comparison includes PyO3 return conversion and
Python-visible reporting cost, not the common Rust report construction.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evaluation/reports/substrate_rule_run_report_overhead_20260924.json"
REPEATS = 7
CALLS_PER_API_PER_REPEAT = 5_000
PROGRESS_BUDGET = 2


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def make_cycle():
    from substrate_rs import _native

    s = _native.Substrate()
    left = s.add_node("PilotVertex")
    right = s.add_node("PilotVertex")
    s.add_edge_unchecked(left, "pilot_toggle_a", right)
    s.add_rule({
        "name": "pilot_a_to_b",
        "match": [["x", "pilot_toggle_a", "y"]],
        "effects": [
            ["del_edge", "x", "pilot_toggle_a", "y"],
            ["add_edge", "x", "pilot_toggle_b", "y", {}],
        ],
    })
    s.add_rule({
        "name": "pilot_b_to_a",
        "match": [["x", "pilot_toggle_b", "y"]],
        "effects": [
            ["del_edge", "x", "pilot_toggle_b", "y"],
            ["add_edge", "x", "pilot_toggle_a", "y", {}],
        ],
    })
    return s, left, right


def timed_calls(substrate, api: str, calls: int) -> dict:
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    last = None
    if api == "legacy_integer":
        for _ in range(calls):
            last = substrate.run_rules(PROGRESS_BUDGET)
    else:
        for _ in range(calls):
            last = substrate.run_rules_report(PROGRESS_BUDGET, False)
    return {
        "wall_time_ns": time.perf_counter_ns() - wall_start,
        "cpu_time_ns": time.process_time_ns() - cpu_start,
        "last_result": last,
    }


def main() -> None:
    from substrate_rs import _native

    _native.Substrate.scale_audit_set_enabled(False)
    _native.Substrate.scale_audit_reset()

    records = []
    for repeat in range(REPEATS):
        legacy, left_l, right_l = make_cycle()
        typed, left_t, right_t = make_cycle()
        # Warm both code paths once; exclude setup and warmup from timing.
        legacy_warm = legacy.run_rules(PROGRESS_BUDGET)
        typed_warm = typed.run_rules_report(PROGRESS_BUDGET, False)
        if legacy_warm != typed_warm["progress_steps"]:
            raise RuntimeError("warmup semantic mismatch")
        order = ("legacy_integer", "typed_report") if repeat % 2 == 0 else (
            "typed_report", "legacy_integer"
        )
        timed = {}
        for api in order:
            substrate = legacy if api == "legacy_integer" else typed
            timed[api] = timed_calls(substrate, api, CALLS_PER_API_PER_REPEAT)

        legacy_state = {
            "toggle_a": legacy.has_edge(left_l, "pilot_toggle_a", right_l),
            "toggle_b": legacy.has_edge(left_l, "pilot_toggle_b", right_l),
        }
        typed_state = {
            "toggle_a": typed.has_edge(left_t, "pilot_toggle_a", right_t),
            "toggle_b": typed.has_edge(left_t, "pilot_toggle_b", right_t),
        }
        typed_result = timed["typed_report"]["last_result"]
        record = {
            "repeat": repeat,
            "call_order": list(order),
            "calls_per_api": CALLS_PER_API_PER_REPEAT,
            "legacy_integer": timed["legacy_integer"],
            "typed_report": timed["typed_report"],
            "legacy_state": legacy_state,
            "typed_state": typed_state,
            "semantic_parity": (
                timed["legacy_integer"]["last_result"]
                == typed_result["progress_steps"]
                and legacy_state == typed_state
            ),
        }
        record["typed_status"] = typed_result["status"]
        record["typed_budget_overshoot"] = typed_result["budget_overshoot"]
        records.append(record)

    ratios = [
        r["typed_report"]["wall_time_ns"] / r["legacy_integer"]["wall_time_ns"]
        for r in records
    ]
    cpu_ratios = [
        r["typed_report"]["cpu_time_ns"] / r["legacy_integer"]["cpu_time_ns"]
        for r in records
    ]
    patch = subprocess.check_output(["git", "diff", "--binary"], cwd=ROOT)
    manifest = {
        "run_state": "pilot",
        "protocol": "paired API overhead microbenchmark v1; benchmark protocol 1.1",
        "command": "PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_rule_run_report_overhead.py",
        "commit": git("rev-parse", "HEAD"),
        "dirty": git("status", "--porcelain") != "",
        "tracked_patch_sha256": hashlib.sha256(patch).hexdigest(),
        "harness_sha256": sha(Path(__file__)),
        "protocol_sha256": sha(ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md"),
        "executor_source_sha256": {
            p: sha(ROOT / p)
            for p in (
                "runners/dsl/src/substrate.rs",
                "runners/dsl/src/py.rs",
                "runners/dsl/python/substrate_rs/ext.py",
            )
        },
        "native_artifacts": {
            "extension_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"),
            "build_record_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
        },
        "workload": {
            "description": "Two-node A->B->A edge-type oscillation; each call uses progress budget 2.",
            "progress_budget": PROGRESS_BUDGET,
            "repeats": REPEATS,
            "calls_per_api_per_repeat": CALLS_PER_API_PER_REPEAT,
            "audit_enabled": False,
        },
        "analysis": {
            "scope": "typed Python dictionary result overhead versus legacy integer return on the same Rust rule-run loop",
            "median_typed_to_legacy_wall_ratio": statistics.median(ratios),
            "wall_ratio_range": [min(ratios), max(ratios)],
            "median_typed_to_legacy_cpu_ratio": statistics.median(cpu_ratios),
            "cpu_ratio_range": [min(cpu_ratios), max(cpu_ratios)],
            "inference_limit": "Descriptive only; isolates caller-visible API cost, not the shared Rust result construction, and uses one synthetic cycle.",
        },
        "records": records,
    }
    OUTPUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUTPUT.relative_to(ROOT)),
        "median_wall_ratio": manifest["analysis"]["median_typed_to_legacy_wall_ratio"],
        "wall_ratio_range": manifest["analysis"]["wall_ratio_range"],
        "semantic_parity_all": all(r["semantic_parity"] for r in records),
        "repeats": len(records),
    }, indent=2))


if __name__ == "__main__":
    main()
