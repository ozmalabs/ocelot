#!/usr/bin/env python3
"""Measure finite-key closure across positive-join arity and graph topology."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/mint_termination_join_work_attribution_v1_2_a_20260926.json"
ARITIES = (1, 2, 3)
PATH_CYCLE_SIZES = (32, 64, 128, 256, 512)
LAYERED_SIZES = (16, 32, 64, 128)
REPEATS = 3
SCHEDULE_SEED = 1702
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_mint_termination_fragment import analyze  # noqa: E402
from substrate_rs import _native  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def graph_spec(topology: str, n: int) -> tuple[list[str], list[tuple[int, int]]]:
    if topology == "path":
        return [f"n{i}" for i in range(n)], [(i, i + 1) for i in range(n - 1)]
    if topology == "cycle":
        return [f"n{i}" for i in range(n)], [(i, (i + 1) % n) for i in range(n)]
    if topology == "layered":
        if n < 4 or (n - 2) % 2:
            raise ValueError(f"invalid layered node count {n}")
        s = (n - 2) // 2
        sizes = [1, s, s, 1]
        offsets, cur = [], 0
        for size in sizes:
            offsets.append(cur)
            cur += size
        edges = []
        for layer in range(3):
            for i in range(sizes[layer]):
                for j in range(sizes[layer + 1]):
                    edges.append((offsets[layer] + i, offsets[layer + 1] + j))
        return [f"n{i}" for i in range(n)], edges
    raise ValueError(topology)


def rule_for(q: int) -> dict:
    match = [[f"x{i}", "link", f"x{i+1}"] for i in range(q)]
    return {"name": f"q{q}_mint", "match": match,
            "effects": [["add_node_if_absent", "w", "Witness", {"tag": "w"}],
                        ["add_edge", f"x{q}", "result", "w", {}]]}


def enumerate_paths(n: int, edges: list[tuple[int, int]], q: int) -> tuple[int, list[int]]:
    adjacency = [[] for _ in range(n)]
    for src, tgt in edges:
        adjacency[src].append(tgt)
    count, endpoints = 0, set()
    def extend(node: int, remaining: int) -> None:
        nonlocal count
        if remaining == 0:
            count += 1
            endpoints.add(node)
            return
        for nxt in adjacency[node]:
            extend(nxt, remaining - 1)
    for start in range(n):
        extend(start, q)
    return count, sorted(endpoints)


def run_case(topology: str, n: int, q: int, replicate: int) -> dict:
    node_names, input_edges = graph_spec(topology, n)
    rule = rule_for(q)
    match_count, terminal_nodes = enumerate_paths(n, input_edges, q)
    classified = analyze([rule], node_names,
                         [[f"n{i}", "link", f"n{j}", {}] for i, j in input_edges])
    if not classified["accepted"]:
        raise RuntimeError(classified["reasons"])

    sub = _native.Substrate()
    node_ids = [sub.add_node("Seed", {"idx": i}) for i in range(n)]
    for i, j in input_edges:
        sub.add_edge_unchecked(node_ids[i], "link", node_ids[j])
    sub.add_rule(rule)
    budget = classified["progress_steps_upper_bound"] + 1
    audit = _native.Substrate
    audit.scale_audit_reset()
    audit.scale_audit_per_rule_reset()
    audit.scale_audit_set_enabled(True)
    audit.scale_audit_set_per_rule_enabled(True)
    try:
        report = sub.run_rules_report(budget, False)
        audit_snapshot = dict(audit.scale_audit_snapshot())
        per_rule_snapshot = audit.scale_audit_per_rule_snapshot()
    finally:
        audit.scale_audit_set_per_rule_enabled(False)
        audit.scale_audit_set_enabled(False)
    graph = sub.graph_to_dict()

    nodes = {(x["type"], json.dumps(x["attrs"], sort_keys=True, separators=(",", ":")))
             for x in graph["nodes"]}
    expected_nodes = {
        *(('Seed', json.dumps({"idx": i}, sort_keys=True, separators=(",", ":"))) for i in range(n)),
        ('Witness', json.dumps({"tag": "w"}, sort_keys=True, separators=(",", ":"))),
    }
    edges = {(e["src"], e["type"], e["tgt"], json.dumps(e["attrs"], sort_keys=True, separators=(",", ":")))
             for e in graph["edges"]}
    expected_edges = {(node_ids[i], "link", node_ids[j], "{}") for i, j in input_edges}
    witness_id = next(x["id"] for x in graph["nodes"] if x["type"] == "Witness")
    expected_edges |= {(node_ids[i], "result", witness_id, "{}") for i in terminal_nodes}

    labels = {x["id"]: (x["type"], tuple(sorted(x["attrs"].items()))) for x in graph["nodes"]}
    projection = {"nodes": sorted((x["type"], tuple(sorted(x["attrs"].items()))) for x in graph["nodes"]),
                  "edges": sorted((labels[e["src"]], e["type"], labels[e["tgt"]],
                                   tuple(sorted(e["attrs"].items()))) for e in graph["edges"])}
    checks = {
        "analyzer_accepts": classified["accepted"],
        "native_fixed_point": report["status"] == "fixed_point",
        "no_budget_overshoot": report["budget_overshoot"] == 0,
        "exact_node_set": nodes == expected_nodes,
        "exact_edge_set": edges == expected_edges,
        "progress_within_bound": report["progress_steps"] <= classified["progress_steps_upper_bound"],
        "enumerated_match_count_positive": match_count > 0,
        "candidate_path_conservation": audit_snapshot.get("cand_enum", 0) == sum(
            audit_snapshot.get(k, 0) for k in ("cand_enum_scan", "cand_enum_local", "cand_enum_hinted")),
        "candidate_epoch_conservation": audit_snapshot.get("cand_enum", 0) == sum(
            audit_snapshot.get(k, 0) for k in ("cand_enum_first", "cand_enum_repeat")),
        "term_variant_conservation": audit_snapshot.get("term_evals_total", 0) == sum(
            value for key, value in audit_snapshot.items() if key.startswith("term_eval:")),
        "term_unit_conservation": audit_snapshot.get("term_units_total", 0) == sum(
            value for key, value in audit_snapshot.items() if key.startswith("term_unit:")),
    }
    per_rule = {(int(i), metric): int(count) for i, metric, count in per_rule_snapshot}
    def rule_sum(metric):
        return sum(v for (idx, name), v in per_rule.items() if name == metric)
    checks.update({
        "per_rule_candidate_pairs_conservation": audit_snapshot.get("cand_enum", 0) == rule_sum("candidate_pairs"),
        "per_rule_candidate_tests_conservation": audit_snapshot.get("cand_tested", 0) == rule_sum("candidate_tests"),
        "per_rule_term_eval_conservation": audit_snapshot.get("term_evals_total", 0) == rule_sum("term_evaluations"),
        "per_rule_term_units_conservation": audit_snapshot.get("term_units_total", 0) == rule_sum("term_units"),
        "per_rule_leaf_conservation": audit_snapshot.get("leaf_visits", 0) == rule_sum("binding_leaves"),
        "per_rule_enumeration_conservation": audit_snapshot.get("rule_enumerations", 0) == rule_sum("rule_enumerations"),
    })
    return {
        "case_id": f"{topology}_n{n}_q{q}_r{replicate}", "topology": topology,
        "n_initial_nodes": n, "n_initial_edges": len(input_edges), "match_arity": q,
        "enumerated_match_bindings": match_count, "distinct_terminal_nodes": len(terminal_nodes),
        "replicate": replicate,
        "native_report": report, "progress_bound": classified["progress_steps_upper_bound"],
        "actual_node_count": len(graph["nodes"]), "actual_edge_count": len(graph["edges"]),
        "actual_graph_projection_sha256": json_sha(projection),
        "scale_audit": audit_snapshot,
        "per_rule_audit": [{"rule_index": int(i), "metric": metric, "count": int(value)}
                            for i, metric, value in per_rule_snapshot],
        "checks": checks, "all_checks_pass": all(checks.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    configs = [(top, n, q) for top, sizes in (("path", PATH_CYCLE_SIZES), ("cycle", PATH_CYCLE_SIZES),
                                                   ("layered", LAYERED_SIZES))
               for n in sizes for q in ARITIES]
    schedule = [(top, n, q, r) for top, n, q in configs for r in range(1, REPEATS + 1)]
    random.Random(SCHEDULE_SEED).shuffle(schedule)
    cases = [run_case(*c) for c in schedule]
    native_path = Path(_native.__file__).resolve()
    hash_paths = [Path(__file__).resolve(),
                  ROOT / "docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_JOIN_WORK_ATTRIBUTION_PREREG_20260926.md",
                  ROOT / "scripts/analyze_mint_termination_fragment.py",
                  ROOT / "runners/dsl/src/rewrite.rs", ROOT / "runners/dsl/src/graph.rs"]
    payload = {
        "schema_version": 1, "run_id": "mint-termination-join-work-attribution-v1.2-20260926",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version, "platform": platform.platform(),
        "provenance": {"source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in hash_paths},
                       "native_path": str(native_path), "native_sha256": sha(native_path)},
        "design": {"arities": list(ARITIES), "path_cycle_sizes": list(PATH_CYCLE_SIZES),
                   "layered_sizes": list(LAYERED_SIZES), "repeats": REPEATS,
                   "warmups_per_cell": 0, "schedule_seed": SCHEDULE_SEED,
                   "configuration_count": len(configs), "case_count": len(cases),
                   "claim_limit": "one fixed finite-key mint/effect schema; authored path/cycle/layered topologies"},
        "cases": cases,
        "failed_cases": [x["case_id"] for x in cases if not x["all_checks_pass"]],
        "all_checks_pass": all(x["all_checks_pass"] for x in cases),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": payload["all_checks_pass"], "configurations": len(configs),
                      "cases": len(cases), "failed_cases": payload["failed_cases"], "output": str(args.output)}, indent=2))
    return 0 if payload["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
