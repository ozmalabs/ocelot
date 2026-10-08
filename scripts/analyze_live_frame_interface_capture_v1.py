#!/usr/bin/env python3
"""Independently audit typed cuts and summarize attributes in live frame proposals."""
from __future__ import annotations

import hashlib
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_workers_raw_20261003.json.gz"
CAPTURE_SUMMARY = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_20261003.json"
OUT = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_analysis_20261003.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_proposal(graph: dict, proposal: dict) -> dict:
    members = {int(node) for node in proposal["member_ids"]}
    node_by_id = {int(node["id"]): node for node in graph.get("nodes", [])}
    internal = crossing = 0
    external: set[int] = set()
    internal_by_type: Counter[str] = Counter()
    crossing_by_type: Counter[str] = Counter()
    for edge in graph.get("edges", []):
        src, tgt, edge_type = int(edge["src"]), int(edge["tgt"]), str(edge["type"])
        src_in, tgt_in = src in members, tgt in members
        if src_in and tgt_in:
            internal += 1
            internal_by_type[edge_type] += 1
        elif src_in != tgt_in:
            crossing += 1
            crossing_by_type[edge_type] += 1
            external.add(tgt if src_in else src)
    ext_type_counts = Counter(str(node_by_id[n].get("type", "<missing>"))
                              for n in external if n in node_by_id)
    attr_counts: Counter[tuple[str, str, str]] = Counter()
    examples: dict[tuple[str, str], set[str]] = defaultdict(set)
    for node_id in members:
        node = node_by_id.get(node_id)
        if node is None:
            continue
        node_type = str(node.get("type", "<missing>"))
        for key, value in node.get("attrs", {}).items():
            attr_counts[(node_type, str(key), type(value).__name__)] += 1
            if len(examples[(node_type, str(key))]) < 3:
                examples[(node_type, str(key))].add(repr(value)[:240])
    return {
        "member_count": len(members),
        "all_members_resolve": members <= set(node_by_id),
        "internal_edge_count": internal,
        "crossing_incidence_count": crossing,
        "distinct_external_node_count": len(external),
        "all_external_nodes_resolve": external <= set(node_by_id),
        "external_node_type_counts": dict(sorted(ext_type_counts.items())),
        "internal_edge_type_counts": dict(sorted(internal_by_type.items())),
        "crossing_edge_type_counts": dict(sorted(crossing_by_type.items())),
        "observed_attribute_counts": [list(key) + [count]
                                       for key, count in sorted(attr_counts.items())],
        "observed_attribute_value_examples": [
            [node_type, key, sorted(values)]
            for (node_type, key), values in sorted(examples.items())
        ],
    }


def main() -> None:
    with gzip.open(RAW, "rt", encoding="utf-8") as stream:
        raw = json.load(stream)
    capture_summary = json.loads(CAPTURE_SUMMARY.read_text())
    raw_digest = hashlib.sha256()
    with gzip.open(RAW, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            raw_digest.update(block)
    if raw_digest.hexdigest() != capture_summary["raw_sha256"]:
        raise SystemExit("compressed raw archive does not match the capture's uncompressed SHA-256")
    run_with_graph = next(row for row in raw["runs"] if "full_graph" in row)
    graph = run_with_graph["full_graph"]
    proposals = []
    exact_matches = 0
    endpoint_integrity = True
    for run in raw["runs"]:
        for turn_index, turn_proposals in enumerate(run["bfs_proposals"]):
            for proposal in turn_proposals:
                recomputed = audit_proposal(graph, proposal)
                endpoint_integrity &= (recomputed["all_members_resolve"]
                                       and recomputed["all_external_nodes_resolve"])
                keys = ("member_count", "internal_edge_count", "crossing_incidence_count",
                        "distinct_external_node_count", "external_node_type_counts")
                match = all(proposal.get(key) == recomputed[key] for key in keys)
                exact_matches += int(match)
                request = run["requests"][turn_index]
                weight_total = sum(int(row[6]) for row in request["access_rows"])
                weight_inside = sum(int(row[6]) for row in request["access_rows"]
                                    if ((row[2] is not None and int(row[2]) in set(proposal["member_ids"]))
                                        or (row[4] is not None and int(row[4]) in set(proposal["member_ids"]))))
                proposals.append({
                    "replicate": run["replicate"], "turn": turn_index,
                    "prompt": request["prompt"], "root_message_id": proposal["root_message_id"],
                    "radius": proposal["radius"], "runner_cut_matches_independent_audit": match,
                    **recomputed,
                    "dynamic_trace_weight_total": weight_total,
                    "dynamic_trace_weight_touching_member_nodes": weight_inside,
                    "dynamic_trace_touch_fraction": weight_inside / weight_total if weight_total else None,
                })
    checks = {
        "runner_cuts_match_independent_raw_graph_recomputation": exact_matches == len(proposals),
        "all_proposal_members_and_external_nodes_resolve": endpoint_integrity,
        "proposals_audited": len(proposals) == 24,
        "source_run_capture_gates_passed": all(raw["checks"].values()),
    }
    result = {
        "schema_version": 1,
        "run_id": "substrate-live-frame-interface-capture-v1-20261003-independent-analysis",
        "raw_path": str(RAW.relative_to(ROOT)), "raw_archive_sha256": sha(RAW),
        "raw_sha256": raw_digest.hexdigest(),
        "analysis_script_sha256": sha(Path(__file__).resolve()),
        "graph_source_replicate": run_with_graph["replicate"],
        "graph_semantic_sha256": run_with_graph["graph_semantic_sha256"],
        "checks": checks,
        "summary": {"proposal_count": len(proposals), "independent_cut_matches": exact_matches,
                    "full_graph_nodes": len(graph["nodes"]), "full_graph_edges": len(graph["edges"])},
        "proposals": proposals,
        "interpretation_boundary": "Independent cut and observed-attribute summaries are reconstructed from the retained full graph. Runtime access tracing is bounded and incomplete by design; candidate coverage does not certify execution dependency coverage or task-frame correctness.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "summary": result["summary"], "sha256": sha(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent frame-interface analysis gate failed")


if __name__ == "__main__":
    main()
