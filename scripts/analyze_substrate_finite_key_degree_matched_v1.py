#!/usr/bin/env python3
"""Independent oracle and fresh-process analysis for degree-matched closure."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) != 3:
    raise SystemExit("usage: analyze_substrate_finite_key_degree_matched_v1.py RAW_A RAW_B")
paths = [Path(x) for x in sys.argv[1:]]
raw_a, raw_b = [json.loads(x.read_text()) for x in paths]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def edges_for(topology, n):
    if topology == "bidirected_path":
        base = {(i, i+1) for i in range(n-1)}
    elif topology == "bidirected_star":
        base = {(0, i) for i in range(1, n)}
    elif topology == "bidirected_balanced_tree":
        base = {((i-1)//2, i) for i in range(1, n)}
    else:
        raise ValueError(topology)
    return sorted((a, b) for u, v in base for a, b in ((u, v), (v, u)))


def oracle(topology, n, q):
    edges = edges_for(topology, n)
    adj = [[] for _ in range(n)]
    deg = Counter()
    for a, b in edges:
        adj[a].append(b)
        deg[a] += 1
    count, ends = 0, set()
    def walk(node, remaining):
        nonlocal count
        if remaining == 0:
            count += 1
            ends.add(node)
            return
        for nxt in adj[node]:
            walk(nxt, remaining-1)
    for start in range(n):
        walk(start, q)
    labels = [("Seed", (("idx", i),)) for i in range(n)]
    witness = ("Witness", (("tag", "w"),))
    nodes = sorted(labels + [witness])
    projected_edges = [(labels[a], "link", labels[b], ()) for a, b in edges]
    projected_edges.extend((labels[i], "result", witness, ()) for i in ends)
    return count, sorted(ends), dict(sorted(Counter(deg.values()).items())), digest({"nodes": nodes, "edges": sorted(projected_edges)}), len(edges)


def audit_semantics(arm):
    return {k: arm[k] for k in ("report", "counters", "per_rule", "graph_sha256",
                                "progress_bound", "node_count", "edge_count", "checks",
                                "all_checks_pass", "binding_count", "terminal_count")}


def case_semantics(case):
    return {k: case[k] for k in ("case_id", "topology", "n", "q", "replicate",
                                 "node_count_initial", "input_edge_count", "degree_histogram",
                                 "max_directed_degree", "checks", "all_checks_pass")} | {
        "timed": audit_semantics(case["timed_arm"]),
        "audited": audit_semantics(case["audit_arm"]),
    }


def check_counter_arm(arm):
    c = arm["counters"]
    pr = defaultdict(int)
    for row in arm["per_rule"]:
        pr[row["metric"]] += row["count"]
    return {
        "candidate_path_split": c["cand_enum"] == c["cand_enum_scan"] + c["cand_enum_local"] + c["cand_enum_hinted"],
        "candidate_epoch_split": c["cand_enum"] == c["cand_enum_first"] + c["cand_enum_repeat"],
        "candidate_test_identity": c["cand_enum"] == c["cand_tested"],
        "term_variant_identity": c["term_evals_total"] == sum(v for k, v in c.items() if k.startswith("term_eval:")),
        "term_unit_identity": c["term_units_total"] == sum(v for k, v in c.items() if k.startswith("term_unit:")),
        "per_rule_pairs": c["cand_enum"] == pr["candidate_pairs"],
        "per_rule_tests": c["cand_tested"] == pr["candidate_tests"],
        "per_rule_terms": c["term_evals_total"] == pr["term_evaluations"],
        "per_rule_units": c["term_units_total"] == pr["term_units"],
        "per_rule_leaves": c["leaf_visits"] == pr["binding_leaves"],
        "per_rule_enumerations": c["rule_enumerations"] == pr["rule_enumerations"],
    }


checks = {
    "case_count_complete": all(len(r["cases"]) == 180 for r in (raw_a, raw_b)),
    "all_runner_gates_pass": raw_a["all_checks_pass"] and raw_b["all_checks_pass"],
    "same_design": raw_a["design"] == raw_b["design"],
    "exact_semantic_fresh_process_replication": {x["case_id"]: case_semantics(x) for x in raw_a["cases"]}
        == {x["case_id"]: case_semantics(x) for x in raw_b["cases"]},
    "same_native_artifact": raw_a["provenance"]["native_sha256"] == raw_b["provenance"]["native_sha256"],
    "current_source_hashes": all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == value
        for r in (raw_a, raw_b) for name, value in r["provenance"]["source_sha256"].items()),
    "current_native_hash": all(hashlib.sha256(Path(r["provenance"]["native_path"]).read_bytes()).hexdigest()
        == r["provenance"]["native_sha256"] for r in (raw_a, raw_b)),
}
groups = defaultdict(list)
for process, raw in ((1, raw_a), (2, raw_b)):
    for case in raw["cases"]:
        key = case["case_id"]
        match_count, terminals, degree_hist, graph_hash, e = oracle(case["topology"], case["n"], case["q"])
        n, q = case["n"], case["q"]
        bound = 1 + 2*(n+1)**2 - 2*(n-1)
        local = {
            "matched_node_and_edge_counts": case["node_count_initial"] == n and case["input_edge_count"] == 2*(n-1),
            "degree_histogram_oracle": case["degree_histogram"] == degree_hist and case["max_directed_degree"] == max(
                [degree for degree, count in degree_hist.items() for _ in range(count)]),
            "walk_binding_oracle": case["timed_arm"]["binding_count"] == match_count == case["audit_arm"]["binding_count"],
            "terminal_oracle": case["timed_arm"]["terminal_count"] == len(terminals) == case["audit_arm"]["terminal_count"],
            "graph_hash_oracle_both_arms": case["timed_arm"]["graph_sha256"] == graph_hash == case["audit_arm"]["graph_sha256"],
            "cross_arm_fixed_point_report": case["timed_arm"]["report"] == case["audit_arm"]["report"],
            "progress_bound_oracle_both_arms": case["timed_arm"]["progress_bound"] == bound == case["audit_arm"]["progress_bound"],
        }
        local.update({f"counter:{k}": v for k, v in check_counter_arm(case["audit_arm"]).items()})
        checks.update({f"p{process}:{key}:{k}": v for k, v in local.items()})
        groups[(process, case["topology"], n, q)].append(case)

summary = []
for (process, topology, n, q), rows in sorted(groups.items()):
    summary.append({"process": process, "topology": topology, "n": n, "q": q,
        "replicates": len(rows), "input_edges": rows[0]["input_edge_count"],
        "degree_histogram": rows[0]["degree_histogram"],
        "bindings": rows[0]["timed_arm"]["binding_count"],
        "median_candidate_pairs": statistics.median(x["audit_arm"]["counters"]["cand_enum"] for x in rows),
        "median_candidate_tests": statistics.median(x["audit_arm"]["counters"]["cand_tested"] for x in rows),
        "median_local_candidates": statistics.median(x["audit_arm"]["counters"]["cand_enum_local"] for x in rows),
        "median_scan_candidates": statistics.median(x["audit_arm"]["counters"]["cand_enum_scan"] for x in rows),
        "median_closure_ms": statistics.median(x["timed_arm"]["closure_ns"]/1e6 for x in rows),
        "closure_range_ms": [min(x["timed_arm"]["closure_ns"]/1e6 for x in rows),
                             max(x["timed_arm"]["closure_ns"]/1e6 for x in rows)]})
result = {"schema": "substrate_finite_key_degree_matched_analysis_v1",
          "raw_sha256": {f"process_{i+1}:{p.name}": hashlib.sha256(p.read_bytes()).hexdigest()
                         for i, p in enumerate(paths)},
          "check_count": len(checks), "checks": checks, "all_checks_pass": all(checks.values()),
          "summary": summary,
          "claim_boundary": "Matched N/E authored bidirected trees; degree changes alongside other topology invariants; timings from audit-off arm only."}
print(json.dumps(result, sort_keys=True, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
