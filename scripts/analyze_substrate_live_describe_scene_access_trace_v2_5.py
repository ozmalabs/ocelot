#!/usr/bin/env python3
"""Source-current task-boundary and selected-access analysis for live describe_scene."""
from __future__ import annotations
import collections, hashlib, json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_5_workers_raw_20260929.json"
CAPTURE = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_5_20260929.json"
OUT = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_5_analysis_20260929.json"
LOCK = ROOT / "evaluation/substrate_capability/live_describe_scene_access_trace_v2_5_lock_20260929.json"
TRACE_SOURCE = ROOT / "runners/dsl/src/access_trace.rs"
PAIR_KINDS = {"pattern_edge", "effect_edge_upsert", "effect_edge_delete", "effect_replace_edge",
              "term_edge_read", "term_edge_attr_read"}
UNARY_KINDS = {"term_attr_read", "term_type_read", "effect_attr_write", "effect_attr_compare_read",
               "jit_attr_read", "jit_type_read", "effect_node_mint", "effect_node_delete",
               "effect_type_candidate_read", "effect_type_query"}
QUERY_KINDS = {"term_index_query"}
HOST_KINDS = {"term_tool_dispatch"}
OWNERSHIP_EDGE_TYPES = {"has_subgoal", "has_intent", "seeks_interpretation_shadow"}
PERSISTENT_EDGE_TYPES = {"has_self_concern", "has_gap_recurrence"}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def derive_descendants(run: dict, request: str) -> tuple[set[int], set[int], dict[int, str]]:
    mine = "a" if request == "request-A" else "b"
    boundary = run["task_boundaries"]
    rows = [x for x in run["access_trace"]["event_rows"] if x["request"] == request]
    minted = {int(x["node"]): str(x["resource"]) for x in rows
              if x["kind"] == "effect_node_mint" and x["node"] is not None}
    edges = [x for x in rows if x["kind"] == "effect_edge_upsert" and x["node"] is not None
             and x["peer"] is not None]
    owned = set(map(int, boundary[mine]["owned_node_ids"])) | set(map(int, boundary["shared_scene_input"]["owned_node_ids"]))
    descendants: set[int] = set()
    changed = True
    while changed:
        changed = False
        for row in edges:
            if row["resource"] not in OWNERSHIP_EDGE_TYPES:
                continue
            src, tgt = int(row["node"]), int(row["peer"])
            candidate = tgt if src in owned else src if tgt in owned and row["resource"] == "has_intent" else None
            if candidate in minted and candidate not in owned:
                owned.add(candidate); descendants.add(candidate); changed = True
    persistent = set()
    for row in edges:
        if row["resource"] in PERSISTENT_EDGE_TYPES:
            persistent.update(n for n in (int(row["node"]), int(row["peer"])) if n in minted)
    return descendants, persistent, minted

def access_partition(run: dict, request: str, descendants_by_request: dict[str, set[int]], persistent_by_request: dict[str, set[int]]) -> dict:
    mine = "a" if request == "request-A" else "b"
    other = "b" if mine == "a" else "a"
    boundaries = run["task_boundaries"]
    own = set(map(int, boundaries[mine]["owned_node_ids"])) | descendants_by_request[request]
    other_req = "request-B" if request == "request-A" else "request-A"
    other_nodes = set(map(int, boundaries[other]["owned_node_ids"])) | descendants_by_request[other_req]
    shared_input = set(map(int, boundaries["shared_scene_input"]["owned_node_ids"]))
    persistent = persistent_by_request[request]
    rows = [x for x in run["access_trace"]["event_rows"] if x["request"] == request]
    buckets = collections.Counter()
    by_kind = collections.defaultdict(collections.Counter)
    by_rule = collections.Counter()
    by_resource = collections.Counter()
    pair_cross = collections.Counter()
    unary_nodes: dict[str, set[int]] = collections.defaultdict(set)
    unknown = collections.Counter()
    for row in rows:
        count = int(row["count"]); kind = row["kind"]
        a = None if row["node"] is None else int(row["node"])
        b = None if row["peer"] is None else int(row["peer"])
        nodes = {n for n in (a, b) if n is not None}
        labels = []
        if nodes & own: labels.append("request_frame")
        if nodes & other_nodes: labels.append("other_request_frame")
        if nodes & shared_input: labels.append("shared_scene_input")
        if nodes & persistent: labels.append("persistent_shared_side_effect")
        buckets["+".join(labels) if labels else "external_or_unclassified"] += count
        by_kind["+".join(labels) if labels else "external_or_unclassified"][kind] += count
        by_rule[str(row.get("rule_name", row.get("rule_uid")))] += count
        by_resource[f"{kind}:{row['resource']}"] += count
        if kind in PAIR_KINDS:
            if a is None or b is None:
                unknown["pair_missing_endpoint"] += count
            elif (a in own and b in other_nodes) or (b in own and a in other_nodes):
                pair_cross["other_request"] += count
            elif (a in own) != (b in own) and not (a in shared_input or b in shared_input):
                pair_cross["external_or_global"] += count
            elif a in own and b in own and a != b:
                pair_cross["within_request"] += count
        elif kind in UNARY_KINDS:
            if a is None: unknown["unary_missing_node"] += count
            elif a in own: unary_nodes["request_frame"].add(a)
            elif a in shared_input: unary_nodes["shared_scene_input"].add(a)
            else: unary_nodes["external_or_global"].add(a)
        elif kind not in QUERY_KINDS | HOST_KINDS:
            unknown[f"unknown_kind:{kind}"] += count
    return {
        "request": request,
        "selected_event_total": sum(int(x["count"]) for x in rows),
        "events_by_node_class_touch": dict(sorted(buckets.items())),
        "event_kinds_by_node_class_touch": {k: dict(sorted(v.items())) for k, v in sorted(by_kind.items())},
        "pairwise_access_counts": dict(sorted(pair_cross.items())),
        "unique_unary_nodes_by_class": {k: len(v) for k, v in sorted(unary_nodes.items())},
        "global_index_query_count": sum(int(x["count"]) for x in rows if x["kind"] in QUERY_KINDS),
        "host_dispatch_count": sum(int(x["count"]) for x in rows if x["kind"] in HOST_KINDS),
        "unclassified_event_counts": dict(sorted(unknown.items())),
        "top_rules": [{"rule": k, "count": v} for k, v in by_rule.most_common(20)],
        "top_kind_resources": [{"kind_resource": k, "count": v} for k, v in by_resource.most_common(30)],
        "trace_event_rows": len(rows),
    }

def main() -> int:
    raw = json.loads(RAW.read_text()); capture = json.loads(CAPTURE.read_text())
    traces = [r for r in raw["runs"] if r["trace_enabled"]]
    source_text = TRACE_SOURCE.read_text()
    source_kinds = {"pattern_edge", "term_attr_read", "term_type_read", "effect_attr_write", "effect_edge_upsert",
                    "effect_edge_delete", "effect_node_mint", "effect_node_delete", "effect_type_query",
                    "effect_type_candidate_read", "effect_replace_edge", "jit_attr_read", "jit_type_read",
                    "term_edge_read", "term_edge_attr_read", "term_index_query", "effect_attr_compare_read",
                    "term_tool_dispatch"}
    observed = {x["kind"] for r in traces for x in r["access_trace"]["event_rows"]}
    checks = {
        "capture_gate_checks_pass": all(capture["checks"].values()),
        "three_distinct_traced_workers": len(traces) == 3 and len({r["pid"] for r in traces}) == 3,
        "source_locked_and_stable": capture["locked_inputs"] == capture["post_run_inputs"] and all(
            r["worker_started_inputs"] == r["worker_finished_inputs"] == capture["locked_inputs"] for r in raw["runs"]),
        "current_trace_source_matches_lock": capture["locked_inputs"]["source_sha256"]["native_access_trace"] == sha(TRACE_SOURCE),
        "zero_access_trace_drops": all(r["access_trace"]["dropped"] == 0 for r in traces),
        "observed_kinds_have_source_definitions": observed <= source_kinds and all(f'"{k}"' in source_text for k in observed),
        "request_intervals_nonempty_and_totals_reconcile": all(
            set(r["request_traces"]) == {"request-A", "request-B"}
            and sum(r["request_traces"][q]["event_count"] for q in ("request-A", "request-B")) == r["access_trace"]["event_count"]
            for r in traces),
        "trace_and_plain_semantic_parity": all(
            all(traced[key] == plain[key] for key in ("replies", "event_rows", "final", "whole_graph_semantic_sha256", "task_boundaries"))
            for traced, plain in ((next(r for r in raw["runs"] if r["replicate"] == rep and r["trace_enabled"]),
                                   next(r for r in raw["runs"] if r["replicate"] == rep and not r["trace_enabled"]))
                                  for rep in capture["schedule"])),
        "request_lifecycle_sets_disjoint": all(
            not (set(r["task_boundaries"]["a"]["owned_node_ids"]) & set(r["task_boundaries"]["b"]["owned_node_ids"]))
            for r in traces),
    }
    rows = []
    for run in traces:
        descendants = {}; persistent = {}; minted = {}
        for req in ("request-A", "request-B"):
            descendants[req], persistent[req], minted[req] = derive_descendants(run, req)
        for req in ("request-A", "request-B"):
            mine = "a" if req == "request-A" else "b"
            own_lifecycle = set(map(int, run["task_boundaries"][mine]["owned_node_ids"]))
            rows.append({"replicate": run["replicate"], "request": req,
                         "owned_lifecycle_nodes": len(own_lifecycle),
                         "task_owned_rule_descendants": len(descendants[req]),
                         "task_owned_descendants_by_type": dict(sorted(collections.Counter(minted[req][n] for n in descendants[req]).items())),
                         "persistent_shared_side_effect_nodes": len(persistent[req]),
                         "shared_scene_input_nodes": len(run["task_boundaries"]["shared_scene_input"]["owned_node_ids"]),
                         "base_lifecycle_graph_cut": {k: run["task_boundaries"][mine][k] for k in
                             ("owned_node_count", "internal_edge_count", "boundary_incidence_count", "boundary_unique_external_node_count",
                              "boundary_edge_type_counts", "boundary_external_node_type_counts", "owned_induced_treewidth_upper_bound")},
                         "selected_access": access_partition(run, req, descendants, persistent),
                         "task_descendant_edge_policy": {"owned": sorted(OWNERSHIP_EDGE_TYPES), "persistent": sorted(PERSISTENT_EDGE_TYPES)}})
    ownership_by_request = collections.defaultdict(list)
    for row in rows:
        ownership_by_request[row["request"]].append((row["task_owned_descendants_by_type"],
                                                       row["persistent_shared_side_effect_nodes"]))
    checks["repeated_semantic_ownership_sets_match"] = all(
        len(signatures) == 3 and all(sig == signatures[0] for sig in signatures[1:])
        for signatures in ownership_by_request.values())
    checks["access_class_counts_reconcile"] = all(
        sum(r["selected_access"]["events_by_node_class_touch"].values()) == r["selected_access"]["selected_event_total"] for r in rows)
    report = {"schema_version": 1, "run_id": "live-describe-scene-access-trace-v2.5-analysis-20260929",
              "raw_sha256": sha(RAW), "capture_summary_sha256": sha(CAPTURE),
              "capture_lock_sha256": sha(LOCK), "analysis_script_sha256": sha(Path(__file__).resolve()),
              "trace_source_sha256": sha(TRACE_SOURCE), "checks": checks, "all_checks_pass": all(checks.values()),
              "ownership_policy": "Request lifecycle nodes are reached through each exact inbound message's Goal relation; temporary rule-minted children connected through has_subgoal/has_intent/seeks_interpretation_shadow are task-owned; has_self_concern/has_gap_recurrence mints are persistent shared side effects; the Scene+Percept input remains a shared interface.",
              "claim_boundary": "Current-source paired capture of one production describe_scene route under one concurrent fixture; dynamic selected rule accesses are partial and not a complete task dependency graph or natural-task prevalence estimate.",
              "unmeasured_dependencies": ["receive-time and host callback work", "scheduler work outside selected native access events", "non-rule native work", "specialized graph scans and omitted access callsites", "factor scopes or inference semantics"],
              "rows": rows}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "row_count": len(rows), "all_checks_pass": report["all_checks_pass"]}, indent=2))
    return 0 if report["all_checks_pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
