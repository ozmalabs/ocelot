#!/usr/bin/env python3
"""Diagnostic typed-path audit for task anchors in retained conversation graphs.

This is deliberately not an ownership inference algorithm. It reports candidate
paths from each captured inbound Message to Goal and DiscourseEvent nodes, both
with all graph nodes available and with high-degree intermediate nodes removed.
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/live_conversation_task_graph_harvest_v1_20261003.jsonl.gz"
OUT = ROOT / "evaluation/reports/live_conversation_task_anchor_paths_v1_20261004.json"
MAX_DEPTH = 6
HUB_DEGREE = 100


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shortest_paths(root, targets, nodes, edges, max_degree=None):
    adj = collections.defaultdict(list)
    degree = collections.Counter()
    for e in edges:
        a, b = int(e["src"]), int(e["tgt"])
        rel = str(e["type"])
        degree[a] += 1
        degree[b] += 1
        adj[a].append((b, rel, ">"))
        adj[b].append((a, rel, "<"))
    queue = collections.deque([(root, [])])
    seen = {root}
    found = {}
    while queue:
        node, path = queue.popleft()
        if node in targets:
            found[node] = path
        if len(path) >= MAX_DEPTH:
            continue
        for nxt, rel, direction in adj[node]:
            if nxt in seen:
                continue
            if max_degree is not None and degree[nxt] > max_degree and nxt not in targets:
                continue
            seen.add(nxt)
            step = {"edge": rel, "direction": direction, "node_type": nodes[nxt]["type"]}
            queue.append((nxt, path + [step]))
    return found


def main():
    header = None
    rows = []
    with gzip.open(CAPTURE, "rt", encoding="utf-8") as stream:
        header = json.loads(next(stream))
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("record_type") == "footer" or not record.get("condition"):
                continue
            graph = record.get("final_graph", {})
            nodes = {int(n["id"]): n for n in graph.get("nodes", [])}
            edges = graph.get("edges", [])
            roots = [i for i, n in nodes.items() if n.get("type") == "Message"
                     and n.get("attrs", {}).get("from") == "interlocutor"
                     and n.get("attrs", {}).get("text") == record.get("prompt")]
            if len(roots) != 1:
                raise ValueError(f"expected one inbound prompt Message, got {len(roots)}")
            root = roots[0]
            goals = {i for i, n in nodes.items() if n.get("type") == "Goal"}
            events = {i for i, n in nodes.items() if n.get("type") == "DiscourseEvent"}
            all_goal = shortest_paths(root, goals, nodes, edges)
            local_goal = shortest_paths(root, goals, nodes, edges, HUB_DEGREE)
            all_event = shortest_paths(root, events, nodes, edges)
            local_event = shortest_paths(root, events, nodes, edges, HUB_DEGREE)

            def describe(ids, paths):
                return [{"id": i, "kind": nodes[i].get("attrs", {}).get("kind"),
                         "path": paths[i]} for i in sorted(ids) if i in paths]

            explicit = {int(e["src"]) for e in edges if e.get("type") == "comprehends"
                        and int(e["tgt"]) == root and int(e["src"]) in goals}
            rows.append({
                "condition": record["condition"], "replicate": record.get("replicate"),
                "graph_digest": record.get("final_graph_digest"),
                "nodes": len(nodes), "edges": len(edges), "prompt_message": root,
                "goal_count": len(goals), "explicit_comprehends_goal_ids": sorted(explicit),
                "goals_reachable_within_depth": describe(goals, all_goal),
                "goals_reachable_without_high_degree_intermediates": describe(goals, local_goal),
                "events_reachable_within_depth": describe(events, all_event),
                "events_reachable_without_high_degree_intermediates": describe(events, local_event),
                "degree_cutoff": HUB_DEGREE, "max_depth": MAX_DEPTH,
            })
    summary = {}
    for condition in sorted({r["condition"] for r in rows}):
        group = [r for r in rows if r["condition"] == condition]
        summary[condition] = {
            "workers": len(group),
            "explicit_prompt_goals": [len(r["explicit_comprehends_goal_ids"]) for r in group],
            "goals_reachable_no_hubs": [len(r["goals_reachable_without_high_degree_intermediates"]) for r in group],
            "goal_counts": [r["goal_count"] for r in group],
            "prompt_events_reachable_no_hubs": [len(r["events_reachable_without_high_degree_intermediates"]) for r in group],
        }
    result = {
        "schema": "LiveConversationTaskAnchorPathsV1",
        "source": str(CAPTURE.relative_to(ROOT)),
        "capture_sha256": sha(CAPTURE),
        "capture_lock": header.get("locked_inputs"),
        "method": "Undirected typed shortest paths from the unique inbound prompt Message; reports paths only and makes no ownership assignment.",
        "limits": ["Authored five-prompt panel with two workers per prompt.",
                   "High-degree cutoff is diagnostic, not a validated separator rule.",
                   "Graph reachability does not establish task ownership or causal relevance."],
        "summary_by_condition": summary,
        "rows": rows,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "workers": len(rows),
                      "summary_by_condition": summary}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
