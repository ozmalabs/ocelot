#!/usr/bin/env python3
"""Compare native matcher work across edge-count-matched degree profiles."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "evaluation/reports/mint_termination_degree_matched_v1_1_a_20260926.json"
SIZES = (32, 64, 128, 256)
TOPOLOGIES = ("bidirected_path", "bidirected_star", "bidirected_balanced_tree")
ARITIES = (1, 2, 3)
REPEATS = 5
SCHEDULE_SEED = 1703
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_mint_termination_fragment import analyze  # noqa: E402
from substrate_rs import _native  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def graph_edges(topology: str, n: int) -> list[tuple[int, int]]:
    undirected = set()
    if topology == "bidirected_path":
        undirected = {(i, i + 1) for i in range(n - 1)}
    elif topology == "bidirected_star":
        undirected = {(0, i) for i in range(1, n)}
    elif topology == "bidirected_balanced_tree":
        undirected = {((i - 1) // 2, i) for i in range(1, n)}
    else:
        raise ValueError(topology)
    return sorted((a, b) for u, v in undirected for a, b in ((u, v), (v, u)))


def walk_oracle(n: int, edges: list[tuple[int, int]], q: int) -> tuple[int, list[int]]:
    adj = [[] for _ in range(n)]
    for src, tgt in edges:
        adj[src].append(tgt)
    count, ends = 0, set()
    used: set[int] = set()
    def extend(node, left):
        nonlocal count
        if left == 0:
            count += 1
            ends.add(node)
            return
        for nxt in adj[node]:
            if nxt not in used:
                used.add(nxt)
                extend(nxt, left - 1)
                used.remove(nxt)
    for start in range(n):
        used = {start}
        extend(start, q)
    return count, sorted(ends)


def rule_for(q: int) -> dict:
    return {"name": f"degree_q{q}",
            "match": [[f"x{i}", "link", f"x{i+1}"] for i in range(q)],
            "effects": [["add_node_if_absent", "w", "Witness", {"tag": "w"}],
                        ["add_edge", f"x{q}", "result", "w", {}]]}


def run_arm(topology: str, n: int, q: int, audited: bool) -> dict:
    edges = graph_edges(topology, n)
    rule = rule_for(q)
    bindings, terminals = walk_oracle(n, edges, q)
    classified = analyze([rule], [f"n{i}" for i in range(n)],
                         [[f"n{i}", "link", f"n{j}", {}] for i, j in edges])
    if not classified["accepted"]:
        raise RuntimeError(classified["reasons"])
    sub = _native.Substrate()
    start = time.perf_counter_ns()
    node_ids = [sub.add_node("Seed", {"idx": i}) for i in range(n)]
    for i, j in edges:
        sub.add_edge_unchecked(node_ids[i], "link", node_ids[j])
    sub.add_rule(rule)
    setup_ns = time.perf_counter_ns() - start
    budget = classified["progress_steps_upper_bound"] + 1
    audit = _native.Substrate
    if audited:
        audit.scale_audit_reset()
        audit.scale_audit_per_rule_reset()
        audit.scale_audit_set_enabled(True)
        audit.scale_audit_set_per_rule_enabled(True)
        try:
            report = sub.run_rules_report(budget, False)
            counters = dict(audit.scale_audit_snapshot())
            per_rule = audit.scale_audit_per_rule_snapshot()
        finally:
            audit.scale_audit_set_per_rule_enabled(False)
            audit.scale_audit_set_enabled(False)
        closure_ns = None
    else:
        start = time.perf_counter_ns()
        report = sub.run_rules_report(budget, False)
        closure_ns = time.perf_counter_ns() - start
        counters, per_rule = None, None
    graph = sub.graph_to_dict()
    node_set = {(x["type"], json.dumps(x["attrs"], sort_keys=True, separators=(",", ":")))
                for x in graph["nodes"]}
    expected_nodes = {("Seed", json.dumps({"idx": i}, sort_keys=True, separators=(",", ":"))) for i in range(n)}
    if bindings:
        expected_nodes.add(("Witness", json.dumps({"tag": "w"}, sort_keys=True, separators=(",", ":"))))
    actual_edges = {(e["src"], e["type"], e["tgt"], json.dumps(e["attrs"], sort_keys=True, separators=(",", ":")))
                    for e in graph["edges"]}
    expected_edges = {(node_ids[i], "link", node_ids[j], "{}") for i, j in edges}
    if bindings:
        witness_id = next(x["id"] for x in graph["nodes"] if x["type"] == "Witness")
        expected_edges |= {(node_ids[i], "result", witness_id, "{}") for i in terminals}
    labels = {x["id"]: (x["type"], tuple(sorted(x["attrs"].items()))) for x in graph["nodes"]}
    projection = {"nodes": sorted((x["type"], tuple(sorted(x["attrs"].items()))) for x in graph["nodes"]),
                  "edges": sorted((labels[e["src"]], e["type"], labels[e["tgt"]],
                                   tuple(sorted(e["attrs"].items()))) for e in graph["edges"])}
    degree = Counter()
    for i, j in edges:
        degree[i] += 1
    checks = {"analyzer_accepts": classified["accepted"],
              "fixed_point": report["status"] == "fixed_point",
              "no_budget_overshoot": report["budget_overshoot"] == 0,
              "exact_nodes": node_set == expected_nodes,
              "exact_edges": actual_edges == expected_edges,
              "progress_within_bound": report["progress_steps"] <= classified["progress_steps_upper_bound"],
              "match_effect_consistency": (len(graph["nodes"]) == n + int(bindings > 0)),
              "zero_match_no_effects": bindings > 0 or (len(graph["nodes"]) == n and len(graph["edges"]) == len(edges)),
              "positive_match_mints": bindings == 0 or len(graph["nodes"]) == n + 1,
              "edge_count_expected": len(graph["edges"]) == len(edges) + len(terminals)}
    if audited:
        checks.update({
            "candidate_path_conservation": counters["cand_enum"] == sum(counters[k] for k in
                ("cand_enum_scan", "cand_enum_local", "cand_enum_hinted")),
            "candidate_epoch_conservation": counters["cand_enum"] == counters["cand_enum_first"] + counters["cand_enum_repeat"],
            "term_variant_conservation": counters["term_evals_total"] == sum(v for k, v in counters.items() if k.startswith("term_eval:")),
            "term_unit_conservation": counters["term_units_total"] == sum(v for k, v in counters.items() if k.startswith("term_unit:")),
        })
        pr = {(int(i), metric): int(value) for i, metric, value in per_rule}
        checks["per_rule_candidate_pairs"] = counters["cand_enum"] == sum(v for (i, m), v in pr.items() if m == "candidate_pairs")
        checks["per_rule_candidate_tests"] = counters["cand_tested"] == sum(v for (i, m), v in pr.items() if m == "candidate_tests")
        checks["per_rule_term_evaluations"] = counters["term_evals_total"] == sum(v for (i, m), v in pr.items() if m == "term_evaluations")
        checks["per_rule_leaf_visits"] = counters["leaf_visits"] == sum(v for (i, m), v in pr.items() if m == "binding_leaves")
        checks["per_rule_enumerations"] = counters["rule_enumerations"] == sum(v for (i, m), v in pr.items() if m == "rule_enumerations")
    hist = dict(sorted(Counter(degree.values()).items()))
    return {"audited": audited, "setup_ns": setup_ns, "closure_ns": closure_ns,
            "report": report, "counters": counters,
            "per_rule": ([{"rule_index": int(i), "metric": m, "count": int(v)} for i, m, v in per_rule]
                         if per_rule is not None else None),
            "binding_count": bindings, "terminal_count": len(terminals),
            "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]),
            "graph_sha256": json_sha(projection), "progress_bound": classified["progress_steps_upper_bound"],
            "degree_histogram": hist, "max_directed_degree": max(degree.values()),
            "checks": checks, "all_checks_pass": all(checks.values())}


def run_case(topology: str, n: int, q: int, replicate: int) -> dict:
    timed = run_arm(topology, n, q, audited=False)
    audited = run_arm(topology, n, q, audited=True)
    checks = {"both_arms_pass": timed["all_checks_pass"] and audited["all_checks_pass"],
              "exact_arm_graph_parity": timed["graph_sha256"] == audited["graph_sha256"],
              "same_bindings_and_terminals": (timed["binding_count"], timed["terminal_count"])
                  == (audited["binding_count"], audited["terminal_count"]),
              "same_fixed_point_progress": timed["report"] == audited["report"]}
    return {"case_id": f"{topology}_n{n}_q{q}_r{replicate}", "topology": topology,
            "n": n, "q": q, "replicate": replicate,
            "node_count_initial": n, "input_edge_count": 2*(n-1),
            "degree_histogram": timed["degree_histogram"],
            "max_directed_degree": timed["max_directed_degree"],
            "timed_arm": timed, "audit_arm": audited,
            "checks": checks, "all_checks_pass": all(checks.values())}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    configs = [(top, n, q) for top in TOPOLOGIES for n in SIZES for q in ARITIES]
    schedule = [(top, n, q, r) for top, n, q in configs for r in range(1, REPEATS+1)]
    random.Random(SCHEDULE_SEED).shuffle(schedule)
    cases = [run_case(*cell) for cell in schedule]
    native_path = Path(_native.__file__).resolve()
    source_paths = [Path(__file__).resolve(), ROOT / "scripts/analyze_substrate_finite_key_degree_matched_v1_1.py",
                    ROOT / "scripts/analyze_mint_termination_fragment.py",
                    ROOT / "docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_DEGREE_MATCHED_V1_1_AMENDMENT_20260926.md",
                    ROOT / "runners/dsl/src/scale_audit.rs", ROOT / "runners/dsl/src/rewrite.rs",
                    ROOT / "runners/dsl/src/graph.rs"]
    payload = {"schema": "substrate_finite_key_degree_matched_v1_1",
               "run_id": "finite-key-degree-matched-v1-1-20260926",
               "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "python": sys.version, "platform": platform.platform(),
               "provenance": {"source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths},
                              "native_path": str(native_path), "native_sha256": sha(native_path)},
               "design": {"sizes": list(SIZES), "topologies": list(TOPOLOGIES), "arities": list(ARITIES),
                          "repeats": REPEATS, "schedule_seed": SCHEDULE_SEED,
                          "configurations": len(configs), "cases": len(cases),
                          "timed_and_audit_arms": True,
                          "claim_limit": "edge-count-matched authored bidirected trees; topology invariants also differ; matches are injective node-simple paths"},
               "cases": cases, "failed_cases": [c["case_id"] for c in cases if not c["all_checks_pass"]],
               "all_checks_pass": all(c["all_checks_pass"] for c in cases)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": payload["all_checks_pass"], "configurations": len(configs),
                      "cases": len(cases), "failed_cases": payload["failed_cases"], "output": str(args.output)}, indent=2))
    return 0 if payload["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
