#!/usr/bin/env python3
"""Check whether independent mixed attribute/edge effects enter Stage A compare."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_stage_a_mixed_effect_probe_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    from substrate_rs import Substrate, _native

    _native.stage_a_compare_enable(True)
    _native.stage_a_compare_reset()
    s = Substrate()
    inner = s._inner
    node_count = 6
    node_ids = []
    for index in range(node_count):
        nid = inner.add_node("MixedEffectNode", {"watched": index + 10})
        inner.add_edge_unchecked(nid, "trigger", nid, {})
        node_ids.append(nid)
    watched = {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "watched"}}
    inner.add_rule({
        "name": "stage_a_mixed_attr_edge_probe",
        "match": [["x", "trigger", "x"]],
        "effects": [
            ["set_attr", "x", "observed", watched],
            ["add_edge", "x", "derived", "x", {"value": watched}],
        ],
    })
    progress = inner.run_rules(100)
    graph = inner.graph_to_dict()
    terminal = inner.run_rules(1)
    nodes = {n["id"]: n for n in graph["nodes"]}
    by_id = {nid.value: nid for nid in node_ids}
    observed = [nodes[nid]["attrs"].get("observed") for nid in by_id]
    edge_values = [next((e["attrs"].get("value") for e in graph["edges"]
                         if e["src"] == nid and e["type"] == "derived" and e["tgt"] == nid), None)
                   for nid in by_id]
    expected = [i + 10 for i in range(node_count)]
    stats = _native.stage_a_compare_stats()
    checks = {
        "stage_a_compared_at_least_one_drain": stats["compared_drains"] > 0,
        "no_stage_a_divergence": stats["diverged_drains"] == 0,
        "no_stage_a_unsound_drain": stats["unsound_drains"] == 0,
        "all_mixed_effect_outputs_match_oracle": observed == expected and edge_values == expected,
        "all_edges_unique_and_present": sum(e["type"] == "derived" for e in graph["edges"]) == node_count,
        "settles_under_terminal_probe": terminal == 0,
    }
    ext = Path(_native.__file__).resolve()
    payload = {
        "schema_version": 1,
        "run_id": "substrate-stage-a-mixed-effect-probe-20260925",
        "scope": "one mixed SetAttr+AddEdge rule over six independent one-variable self-loop bindings; Stage A compare mode enabled",
        "claim_boundary": "Mechanism evidence that this independent one-variable form is admitted to Stage A compare. It does not establish admission or correctness for multi-variable, contended, writer/reader-interacting, or authored workload cases.",
        "inputs": {"node_count": node_count, "watched_values": expected, "rule_match": [["x", "trigger", "x"]]},
        "outcome": {"progress": progress, "terminal_progress": terminal, "observed_values": observed,
                    "derived_edge_values": edge_values, "stage_a_compare_stats": stats},
        "checks": checks,
        "graph": graph,
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(ext), "native_extension_sha256": sha(ext),
            "source_sha256": {
                "harness": sha(Path(__file__).resolve()),
                "stage_a": sha(ROOT / "runners/dsl/src/stage_a.rs"),
                "substrate": sha(ROOT / "runners/dsl/src/substrate.rs"),
                "rewrite": sha(ROOT / "runners/dsl/src/rewrite.rs"),
                "native_build_manifest": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            },
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "stage_a_compare_stats": stats, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("Stage A mixed-effect probe failed")


if __name__ == "__main__":
    main()
