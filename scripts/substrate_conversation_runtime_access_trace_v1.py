#!/usr/bin/env python3
"""Paired partial native access traces on conversation deliberation."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_conversation_runtime_access_trace_v1_20260925.json"
SIZES = (1, 2)
REPLICATES = 2
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_arm(size: int, replicate: int, trace_enabled: bool, scale_enabled: bool | None = None) -> dict:
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from domains.conversation_deliberation import materialize_deliberation
    from substrate_rs import _native
    import substrate_conversation_frame_scoped_scale_v1_1 as conversation_scale

    adapter = WorldAdapter(seeds=())
    adapter.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), adapter.agent)
    tasks = []
    for i in range(size):
        key = f"trace_rep{replicate}_frame_{i}"
        goal = adapter.s.add_node("Goal", {"kind": "answer", "status": "active", "frame_key": key})
        candidates = [
            {"candidate_id": f"{key}_repair", "kind": "repair", "grounding": 1.0,
             "expected_value": 0.55, "residual_cost": 0.1, "consequence": 0.2,
             "novelty": 0.1, "evidence_path": "goal->gap->repair"},
            {"candidate_id": f"{key}_answer", "kind": "answer", "grounding": 1.0,
             "expected_value": 0.8, "residual_cost": 0.1, "consequence": 0.5,
             "novelty": 0.2, "evidence_path": "goal->referent->fact"},
            {"candidate_id": f"{key}_unsupported", "kind": "answer", "grounding": 0.0,
             "expected_value": 1.0, "residual_cost": 0.0, "consequence": 1.0,
             "novelty": 1.0, "evidence_path": ""},
        ]
        deliberation = materialize_deliberation(adapter, goal=goal, candidates=candidates)
        microtheory = adapter.inner.add_node("Microtheory", {"name": key})
        owned = [goal, deliberation, *adapter.inner.neighbours(deliberation, "has_candidate")]
        for node in owned:
            adapter.inner.add_edge_unchecked(microtheory, "has_concept", node, {})
        tasks.append((key, deliberation))

    inner = adapter.inner
    if scale_enabled is None:
        scale_enabled = trace_enabled
    inner.runtime_access_trace_set_enabled(False)
    inner.runtime_access_trace_reset()
    inner.scale_audit_reset()
    inner.scale_audit_per_rule_reset()
    inner.scale_audit_set_enabled(scale_enabled)
    inner.scale_audit_set_per_rule_enabled(scale_enabled)
    inner.runtime_access_trace_set_enabled(trace_enabled)
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    outcome = inner.run_rules_report(CAP, False)
    wall_time_ns = time.perf_counter_ns() - wall_start
    cpu_time_ns = time.process_time_ns() - cpu_start
    progress = int(outcome["progress_steps"])
    terminal = int(inner.run_rules(1))
    projections = conversation_scale.projection(adapter, tasks)
    events, dropped = inner.runtime_access_trace_snapshot()
    global_counters = dict(inner.scale_audit_snapshot()) if scale_enabled else {}
    per_rule_raw = inner.scale_audit_per_rule_snapshot() if scale_enabled else []
    inner.runtime_access_trace_set_enabled(False)
    inner.scale_audit_set_per_rule_enabled(False)
    inner.scale_audit_set_enabled(False)

    access = inner.rule_access_sets()
    exported = inner.export_rules()
    static_by_uid = {}
    index_to_uid = {}
    for index, name, active, reads, term_edges, writes, reads_any, writes_any in access:
        uid = int(inner.rule_metadata(index)["rule_uid"])
        index_to_uid[int(index)] = uid
        static_by_uid[uid] = {
            "rule_name": name,
            "reads": sorted(set(reads) | set(term_edges)), "writes": sorted(set(writes)),
            "reads_any": bool(reads_any), "writes_any": bool(writes_any),
            "match_edge_count": len(exported[index]["match"]),
        }
    per_rule = {}
    for index, metric, count in per_rule_raw:
        uid = index_to_uid.get(int(index))
        if uid is not None:
            per_rule.setdefault(str(uid), {})[str(metric)] = int(count)

    rows = []
    mismatches = []
    for uid, kind, node, resource, peer, count in events:
        uid = int(uid)
        rule = static_by_uid.get(uid)
        row = {"rule_uid": uid, "rule_name": rule["rule_name"] if rule else None,
               "kind": kind, "node": node, "resource": resource, "peer": peer, "count": int(count)}
        rows.append(row)
        direction = None
        key = None
        if kind in ("pattern_edge", "term_edge_read"):
            direction, key = "read", f"edge:{resource}"
        elif kind in ("term_attr_read", "jit_attr_read"):
            direction, key = "read", f"attr:{resource}"
        elif kind == "jit_type_read":
            direction, key = "read", f"type:{resource}"
        elif kind == "term_type_read":
            direction, key = "read", f"type:{resource}"
        elif kind in ("term_index_query", "term_edge_attr_read"):
            direction, key = "read", f"attr:{resource}"
        elif kind == "effect_attr_write":
            direction, key = "write", f"attr:{resource}"
        elif kind in ("effect_edge_upsert", "effect_edge_delete", "effect_replace_edge"):
            direction, key = "write", f"edge:{resource}"
        elif kind == "effect_node_mint":
            direction, key = "write", f"type:{resource}"
        elif kind in ("effect_type_query", "effect_type_candidate_read"):
            direction, key = "read", f"type:{resource}"
        if rule and key:
            known = rule["reads"] if direction == "read" else rule["writes"]
            any_flag = rule["reads_any"] if direction == "read" else rule["writes_any"]
            if key not in known and not any_flag:
                mismatches.append({**row, "direction": direction, "key": key})

    observed_uids = {row["rule_uid"] for row in rows}
    trace_counts = {}
    for row in rows:
        key = (row["rule_uid"], row["kind"])
        trace_counts[key] = trace_counts.get(key, 0) + row["count"]
    coverage = []
    for uid in sorted(observed_uids):
        metrics = per_rule.get(str(uid), {})
        rule = static_by_uid[uid]
        counts = {
            "pattern_edge_events": trace_counts.get((uid, "pattern_edge"), 0),
            "accepted_bindings_times_pattern_arity": metrics.get("binding_leaves", 0) * rule["match_edge_count"],
            "term_attr_read_events": trace_counts.get((uid, "term_attr_read"), 0),
            "term_attr_evaluations": metrics.get("Attr", 0),
            "effect_attr_write_events": trace_counts.get((uid, "effect_attr_write"), 0),
            "effect_attr_write_attempts": metrics.get("effect_attr_set_attempts", 0),
            "effect_edge_upsert_events": trace_counts.get((uid, "effect_edge_upsert"), 0),
            "effect_edge_insert_attempts": metrics.get("effect_edge_insert_attempts", 0),
            "effect_node_mint_events": trace_counts.get((uid, "effect_node_mint"), 0),
            "effect_node_insertions": metrics.get("effect_node_inserts", 0),
        }
        coverage.append({"rule_uid": uid, "rule_name": rule["rule_name"], "counts": counts,
                         "pattern_edge_exact": counts["pattern_edge_events"] == counts["accepted_bindings_times_pattern_arity"],
                         "attr_read_exact": counts["term_attr_read_events"] == counts["term_attr_evaluations"],
                         "attr_write_exact": counts["effect_attr_write_events"] == counts["effect_attr_write_attempts"],
                         "edge_upsert_exact": counts["effect_edge_upsert_events"] == counts["effect_edge_insert_attempts"],
                         "node_mint_exact": counts["effect_node_mint_events"] == counts["effect_node_insertions"]})
    static_pairs = set()
    wildcard_pairs = set()
    for writer_uid in observed_uids:
        writer = static_by_uid[writer_uid]
        for reader_uid in observed_uids:
            reader = static_by_uid[reader_uid]
            if set(writer["writes"]) & set(reader["reads"]):
                static_pairs.add((writer_uid, reader_uid))
            if writer["writes_any"] or reader["reads_any"]:
                wildcard_pairs.add((writer_uid, reader_uid))
    static_pairs |= wildcard_pairs

    concrete_writes, concrete_reads = {}, {}
    for row in rows:
        kind = row["kind"]
        if kind == "effect_attr_write":
            key = ("attr", row["node"], row["resource"])
            concrete_writes.setdefault(key, set()).add(row["rule_uid"])
        elif kind in ("effect_edge_upsert", "effect_edge_delete", "effect_replace_edge"):
            key = ("edge", row["node"], row["resource"], row["peer"])
            concrete_writes.setdefault(key, set()).add(row["rule_uid"])
        elif kind in ("term_attr_read", "jit_attr_read"):
            key = ("attr", row["node"], row["resource"])
            concrete_reads.setdefault(key, set()).add(row["rule_uid"])
        elif kind in ("pattern_edge", "term_edge_read"):
            key = ("edge", row["node"], row["resource"], row["peer"])
            concrete_reads.setdefault(key, set()).add(row["rule_uid"])
    dynamic_pairs = {
        (writer_uid, reader_uid)
        for key, writers in concrete_writes.items()
        for writer_uid in writers
        for reader_uid in concrete_reads.get(key, set())
    }
    expected = all(row["status"] == "selected"
                   and row["selection"] == [f"{row['frame']}_answer"]
                   and row["candidates"][f"{row['frame']}_answer"]["status"] == "selected"
                   and row["candidates"][f"{row['frame']}_repair"]["status"] == "rejected"
                   and row["candidates"][f"{row['frame']}_unsupported"]["status"] == "rejected"
                   and row["candidates"][f"{row['frame']}_unsupported"]["reason"] == "missing_grounding_evidence"
                   for row in projections)
    return {
        "size": size, "replicate": replicate, "trace_enabled": trace_enabled,
        "progress": progress, "runner_status": str(outcome["status"]), "terminal_progress": terminal,
        "wall_time_ns": wall_time_ns, "cpu_time_ns": cpu_time_ns,
        "projections": projections, "expected_outcomes_pass": expected,
        "event_rows": rows, "event_total": sum(row["count"] for row in rows),
        "dropped_events": int(dropped), "static_resource_mismatches": mismatches,
        "instrumented_site_coverage": coverage,
        "observed_rule_count": len(observed_uids),
        "static_possible_pairs": len(static_pairs), "dynamic_concrete_pairs": len(dynamic_pairs),
        "static_pairs_unobserved": len(static_pairs - dynamic_pairs),
        "dynamic_pairs_outside_static": sorted([list(pair) for pair in dynamic_pairs - static_pairs]),
        "scale_audit": global_counters, "per_rule_audit": per_rule,
        "static_rules": [{"rule_uid": uid, **row} for uid, row in sorted(static_by_uid.items())],
    }


def main() -> None:
    cells = []
    for size in SIZES:
        for replicate in range(REPLICATES):
            plain = run_arm(size, replicate, False)
            traced = run_arm(size, replicate, True)
            cells.append({"size": size, "replicate": replicate, "plain": plain, "traced": traced,
                          "projection_match": plain["projections"] == traced["projections"],
                          "progress_match": plain["progress"] == traced["progress"],
                          "both_expected": plain["expected_outcomes_pass"] and traced["expected_outcomes_pass"],
                          "both_fixed_point": plain["runner_status"] == traced["runner_status"] == "fixed_point"
                          and plain["terminal_progress"] == traced["terminal_progress"] == 0})
    checks = {
        "all_paired_projections_match": all(cell["projection_match"] for cell in cells),
        "all_paired_progress_matches": all(cell["progress_match"] for cell in cells),
        "all_pairs_pass_expected_outcomes_and_fixed_point": all(
            cell["both_expected"] and cell["both_fixed_point"] for cell in cells),
        "trace_events_present_without_overflow": all(
            cell["traced"]["event_total"] > 0 and cell["traced"]["dropped_events"] == 0 for cell in cells),
        "no_observed_resource_false_negative_against_static": all(
            not cell["traced"]["static_resource_mismatches"] for cell in cells),
        "observed_dynamic_pairs_subset_static_projection": all(
            not cell["traced"]["dynamic_pairs_outside_static"] for cell in cells),
        "disabled_trace_emits_no_events": all(cell["plain"]["event_total"] == 0 for cell in cells),
    }
    extension = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    report = {
        "schema_version": 1,
        "run_id": "substrate-conversation-runtime-access-trace-v1-20260925",
        "scope": "native conversation_deliberation_phase4a rules; one/two generated deliberations; two fresh graph replicates per size; traced/untraced pairs",
        "claim_boundary": "Partial concrete access traces on one authored conversation rule family; no trace-completeness, overhead, cross-frame dependency, or partition-preservation claim.",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(extension), "native_extension_sha256": sha(extension),
            "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "source_sha256": {path: sha(ROOT / path) for path in (
                "runners/dsl/src/access_trace.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/term.rs",
                "runners/dsl/src/py.rs", "scripts/substrate_conversation_runtime_access_trace_v1.py",
                "scripts/substrate_conversation_frame_scoped_scale_v1_1.py",
                "domains/conversation_deliberation.py", "substrate/world_adapter.py")},
        },
        "checks": checks, "cells": cells,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "cells": len(cells),
                      "trace_event_total": sum(cell["traced"]["event_total"] for cell in cells),
                      "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("conversation access trace measurement failed")


if __name__ == "__main__":
    main()
