#!/usr/bin/env python3
"""Measure rule-effect progress against graph-state changes on small controls."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_effect_progress_matrix_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_case(name: str, effect: list, *, setup: str = "", rule_match=None) -> dict:
    from substrate_rs import Substrate

    substrate = Substrate()
    inner = substrate._inner
    source = inner.add_node("EffectAuditRoot", {})
    target = inner.add_node("EffectAuditTarget", {})
    inner.add_edge_unchecked(source, "trigger", target, {})
    ids = {"source": source, "target": target}
    if setup == "edge_same":
        inner.add_edge_unchecked(source, "out", target, {"value": 1})
    elif setup == "edge_old_value":
        inner.add_edge_unchecked(source, "out", target, {"value": 0})
    elif setup == "edge_delete":
        inner.add_edge_unchecked(source, "out", target, {})
    elif setup == "node_if_absent_exists":
        inner.add_node("Witness", {"tag": "same"})
    elif setup == "attr_same":
        inner.set_attr(source, "tag", 1)
    elif setup == "replace_no_incoming":
        anchor = inner.add_node("EffectAuditAnchor", {})
        inner.add_edge_unchecked(anchor, "anchor", source, {})
        rule_match = [["x", "trigger", "y"], ["c", "anchor", "x"]]
    elif setup in ("replace_incoming", "replace_collision"):
        anchor = inner.add_node("EffectAuditAnchor", {})
        inner.add_edge_unchecked(anchor, "anchor", source, {})
        inner.add_edge_unchecked(anchor, "uses", target, {"value": 5})
        if setup == "replace_collision":
            inner.add_edge_unchecked(anchor, "uses", source, {"value": 99})
        rule_match = [["x", "trigger", "y"], ["c", "anchor", "x"]]
    elif setup == "node_delete_twice":
        effect.extend([["del_node", "y"]])
    elif setup not in ("", "attr_same"):
        raise ValueError(setup)

    match = rule_match or [["x", "trigger", "y"]]
    rule_index = inner.add_rule({
        "name": f"effect_progress_{name}", "match": match, "effects": [effect],
    })
    before = inner.graph_to_dict()
    progress = inner.run_rules(100)
    after = inner.graph_to_dict()
    terminal = inner.run_rules(1)
    exported = inner.export_rules()
    installed = next(r for r in exported if r["name"] == f"effect_progress_{name}")
    return {
        "case": name, "rule_index": rule_index, "effect": effect,
        "setup": setup, "progress_count": progress,
        "terminal_progress": terminal,
        "graph_changed": before != after,
        "node_count_before": len(before["nodes"]), "node_count_after": len(after["nodes"]),
        "edge_count_before": len(before["edges"]), "edge_count_after": len(after["edges"]),
        "final_graph": after,
        "final_rule": installed,
    }


def main() -> None:
    cases = [
        build_case("add_edge_insert", ["add_edge", "x", "out", "y", {"value": 1}]),
        build_case("add_edge_exact_duplicate", ["add_edge", "x", "out", "y", {"value": 1}], setup="edge_same"),
        build_case("add_edge_replace_attrs", ["add_edge", "x", "out", "y", {"value": 1}], setup="edge_old_value"),
        build_case("del_edge_present", ["del_edge", "x", "out", "y"], setup="edge_delete"),
        build_case("del_edge_absent", ["del_edge", "x", "out", "y"]),
        build_case("add_node", ["add_node", "fresh", "Witness", {"tag": "new"}]),
        build_case("add_node_if_absent_insert", ["add_node_if_absent", "fresh", "Witness", {"tag": "same"}]),
        build_case("add_node_if_absent_existing", ["add_node_if_absent", "fresh", "Witness", {"tag": "same"}], setup="node_if_absent_exists"),
        build_case("del_node", ["del_node", "y"]),
        build_case("del_node_duplicate_effect", ["del_node", "y"], setup="node_delete_twice"),
        build_case("set_attr_change", ["set_attr", "x", "tag", 1]),
        build_case("set_attr_same", ["set_attr", "x", "tag", 1], setup="attr_same"),
        build_case("set_attr_if_different_change", ["set_attr_if_different", "x", "tag", 1]),
        build_case("set_attr_if_different_same", ["set_attr_if_different", "x", "tag", 1], setup="attr_same"),
        build_case("replace_value_no_incoming", ["replace_value", "y", "x"], setup="replace_no_incoming"),
        build_case("replace_value_rewire", ["replace_value", "y", "x"], setup="replace_incoming"),
        build_case("replace_value_destination_collision", ["replace_value", "y", "x"], setup="replace_collision"),
    ]
    checks = {
        "all_cases_settle": all(c["terminal_progress"] == 0 for c in cases),
        "every_reported_progress_case_changes_serialized_graph": all(
            c["progress_count"] == 0 or c["graph_changed"] for c in cases),
        "changed_graph_cases_report_progress": all(
            c["progress_count"] > 0 for c in cases if c["graph_changed"]),
        "edge_attr_replacement_is_counted": next(c for c in cases if c["case"] == "add_edge_replace_attrs")["progress_count"] > 0,
        "noop_effects_do_not_report_progress": all(
            next(c for c in cases if c["case"] == name)["progress_count"] == 0
            for name in ("add_edge_exact_duplicate", "del_edge_absent", "add_node_if_absent_existing",
                         "set_attr_same", "set_attr_if_different_same")),
    }
    from substrate_rs import _native
    ext_path = Path(_native.__file__).resolve()
    payload = {
        "schema_version": 1,
        "run_id": "substrate-effect-progress-matrix-20260925",
        "scope": "17 controlled native graph-effect cases; compares run_rules progressing firings with serialized graph changes and terminal settlement",
        "claim_boundary": "This covers common structural and attribute effects only. It does not audit queued rule edits, patch commits, concept definitions, perception, identity tracking, network collapse, or undo correctness for ReplaceValue destination collisions.",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(ext_path), "native_extension_sha256": sha(ext_path),
            "source_sha256": {
                "harness": sha(Path(__file__).resolve()),
                "rewrite": sha(ROOT / "runners/dsl/src/rewrite.rs"),
                "graph": sha(ROOT / "runners/dsl/src/graph.rs"),
                "substrate": sha(ROOT / "runners/dsl/src/substrate.rs"),
                "native_build_manifest": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            },
        },
        "checks": checks, "cases": cases,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(cases), "checks": checks, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("effect progress audit failed")


if __name__ == "__main__":
    main()
