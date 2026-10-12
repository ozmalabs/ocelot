#!/usr/bin/env python3
"""Reanalyse selected locked live task-cut captures against locality contract v1.

This is a structural inventory, not a new runtime run or a cheap-cut prevalence
estimate. It extracts only fields present in the source reports and marks missing
interface/dependency quantities explicitly.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/frame_locality_contract_reanalysis_v1_20260928.json"
SOURCES = {
    "held_topic": ROOT / "evaluation/reports/substrate_live_held_topic_evidence_v1_6_20260926.json",
    "self_report": ROOT / "evaluation/reports/substrate_live_self_report_task_boundary_v2_1_20260927.json",
    "describe_scene": ROOT / "evaluation/reports/substrate_live_describe_scene_boundary_v1_20260926.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def pick(value: dict[str, Any], family: str, *keys: str) -> dict[str, Any]:
    """Project a frame to directly reported contract fields."""
    owned_key = "owned_node_ids" if "owned_node_ids" in value else "node_ids"
    nodes = value.get(owned_key)
    if not isinstance(nodes, list):
        raise ValueError(f"frame missing node list ({owned_key})")
    edges = value.get("boundary_edges", [])
    internal = value.get("internal_edges", [])
    width = value.get("owned_induced_treewidth_upper_bound",
                      value.get("member_induced_treewidth_upper_bound"))
    width_value = width.get("value") if isinstance(width, dict) else width
    result = {
        "family": family,
        "frame_id": "/".join(keys),
        "frame_provenance": "protocol_declared operational task projection",
        "unit": "runtime graph nodes",
        "frame_size": len(nodes),
        "internal_edge_count": len(internal),
        "crossing_incidences": len(edges),
        "crossing_edge_type_counts": value.get("boundary_edge_type_counts"),
        "distinct_external_units": value.get("boundary_unique_external_node_count"),
        "external_unit_type_histogram": value.get("boundary_external_node_type_counts"),
        "owned_induced_width_upper_bound": width_value,
        "whole_graph_nodes": value.get("whole_graph_node_count"),
        "whole_graph_edges": value.get("whole_graph_edge_count"),
        "boundary_endpoint_ids_present": bool(edges),
        "endpoint_type_mapping_present": False,
        "task_relevant_interface_variables": None,
        "interface_domain_sizes": None,
        "operation_dependency_coverage": None,
        "partition_discovery_cost": None,
        "partition_provenance": "protocol_declared",
    }
    if result["distinct_external_units"] is None and edges:
        owned = set(nodes)
        outside = set()
        for edge in edges:
            if len(edge) == 3:
                outside.update(x for x in (edge[0], edge[2]) if x not in owned)
        result["distinct_external_units"] = len(outside) if outside else None
    return result


def stable_gate(report: dict[str, Any]) -> dict[str, Any]:
    runs = report.get("runs", [])
    if not runs:
        raise ValueError("source report has no runs")
    started_finished_equal = []
    for run in runs:
        started = run.get("worker_started_inputs")
        finished = run.get("worker_finished_inputs")
        started_finished_equal.append(bool(started and finished and started == finished))
    return {
        "run_count": len(runs),
        "source_lock_stable_each_run": all(started_finished_equal),
        "per_run_lock_checks": started_finished_equal,
        "locked_inputs_sha256": sha256_bytes(canonical(report.get("locked_inputs", {})).encode()),
    }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    loaded = {name: json.loads(path.read_text()) for name, path in SOURCES.items()}
    families: dict[str, list[dict[str, Any]]] = {name: [] for name in SOURCES}

    for run_i, run in enumerate(loaded["held_topic"]["runs"]):
        for turn_i, turn in enumerate(run.get("turns", [])):
            frame = turn.get("task_frame")
            if isinstance(frame, dict):
                families["held_topic"].append(pick(frame, "held_topic", f"replicate_{run_i}", f"turn_{turn_i}"))

    for run_i, run in enumerate(loaded["self_report"]["runs"]):
        cuts = run.get("task_boundaries", {})
        for name in ("turn_0", "turn_1"):
            frame = cuts.get(name)
            if isinstance(frame, dict):
                families["self_report"].append(pick(frame, "self_report", f"replicate_{run_i}", name))

    for run_i, run in enumerate(loaded["describe_scene"]["runs"]):
        cuts = run.get("task_boundaries", {})
        for name in ("a", "b"):
            frame = cuts.get(name)
            if isinstance(frame, dict):
                families["describe_scene"].append(pick(frame, "describe_scene", f"replicate_{run_i}", name))

    source_records = {}
    for name, path in SOURCES.items():
        source_records[name] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "lock_audit": stable_gate(loaded[name]),
        }

    # Cardinality signatures must replicate across fresh workers for each case.
    stability = {}
    for family, rows in families.items():
        by_case: dict[str, list[str]] = {}
        for row in rows:
            case = row["frame_id"].split("/", 1)[1]
            signature = canonical({k: row[k] for k in (
                "frame_size", "internal_edge_count", "crossing_incidences",
                "distinct_external_units", "owned_induced_width_upper_bound",
                "crossing_edge_type_counts", "external_unit_type_histogram")})
            by_case.setdefault(case, []).append(signature)
        stability[family] = {
            "frame_records": len(rows),
            "case_replicates": {k: len(v) for k, v in sorted(by_case.items())},
            "signatures_identical_across_replicates": {
                k: len(set(v)) == 1 for k, v in sorted(by_case.items())
            },
        }

    output = {
        "schema_version": 1,
        "analysis_id": "frame_locality_contract_reanalysis_v1_20260928",
        "analysis_kind": "offline reanalysis of existing locked reports",
        "claim_boundary": "No new runtime executions; protocol-declared node cuts only; no natural-task prevalence or learned-partition claim.",
        "source_reports": source_records,
        "frames": [row for family in families.values() for row in family],
        "replication_audit": stability,
        "contract_field_audit": {
            "present_or_recoverable": [
                "runtime node frame size", "internal typed-edge count", "crossing typed-edge incidences",
                "crossing edge-type histogram", "aggregate external node-type histogram",
                "distinct external node count", "owned-induced-width upper bound where recorded",
                "whole-graph node/edge totals where recorded", "source report and worker lock provenance"
            ],
            "missing_from_selected_reports": [
                "boundary endpoint to external node-type mapping", "task-relevant state variables/attributes",
                "finite interface domain sizes", "complete operation/factor dependency graph",
                "decomposition width for that operation graph", "partition discovery and maintenance cost"
            ],
            "interpretation": "Raw boundary endpoints identify runtime node IDs and edge labels, while node types are supplied only as aggregate histograms. The reports do not define task variables/domains or complete operation dependency graphs, so these fields cannot be reconstructed by this analysis."
        },
    }
    if not all(s["lock_audit"]["source_lock_stable_each_run"] for s in source_records.values()):
        raise SystemExit("source lock changed within at least one captured run")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "families": {k: len(v) for k, v in families.items()},
        "replication_audit": stability,
        "source_lock_stable": True,
    }, indent=2))


if __name__ == "__main__":
    main()
