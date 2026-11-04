"""Opt-in, read-only export of existing native search-attempt graph records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ATTEMPT_FIELDS = (
    "operator_kind", "status", "depth", "work_cost", "rank_score",
    "domain", "kind", "source_epoch", "model_epoch", "frame_epoch",
    "expression_key", "expression_digest", "expression_digest_status",
    "effect_digest", "predicted_state", "goal_state", "guard_state",
    "subgoal_state",
)


def _graph_snapshots(value):
    if isinstance(value, dict):
        if isinstance(value.get("nodes"), list) and isinstance(value.get("edges"), list):
            yield value
        for key, child in value.items():
            if key == "native_graph_snapshot_json" and isinstance(child, str):
                try:
                    decoded = json.loads(child)
                except json.JSONDecodeError:
                    continue
                yield from _graph_snapshots(decoded)
            else:
                yield from _graph_snapshots(child)
    elif isinstance(value, list):
        for child in value:
            yield from _graph_snapshots(child)


def export_attempt_details(payload: dict) -> dict:
    """Project only existing attempt nodes and provenance edges from snapshots."""
    snapshots = list(_graph_snapshots(payload))
    rows = {}
    for graph in snapshots:
        nodes = {row.get("id"): row for row in graph["nodes"]
                 if isinstance(row, dict) and isinstance(row.get("id"), (int, str))}
        edges = [edge for edge in graph["edges"] if isinstance(edge, dict)]
        outgoing_by_node = {}
        request_ids_by_attempt = {}
        for edge in edges:
            source, target = edge.get("src"), edge.get("tgt")
            if source in nodes:
                outgoing_by_node.setdefault(source, []).append(edge)
            if (edge.get("type") == "has_search_attempt" and target in nodes
                    and source in nodes):
                request_ids_by_attempt.setdefault(target, []).append(source)
        attempts = {node_id: row for node_id, row in nodes.items()
                    if row.get("type") == "OpenProcessSearchAttempt"}
        candidate_ids_by_attempt = {}
        for candidate_id, candidate in nodes.items():
            if candidate.get("type") != "OpenProcessCandidate":
                continue
            for edge in outgoing_by_node.get(candidate_id, ()):
                if (edge.get("type") == "derived_from_attempt"
                        and edge.get("tgt") in attempts):
                    candidate_ids_by_attempt.setdefault(edge["tgt"], []).append(
                        candidate_id)
        for node_id, node in attempts.items():
            attrs = node.get("attrs") or {}
            row = {"attempt_id": node_id}
            row.update({field: attrs[field] for field in ATTEMPT_FIELDS if field in attrs})
            outgoing = outgoing_by_node.get(node_id, ())
            row["parent_process_ids"] = sorted(
                edge["tgt"] for edge in outgoing
                if edge.get("type") == "uses_parent_process" and edge.get("tgt") in nodes)
            row["source_attempt_ids"] = sorted(
                edge["tgt"] for edge in outgoing
                if edge.get("type") == "extends_search_attempt" and edge.get("tgt") in attempts)
            row["derived_candidate_ids"] = sorted(
                set(candidate_ids_by_attempt.get(node_id, ())), key=lambda value: str(value))
            row["parent_candidate_ids"] = sorted({edge["tgt"] for edge in outgoing
                if edge.get("type") == "extends_candidate" and edge.get("tgt") in nodes},
                key=lambda value: str(value))
            row["candidate_ids"] = sorted(set(row["derived_candidate_ids"])
                | set(row["parent_candidate_ids"]), key=lambda value: str(value))
            row["task_ids"] = sorted(
                edge["tgt"] for edge in outgoing
                if edge.get("type") == "about_task" and edge.get("tgt") in nodes)
            row["request_ids"] = sorted(request_ids_by_attempt.get(node_id, ()),
                                         key=lambda value: str(value))
            identity = json.dumps((str(node_id), row.get("domain"),
                row.get("expression_key"), row.get("effect_digest")),
                sort_keys=True, default=str)
            rows[identity] = row
    ordered = [rows[key] for key in sorted(rows)]
    return {"schema": "native-search-attempt-details-v1",
            "read_only": True, "agent_feedback": False,
            "source_graph_count": len(snapshots), "attempt_count": len(ordered),
            "attempts": ordered}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-attempt-details", action="store_true",
                        help="explicitly opt in to a read-only native-attempt projection")
    parser.add_argument("--input", type=Path, required=True,
                        help="P22/P26 result JSON containing a native graph snapshot")
    parser.add_argument("--output", type=Path, required=True,
                        help="new external report path; existing files are never overwritten")
    args = parser.parse_args(argv)
    if not args.export_attempt_details:
        parser.error("attempt export is disabled by default; pass --export-attempt-details")
    if args.output.exists():
        parser.error("refusing to overwrite an existing attempt-detail report")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = export_attempt_details(payload)
    if result["source_graph_count"] == 0:
        parser.error("input contains no native graph snapshot")
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2, default=str) + "\n",
                           encoding="utf-8")
    print(json.dumps({"attempt_count": result["attempt_count"],
                      "source_graph_count": result["source_graph_count"],
                      "read_only": True}, sort_keys=True))


if __name__ == "__main__":
    main()
