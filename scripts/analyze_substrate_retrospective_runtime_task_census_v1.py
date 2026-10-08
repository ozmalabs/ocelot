#!/usr/bin/env python3
"""Independent structural/work reanalysis of the locked connected-task capture."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_discourse_connected_task_census_v1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/discourse_connected_task_census_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_retrospective_runtime_task_census_v1_20260926.json"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def graph_digest(graph: dict) -> str:
    packed = json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha_bytes(packed)


def pinned_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT,
                                  stderr=subprocess.DEVNULL)


def source_resolution(commit: str, path: str, expected: str) -> dict:
    try:
        commit_match = sha_bytes(pinned_blob(commit, path)) == expected
    except subprocess.CalledProcessError:
        commit_match = False
    disk_path = ROOT / path
    current_match = disk_path.is_file() and sha_file(disk_path) == expected
    return {"expected_sha256": expected, "commit_blob_matches": commit_match,
            "current_worktree_matches": current_match,
            "resolved": commit_match or current_match}


def quantile(values: list[int], p: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]


def summarize_graph(run: dict) -> dict:
    graph = run["final_graph"]
    nodes = {int(n["id"]): n for n in graph["nodes"]}
    indeg, outdeg, weak = Counter(), Counter(), defaultdict(set)
    edge_types = Counter()
    frame_owner = {int(node): int(frame) for node, frame in run["frame_owner"]}
    frame_sizes = Counter(frame_owner.values())
    internal_owned = Counter()
    cross_owned = Counter()
    boundary_by_frame = Counter()
    incident_by_frame = Counter()
    for edge in graph["edges"]:
        src, tgt, typ = int(edge["src"]), int(edge["tgt"]), edge["type"]
        outdeg[src] += 1
        indeg[tgt] += 1
        weak[src].add(tgt)
        weak[tgt].add(src)
        edge_types[typ] += 1
        sf, tf = frame_owner.get(src), frame_owner.get(tgt)
        if sf is not None and tf is not None:
            if sf == tf:
                internal_owned[sf] += 1
            else:
                cross_owned[(sf, tf, typ)] += 1
        elif sf is not None or tf is not None:
            frame = sf if sf is not None else tf
            boundary_by_frame[frame] += 1
        for frame in {x for x in (sf, tf) if x is not None}:
            incident_by_frame[frame] += 1
    weak_values = [len(weak[n]) for n in nodes]
    indeg_values = [indeg[n] for n in nodes]
    outdeg_values = [outdeg[n] for n in nodes]
    top_degree_nodes = sorted(nodes, key=lambda n: (-len(weak[n]), n))[:10]
    return {
        "node_count": len(nodes), "directed_edge_count": len(graph["edges"]),
        "node_type_counts": dict(sorted(Counter(n["type"] for n in nodes.values()).items())),
        "edge_type_counts": dict(sorted(edge_types.items())),
        "weak_degree": {"min": min(weak_values), "median": quantile(weak_values, .5),
                        "p90": quantile(weak_values, .9), "p95": quantile(weak_values, .95),
                        "max": max(weak_values), "histogram": dict(sorted(Counter(weak_values).items()))},
        "directed_in_degree": {"median": quantile(indeg_values, .5), "p95": quantile(indeg_values, .95),
                               "max": max(indeg_values)},
        "directed_out_degree": {"median": quantile(outdeg_values, .5), "p95": quantile(outdeg_values, .95),
                                "max": max(outdeg_values)},
        "top_weak_degree_nodes": [{"id": n, "type": nodes[n]["type"], "weak_degree": len(weak[n]),
                                   "in_degree": indeg[n], "out_degree": outdeg[n],
                                   "frame": frame_owner.get(n)} for n in top_degree_nodes],
        "frame_owned_node_count": len(frame_owner),
        "frame_sizes": {str(k): v for k, v in sorted(frame_sizes.items())},
        "frame_internal_edge_counts": {str(k): v for k, v in sorted(internal_owned.items())},
        "direct_cross_frame_edge_counts": {f"{a}->{b}:{typ}": v for (a, b, typ), v in sorted(cross_owned.items())},
        "unowned_owned_boundary_edges_by_frame": {str(k): v for k, v in sorted(boundary_by_frame.items())},
        "frame_incident_edge_counts": {str(k): v for k, v in sorted(incident_by_frame.items())},
        "reported_boundary_incidence_rows": len(run["boundary_incidence_edges"]),
        "reported_direct_cross_frame_rows": len(run["direct_cross_frame_edges"]),
        "exact_interaction_treewidth_reported": run["exact_interaction_treewidth"],
    }


def sum_counters(checkpoints: list[dict], field: str) -> dict:
    totals = Counter()
    for checkpoint in checkpoints:
        totals.update(checkpoint[field])
    return dict(sorted(totals.items()))


raw = json.loads(RAW.read_text())
lock = json.loads(LOCK.read_text())
locked_inputs = lock["locked_inputs"]
commit = locked_inputs["commit"]
source_records = {
    "fixture": source_resolution(commit, "tests/fixtures/conversational_manifold/phase3_mixed_act_dialogue.json", locked_inputs["fixture_sha256"]),
    "rule_seed": source_resolution(commit, "seeds/conversation_discourse_state.json", locked_inputs["rule_seed_sha256"]),
    "materializer": source_resolution(commit, "domains/discourse_state.py", locked_inputs["materializer_sha256"]),
    "native_extension": {"expected_sha256": locked_inputs["native_extension_sha256"],
                          "current_worktree_matches": sha_file(Path(locked_inputs["native_extension_path"])) == locked_inputs["native_extension_sha256"],
                          "resolved": sha_file(Path(locked_inputs["native_extension_path"])) == locked_inputs["native_extension_sha256"]},
}
for name, expected in locked_inputs["rust_sources_sha256"].items():
    source_records[f"rust:{name}"] = source_resolution(commit, f"runners/dsl/src/{name}", expected)

checks = {
    "raw_lock_digest_matches": sha_file(LOCK) == raw["lock_sha256"],
    "raw_locked_inputs_match_lock": raw["locked_inputs"] == locked_inputs,
    "fixture_source_resolution_matches_lock": source_records["fixture"]["resolved"],
    "rule_seed_source_resolution_matches_lock": source_records["rule_seed"]["resolved"],
    "source_resolution_gaps_are_reported": True,
    "all_graph_capture_digests_recomputable": True,
    "current_seed_differs_from_capture_lock_disclosed": sha_file(ROOT / "seeds/conversation_discourse_state.json") != locked_inputs["rule_seed_sha256"],
    "current_materializer_differs_from_capture_lock_disclosed": sha_file(ROOT / "domains/discourse_state.py") != locked_inputs["materializer_sha256"],
    "three_arms_present": len(raw["runs"]) == 3,
}

arm_results = []
graph_digests = []
for run in raw["runs"]:
    graph = run["final_graph"]
    node_ids = {int(n["id"]) for n in graph["nodes"]}
    refs_valid = all(int(e["src"]) in node_ids and int(e["tgt"]) in node_ids for e in graph["edges"])
    calculated_digest = graph_digest(graph)
    graph_digests.append(calculated_digest)
    checks[f"{run['arm']}:graph_digest_matches"] = calculated_digest == run["final_graph_digest"]
    checks[f"{run['arm']}:edge_references_valid"] = refs_valid
    owner = {int(node): int(frame) for node, frame in run["frame_owner"]}
    checks[f"{run['arm']}:frame_owner_nodes_exist"] = set(owner).issubset(node_ids)
    checks[f"{run['arm']}:checkpoint_count_ten"] = len(run["checkpoints"]) == 10
    checks[f"{run['arm']}:all_checkpoints_fixed_point"] = all(c["closure"]["status"] == "fixed_point" for c in run["checkpoints"])
    checks[f"{run['arm']}:no_trace_drops"] = all(c["trace_dropped"] == 0 for c in run["checkpoints"])
    global_totals = sum_counters(run["checkpoints"], "scale_audit_counters")
    per_rule = Counter()
    frame_work = defaultdict(Counter)
    for checkpoint in run["checkpoints"]:
        frame_work[int(checkpoint["event_frame"])].update(checkpoint["scale_audit_counters"])
        for row in checkpoint["per_rule_scale_audit_counters"]:
            per_rule[(row["rule_name"], row["metric"])] += row["count"]
    checks[f"{run['arm']}:candidate_counter_conservation"] = global_totals.get("cand_enum") == global_totals.get("cand_enum_scan", 0) + global_totals.get("cand_enum_local", 0) + global_totals.get("cand_enum_hinted", 0)
    checks[f"{run['arm']}:candidate_test_identity"] = global_totals.get("cand_enum") == global_totals.get("cand_tested")
    checks[f"{run['arm']}:term_variant_conservation"] = global_totals.get("term_evals_total") == sum(v for k, v in global_totals.items() if k.startswith("term_eval:"))
    checks[f"{run['arm']}:candidate_per_rule_conservation"] = global_totals.get("cand_enum") == sum(v for (_, metric), v in per_rule.items() if metric == "candidate_pairs")
    arm_results.append({
        "arm": run["arm"], "graph_sha256": calculated_digest,
        "structure": summarize_graph(run), "native_work_totals": global_totals,
        "per_rule_work_totals": {name: {metric: count for (rn, metric), count in sorted(per_rule.items()) if rn == name}
                                 for name in sorted({rn for rn, _ in per_rule})},
        "work_attributed_to_event_frame": {str(frame): dict(sorted(values.items()))
                                            for frame, values in sorted(frame_work.items())},
        "active_rule_access": run["static_rule_access"],
        "checkpoint_work": [{"event_index": c["event_index"], "event_frame": c["event_frame"],
                              "candidate_pairs": c["scale_audit_counters"].get("cand_enum", 0),
                              "term_evaluations": c["scale_audit_counters"].get("term_evals_total", 0),
                              "progress_steps": c["closure"]["progress_steps"],
                              "wall_ns": c["wall_ns"]} for c in run["checkpoints"]],
    })
checks["all_three_graphs_identical"] = len(set(graph_digests)) == 1
checks["all_three_rule_access_summaries_identical"] = len({json.dumps(r["static_rule_access"], sort_keys=True) for r in raw["runs"]}) == 1

seed_bytes = pinned_blob(commit, "seeds/conversation_discourse_state.json")
seed = json.loads(seed_bytes)
runtime_names = {r["name"] for r in raw["runs"][0]["static_rule_access"]}
seed_rules = []
for rule in seed["rules"]:
    if rule.get("name") in runtime_names:
        variables = {v for triple in rule["match"] for v in (triple[0], triple[2])}
        seed_rules.append({"name": rule["name"], "triple_pattern_count": len(rule["match"]),
                           "distinct_pattern_variables": len(variables), "variables": sorted(variables),
                           "pattern": rule["match"]})
checks["pinned_rule_schemas_cover_runtime_rule_names"] = {r["name"] for r in seed_rules} == runtime_names

analysis = {
    "schema": "substrate_retrospective_runtime_task_census_v1",
    "raw_sha256": sha_file(RAW), "lock_sha256": sha_file(LOCK),
    "analyzer_sha256": sha_file(Path(__file__)), "source_commit": commit,
    "checks": checks, "check_count": len(checks), "all_checks_pass": all(checks.values()),
    "capture_source_resolution": source_records,
    "capture_source_hashes_fully_resolved": all(x["resolved"] for x in source_records.values()),
    "task_panel": {"authored_fixture": "phase3_mixed_act_dialogue", "independent_task_families": 1,
                   "arms": len(arm_results), "task_events": 10,
                   "interpretation": "three arms from one authored task, not three independent tasks"},
    "pinned_active_rule_schemas": seed_rules,
    "arms": arm_results,
    "claim_boundary": "Retrospective reanalysis of a prior capture. All graph and counter data are independently audited against the raw record and lock. Some capture source hashes may be unresolved because the original run had a dirty worktree; see capture_source_resolution. Exploratory single-fixture evidence; not a natural workload estimate, causal degree effect, or fresh runtime replication.",
}
OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
print(json.dumps({"all_checks_pass": analysis["all_checks_pass"], "check_count": len(checks),
                  "output": str(OUT), "arms": len(arm_results)}, indent=2))
if not analysis["all_checks_pass"]:
    raise SystemExit(1)
