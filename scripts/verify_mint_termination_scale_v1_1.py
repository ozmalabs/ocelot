#!/usr/bin/env python3
"""Native finite-key termination family gate; emits per-case raw graph states."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/mint_termination_scale_v1_1_20260926.json"
ANALYZER = ROOT / "scripts/analyze_mint_termination_fragment.py"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_PREREG_20260926.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_V1_1_AMENDMENT_20260926.md"
RUNNER = Path(__file__).resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_mint_termination_fragment import analyze  # noqa: E402
from substrate_rs import _native  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


TAG_VALUES = (None, True, 1, "w3")


def specs(m: int) -> list[dict]:
    result = []
    for i in range(m):
        result.append({
            "name": f"mint_tag_{i}",
            "match": [["x", "link", "y"]],
            "effects": [
                ["add_node_if_absent", f"w{i}", "Witness", {"tag": TAG_VALUES[i]}],
                ["add_edge", "y", "link", f"w{i}", {}],
            ],
        })
    return result


def initial_edges(n: int, topology: str) -> list[tuple[int, int]]:
    if topology == "cycle":
        return [(i, (i + 1) % n) for i in range(n)]
    if topology == "dense_no_self":
        return [(i, j) for i in range(n) for j in range(n) if i != j]
    raise ValueError(topology)


def native_case(n: int, m: int, topology: str, replicate: int) -> dict:
    ins = initial_edges(n, topology)
    rule_specs = specs(m)
    input_edges = [[f"n{i}", "link", f"n{j}", {}] for i, j in ins]
    classified = analyze(rule_specs, [f"n{i}" for i in range(n)], input_edges)

    sub = _native.Substrate()
    node_ids = [sub.add_node("Seed", {"idx": i}) for i in range(n)]
    for i, j in ins:
        sub.add_edge_unchecked(node_ids[i], "link", node_ids[j])
    for rule in rule_specs:
        sub.add_rule(rule)
    report = sub.run_rules_report(200000, False)
    graph = sub.graph_to_dict()

    actual_nodes = {(node["type"], json.dumps(node["attrs"], sort_keys=True))
                    for node in graph["nodes"]}
    expected_nodes = {
        *(('Seed', json.dumps({"idx": i}, sort_keys=True)) for i in range(n)),
    }
    runtime_tags = []
    for value in TAG_VALUES[:m]:
        if not any(value == earlier for earlier in runtime_tags):
            runtime_tags.append(value)
    expected_nodes.update(('Witness', json.dumps({"tag": value}, sort_keys=True))
                          for value in runtime_tags)
    actual_edges = {(e["src"], e["type"], e["tgt"], json.dumps(e["attrs"], sort_keys=True))
                    for e in graph["edges"]}
    edge_pairs = set(ins)
    for y in range(n + len(runtime_tags)):
        for wi in range(n, n + len(runtime_tags)):
            edge_pairs.add((y, wi))
    expected_edges = {(i, "link", j, "{}") for i, j in edge_pairs}
    bound = classified.get("progress_steps_upper_bound")
    checks = {
        "analyzer_accepts": classified["accepted"],
        "native_fixed_point": report["status"] == "fixed_point",
        "exact_node_multiset": actual_nodes == expected_nodes,
        "exact_edge_set": actual_edges == expected_edges,
        "progress_within_bound": report["progress_steps"] <= bound,
        "no_budget_overshoot": report["budget_overshoot"] == 0,
        "analyzer_count_is_conservative": classified["unique_mint_signatures"] >= len(runtime_tags),
    }
    return {
        "case_id": f"n{n}_m{m}_{topology}_r{replicate}",
        "n_initial_nodes": n, "m_mint_signatures": m,
        "n_rules": len(rule_specs), "topology": topology,
        "replicate": replicate, "analyzer": classified,
        "native_report": report, "actual_node_count": len(graph["nodes"]),
        "actual_edge_count": len(graph["edges"]), "actual_graph": graph,
        "authored_mint_signatures": m, "runtime_distinct_witnesses": len(runtime_tags),
        "expected_node_count": n + len(runtime_tags), "expected_edge_count": len(expected_edges),
        "checks": checks, "all_checks_pass": all(checks.values()),
    }


def main() -> int:
    cases = [native_case(n, m, topology, rep)
             for n in (4, 16, 64) for topology in ("cycle", "dense_no_self")
             for m in (1, 2, 4) for rep in (1, 2, 3)]
    native_path = Path(_native.__file__).resolve()
    result = {
        "schema_version": 1,
        "run_id": "mint-termination-scale-v1.1-20260926",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version, "platform": platform.platform(),
        "provenance": {"runner_sha256": sha(RUNNER), "analyzer_sha256": sha(ANALYZER),
                       "prereg_sha256": sha(PREREG),
                       "amendment_sha256": sha(AMENDMENT),
                       "native_sha256": sha(native_path), "native_path": str(native_path)},
        "design": {"initial_node_counts": [4, 16, 64], "mint_signature_counts": [1, 2, 4],
                   "topologies": ["cycle", "dense_no_self"], "replicates_per_cell": 3,
                   "cases": len(cases), "budget": 200000,
                   "scalar_literal_types": ["null", "boolean", "integer", "string"],
                   "amendment": str(AMENDMENT.relative_to(ROOT)),
                   "claim_limit": "fixed synthetic positive rules; no deletion, mutation, external state, or natural workload"},
        "cases": cases,
        "failed_cases": [c["case_id"] for c in cases if not c["all_checks_pass"]],
        "all_checks_pass": all(c["all_checks_pass"] for c in cases),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": result["all_checks_pass"],
                      "cases": len(cases), "failed_cases": result["failed_cases"],
                      "output": str(OUT)}, indent=2))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
