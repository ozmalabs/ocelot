#!/usr/bin/env python3
"""Independent recomputation for the retrospective cut-ranking diagnostic."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/substrate_authored_capture_cut_ranking_v1.py"
ANALYZER = Path(__file__)
RAW = ROOT / "evaluation/reports/substrate_authored_capture_cut_ranking_v1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/authored_capture_cut_ranking_v1_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_authored_capture_cut_ranking_v1_analysis_20260926.json"
BIGVILLE = ROOT / "evaluation/reports/substrate_bigville_task_access_census_v1_20260926.json"
DIALOGUE = ROOT / "evaluation/reports/substrate_discourse_connected_task_census_v1_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph_sha(graph: dict) -> str:
    packed = json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(packed).hexdigest()


def minfill(nodes: list[int], pairs: set[tuple[int, int]]) -> tuple[list[int], int]:
    g = {n: set() for n in nodes}
    for a, b in pairs:
        if a != b:
            g[a].add(b); g[b].add(a)
    order, width = [], 0
    while g:
        scored = []
        for n, ns in g.items():
            q = sorted(ns)
            fill = sum(1 for i, a in enumerate(q) for b in q[i + 1:] if b not in g[a])
            scored.append((fill, n))
        node = min(scored)[1]
        ns = list(g[node]); width = max(width, len(ns))
        for i, a in enumerate(ns):
            for b in ns[i + 1:]:
                g[a].add(b); g[b].add(a)
        for a in ns:
            g[a].discard(node)
        del g[node]; order.append(node)
    return order, width


def build_groups(order: list[int], sizes: list[int], frames: list[int]) -> dict[int, int]:
    out, p = {}, 0
    for f, size in zip(frames, sizes):
        for node in order[p:p + size]:
            out[node] = f
        p += size
    if p != len(order):
        raise ValueError("bad group coverage")
    return out


def recompute(case: dict, authored: dict[int, int], edges: list[tuple[int, int]],
              obs: list[tuple[int, int, int]]) -> tuple[list[int], int, dict[str, dict]]:
    frames = sorted(set(authored.values())); nodes = sorted(authored)
    sizes = [sum(x == f for x in authored.values()) for f in frames]
    deps = {tuple(sorted((a, b))) for a, b in edges if a in authored and b in authored and a != b}
    deps |= {tuple(sorted((a, b))) for a, b, _ in obs if a in authored and b in authored and a != b}
    order, width = minfill(nodes, deps)
    partitions = {"authored": dict(authored), "balanced_id": build_groups(nodes, sizes, frames),
                  "dependency_min_fill": build_groups(order, sizes, frames)}
    expected = {}
    within = [(a, b) for i, a in enumerate(nodes) for b in nodes[i + 1:]
              if authored[a] == authored[b]]
    for name, owner in partitions.items():
        cross = [(a, b) for a, b in edges if a in authored and b in authored and owner[a] != owner[b]]
        glob = ([(a, b) for a, b in edges if (a in authored) != (b in authored)]
                if case["edge_inventory_scope"] == "all final graph edge types" else None)
        crossobs = [(a, b, c) for a, b, c in obs if a in authored and b in authored and owner[a] != owner[b]]
        touched = set()
        for a, b in cross:
            touched.update((a, b))
        if glob is not None:
            touched.update(a if a in authored else b for a, b in glob)
        perframe = {str(f): sum(owner[n] == f and n in touched for n in nodes) for f in frames}
        keep = sum(owner[a] == owner[b] for a, b in within)
        expected[name] = {
            "frame_sizes": [sum(owner[n] == f for n in nodes) for f in frames],
            "cross_frame_captured_dependency_edge_count": len(cross),
            "distinct_cross_frame_observed_access_pairs": len({tuple(sorted((a, b))) for a, b, _ in crossobs if a != b}),
            "weighted_cross_frame_observed_access_count": sum(c for _, _, c in crossobs),
            "within_authored_frame_pair_retention": {"retained": keep, "total": len(within),
                                                     "fraction": keep / len(within) if within else 1.0},
            "distinct_task_nodes_on_cut_or_known_global_boundary": len(touched) if glob is not None else None,
            "boundary_nodes_by_frame": perframe,
            "captured_global_boundary_edge_incidence": len(glob) if glob is not None else None,
            "global_boundary_incidence_coverage": "complete_graph_edge_inventory" if glob is not None
                else "unavailable; source capture contains causal_influence dependencies only",
            "dependency_min_fill_induced_width": width,
        }
    return order, width, expected


def source_cases() -> dict[str, tuple[dict[int, int], list[tuple[int, int]], list[tuple[int, int, int]], str]]:
    big = json.loads(BIGVILLE.read_text()); dia = json.loads(DIALOGUE.read_text())
    br = next(r for r in big["runs"] if r.get("traced") and r.get("policy") == "event")
    be = [(int(a), int(b)) for a, b in br["runtime_dependency_edges"]]
    bo = [(int(x["node"]), int(x["peer"]), int(x["count"])) for x in br["runtime_access_events"]
          if x.get("node") is not None and x.get("peer") is not None]
    dr = next(r for r in dia["runs"] if r.get("arm") == "trace")
    de = [(int(e["src"]), int(e["tgt"])) for e in dr["final_graph"]["edges"]]
    do = [(int(x["node"]), int(x["peer"]), int(x["count"]))
          for cp in dr["checkpoints"] for x in cp["trace_events"]
          if x.get("node") is not None and x.get("peer") is not None]
    return {"bigville_task_access_census": ({int(n): int(f) for n, f in br["runtime_node_frame"]}, be, bo,
                                              br["graph_digest"], True,
                                              "source digest record; accepted trace-off parity gate"),
            "connected_mixed_dialogue_census": ({int(n): int(f) for n, f in dr["frame_owner"]}, de, do,
                                                 graph_sha(dr["final_graph"]),
                                                 graph_sha(dr["final_graph"]) == dr["final_graph_digest"],
                                                 "recomputed canonical digest from full graph JSON")}


def main() -> None:
    raw = json.loads(RAW.read_text()); lock = json.loads(LOCK.read_text())
    input_digests = {"runner_sha256": sha(RUNNER), "analyzer_sha256": sha(ANALYZER),
                     "bigville_raw_sha256": sha(BIGVILLE), "dialogue_raw_sha256": sha(DIALOGUE)}
    big_source = json.loads(BIGVILLE.read_text()); dialogue_source = json.loads(DIALOGUE.read_text())
    checks = {"lock_runner_and_capture_hashes_match": all(lock.get(k) == v for k, v in input_digests.items()),
              "raw_cites_current_lock": raw.get("locked_inputs") == lock,
              "raw_case_set_complete": {c["case_id"] for c in raw["cases"]} == set(source_cases()),
              "raw_is_retrospective_only": raw.get("status") == "retrospective_development_diagnostic_not_confirmatory",
              "source_capture_checks_all_pass": all(big_source["checks"].values()) and all(dialogue_source["checks"].values())}
    case_checks = {}
    for case in raw["cases"]:
        authored, edges, obs, digest, graph_identity_validated, digest_method = source_cases()[case["case_id"]]
        order, width, expected = recompute(case, authored, edges, obs)
        case_checks[case["case_id"]] = {
            "captured_graph_digest_matches_accepted_source_record": case["captured_graph_digest"] == digest,
            "graph_digest_validation_method": digest_method,
            "graph_identity_validated": graph_identity_validated,
            "min_fill_order_matches": case["min_fill_order_node_ids"] == order,
            "induced_width_matches": all(p["dependency_min_fill_induced_width"] == width for p in case["partitions"]),
            "partition_metrics_match_independent_recomputation": all(
                {k: p[k] for k in m} == m for p in case["partitions"]
                for name, m in expected.items() if p["partition"] == name),
            "three_partition_arms": {p["partition"] for p in case["partitions"]} == set(expected),
            "task_ownership_complete": len(authored) == case["task_node_count"] and len(authored) == len(set(authored)),
        }
    checks["all_case_checks_pass"] = all(all(x.values()) for x in case_checks.values())
    result = {"schema_version": 1, "run_id": "substrate-authored-capture-cut-ranking-v1-analysis-20260926",
              "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK), "checks": checks,
              "case_checks": case_checks,
              "claim_boundary": raw["claim_boundary"],
              "unmet_confirmatory_requirements": raw["confirmatory_requirements_not_satisfied"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "case_checks": case_checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent retrospective analysis failed")


if __name__ == "__main__":
    main()
