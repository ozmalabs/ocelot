#!/usr/bin/env python3
"""Measure prompt-anchored cuts against Message census and non-Message controls."""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/live_conversation_task_graph_harvest_v1_20261003.jsonl.gz"
PATHS = ROOT / "evaluation/reports/live_conversation_task_anchor_paths_v1_20261004.json"
LOCK = ROOT / "evaluation/substrate_capability/live_graph_prompt_neighborhood_cuts_v2_lock_20261004.json"
OUT = ROOT / "evaluation/reports/live_graph_prompt_neighborhood_cuts_v2_20261004.json"
RADII = (1, 2, 3)
HUB_CUTOFFS = (10, 100, 1000, None)
CONTROL_N = 64


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def neighborhood(root: int, nodes: dict[int, dict], edges: list[dict], adjacency: dict[int, list[int]],
                 degree: collections.Counter, radius: int, hub_cutoff: int | None) -> dict:
    distances = {root: 0}
    queue = collections.deque([root])
    while queue:
        cur = queue.popleft()
        if distances[cur] == radius:
            continue
        for nxt in adjacency.get(cur, ()):
            if nxt in distances:
                continue
            if hub_cutoff is not None and degree[nxt] > hub_cutoff and nxt != root:
                continue
            distances[nxt] = distances[cur] + 1
            queue.append(nxt)
    frame = set(distances)
    cut_edge_ids = []
    outside = set()
    for i, edge in enumerate(edges):
        src, tgt = int(edge["src"]), int(edge["tgt"])
        if (src in frame) != (tgt in frame):
            cut_edge_ids.append(i)
            outside.add(tgt if src in frame else src)
    frontier = sum(d == radius for d in distances.values())
    return {
        "root_id": root,
        "root_degree": int(degree[root]),
        "radius": radius,
        "hub_cutoff": hub_cutoff,
        "frame_nodes": len(frame),
        "frame_fraction": len(frame) / max(1, len(nodes)),
        "frontier_nodes": frontier,
        "cut_edges": len(cut_edge_ids),
        "outside_boundary_nodes": len(outside),
        "cut_edges_per_frame_node": len(cut_edge_ids) / max(1, len(frame)),
    }


def main() -> int:
    if not LOCK.is_file():
        raise SystemExit("source lock missing")
    lock = json.loads(LOCK.read_text())
    inputs = {"capture_sha256": sha_file(CAPTURE), "path_analysis_sha256": sha_file(PATHS),
              "runner_sha256": sha_file(Path(__file__).resolve())}
    if lock.get("locked_inputs") != inputs:
        raise SystemExit("locked inputs changed; refusing analysis")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    path_data = json.loads(PATHS.read_text())
    expected_digests = {row["graph_digest"] for row in path_data["rows"]}
    header = None
    unique: dict[str, dict] = {}
    records = 0
    with gzip.open(CAPTURE, "rt", encoding="utf-8") as stream:
        header = json.loads(next(stream))
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("record_type") == "footer" or not record.get("condition"):
                continue
            records += 1
            digest = record["final_graph_digest"]
            if digest not in expected_digests:
                raise SystemExit(f"unmatched graph digest {digest}")
            unique.setdefault(digest, record)
    rows = []
    for digest, record in sorted(unique.items()):
        graph = record["final_graph"]
        nodes = {int(node["id"]): node for node in graph["nodes"]}
        edges = graph["edges"]
        adjacency: dict[int, list[int]] = collections.defaultdict(list)
        degree: collections.Counter = collections.Counter()
        for edge in edges:
            src, tgt = int(edge["src"]), int(edge["tgt"])
            adjacency[src].append(tgt)
            adjacency[tgt].append(src)
            degree[src] += 1
            degree[tgt] += 1
        roots = [nid for nid, node in nodes.items()
                 if node.get("type") == "Message" and node.get("attrs", {}).get("from") == "interlocutor"
                 and node.get("attrs", {}).get("text") == record.get("prompt")]
        if len(roots) != 1:
            raise SystemExit(f"expected one prompt Message root for {digest}, found {len(roots)}")
        root = roots[0]
        message_candidates = [nid for nid, node in nodes.items() if node.get("type") == "Message" and nid != root]
        message_candidates.sort(key=lambda nid: (abs(degree[nid] - degree[root]),
            sha_bytes(f"{digest}:{nid}:message-control-v2".encode()), nid))
        message_controls = message_candidates[:CONTROL_N]
        nonmessage_candidates = [nid for nid, node in nodes.items() if node.get("type") != "Message"]
        nonmessage_candidates.sort(key=lambda nid: (abs(degree[nid] - degree[root]),
            sha_bytes(f"{digest}:{nid}:nonmessage-control-v2".encode()), nid))
        controls = nonmessage_candidates[:CONTROL_N]
        cell_rows = []
        for cutoff in HUB_CUTOFFS:
            for radius in RADII:
                prompt_metric = neighborhood(root, nodes, edges, adjacency, degree, radius, cutoff)
                control_metrics = [neighborhood(nid, nodes, edges, adjacency, degree, radius, cutoff)
                                   for nid in controls]
                message_metrics = [neighborhood(nid, nodes, edges, adjacency, degree, radius, cutoff)
                                   for nid in message_controls]
                observed = prompt_metric["cut_edges_per_frame_node"]
                control_values = [m["cut_edges_per_frame_node"] for m in control_metrics]
                message_values = [m["cut_edges_per_frame_node"] for m in message_metrics]
                gaps = [abs(m["root_degree"] - degree[root]) for m in control_metrics]
                message_gaps = [abs(m["root_degree"] - degree[root]) for m in message_metrics]
                prompt_metric["nonmessage_control_count"] = len(control_metrics)
                prompt_metric["nonmessage_control_degree_gap_min"] = min(gaps, default=None)
                prompt_metric["nonmessage_control_degree_gap_median"] = statistics.median(gaps) if gaps else None
                prompt_metric["nonmessage_control_degree_gap_max"] = max(gaps, default=None)
                prompt_metric["nonmessage_control_exact_degree_count"] = sum(gap == 0 for gap in gaps)
                prompt_metric["nonmessage_control_median_cut_per_frame_node"] = statistics.median(control_values) if control_values else None
                prompt_metric["prompt_percentile_vs_nonmessage_controls"] = sum(v <= observed for v in control_values) / len(control_values) if control_values else None
                prompt_metric["message_control_count"] = len(message_metrics)
                prompt_metric["message_control_degree_gap_min"] = min(message_gaps, default=None)
                prompt_metric["message_control_degree_gap_max"] = max(message_gaps, default=None)
                prompt_metric["message_control_median_cut_per_frame_node"] = statistics.median(message_values) if message_values else None
                prompt_metric["prompt_percentile_vs_message_census"] = sum(v <= observed for v in message_values) / len(message_values) if message_values else None
                cell_rows.append({"prompt": prompt_metric, "controls": control_metrics, "message_controls": message_metrics})
        rows.append({"graph_digest": digest, "condition": record["condition"],
            "prompt": record["prompt"], "replicates_with_same_digest": sum(
                1 for _ in path_data["rows"] if _["graph_digest"] == digest),
            "node_count": len(nodes), "edge_count": len(edges),
            "prompt_root": root, "prompt_root_degree": int(degree[root]),
            "message_candidates": len(message_candidates), "message_controls_used": len(message_controls),
            "nonmessage_candidates": len(nonmessage_candidates), "nonmessage_controls_used": len(controls),
            "cells": cell_rows})
    result = {
        "schema": "LiveGraphPromptNeighborhoodCutsV2",
        "method": {"directionality": "weak/undirected graph for neighborhoods; original edge triples for cut counting",
                   "radii": list(RADII), "hub_cutoffs": list(HUB_CUTOFFS), "matched_controls_per_graph": CONTROL_N,
                   "control_arms": ["complete census of other Message nodes (up to 64), degree gap reported", "up to 64 non-Message nodes ranked by absolute degree gap with deterministic SHA-256 tie-break and actual gap distribution reported"],
                   "cut_metric": "unique crossing edge count and crossing edges per frame node",
                   "annotation_use": "none; provisional owner labels excluded"},
        "inputs": {**inputs, "archive_header_claim_boundary": header.get("claim_boundary")},
        "record_count": records, "unique_graphs": len(rows), "rows": rows,
        "limits": ["Five authored prompts, with duplicate graph replicates collapsed by digest.",
                   "Prompt-root balls are structural probes, not discovered task frames.",
                   "The Message census is small and may not be degree-matched; non-Message controls are degree-ranked but differ in type.",
                   "Hub cutoffs and radii are sensitivity settings, not learned parameters."]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "unique_graphs": len(rows),
        "input_records": records, "capture_sha256": inputs["capture_sha256"],
        "result_sha256": sha_file(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
