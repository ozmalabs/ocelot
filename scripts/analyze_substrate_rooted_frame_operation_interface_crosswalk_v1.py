#!/usr/bin/env python3
"""Join rooted BFS candidates to corrected static/dynamic access records."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evaluation/reports/rooted_frame_proposal_panel_v1_1_20260928.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/rooted_frame_proposal_panel_v1_1_analysis_20260928.json"
ACCESS = ROOT / "evaluation/reports/rooted_frame_access_scope_reconciliation_v1_2_20260928.json"
ACCESS_ANALYSIS = ROOT / "evaluation/reports/rooted_frame_access_scope_reconciliation_v1_2_analysis_20260928.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ROOTED_FRAME_OPERATION_INTERFACE_CROSSWALK_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_ROOTED_FRAME_OPERATION_INTERFACE_CROSSWALK_V1_AMENDMENT_20260928.md"
OUT = ROOT / "evaluation/reports/rooted_frame_operation_interface_crosswalk_v1_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def boundary(graph: dict, members: set[int]) -> tuple[list[tuple], list[tuple]]:
    internal, cut = [], []
    for edge in graph.get("edges", []):
        row = (int(edge[0]), str(edge[1]), int(edge[2]))
        left, right = row[0] in members, row[2] in members
        if left and right:
            internal.append(row)
        elif left != right:
            cut.append(row)
    return sorted(internal), sorted(cut)


def rebuild_bfs(graph: dict, root: int) -> list[set[int]]:
    nodes = {int(node["id"]) for node in graph.get("nodes", [])}
    if root not in nodes:
        raise ValueError(f"root node {root} absent from snapshot")
    adj = {node: set() for node in nodes}
    for edge in graph.get("edges", []):
        source, target = int(edge[0]), int(edge[2])
        if source in adj and target in adj:
            adj[source].add(target)
            adj[target].add(source)
    sets = [{root}]
    for _ in (1, 2):
        current = sets[-1]
        following = current | set().union(*(adj[n] for n in current))
        sets.append(following)
    return sets


def frame_metrics(graph: dict, members: set[int], trace_rows: list[dict], rules: dict[int, dict]) -> dict:
    types = {int(node["id"]): str(node.get("type", "<missing>")) for node in graph.get("nodes", [])}
    per_uid: dict[int, dict] = defaultdict(lambda: {"inside_weight": 0, "outside_weight": 0, "unlocated_weight": 0,
                                                      "inside_ids": set(), "outside_ids": set()})
    total = inside = outside = unlocated = wholly_inside = wholly_outside = partial = 0
    crossing_edges = Counter()
    cross_rule_external_attrs = Counter()
    cross_rule_external_attr_types = Counter()
    static_cross_reads, static_cross_writes = set(), set()
    wildcard_read_uids, wildcard_write_uids = set(), set()
    for row in trace_rows:
        uid, kind = int(row["rule_uid"]), str(row["kind"])
        weight = int(row["count"])
        total += weight
        ids = {int(value) for value in (row.get("node"), row.get("peer")) if value is not None}
        state = per_uid[uid]
        if not ids:
            unlocated += weight
            state["unlocated_weight"] += weight
            continue
        inside_ids = ids & members
        outside_ids = ids - members
        state["inside_ids"].update(inside_ids)
        state["outside_ids"].update(outside_ids)
        if inside_ids:
            inside += weight
            state["inside_weight"] += weight
        if outside_ids:
            outside += weight
            state["outside_weight"] += weight
        if inside_ids and not outside_ids:
            wholly_inside += weight
        elif outside_ids and not inside_ids:
            wholly_outside += weight
        elif inside_ids and outside_ids:
            partial += weight

        if kind in ("pattern_edge", "term_edge_read", "effect_edge_upsert", "effect_edge_delete", "effect_replace_edge") and len(ids) == 2:
            src, peer = int(row["node"]), int(row["peer"])
            if (src in members) != (peer in members):
                direction = "read" if kind in ("pattern_edge", "term_edge_read") else "write"
                crossing_edges[(direction, kind, str(row.get("resource")))] += weight

    cross_uids = {uid for uid, state in per_uid.items() if state["inside_ids"] and state["outside_ids"]}
    for uid in cross_uids:
        rule = rules.get(uid)
        if rule is None:
            continue
        static_cross_reads.update(map(str, rule.get("reads", [])))
        static_cross_reads.update(map(str, rule.get("term_edge_reads", [])))
        static_cross_writes.update(map(str, rule.get("writes", [])))
        if rule.get("reads_any"):
            wildcard_read_uids.add(uid)
        if rule.get("writes_any"):
            wildcard_write_uids.add(uid)
        for row in trace_rows:
            if int(row["rule_uid"]) != uid or row.get("kind") not in ("term_attr_read", "jit_attr_read", "effect_attr_write", "effect_attr_compare_read"):
                continue
            node = row.get("node")
            if node is not None and int(node) not in members and row.get("resource") is not None:
                signature = (types.get(int(node), "<missing>"), str(row["resource"]))
                cross_rule_external_attrs[signature] += int(row["count"])
                cross_rule_external_attr_types[signature[0]] += int(row["count"])

    return {
        "candidate_node_count": len(members),
        "crossing_state_graph_edge_count": len(boundary(graph, members)[1]),
        "weighted_trace_events": total,
        "weighted_events_touching_candidate": inside,
        "weighted_events_with_outside_ids": outside,
        "weighted_events_wholly_inside": wholly_inside,
        "weighted_events_wholly_outside": wholly_outside,
        "weighted_events_with_ids_on_both_sides": partial,
        "weighted_events_without_node_ids": unlocated,
        "distinct_observed_rule_uids": len(per_uid),
        "rule_uids_with_crossing_observed_footprint": len(cross_uids),
        "crossing_concrete_edge_events_by_direction_kind_type": {
            "|".join(key): value for key, value in sorted(crossing_edges.items())
        },
        "crossing_concrete_edge_event_weight": sum(crossing_edges.values()),
        "cross_scope_static_read_key_count": len(static_cross_reads),
        "cross_scope_static_write_key_count": len(static_cross_writes),
        "cross_scope_static_read_keys": sorted(static_cross_reads),
        "cross_scope_static_write_keys": sorted(static_cross_writes),
        "cross_scope_wildcard_reader_uids": sorted(wildcard_read_uids),
        "cross_scope_wildcard_writer_uids": sorted(wildcard_write_uids),
        "cross_scope_external_attribute_event_weight_by_node_type_and_key": {
            f"{node_type}.{attr}": count for (node_type, attr), count in sorted(cross_rule_external_attrs.items())
        },
        "cross_scope_external_attribute_event_weight_by_node_type": dict(sorted(cross_rule_external_attr_types.items())),
        "observed_finite_domain_sizes": None,
    }


def main() -> None:
    base = json.loads(BASE.read_text())
    base_analysis = json.loads(BASE_ANALYSIS.read_text())
    access = json.loads(ACCESS.read_text())
    access_analysis = json.loads(ACCESS_ANALYSIS.read_text())
    checks = {
        "rooted_input_analysis_passes": bool(base_analysis.get("checks")) and all(base_analysis["checks"].values()),
        "access_input_integrity_checks_pass": all(access_analysis.get("checks", {}).values()),
        "rooted_lock_stable": base.get("locked_inputs") == base.get("post_run_inputs"),
        "access_lock_stable": access.get("locked_inputs") == access.get("post_run_inputs"),
        "same_replicates": sorted(int(run["replicate"]) for run in base["runs"]) == sorted(int(run["replicate"]) for run in access["runs"]),
    }
    base_runs = {int(run["replicate"]): run for run in base["runs"]}
    access_runs = {int(run["replicate"]): run for run in access["runs"]}
    output_rows = []
    for replicate in sorted(set(base_runs) & set(access_runs)):
        br, ar = base_runs[replicate], access_runs[replicate]
        same_graph = br["whole_graph_semantic_sha256"] == ar["whole_graph_semantic_sha256"]
        checks[f"replicate_{replicate}_graph_digest_matches"] = same_graph
        graph = br["structural_graph_snapshot"]
        access_turns = {int(turn["turn"]): turn for turn in ar["turns"]}
        for turn_idx, turn in enumerate(br["turns"]):
            at = access_turns[turn_idx]
            checks[f"replicate_{replicate}_turn_{turn_idx}_prompt_matches"] = turn["prompt"] == at["prompt"]
            rules = {int(rule["rule_uid"]): rule for rule in at["static_rules_for_observed_uids"]}
            candidates = br["rooted_candidates"][f"turn_{turn_idx}"]
            operational = set(map(int, br["task_boundaries"][f"turn_{turn_idx}"]["owned_node_ids"]))
            rebuilt = rebuild_bfs(graph, int(turn["message_id"]))
            for radius, members in enumerate(rebuilt):
                saved = set(map(int, candidates[radius]["candidate_node_ids"]))
                exact = members == saved
                checks[f"replicate_{replicate}_turn_{turn_idx}_radius_{radius}_bfs_exact"] = exact
                internal, cut = boundary(graph, members)
                checks[f"replicate_{replicate}_turn_{turn_idx}_radius_{radius}_boundary_recomputed"] = (
                    len(internal) == int(candidates[radius]["internal_edge_count"])
                    and len(cut) == int(candidates[radius]["crossing_incidence_count"])
                )
                trace_metrics = frame_metrics(graph, members, at["trace_rows"], rules)
                output_rows.append({
                    "replicate": replicate, "turn": turn_idx, "prompt": turn["prompt"],
                    "frame_kind": "rooted_bfs_candidate", "radius": radius,
                    "candidate_id_sha256": hashlib.sha256(canonical(sorted(members))).hexdigest(),
                    "overlap_with_operational_reference": {
                        "intersection_nodes": len(members & operational),
                        "candidate_precision": len(members & operational) / len(members) if members else None,
                        "reference_recall": len(members & operational) / len(operational) if operational else None,
                        "jaccard": len(members & operational) / len(members | operational) if members | operational else 1.0,
                    },
                    "observed_interface": trace_metrics,
                })
            reference_metrics = frame_metrics(graph, operational, at["trace_rows"], rules)
            output_rows.append({
                "replicate": replicate, "turn": turn_idx, "prompt": turn["prompt"],
                "frame_kind": "protocol_operational_reference", "radius": None,
                "candidate_id_sha256": hashlib.sha256(canonical(sorted(operational))).hexdigest(),
                "overlap_with_operational_reference": {"intersection_nodes": len(operational), "candidate_precision": 1.0, "reference_recall": 1.0, "jaccard": 1.0},
                "observed_interface": reference_metrics,
            })
    checks["all_joined_graphs_match"] = all(v for k, v in checks.items() if k.endswith("_graph_digest_matches"))
    result = {
        "schema_version": 1,
        "analysis_id": "rooted-frame-operation-interface-crosswalk-v1-20260928",
        "protocol_sha256": sha(PROTOCOL),
        "amendment_sha256": sha(AMENDMENT),
        "analyzer_sha256": sha(Path(__file__)),
        "input_records": {path.name: {"sha256": sha(path), "path": str(path.relative_to(ROOT))}
                          for path in (BASE, BASE_ANALYSIS, ACCESS, ACCESS_ANALYSIS)},
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "claim_boundary": "Offline join and independent BFS/cut reconstruction on one authored two-prompt live task family. Observed accesses are a partial trace, static keys are not a finite task-variable interface, and the operational frame is protocol-declared.",
        "frames": output_rows,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "all_checks_pass": result["all_checks_pass"],
                      "checks": checks, "frame_records": len(output_rows)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("rooted frame operation-interface crosswalk failed")


if __name__ == "__main__":
    main()
