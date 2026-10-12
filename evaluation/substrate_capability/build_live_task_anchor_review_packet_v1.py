#!/usr/bin/env python3
"""Build an anonymized review packet for task-frame ownership annotation.

The packet supplies prompt text, all Goal candidates, prompt-linked event paths,
and only the typed nodes on those paths. It withholds condition/worker labels.
It is a review aid, not an automatically inferred ownership map.
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/live_conversation_task_graph_harvest_v1_20261003.jsonl.gz"
PATH_ANALYSIS = ROOT / "evaluation/reports/live_conversation_task_anchor_paths_v1_20261004.json"
OUT = ROOT / "evaluation/reports/live_conversation_task_anchor_review_packet_v1_20261004.json"
HUB_DEGREE = 100
MAX_DEPTH = 6


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths_from(root, nodes, edges, targets):
    adjacency = collections.defaultdict(list)
    degree = collections.Counter()
    for edge in edges:
        a, b = int(edge["src"]), int(edge["tgt"])
        rel = str(edge["type"])
        degree[a] += 1
        degree[b] += 1
        adjacency[a].append((b, rel, ">"))
        adjacency[b].append((a, rel, "<"))
    parent = {root: None}
    queue = collections.deque([(root, 0)])
    while queue:
        current, depth = queue.popleft()
        if depth == MAX_DEPTH:
            continue
        for nxt, relation, direction in adjacency[current]:
            if nxt in parent or (degree[nxt] > HUB_DEGREE and nxt not in targets):
                continue
            parent[nxt] = (current, relation, direction)
            queue.append((nxt, depth + 1))

    def recover(target):
        if target not in parent:
            return None
        ids = [target]
        steps = []
        cur = target
        while cur != root:
            prev, relation, direction = parent[cur]
            steps.append({"edge": relation, "direction": direction})
            ids.append(prev)
            cur = prev
        return {"node_ids": list(reversed(ids)), "steps": list(reversed(steps))}

    return {target: recover(target) for target in targets}


def main():
    path_data = json.loads(PATH_ANALYSIS.read_text(encoding="utf-8"))
    path_digests = {r["graph_digest"] for r in path_data["rows"]}
    header = None
    records = []
    with gzip.open(CAPTURE, "rt", encoding="utf-8") as stream:
        header = json.loads(next(stream))
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("record_type") == "footer" or not record.get("condition"):
                continue
            if record.get("replicate") != 0:
                continue  # replicate 1 is held back for a later blind reliability pass
            graph = record["final_graph"]
            if record["final_graph_digest"] not in path_digests:
                raise ValueError("graph digest is absent from the path audit")
            nodes = {int(n["id"]): n for n in graph.get("nodes", [])}
            edges = graph.get("edges", [])
            roots = [i for i, n in nodes.items() if n.get("type") == "Message"
                     and n.get("attrs", {}).get("from") == "interlocutor"
                     and n.get("attrs", {}).get("text") == record.get("prompt")]
            if len(roots) != 1:
                raise ValueError(f"expected one inbound prompt message; found {len(roots)}")
            root = roots[0]
            goal_ids = {i for i, n in nodes.items() if n.get("type") == "Goal"}
            event_ids = {i for i, n in nodes.items() if n.get("type") == "DiscourseEvent"}
            paths = paths_from(root, nodes, edges, goal_ids | event_ids)
            selected = {root}
            for path in paths.values():
                if path:
                    selected.update(path["node_ids"])
            # Include every Goal, even disconnected candidates, so reviewers can
            # distinguish absence of a path from absence of a task-level Goal.
            selected.update(goal_ids)
            labels = {}
            counters = collections.Counter()
            for node_id in sorted(selected, key=lambda i: (nodes[i]["type"], i)):
                kind = nodes[node_id]["type"]
                counters[kind] += 1
                prefix = {"Message": "M", "Goal": "G", "DiscourseEvent": "E"}.get(kind)
                if prefix is None:
                    prefix = "N" + hashlib.sha256(kind.encode()).hexdigest()[:3].upper()
                labels[node_id] = f"{prefix}{counters[kind]:02d}"
            candidate_nodes = []
            for node_id in sorted(selected, key=lambda i: labels[i]):
                node = nodes[node_id]
                attrs = node.get("attrs", {})
                safe_attrs = {k: attrs[k] for k in ("kind", "status", "lifecycle_status", "event_index") if k in attrs}
                path = paths.get(node_id)
                if path:
                    path = {"node_ids": [labels[i] for i in path["node_ids"]], "steps": path["steps"]}
                candidate_nodes.append({"label": labels[node_id], "type": node["type"], "attrs": safe_attrs,
                    "prompt_path": path,
                    "is_prompt_root": node_id == root})
            candidate_edges = []
            for edge in edges:
                a, b = int(edge["src"]), int(edge["tgt"])
                if a in selected and b in selected:
                    candidate_edges.append({"src": labels[a], "edge": str(edge["type"]), "tgt": labels[b]})
            case = {
                "case_id": "case_" + hashlib.sha256((record["final_graph_digest"] + "review-v1").encode()).hexdigest()[:10],
                "prompt": record.get("prompt"),
                "task_instruction": "Mark each candidate node as request-specific, shared/background, or uncertain. A request-specific node is needed to represent this request or its immediate response task. Use uncertain when the graph does not support a reliable decision. Do not infer ownership from reachability alone.",
                "candidates": candidate_nodes,
                "typed_edges": candidate_edges,
            }
            records.append(case)
    records.sort(key=lambda row: row["case_id"])
    out = {
        "schema": "LiveTaskAnchorReviewPacketV1",
        "source_capture": str(CAPTURE.relative_to(ROOT)),
        "source_capture_sha256": sha(CAPTURE),
        "path_analysis_sha256": sha(PATH_ANALYSIS),
        "source_capture_lock": header.get("locked_inputs"),
        "selection": "One worker graph per prompt condition; the second identical replicate is held back for a separate blind reliability review.",
        "blinding": "Condition, replicate, task-oracle outcome, and prior ownership labels are withheld. Prompt wording is retained because it is the annotation target.",
        "limits": ["Five authored prompts only.", "Review packet contains Goals and nodes on bounded prompt-to-Goal/event paths, not each full graph.", "This packet does not contain annotations or validate any mapping policy."],
        "cases": records,
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "cases": len(records),
        "case_ids": [r["case_id"] for r in records], "capture_sha256": out["source_capture_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
