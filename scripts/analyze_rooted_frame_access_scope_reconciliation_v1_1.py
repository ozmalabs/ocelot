#!/usr/bin/env python3
"""Analyze static key concordance, concrete overlaps, and counter coverage."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/rooted_frame_access_scope_reconciliation_v1_1_20260928.json"
BASE = ROOT / "evaluation/reports/rooted_frame_proposal_panel_v1_1_20260928.json"
OUT = ROOT / "evaluation/reports/rooted_frame_access_scope_reconciliation_v1_1_analysis_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def requested_access(row: dict[str, Any]) -> tuple[str, str, str] | None:
    kind, resource = row["kind"], row.get("resource")
    if kind in ("pattern_edge", "term_edge_read") and resource is not None:
        return "read", f"edge:{resource}", "static_key"
    if kind in ("term_attr_read", "jit_attr_read") and resource is not None:
        return "read", f"attr:{resource}", "static_key"
    if kind in ("term_type_read", "jit_type_read", "effect_type_query", "effect_type_candidate_read") and resource is not None:
        return "read", f"type:{resource}", "static_key"
    if kind == "term_index_query" and resource is not None:
        return "read", f"attr:{resource}", "static_key_type_symbol_peer_unresolved"
    if kind == "term_edge_attr_read":
        return "read", None, "edge_attribute_scope_not_represented_by_static_keys"
    if kind == "effect_attr_write" and resource is not None:
        return "write", f"attr:{resource}", "static_key"
    if kind == "effect_attr_compare_read" and resource is not None:
        return "implicit_read", f"attr:{resource}", "compare_read_may_be_covered_by_write_key"
    if kind in ("effect_edge_upsert", "effect_edge_delete", "effect_replace_edge") and resource is not None:
        return "write", f"edge:{resource}", "static_key"
    if kind == "effect_node_mint" and resource is not None:
        return "write", f"type:{resource}", "static_key"
    if kind == "effect_node_delete":
        return None
    if kind == "term_tool_dispatch":
        return None
    return None


def static_match(row: dict[str, Any], rule: dict[str, Any]) -> str:
    mapped = requested_access(row)
    if mapped is None:
        return "uncheckable_no_resource_key"
    direction, key, category = mapped
    if key is None:
        return category
    reads = set(rule["reads"]) | set(rule["term_edge_reads"])
    writes = set(rule["writes"])
    if direction == "read":
        return "static_key_match" if key in reads else "static_read_wildcard" if rule["reads_any"] else "static_key_mismatch"
    if direction == "write":
        return "static_key_match" if key in writes else "static_write_wildcard" if rule["writes_any"] else "static_key_mismatch"
    if key in reads:
        return "implicit_read_explicitly_declared"
    if rule["reads_any"]:
        return "implicit_read_wildcard_declared"
    if key in writes or rule["writes_any"]:
        return "implicit_read_covered_by_static_write"
    return "implicit_read_not_declared"


def concrete_identity(row: dict[str, Any]) -> tuple[str, tuple] | None:
    kind, node, resource, peer = row["kind"], row.get("node"), row.get("resource"), row.get("peer")
    if kind in ("term_attr_read", "jit_attr_read", "effect_attr_write", "effect_attr_compare_read") and node is not None and resource is not None:
        return ("read" if kind != "effect_attr_write" else "write", ("attr", int(node), str(resource)))
    if kind in ("pattern_edge", "term_edge_read", "effect_edge_upsert", "effect_edge_delete", "effect_replace_edge") and node is not None and peer is not None and resource is not None:
        return ("read" if kind in ("pattern_edge", "term_edge_read") else "write", ("edge", int(node), str(resource), int(peer)))
    return None


def analyze_turn(turn: dict[str, Any]) -> dict[str, Any]:
    rows = turn["trace_rows"]
    rules = {int(rule["rule_uid"]): rule for rule in turn["static_rules_for_observed_uids"]}
    static_categories = Counter()
    static_mismatches = []
    mapped_rows = []
    per_uid_trace: dict[int, Counter] = {}
    trace_by_uid_kind = Counter()
    read_identities: dict[tuple, set[int]] = {}
    write_identities: dict[tuple, set[int]] = {}
    for row in rows:
        uid, kind, count = int(row["rule_uid"]), str(row["kind"]), int(row["count"])
        trace_by_uid_kind[(uid, kind)] += count
        per_uid_trace.setdefault(uid, Counter())[kind] += count
        rule = rules.get(uid)
        category = "uid_unresolved" if rule is None else static_match(row, rule)
        static_categories[category] += count
        if category == "static_key_mismatch" or category == "implicit_read_not_declared":
            static_mismatches.append({"rule_uid": uid, "rule_name": rule["rule_name"] if rule else None,
                                      "kind": kind, "resource": row.get("resource"), "count": count,
                                      "category": category})
        mapped_rows.append({"rule_uid": uid, "kind": kind, "count": count, "static_category": category})
        identity = concrete_identity(row)
        if identity:
            direction, key = identity
            target = read_identities if direction == "read" else write_identities
            target.setdefault(key, set()).add(uid)
    observed_uids = set(rules)
    implicit_reads: dict[int, set[str]] = {}
    for row in rows:
        if row["kind"] == "effect_attr_compare_read" and row.get("resource") is not None:
            implicit_reads.setdefault(int(row["rule_uid"]), set()).add(f"attr:{row['resource']}")
    static_pairs = set()
    for writer_uid, writer in rules.items():
        writes = set(writer["writes"])
        for reader_uid, reader in rules.items():
            reads = set(reader["reads"]) | set(reader["term_edge_reads"]) | implicit_reads.get(reader_uid, set())
            if writes & reads or writer["writes_any"] or reader["reads_any"]:
                static_pairs.add((writer_uid, reader_uid))
    dynamic_pairs = set()
    for key, writers in write_identities.items():
        for reader_uid in read_identities.get(key, set()):
            for writer_uid in writers:
                dynamic_pairs.add((writer_uid, reader_uid))
    scale = turn["per_rule_scale_audit_counters"]
    counter_rows = []
    for uid in sorted(observed_uids):
        rule = rules[uid]
        metrics = {str(k): int(v) for k, v in scale.get(str(uid), {}).items()}
        counts = {
            "pattern_edge_trace": int(trace_by_uid_kind[(uid, "pattern_edge")]),
            "binding_leaves_times_match_edges": metrics.get("binding_leaves", 0) * int(rule["match_edge_count"]),
            "term_attr_read_trace": int(trace_by_uid_kind[(uid, "term_attr_read")]),
            "Attr_evaluations": metrics.get("Attr", 0),
            "effect_attr_write_trace": int(trace_by_uid_kind[(uid, "effect_attr_write")]),
            "effect_attr_set_attempts": metrics.get("effect_attr_set_attempts", 0),
            "effect_edge_upsert_trace": int(trace_by_uid_kind[(uid, "effect_edge_upsert")]),
            "effect_edge_insert_attempts": metrics.get("effect_edge_insert_attempts", 0),
        }
        counter_rows.append({
            "rule_uid": uid,
            "rule_name": rule["rule_name"],
            "counts": counts,
            "pattern_edge_conserved": counts["pattern_edge_trace"] == counts["binding_leaves_times_match_edges"],
            "term_attr_read_conserved": counts["term_attr_read_trace"] == counts["Attr_evaluations"],
            "effect_attr_write_conserved": counts["effect_attr_write_trace"] == counts["effect_attr_set_attempts"],
            "effect_edge_upsert_conserved": counts["effect_edge_upsert_trace"] == counts["effect_edge_insert_attempts"],
        })
    return {
        "turn": int(turn["turn"]),
        "prompt": turn["prompt"],
        "trace_rows": len(rows),
        "weighted_trace_events": int(turn["weighted_trace_event_count"]),
        "observed_rule_uids": len(observed_uids),
        "unresolved_rule_uids": turn["observed_uid_static_resolution"],
        "static_event_class_counts_weighted": dict(sorted(static_categories.items())),
        "static_key_mismatches": static_mismatches,
        "static_mismatch_event_weight": sum(x["count"] for x in static_mismatches),
        "concrete_read_identity_count": len(read_identities),
        "concrete_write_identity_count": len(write_identities),
        "concrete_dependency_pairs": len(dynamic_pairs),
        "static_possible_pairs_among_observed_rules": len(static_pairs),
        "dynamic_pairs_outside_static_projection": sorted([list(p) for p in dynamic_pairs - static_pairs]),
        "static_pairs_without_observed_concrete_overlap": len(static_pairs - dynamic_pairs),
        "site_counter_rows": counter_rows,
    }


def main() -> None:
    raw = json.loads(RAW.read_text())
    base = json.loads(BASE.read_text())
    checks = dict(raw.get("checks", {}))
    checks["accepted_baseline_hash_matches"] = raw.get("baseline_v1_1_sha256") == sha(BASE)
    checks["three_replicate_semantic_parity_to_baseline"] = True
    by_replicate = {int(run["replicate"]): run for run in raw["runs"]}
    base_by_replicate = {int(run["replicate"]): run for run in base["runs"]}
    replay_groups = []
    semantic_task_parity = True
    for replicate, run in sorted(by_replicate.items()):
        baseline = base_by_replicate.get(replicate)
        semantic_match = baseline is not None and run["whole_graph_semantic_sha256"] == baseline["whole_graph_semantic_sha256"]
        checks["three_replicate_semantic_parity_to_baseline"] &= semantic_match
        task_match = baseline is not None and all(
            run["turns"][i]["reply_nonempty"] == baseline["turns"][i]["reply_nonempty"]
            and run["turns"][i]["route"] == baseline["turns"][i]["route"]
            and run["turns"][i]["goal_count"] == baseline["turns"][i]["goal_count"]
            for i in (0, 1)
        )
        semantic_task_parity &= task_match
        replay_groups.append({
            "replicate": replicate,
            "semantic_graph_matches_baseline": semantic_match,
            "trace_rows_match_baseline": None,
            "turns": [analyze_turn(turn) for turn in run["turns"]],
        })
    counter_equations_all_exact = all(
        row[key]
        for group in replay_groups for turn in group["turns"] for row in turn["site_counter_rows"]
        for key in ("pattern_edge_conserved", "term_attr_read_conserved", "effect_attr_write_conserved", "effect_edge_upsert_conserved")
    )
    checks["static_access_records_resolve_all_trace_uids"] = all(
        not turn["unresolved_rule_uids"] for group in replay_groups for turn in group["turns"]
    )
    corrected_trace_signatures = [
        hashlib.sha256(json.dumps([t["trace_rows"] for t in run["turns"]], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        for run in sorted(by_replicate.values(), key=lambda item: int(item["replicate"]))
    ]
    checks["corrected_trace_parity_across_workers"] = len(set(corrected_trace_signatures)) == 1
    checks["scope_isolation_control"] = bool(raw.get("scope_isolation_control", {}).get("passed"))
    checks["semantic_task_parity_to_baseline"] = semantic_task_parity
    analysis = {
        "analysis_id": "rooted_frame_access_scope_reconciliation_v1_1_analysis_20260928",
        "raw_sha256": sha(RAW),
        "accepted_baseline_sha256": sha(BASE),
        "checks": checks,
        "all_static_resource_keys_concordant": all(
            turn["static_mismatch_event_weight"] == 0 for group in replay_groups for turn in group["turns"]
        ),
        "exploratory_counter_equations_all_exact": counter_equations_all_exact,
        "all_dynamic_concrete_pairs_in_static_projection": all(
            not turn["dynamic_pairs_outside_static_projection"] for group in replay_groups for turn in group["turns"]
        ),
        "replays": replay_groups,
        "claim_boundary": "Corrected trace-scope isolation and selected static/dynamic access reconciliation on one authored two-prompt task pair. Static concordance is not trace completeness; unobserved overlap is not independence; no causal necessity or frame safety is inferred. Counter equations are descriptive, not integrity gates.",
    }
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT),
        "checks": checks,
        "all_static_resource_keys_concordant": analysis["all_static_resource_keys_concordant"],
        "all_dynamic_concrete_pairs_in_static_projection": analysis["all_dynamic_concrete_pairs_in_static_projection"],
    }, indent=2))
    if not all(checks.values()):
        raise SystemExit("access-scope independent analysis failed an integrity/counter gate")


if __name__ == "__main__":
    main()
