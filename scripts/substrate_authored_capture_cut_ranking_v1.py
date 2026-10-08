#!/usr/bin/env python3
"""Retrospective structural comparison of frozen authored graph captures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_AUTHORED_CAPTURE_CUT_RANKING_DIAGNOSTIC_20260926.md"
BIGVILLE = ROOT / "evaluation/reports/substrate_bigville_task_access_census_v1_20260926.json"
DIALOGUE = ROOT / "evaluation/reports/substrate_discourse_connected_task_census_v1_20260926.json"
BIGVILLE_LOCK = ROOT / "evaluation/substrate_capability/bigville_task_access_census_lock_20260926.json"
DIALOGUE_LOCK = ROOT / "evaluation/substrate_capability/discourse_connected_task_census_lock_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/authored_capture_cut_ranking_v1_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_authored_capture_cut_ranking_v1_20260926.json"
ANALYZER = ROOT / "scripts/analyze_substrate_authored_capture_cut_ranking_v1.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_lock() -> dict:
    return {"protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__)),
            "analyzer_sha256": sha(ANALYZER),
            "bigville_raw_sha256": sha(BIGVILLE), "dialogue_raw_sha256": sha(DIALOGUE),
            "bigville_source_lock_sha256": sha(BIGVILLE_LOCK),
            "dialogue_source_lock_sha256": sha(DIALOGUE_LOCK)}


def min_fill_order(nodes: list[int], pairs: set[tuple[int, int]]) -> tuple[list[int], int]:
    graph = {n: set() for n in nodes}
    for a, b in pairs:
        if a != b:
            graph[a].add(b); graph[b].add(a)
    order: list[int] = []
    width = 0
    while graph:
        best = None
        best_score = None
        for node, neighbors in graph.items():
            adjacent = sorted(neighbors)
            missing = sum(1 for i, a in enumerate(adjacent)
                          for b in adjacent[i + 1:] if b not in graph[a])
            score = (missing, node)
            if best_score is None or score < best_score:
                best, best_score = node, score
        assert best is not None
        neighbors = list(graph[best])
        width = max(width, len(neighbors))
        for i, a in enumerate(neighbors):
            for b in neighbors[i + 1:]:
                graph[a].add(b); graph[b].add(a)
        for other in neighbors:
            graph[other].discard(best)
        del graph[best]
        order.append(best)
    return order, width


def groups_from_order(order: list[int], sizes: list[int], frame_ids: list[int]) -> dict[int, int]:
    result: dict[int, int] = {}
    cursor = 0
    for frame, size in zip(frame_ids, sizes):
        for node in order[cursor:cursor + size]:
            result[node] = frame
        cursor += size
    if cursor != len(order) or len(result) != len(order):
        raise ValueError("partition size sequence does not cover each task node once")
    return result


def metrics(name: str, owner: dict[int, int], authored: dict[int, int],
            sizes: list[int], frame_ids: list[int], edges: list[tuple[int, int]],
            observed: list[tuple[int, int, int]], width: int,
            static_rules: list[dict], *, edge_inventory_complete: bool,
            static_rule_scope: str) -> dict:
    task_nodes = set(authored)
    cross_edges = [(a, b) for a, b in edges if a in task_nodes and b in task_nodes
                   and owner[a] != owner[b]]
    global_edges = ([(a, b) for a, b in edges
                     if (a in task_nodes) != (b in task_nodes)]
                    if edge_inventory_complete else None)
    observed_cross = [(a, b, count) for a, b, count in observed
                      if a in task_nodes and b in task_nodes and owner[a] != owner[b]]
    observed_pairs = sorted({tuple(sorted((a, b))) for a, b, _ in observed_cross if a != b})
    authored_pairs = [(a, b) for i, a in enumerate(sorted(task_nodes))
                      for b in sorted(task_nodes)[i + 1:] if authored[a] == authored[b]]
    retained = sum(owner[a] == owner[b] for a, b in authored_pairs)
    boundary_nodes: set[int] = set()
    for a, b in cross_edges:
        boundary_nodes.update((a, b))
    global_task_nodes = ({a if a in task_nodes else b for a, b in global_edges}
                         if global_edges is not None else set())
    boundary_nodes |= global_task_nodes
    per_frame_boundary = {str(f): 0 for f in frame_ids}
    frame_touches: dict[int, set[int]] = {f: set() for f in frame_ids}
    for node in boundary_nodes:
        frame_touches[owner[node]].add(node)
    per_frame_boundary = {str(f): len(frame_touches[f]) for f in frame_ids}
    return {
        "partition": name,
        "frame_sizes": [sum(owner[n] == f for n in task_nodes) for f in frame_ids],
        "cross_frame_captured_dependency_edge_count": len(cross_edges),
        "distinct_cross_frame_observed_access_pairs": len(observed_pairs),
        "weighted_cross_frame_observed_access_count": sum(x[2] for x in observed_cross),
        "within_authored_frame_pair_retention": {
            "retained": retained, "total": len(authored_pairs),
            "fraction": retained / len(authored_pairs) if authored_pairs else 1.0},
        "distinct_task_nodes_on_cut_or_known_global_boundary":
            len(boundary_nodes) if edge_inventory_complete else None,
        "boundary_nodes_by_frame": per_frame_boundary,
        "captured_global_boundary_edge_incidence": len(global_edges) if global_edges is not None else None,
        "global_boundary_incidence_coverage": "complete_graph_edge_inventory" if edge_inventory_complete
            else "unavailable; source capture contains causal_influence dependencies only",
        "dependency_min_fill_induced_width": width,
        "static_rule_potential": {
            "coverage": static_rule_scope,
            "active_rule_count": sum(bool(r.get("active")) for r in static_rules),
            "read_any_rule_count": sum(bool(r.get("active")) and bool(r.get("reads_any")) for r in static_rules),
            "write_any_rule_count": sum(bool(r.get("active")) and bool(r.get("writes_any")) for r in static_rules),
            "declared_read_key_count": sum(len(r.get("reads", [])) for r in static_rules if r.get("active")),
            "declared_write_key_count": sum(len(r.get("writes", [])) for r in static_rules if r.get("active")),
            "interpretation": "Potential coupling is global to this run's rule set; native keys do not identify concrete frame pairs."},
    }


def make_case(case_id: str, authored: dict[int, int], edges: list[tuple[int, int]],
              observed: list[tuple[int, int, int]], static_rules: list[dict],
              graph_digest: str, source_raw: Path, source_lock: Path,
              *, edge_inventory_complete: bool, edge_inventory_scope: str,
              static_rule_scope: str) -> dict:
    if isinstance(static_rules, dict):
        static_rules = [static_rules]
    frame_ids = sorted(set(authored.values()))
    sizes = [sum(v == frame for v in authored.values()) for frame in frame_ids]
    nodes = sorted(authored)
    dependencies = {tuple(sorted((a, b))) for a, b in edges
                    if a in authored and b in authored and a != b}
    dependencies.update(tuple(sorted((a, b))) for a, b, _ in observed
                        if a in authored and b in authored and a != b)
    order, width = min_fill_order(nodes, dependencies)
    authored_part = dict(authored)
    balanced_part = groups_from_order(nodes, sizes, frame_ids)
    derived_part = groups_from_order(order, sizes, frame_ids)
    return {"case_id": case_id, "source_raw_sha256": sha(source_raw),
            "source_lock_sha256": sha(source_lock), "captured_graph_digest": graph_digest,
            "task_node_count": len(nodes), "authored_frame_sizes": sizes,
            "authored_frame_ids": frame_ids, "captured_graph_edge_count": len(edges),
            "edge_inventory_scope": edge_inventory_scope,
            "concrete_task_dependency_pair_count": len(dependencies),
            "observed_access_event_count": sum(x[2] for x in observed),
            "observed_task_access_pair_count": len({tuple(sorted((a, b))) for a, b, _ in observed
                                                     if a in authored and b in authored and a != b}),
            "trace_assessment": "partial; no unobserved access is treated as absent",
            "min_fill_order_node_ids": order,
            "partitions": [
                metrics("authored", authored_part, authored, sizes, frame_ids, edges, observed, width, static_rules, edge_inventory_complete=edge_inventory_complete, static_rule_scope=static_rule_scope),
                metrics("balanced_id", balanced_part, authored, sizes, frame_ids, edges, observed, width, static_rules, edge_inventory_complete=edge_inventory_complete, static_rule_scope=static_rule_scope),
                metrics("dependency_min_fill", derived_part, authored, sizes, frame_ids, edges, observed, width, static_rules, edge_inventory_complete=edge_inventory_complete, static_rule_scope=static_rule_scope),
            ],
            "execution_status": "not_run_retrospective_structural_only"}


def main() -> None:
    current = input_lock()
    if not LOCK.exists() or json.loads(LOCK.read_text()) != current:
        raise SystemExit("missing or stale retrospective-analysis lock; print --lock and freeze inputs first")
    big = json.loads(BIGVILLE.read_text())
    dia = json.loads(DIALOGUE.read_text())
    if not all(big.get("checks", {}).values()) or not all(dia.get("checks", {}).values()):
        raise SystemExit("source capture's accepted checks are not all true")
    btrace = next(r for r in big["runs"] if r.get("traced") and r.get("policy") == "event")
    bfull = next(r for r in big["runs"] if not r.get("traced") and r.get("policy") == "full")
    if btrace["graph_digest"] != next(r["graph_digest"] for r in big["runs"]
                                      if not r.get("traced") and r.get("policy") == "event"):
        raise SystemExit("Bigville traced and trace-off event graph digests differ")
    b_owner = {int(n): int(f) for n, f in btrace["runtime_node_frame"]}
    b_edges = [(int(a), int(b)) for a, b in btrace["runtime_dependency_edges"]]
    b_observed = [(int(x["node"]), int(x["peer"]), int(x["count"]))
                  for x in btrace["runtime_access_events"]
                  if x.get("node") is not None and x.get("peer") is not None]
    cases = [make_case("bigville_task_access_census", b_owner, b_edges, b_observed,
                        btrace["static_rule_access"], btrace["graph_digest"], BIGVILLE, BIGVILLE_LOCK,
                        edge_inventory_complete=False, edge_inventory_scope="causal_influence only",
                        static_rule_scope="target_rule_only; not a complete active-rule inventory")]
    dtrace = next(r for r in dia["runs"] if r.get("arm") == "trace")
    dplain = next(r for r in dia["runs"] if r.get("arm") == "plain")
    if dtrace["final_graph_digest"] != dplain["final_graph_digest"]:
        raise SystemExit("dialogue trace and plain final graphs differ")
    d_owner = {int(n): int(f) for n, f in dtrace["frame_owner"]}
    graph = dtrace["final_graph"]
    d_edges = [(int(e["src"]), int(e["tgt"])) for e in graph["edges"]]
    d_observed = []
    for cp in dtrace["checkpoints"]:
        for event in cp["trace_events"]:
            if event.get("node") is not None and event.get("peer") is not None:
                d_observed.append((int(event["node"]), int(event["peer"]), int(event["count"])))
    cases.append(make_case("connected_mixed_dialogue_census", d_owner, d_edges, d_observed,
                           dtrace["static_rule_access"], dtrace["final_graph_digest"], DIALOGUE, DIALOGUE_LOCK,
                           edge_inventory_complete=True, edge_inventory_scope="all final graph edge types",
                           static_rule_scope="all loaded active rules"))
    result = {"schema_version": 1,
              "run_id": "substrate-authored-capture-cut-ranking-v1-20260926",
              "status": "retrospective_development_diagnostic_not_confirmatory",
              "analysis_lock_sha256": sha(LOCK), "locked_inputs": current,
              "claim_boundary": "Cut ranking on two previously captured task graphs only; no rerun, mutation, partitioned closure, parity, natural-task prevalence, or speed claim.",
              "cases": cases,
              "confirmatory_requirements_not_satisfied": ["fresh trace-on/off/control runs under this protocol", "three boundary mutation branches", "partition rebuild/update cost", "shared-state refusal or audited boundary delivery", "partitioned-vs-monolithic parity at every checkpoint", "omitted-boundary divergence control"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "case_summaries": [
        {"case_id": c["case_id"], "partitions": c["partitions"]} for c in cases]}, indent=2))


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps(input_lock(), indent=2, sort_keys=True))
    else:
        main()
