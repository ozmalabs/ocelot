#!/usr/bin/env python3
"""Source-locked field inventory for the thoughtexperiment fork boundary.

This is a fail-closed declaration census, not a proof that the documented
branch policies are semantically correct. New or removed Rust fields require
an explicit policy-map update before a capture can be emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "TypedGraph": ROOT / "runners/dsl/src/graph.rs",
    "Substrate": ROOT / "runners/dsl/src/substrate.rs",
}
POLICIES = {
    "TypedGraph": {
        "mutation_version": "branch_local_version",
        "mutation_log": "branch_local_observation",
        "edge_read_scope": "branch_local_derived_read_view",
        "nodes": "semantic_overlay_required",
        "node_freelist": "branch_local_allocator",
        "edges": "semantic_overlay_required",
        "edge_freelist": "branch_local_allocator",
        "edge_delete_generation": "branch_local_version",
        "edge_attrs": "semantic_overlay_required",
        "by_type": "derived_index_rebuild_or_overlay",
        "out": "derived_index_rebuild_or_overlay",
        "in_": "derived_index_rebuild_or_overlay",
        "out_by_type": "derived_index_rebuild_or_overlay",
        "out_by_type_target_index": "derived_index_rebuild_or_overlay",
        "in_by_type": "derived_index_rebuild_or_overlay",
        "edges_by_type": "derived_index_rebuild_or_overlay",
        "edge_delete_version_by_type": "branch_local_version",
        "attr_indices": "derived_index_rebuild_or_overlay",
        "pending_rule_edits": "empty_at_fork_branch_local_drain",
        "pending_rule_patches": "empty_at_fork_branch_local_drain",
        "pending_fb_samples": "empty_at_fork_branch_local_drain",
        "pending_track_identity": "empty_at_fork_branch_local_drain",
        "pending_net_collapses": "empty_at_fork_branch_local_drain",
        "attr_write_log": "empty_at_fork_branch_local_drain",
        "log_attr_writes": "branch_local_configuration",
    },
    "Substrate": {
        "graph": "semantic_overlay_required",
        "interner": "semantic_overlay_required_stable_symbol_namespace",
        "checker": "semantic_branch_copy_or_immutable_share",
        "terms": "semantic_overlay_required_stable_term_namespace",
        "concepts": "semantic_branch_copy_or_immutable_share",
        "counters": "branch_local_telemetry",
        "rules": "semantic_overlay_required",
        "next_rule_uid": "branch_local_allocator",
        "rule_firing_capture_active": "branch_local_observation",
        "pending_turn_last_progress_rule": "branch_local_observation",
        "rule_state_trace_config": "branch_local_configuration",
        "rule_state_trace_events": "branch_local_telemetry",
        "rule_state_trace_dropped": "branch_local_telemetry",
        "rule_edge_type_deps": "derived_rebuild_or_invalidate",
        "rule_readers_by_key": "derived_rebuild_or_invalidate",
        "rule_reads_any": "derived_rebuild_or_invalidate",
        "rule_has_where": "derived_rebuild_or_invalidate",
        "rule_dirty": "derived_rebuild_or_invalidate",
        "rule_cost_micros": "branch_local_telemetry",
        "rule_cost_count": "branch_local_telemetry",
        "rule_cost_progress": "branch_local_telemetry",
        "any_mutation": "branch_local_execution_state",
        "eval_cache": "derived_rebuild_or_invalidate",
        "rule_where_jit": "derived_rebuild_or_invalidate",
        "rule_cursors": "derived_rebuild_or_invalidate",
        "edge_delete_version": "branch_local_version",
        "gamma_epoch": "semantic_branch_local_version",
        "gamma_graph_root": "semantic_branch_local_reference",
        "shape_cache": "derived_rebuild_or_invalidate",
        "active_shape_target": "semantic_branch_local_value",
        "shape_pruned_count": "branch_local_telemetry",
        "framebuffers": "external_exclude_or_sandbox",
        "precise_dirty": "branch_local_configuration",
        "dirty_marks": "branch_local_telemetry",
        "dirty_telemetry": "branch_local_configuration",
        "dirty_overaggressive": "branch_local_configuration",
        "binding_projection": "branch_local_configuration",
        "projection_overaggressive": "branch_local_configuration",
        "empty_match_proof": "branch_local_configuration",
        "empty_match_proof_unsound": "branch_local_configuration",
        "empty_match_skips": "branch_local_telemetry",
        "incremental_match": "branch_local_configuration",
        "incremental_match_unsound": "branch_local_configuration",
        "predicate_retraction": "branch_local_configuration",
        "predicate_retraction_unsound": "branch_local_configuration",
        "rule_dirty_nodes": "derived_rebuild_or_invalidate",
        "rule_pred_retract_ok": "derived_rebuild_or_invalidate",
        "gamma_residual_capture": "branch_local_configuration",
        "gamma_residual_root": "branch_local_observation",
        "next_fb_id": "branch_local_allocator",
    },
}

FIELD_RE = re.compile(r"^\s{4}(?:pub(?:\([^)]*\))?\s+)?([A-Za-z_]\w*)\s*:")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def declared_fields(path: Path, struct_name: str) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    marker = f"pub struct {struct_name} {{"
    if text.count(marker) != 1:
        raise ValueError(f"expected one {marker!r} in {path}")
    start = text.index(marker) + len(marker)
    end = text.index("\n}", start)
    found = []
    for line_no, line in enumerate(text[start:end].splitlines(), text[:start].count("\n") + 1):
        match = FIELD_RE.match(line)
        if match:
            found.append({"name": match.group(1), "line": line_no})
    return found


def build_capture(runner: Path) -> dict[str, object]:
    structures = {}
    for name, path in SOURCES.items():
        fields = declared_fields(path, name)
        actual = {field["name"] for field in fields}
        expected = set(POLICIES[name])
        missing = sorted(actual - expected)
        stale = sorted(expected - actual)
        if missing or stale:
            raise ValueError(f"{name} policy mismatch; unclassified={missing}, removed={stale}")
        structures[name] = [
            {**field, "branch_policy": POLICIES[name][field["name"]]}
            for field in fields
        ]
    return {
        "schema": "ThoughtexperimentStateInventoryV1",
        "scope": "Rust struct field census; policy labels are an explicit design checklist, not semantic verification",
        "structures": structures,
        "field_counts": {name: len(fields) for name, fields in structures.items()},
        "inputs": {
            "runner_sha256": sha256(runner),
            **{f"{name.lower()}_source_sha256": sha256(path) for name, path in SOURCES.items()},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "evaluation/reports/thoughtexperiment_state_inventory_v1.json")
    args = parser.parse_args()
    result = build_capture(Path(__file__).resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out), "field_counts": result["field_counts"], "source_locks": result["inputs"]}, indent=2))


if __name__ == "__main__":
    main()
