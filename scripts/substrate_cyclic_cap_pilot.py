#!/usr/bin/env python3
"""Probe native rule-runner progress-cap behavior on a two-rule oscillation.

Exploratory diagnostic. It tests cap granularity and post-call settlement; it
does not establish general cycle-detection or resource-bound guarantees.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_cyclic_cap_pilot_20260924.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def build_case():
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


def build_one_shot_case():
    from substrate_rs import _native

    s = _native.Substrate()
    left = s.add_node("PilotVertex")
    right = s.add_node("PilotVertex")
    s.add_edge_unchecked(left, "pilot_seed", right)
    s.add_rule({
        "name": "pilot_one_shot",
        "match": [["x", "pilot_seed", "y"]],
        "effects": [["add_edge", "x", "pilot_done", "y", {}]],
    })
    return s, left, right


def main() -> None:
    # Import once up front so each fresh Substrate starts from the same native
    # process state while each graph/rule set is independent.
    from substrate_rs import _native

    records = []
    for cap in (1, 2, 3, 4, 8):
        s, left, right = build_case()
        start = time.perf_counter_ns()
        returned_progress_steps = s.run_rules(cap)
        elapsed_ns = time.perf_counter_ns() - start
        after_cap = {
            "toggle_a": s.has_edge(left, "pilot_toggle_a", right),
            "toggle_b": s.has_edge(left, "pilot_toggle_b", right),
        }
        probe_steps = s.run_rules(1)
        after_probe = {
            "toggle_a": s.has_edge(left, "pilot_toggle_a", right),
            "toggle_b": s.has_edge(left, "pilot_toggle_b", right),
        }
        typed, typed_left, typed_right = build_case()
        typed_report = typed.run_rules_report(cap, False)
        typed_state = {
            "toggle_a": typed.has_edge(typed_left, "pilot_toggle_a", typed_right),
            "toggle_b": typed.has_edge(typed_left, "pilot_toggle_b", typed_right),
        }
        typed_probe_steps = typed.run_rules(1)
        records.append({
            "requested_max_steps": cap,
            "returned_progress_steps": returned_progress_steps,
            "returned_steps_exceed_cap": returned_progress_steps > cap,
            "primary_wall_time_ns": elapsed_ns,
            "state_after_primary": after_cap,
            "terminal_probe_progress_steps": probe_steps,
            "state_after_probe": after_probe,
            "still_unsettled_after_primary": probe_steps > 0,
            "typed_report": typed_report,
            "typed_state_after_primary": typed_state,
            "typed_terminal_probe_progress_steps": typed_probe_steps,
            "typed_legacy_parity": (
                typed_report["progress_steps"] == returned_progress_steps
                and typed_state == after_cap
                and typed_probe_steps == probe_steps
            ),
        })

    # The additive scoped API exposes opt-in repeated-state detection. Keep
    # that separate from ordinary cap behavior and verify that a recurrence
    # was stopped yet remains semantically non-settled.
    s, left, right = build_case()
    detected_report = s.run_rules_report(100, True)
    detected_state = {
        "toggle_a": s.has_edge(left, "pilot_toggle_a", right),
        "toggle_b": s.has_edge(left, "pilot_toggle_b", right),
    }
    post_detection_probe = s.run_rules(1)
    legacy_cycle, legacy_left, legacy_right = build_case()
    legacy_detected_steps = legacy_cycle.run_rules_scoped(100, True)
    legacy_detected_state = {
        "toggle_a": legacy_cycle.has_edge(legacy_left, "pilot_toggle_a", legacy_right),
        "toggle_b": legacy_cycle.has_edge(legacy_left, "pilot_toggle_b", legacy_right),
    }
    records.append({
        "condition": "opt_in_cycle_detection",
        "requested_max_steps": 100,
        "returned_progress_steps": detected_report["progress_steps"],
        "returned_steps_exceed_cap": detected_report["progress_steps"] > 100,
        "typed_report": detected_report,
        "state_after_primary": detected_state,
        "terminal_probe_progress_steps": post_detection_probe,
        "still_unsettled_after_primary": post_detection_probe > 0,
        "legacy_scoped_progress_steps": legacy_detected_steps,
        "legacy_scoped_state": legacy_detected_state,
        "typed_legacy_parity": (
            detected_report["progress_steps"] == legacy_detected_steps
            and detected_state == legacy_detected_state
        ),
        "interpretation": "repeated-state detection stops the orbit but does not make it a fixed point",
    })

    # Status boundary controls: no eligible match, zero budget, and a finite
    # one-shot rule whose single progress event lands exactly on the budget.
    s, left, right = build_one_shot_case()
    s.remove_edge(left, "pilot_seed", right)
    immediate = s.run_rules_report(10, False)
    records.append({"condition": "immediate_fixed_point", "typed_report": immediate})

    s, left, right = build_one_shot_case()
    zero_budget = s.run_rules_report(0, False)
    resume_after_zero = s.run_rules_report(10, False)
    records.append({
        "condition": "zero_budget_then_resume",
        "typed_report": zero_budget,
        "resume_report": resume_after_zero,
        "seed_preserved_after_zero_budget": s.has_edge(left, "pilot_seed", right),
        "done_edge_after_resume": s.has_edge(left, "pilot_done", right),
    })

    s, left, right = build_one_shot_case()
    exact_boundary = s.run_rules_report(1, False)
    boundary_probe = s.run_rules_report(10, False)
    records.append({
        "condition": "one_shot_exact_budget_then_probe",
        "typed_report": exact_boundary,
        "follow_up_report": boundary_probe,
        "done_edge_after_budget_call": s.has_edge(left, "pilot_done", right),
    })

    patch = subprocess.check_output(["git", "diff", "--binary"], cwd=ROOT)
    manifest = {
        "protocol": "exploratory cyclic progress-cap diagnostic v2 (benchmark protocol 1.1)",
        "command": "PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_cyclic_cap_pilot.py",
        "commit": git("rev-parse", "HEAD"),
        "dirty": git("status", "--porcelain") != "",
        "tracked_patch_sha256": hashlib.sha256(patch).hexdigest(),
        "harness_sha256": sha(Path(__file__)),
        "protocol_sha256": sha(ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md"),
        "executor_source_sha256": {
            path: sha(ROOT / path)
            for path in (
                "runners/dsl/src/rewrite.rs",
                "runners/dsl/src/substrate.rs",
                "runners/dsl/src/py.rs",
            )
        },
        "python": sys.version,
        "platform": platform.platform(),
        "native_extension_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"),
        "native_build_record_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "environment": {"PYTHONPATH": os.environ.get("PYTHONPATH")},
        "input": "Two nodes; one pilot_toggle_a edge; A->B and B->A rules each delete the matched edge and add its counterpart.",
        "limits": [
            "One synthetic two-rule oscillation only.",
            "max_steps is measured through the public run_rules API; this pilot does not alter cap semantics.",
            "No wall-time, CPU-time, or memory cap is applied; opt-in graph-state cycle detection is included as a separate condition.",
            "Project-self-custodied; no independent evaluator is involved.",
        ],
        "records": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "records": records}, indent=2))


if __name__ == "__main__":
    main()
