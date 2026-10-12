#!/usr/bin/env python3
"""Measure effect-only Attr replay with AddNodeIfAbsent identity choices.

This is an append-only companion to substrate_effect_only_attr_replay_safety.py.
It contrasts a value-dependent dedup key with a stable identity key followed by
an idempotent SetAttr on the reused witness. Full rescan is diagnostic only.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_add_node_if_absent_replay_probe_v1_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def attr(node: str, key: str) -> dict:
    return {"__term__": {"type": "Attr", "node": {"type": "Var", "name": node}, "key": key}}


def lit(value: str) -> dict:
    return {"__term__": {"type": "Lit", "value": value}}


def run_case(identity_mode: str) -> dict:
    from substrate_rs import Substrate, _native

    _native.stage_a_compare_enable(True)
    _native.stage_a_compare_reset()
    substrate = Substrate()
    inner = substrate._inner
    root = inner.add_node("ReplayRoot", {"watched": 0})
    target = inner.add_node("ReplayTarget", {})
    inner.add_edge_unchecked(root, "trigger", target, {})

    if identity_mode == "value_in_dedup_key":
        effects = [["add_node_if_absent", "born", "ReplayBorn", {"value": attr("x", "watched")}]]
        expected_effect_count_after_rescan = 2
        expected_values_after_rescan = [0, 7]
    elif identity_mode == "stable_key_then_set_attr":
        effects = [
            ["add_node_if_absent", "born", "ReplayBorn", {"identity": lit("root-1")}],
            ["set_attr", "born", "value", attr("x", "watched")],
        ]
        expected_effect_count_after_rescan = 1
        expected_values_after_rescan = [7]
    else:
        raise ValueError(identity_mode)

    inner.add_rule({"name": f"add_node_if_absent_{identity_mode}_reader",
                    "match": [["x", "trigger", "y"]], "effects": effects})
    initial_progress = inner.run_rules(100)
    # Install the writer only after the reader reaches its initial fixed point.
    # Otherwise AddNodeIfAbsent's type-level dedup read can self-wake during
    # cold closure and confound the deliberately isolated later replay.
    inner.add_rule({"name": f"add_node_if_absent_{identity_mode}_writer",
                    "match": [["x", "trigger", "y"]],
                    "effects": [["set_attr", "x", "watched", 7]]})
    writer_progress = inner.run_rules(100)
    before = inner.graph_to_dict()
    before_nodes = [node for node in before["nodes"] if node["type"] == "ReplayBorn"]
    before_values = [node["attrs"].get("value") for node in before_nodes]

    inner.force_all_dirty()
    rescan_progress = inner.run_rules(100)
    after = inner.graph_to_dict()
    after_nodes = [node for node in after["nodes"] if node["type"] == "ReplayBorn"]
    after_values = [node["attrs"].get("value") for node in after_nodes]
    terminal_progress = inner.run_rules(1)

    return {
        "identity_mode": identity_mode,
        "initial_progress": initial_progress,
        "writer_progress": writer_progress,
        "rescan_progress": rescan_progress,
        "terminal_progress": terminal_progress,
        "before_count": len(before_nodes),
        "before_values": before_values,
        "after_count": len(after_nodes),
        "after_values": after_values,
        "expected_after_count": expected_effect_count_after_rescan,
        "expected_after_values": expected_values_after_rescan,
        "rescan_matches_declared_oracle": (
            len(after_nodes) == expected_effect_count_after_rescan
            and after_values == expected_values_after_rescan
        ),
        "stage_a_compare": _native.stage_a_compare_stats(),
        "graph_before_rescan": before,
        "graph_after_rescan": after,
    }


def main() -> None:
    from substrate_rs import _native

    cases = [run_case(mode) for mode in ("value_in_dedup_key", "stable_key_then_set_attr")]
    checks = {
        "value_dependent_dedup_key_mints_duplicate_on_changed_value": (
            cases[0]["before_count"] == 1 and cases[0]["before_values"] == [0]
            and cases[0]["after_count"] == 2
            and cases[0]["after_values"] == [0, 7]
            and cases[0]["rescan_matches_declared_oracle"]
        ),
        "stable_identity_reuses_node_and_refreshes_value": (
            cases[1]["before_count"] == 1 and cases[1]["before_values"] == [0]
            and cases[1]["after_count"] == 1
            and cases[1]["after_values"] == [7]
            and cases[1]["rescan_matches_declared_oracle"]
        ),
        "both_cases_reach_terminal_probe": all(row["terminal_progress"] == 0 for row in cases),
        "stage_a_compare_admission_is_zero_and_reports_no_divergence": all(
            row["stage_a_compare"]["compared_drains"] == 0
            and row["stage_a_compare"]["diverged_drains"] == 0
            and row["stage_a_compare"]["unsound_drains"] == 0
            for row in cases
        ),
    }
    extension = Path(_native.__file__).resolve()
    report = {
        "schema_version": 1,
        "run_id": "substrate-add-node-if-absent-replay-probe-v1-20260925",
        "scope": "two controlled single-binding AddNodeIfAbsent readers under full dirty rescan",
        "claim_boundary": (
            "Mechanism probe for two authored identity policies. Does not establish a general replay contract, "
            "arbitrary dedup-key safety, workload frequency, or frame locality."
        ),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(extension),
            "native_extension_sha256": sha(extension),
            "source_sha256": {
                "harness": sha(Path(__file__).resolve()),
                "rewrite": sha(ROOT / "runners/dsl/src/rewrite.rs"),
                "substrate": sha(ROOT / "runners/dsl/src/substrate.rs"),
                "py_binding": sha(ROOT / "runners/dsl/src/py.rs"),
                "native_build_manifest": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            },
        },
        "checks": checks,
        "cases": cases,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("AddNodeIfAbsent replay probe failed")


if __name__ == "__main__":
    main()
