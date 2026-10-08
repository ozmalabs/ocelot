#!/usr/bin/env python3
"""Independent graph/trace reconstruction for anaphora boundary capture v1."""
from __future__ import annotations
import hashlib, json, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/anaphora_operation_boundary_capture_v1_1_raw_20260929.json"
OUT = ROOT / "evaluation/reports/anaphora_operation_boundary_capture_v1_1_analysis_20260929.json"
SUITE_PATH = ROOT / "evaluation/substrate_capability/anaphora_independent_task_suite_v1.json"
SUITE = json.loads(SUITE_PATH.read_text())["cases"]
TASKS = {x["case_id"]: x for x in SUITE}
GLOBAL_TYPES = {"Agent", "Concept", "CommonGround", "DiscourseState", "Interlocutor",
                "LexicalEntry", "Microtheory", "Rule", "Seed", "SeedSummary"}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def elimination(nodes, edges):
    graph = {int(n): set() for n in nodes}
    for a, b in edges:
        if a in graph and b in graph and a != b:
            graph[a].add(b); graph[b].add(a)
    width, order = 0, []
    while graph:
        def score(n):
            ns = sorted(graph[n])
            fill = sum(1 for i, a in enumerate(ns) for b in ns[i+1:] if b not in graph[a])
            return fill, len(ns), n
        node = min(graph, key=score)
        neighbours = set(graph[node]); width = max(width, len(neighbours)); order.append(node)
        for a in neighbours:
            graph[a].update(neighbours - {a}); graph[a].discard(node)
        del graph[node]
    return width, order

def relation_score(reference, candidate, nodes):
    tp = fp = fn = 0
    nodes = sorted(nodes)
    for i, a in enumerate(nodes):
        for b in nodes[i+1:]:
            truth = reference[a] == reference[b]
            pred = candidate[a] == candidate[b]
            if truth and pred: tp += 1
            elif pred: fp += 1
            elif truth: fn += 1
    return {"same_frame_tp": tp, "same_frame_fp": fp, "same_frame_fn": fn,
            "same_frame_precision": tp/(tp+fp) if tp+fp else None,
            "same_frame_recall": tp/(tp+fn) if tp+fn else None}

def partition_metrics(graph, owner, trace_rows, mapping, width=None):
    owners = {int(n): int(f) for n, f in mapping.items()}
    nodes = set(owners)
    state_cross = state_global = 0
    boundary_ids = set()
    edge_rows = graph.get("edges", [])
    for edge in edge_rows:
        a, b = int(edge["src"]), int(edge["tgt"])
        if a in nodes and b in nodes:
            if owners[a] != owners[b]:
                state_cross += 1; boundary_ids.update((a, b))
        elif (a in nodes) != (b in nodes):
            state_global += 1; boundary_ids.update((b if a in nodes else a, a if a in nodes else b))
    trace_cross = trace_global = trace_unresolved = trace_total = 0
    trace_boundary_ids = set()
    for row in trace_rows:
        _, _, node, _, peer, count = row
        count = int(count); trace_total += count
        endpoints = [None if node is None else int(node), None if peer is None else int(peer)]
        known = [x for x in endpoints if x is not None]
        if len(known) < 2:
            trace_unresolved += count
        a, b = endpoints
        if a in nodes and b in nodes and owners[a] != owners[b]:
            trace_cross += count; trace_boundary_ids.update((a, b))
        elif (a in nodes) != (b in nodes):
            trace_global += count; trace_boundary_ids.add(b if a in nodes else a)
    return {"state_edge_count": len(edge_rows), "cross_frame_state_edge_count": state_cross,
            "global_boundary_state_incidence_count": state_global,
            "unique_state_boundary_nodes": len(boundary_ids),
            "trace_event_count": trace_total, "cross_frame_trace_count": trace_cross,
            "global_boundary_trace_count": trace_global,
            "unresolved_trace_endpoint_count": trace_unresolved,
            "unique_trace_boundary_nodes": len(trace_boundary_ids),
            "dependency_induced_width_upper_bound": width,
            **relation_score(owner, owners, nodes)}

def analyze_run(case_id, pair):
    traced = pair["trace"]
    owner = {int(n): int(f) for n, f in traced["frame_owner"]}
    checkpoints = []
    for checkpoint in traced["checkpoints"]:
        graph = checkpoint["graph"]
        graph_node_ids = {int(n["id"]) for n in graph["nodes"]}
        current_owner = {n: f for n, f in owner.items() if n in graph_node_ids}
        sizes = [sum(f == turn["turn_index"] for f in current_owner.values())
                 for turn in traced["turns"] if any(v == turn["turn_index"] for v in current_owner.values())]
        nodes = sorted(current_owner)
        dep_edges = set()
        for row in checkpoint["trace_rows"]:
            _, _, a, _, b, _ = row
            if a is not None and b is not None and int(a) in current_owner and int(b) in current_owner and int(a) != int(b):
                dep_edges.add(tuple(sorted((int(a), int(b)))))
        for edge in graph["edges"]:
            a, b = int(edge["src"]), int(edge["tgt"])
            if a in current_owner and b in current_owner and a != b:
                dep_edges.add(tuple(sorted((a, b))))
        dep_width, order = elimination(nodes, dep_edges)
        authored = dict(current_owner)
        sorted_sizes = sorted(sizes, reverse=True)
        balanced = {}; cursor = 0
        for frame, size in enumerate(sorted_sizes):
            for node in nodes[cursor:cursor+size]: balanced[node] = frame
            cursor += size
        minfill = {}; cursor = 0
        for frame, size in enumerate(sorted_sizes):
            for node in order[cursor:cursor+size]: minfill[node] = frame
            cursor += size
        trace_rows = checkpoint["trace_rows"]
        arms = {}
        for name, mapping in (("authored_turn", authored), ("balanced_stable_id", balanced),
                              ("dependency_min_fill", minfill)):
            arms[name] = partition_metrics(graph, current_owner, trace_rows, mapping,
                                           dep_width if name == "dependency_min_fill" else None)
        type_by_id = {int(n["id"]): str(n["type"]) for n in graph["nodes"]}
        owner_valid = all(n in type_by_id and type_by_id[n] not in GLOBAL_TYPES for n in current_owner)
        active = [r for r in traced["static_rule_access"] if r["active"]]
        checkpoints.append({"turn_index": checkpoint["turn_index"],
                            "node_count": checkpoint["node_count"], "edge_count": checkpoint["edge_count"],
                            "owned_task_nodes": len(current_owner), "frame_sizes": sizes,
                            "global_node_count": len(type_by_id)-len(current_owner),
                            "active_rule_count": len(active),
                            "active_wildcard_reader_count": sum(bool(r["reads_any"]) for r in active),
                            "active_wildcard_writer_count": sum(bool(r["writes_any"]) for r in active),
                            "static_read_key_count": sum(len(r["reads"]) for r in active),
                            "static_write_key_count": sum(len(r["writes"]) for r in active),
                            "trace_dropped": checkpoint["trace_dropped"],
                            "owner_types_valid": owner_valid, "partition_arms": arms,
                            "dependency_order": order, "dependency_edge_count": len(dep_edges),
                            "dependency_width": dep_width})
    return checkpoints

def analyze(raw):
    runs = [r for r in raw["runs"] if "worker_error" not in r]
    pids = [r["worker"]["pid"] for r in runs]
    case_ids = list(TASKS)
    checks = {
        "ten_worker_rows": len(raw["runs"]) == 10 and len(runs) == 10,
        "ten_distinct_processes": len(set(pids)) == 10,
        "source_lock_stable": raw.get("post_run_inputs") == raw.get("locked_inputs")
            and all(r.get("before") == r.get("after") == raw["locked_inputs"] for r in runs),
        "complete_case_order": all([p["case_id"] for p in r["worker"]["pairs"]] == case_ids for r in runs),
        "plain_trace_final_graph_parity": all(p["plain"]["final_graph_sha256"] == p["trace"]["final_graph_sha256"]
                                               for r in runs for p in r["worker"]["pairs"]),
        "plain_trace_checkpoint_parity": all(
            [x["graph_sha256"] for x in p["plain"]["checkpoints"]] ==
            [x["graph_sha256"] for x in p["trace"]["checkpoints"]]
            for r in runs for p in r["worker"]["pairs"]),
        "all_frozen_task_oracles_pass": all(p[a]["task_oracle_pass"] for r in runs
                                             for p in r["worker"]["pairs"] for a in ("plain", "trace")),
        "trace_drops_zero": all(cp["trace_dropped"] == 0 for r in runs for p in r["worker"]["pairs"]
                                 for cp in p["trace"]["checkpoints"]),
        "turn_owner_maps_complete_and_disjoint": all(
            len(dict(p["trace"]["frame_owner"])) == len(p["trace"]["frame_owner"])
            and all(n in {int(x["id"]) for x in p["trace"]["checkpoints"][-1]["graph"]["nodes"]}
                    for n, _ in p["trace"]["frame_owner"])
            and set(dict(p["trace"]["frame_owner"])) ==
                {int(n) for turn in p["trace"]["turns"] for n in turn["owned_node_ids"]}
            and all(mid in dict(p["trace"]["frame_owner"]) for mid in p["trace"]["frame_message_ids"])
            for r in runs for p in r["worker"]["pairs"]),
        "graph_snapshots_match_digests": all(
            hashlib.sha256(json.dumps(cp["graph"], sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
            == cp["graph_sha256"] for r in runs for p in r["worker"]["pairs"]
            for cp in p["trace"]["checkpoints"]),
    }
    derived = {}
    for case_id in case_ids:
        all_cp = []
        for r in runs:
            pair = next(p for p in r["worker"]["pairs"] if p["case_id"] == case_id)
            all_cp.append(analyze_run(case_id, pair))
        turns = len(TASKS[case_id]["turns"])
        by_turn = []
        for ti in range(turns):
            rows = [cp[ti] for cp in all_cp]
            arms = {}
            for arm in ("authored_turn", "balanced_stable_id", "dependency_min_fill"):
                fields = ("cross_frame_state_edge_count", "global_boundary_state_incidence_count",
                          "cross_frame_trace_count", "global_boundary_trace_count",
                          "unresolved_trace_endpoint_count", "unique_state_boundary_nodes",
                          "unique_trace_boundary_nodes", "same_frame_precision", "same_frame_recall")
                arms[arm] = {field: (round(statistics.median([x["partition_arms"][arm][field] for x in rows]), 4)
                                     if any(x["partition_arms"][arm][field] is not None for x in rows) else None)
                             for field in fields}
            by_turn.append({"turn_index": ti,
                            "median_full_graph_nodes": int(statistics.median(x["node_count"] for x in rows)),
                            "median_full_graph_edges": int(statistics.median(x["edge_count"] for x in rows)),
                            "median_owned_nodes": int(statistics.median(x["owned_task_nodes"] for x in rows)),
                            "median_frame_sizes": rows[0]["frame_sizes"],
                            "median_dependency_edges": int(statistics.median(x["dependency_edge_count"] for x in rows)),
                            "median_dependency_width": int(statistics.median(x["dependency_width"] for x in rows)),
                            "active_wildcard_rules": {"readers": int(statistics.median(x["active_wildcard_reader_count"] for x in rows)),
                                                       "writers": int(statistics.median(x["active_wildcard_writer_count"] for x in rows))},
                            "partition_arms": arms,
                            "all_trace_drops_zero": all(x["trace_dropped"] == 0 for x in rows),
                            "all_owned_types_valid": all(x["owner_types_valid"] for x in rows)})
        derived[case_id] = {"worker_count": len(all_cp), "checkpoints": by_turn}
    payload = {"schema_version": 1, "run_id": "anaphora-operation-boundary-capture-v1-20260929",
               "raw_sha256": sha(RAW), "suite_sha256": sha(SUITE_PATH), "checks": checks,
               "case_summaries": derived,
               "scoped_execution_status": "unsupported_generic_message_scope",
               "unmeasured_dependencies": ["receive-time effects", "Python parsing and host callbacks",
                    "scheduler work outside comprehension trace", "trace-omitted native accesses",
                    "factor scopes and inference domains"],
               "claim_boundary": "Protocol-owned message-turn nodes in one assistant-authored anaphora family; graph and partial runtime-access cuts only, not learned frames or safe partitioned execution."}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "case_count": len(derived), "scoped_execution_status": payload["scoped_execution_status"]}, indent=2))
    return all(checks.values())

if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW
    raw = json.loads(source.read_text())
    if source != RAW: RAW = source
    raise SystemExit(0 if analyze(raw) else 1)
