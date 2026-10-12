#!/usr/bin/env python3
"""Analyze semantic, task-oracle, and wire-order parity for mixed-act replay."""
from __future__ import annotations
import json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/thoughtexperiment_receipt_edge_order_diagnostic_v1_raw_20261001.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_receipt_edge_order_diagnostic_v1_analysis_20261001.json"
ARMS = ("direct", "eager_receipt", "shared_snapshot_receipt")
EXPECTED_GOALS = [{"status": "resolved", "transition_event_indices": [1, 2, 3]},
                  {"status": "resolved", "transition_event_indices": [6, 7, 8]}]
EXPECTED_GROUNDS = [["calendar_checked", "location_shared"],
                    ["calendar_request", "calendar_shared"]]

def main() -> int:
    capture = json.loads(RAW.read_text())
    runs = capture.get("runs", [])
    if capture.get("schema") != "ReceiptEdgeOrderDiagnosticV1Capture" or len(runs) != 8:
        raise SystemExit("capture schema or worker count mismatch")
    lock = capture["locked_inputs"]
    if capture["post_run_inputs"] != lock or len({r["pid"] for r in runs}) != 8:
        raise SystemExit("worker identity or source stability gate failed")
    route_ms = {arm: [] for arm in ARMS}
    stages = {arm: {} for arm in ARMS}
    order = {arm: {"event_state_comparisons": 0, "edge_slab_mismatches": 0,
                   "incident_edge_state_mismatches": 0, "incident_node_bucket_comparisons": 0,
                   "incident_node_bucket_mismatches": 0, "typed_neighbor_bucket_comparisons": 0,
                   "typed_neighbor_bucket_mismatches": 0, "first_edge_divergence": None,
                   "first_incident_divergence": None, "first_typed_neighbor_divergence": None}
             for arm in ARMS if arm != "direct"}
    receipts = {arm: {"receipt_count": 0, "nonempty_receipt_count": 0,
                      "total_effect_count": 0}
                for arm in ARMS if arm != "direct"}
    for run in runs:
        if run["before"] != lock or run["after"] != lock:
            raise SystemExit(f"source lock drift in rep {run['replicate']}")
        eps = {e["arm"]: e for e in run["episodes"]}
        if set(eps) != set(ARMS) or run["arm_order"] != [e["arm"] for e in run["episodes"]]:
            raise SystemExit("arm schedule incomplete")
        direct = eps["direct"]
        for arm, ep in eps.items():
            if ep["pid"] != run["pid"] or ep["replicate"] != run["replicate"]:
                raise SystemExit("episode/worker identity mismatch")
            if ep["loaded_seed_ids"] != direct["loaded_seed_ids"]:
                raise SystemExit("loaded seed identity differs across arms")
            if ep["active_lifecycle_rules"] != ["discourse_goal_execute", "discourse_goal_resolve",
                                                  "discourse_goal_select"]:
                raise SystemExit(f"active discourse-rule gate failed: {ep['active_lifecycle_rules']}")
            if len(ep["event_ids"]) != 10 or ep["event_ids"] != direct["event_ids"]:
                raise SystemExit("event identity/coverage mismatch")
            if ep["goal_ids"] != direct["goal_ids"] or len(ep["goal_ids"]) != 2:
                raise SystemExit("goal identity/coverage mismatch")
            normalized_goals = [{"status": g["status"],
                                 "transition_event_indices": g["transition_event_indices"]}
                                for g in ep["goals"]]
            if normalized_goals != EXPECTED_GOALS:
                raise SystemExit(f"mixed-act lifecycle oracle failed: {normalized_goals}")
            if ep["common_grounds"] != EXPECTED_GROUNDS:
                raise SystemExit(f"common-ground oracle failed: {ep['common_grounds']}")
            if ep["final_state_attrs"].get("expectation_disposition") != "deferred" or \
                    ep["final_state_attrs"].get("unresolved_residuals") != ["location_unresolved"]:
                raise SystemExit("epistemic-limit/deferred residual oracle failed")
            if ep["terminal_progress_steps"] != 0 or not ep["terminal_graph_unchanged"]:
                raise SystemExit(f"terminal fixed-point gate failed for {arm}")
            if arm != "direct" and (ep["terminal_receipt_counts"] is None or
                                      any(ep["terminal_receipt_counts"].values())):
                raise SystemExit("terminal receipt should be empty")
            if len(ep["per_event_states"]) != 10 or \
                    len(ep["per_event_states"]) != len(direct["per_event_states"]):
                raise SystemExit("per-event state coverage mismatch")
            for a, b in zip(direct["per_event_states"], ep["per_event_states"]):
                if a["event_index"] != b["event_index"] or \
                        a["canonical_graph_sha256"] != b["canonical_graph_sha256"] or \
                        a["settlement_progress_steps"] != b["settlement_progress_steps"] or \
                        a["goals"] != b["goals"]:
                    raise SystemExit(f"per-event semantic parity failed: rep={run['replicate']} arm={arm}")
                if arm != "direct":
                    o = order[arm]
                    o["event_state_comparisons"] += 1
                    edge_a, edge_b = a["edge_order"], b["edge_order"]
                    if edge_a != edge_b:
                        o["edge_slab_mismatches"] += 1
                        if o["first_edge_divergence"] is None:
                            pos = next((i for i, (x, y) in enumerate(zip(edge_a, edge_b)) if x != y),
                                       min(len(edge_a), len(edge_b)))
                            o["first_edge_divergence"] = {
                                "replicate": run["replicate"], "event_index": a["event_index"],
                                "position": pos, "direct_length": len(edge_a), "receipt_length": len(edge_b),
                                "direct_window": edge_a[max(0, pos-2):pos+3],
                                "receipt_window": edge_b[max(0, pos-2):pos+3]}
                    inc_a = {int(n): edges for n, edges in a["incident_order"]}
                    inc_b = {int(n): edges for n, edges in b["incident_order"]}
                    inc_bad = False
                    for node in sorted(set(inc_a) | set(inc_b)):
                        o["incident_node_bucket_comparisons"] += 1
                        if inc_a.get(node, []) != inc_b.get(node, []):
                            o["incident_node_bucket_mismatches"] += 1
                            inc_bad = True
                            if o["first_incident_divergence"] is None:
                                o["first_incident_divergence"] = {
                                    "replicate": run["replicate"], "event_index": a["event_index"],
                                    "node_id": node, "direct": inc_a.get(node, []),
                                    "receipt": inc_b.get(node, [])}
                    if inc_bad:
                        o["incident_edge_state_mismatches"] += 1
                    typed_a = {(x[0], int(x[1]), x[2]): x[3] for x in a["typed_neighbor_order"]}
                    typed_b = {(x[0], int(x[1]), x[2]): x[3] for x in b["typed_neighbor_order"]}
                    for key in sorted(set(typed_a) | set(typed_b)):
                        o["typed_neighbor_bucket_comparisons"] += 1
                        if typed_a.get(key, []) != typed_b.get(key, []):
                            o["typed_neighbor_bucket_mismatches"] += 1
                            if o["first_typed_neighbor_divergence"] is None:
                                o["first_typed_neighbor_divergence"] = {
                                    "replicate": run["replicate"], "event_index": a["event_index"],
                                    "direction": key[0], "node_id": key[1], "edge_type": key[2],
                                    "direct": typed_a.get(key, []), "receipt": typed_b.get(key, [])}
            if ep["final_canonical_graph_sha256"] != direct["final_canonical_graph_sha256"]:
                raise SystemExit(f"final canonical graph mismatch in {arm}")
            if arm != "direct":
                if len(ep["receipts"]) != 16 or not all(r["adopted_branch_match"] for r in ep["receipts"]):
                    raise SystemExit(f"task-producer/settlement receipt parity failed for {arm}")
                if sum(r["phase"] == "production_helper" for r in ep["receipts"]) != 6 or \
                        sum(r["phase"] == "ordinary_settlement" for r in ep["receipts"]) != 10:
                    raise SystemExit("expected six producer and ten settlement receipts")
                counts = [sum(r["effect_counts"].values()) for r in ep["receipts"]]
                receipts[arm]["receipt_count"] += len(counts)
                receipts[arm]["nonempty_receipt_count"] += sum(x > 0 for x in counts)
                receipts[arm]["total_effect_count"] += sum(counts)
            route_ms[arm].append(ep["measured_route_wall_ns"] / 1e6)
            for key, val in ep["timing_stages_ns"].items():
                stages[arm].setdefault(key, []).append(val / 1e6)
    summary = {arm: {"median_route_ms": statistics.median(v), "min_route_ms": min(v),
                     "max_route_ms": max(v),
                     "stage_median_ms": {k: statistics.median(x) for k, x in stages[arm].items()}}
               for arm, v in route_ms.items()}
    result = {"schema": "ReceiptEdgeOrderDiagnosticV1Analysis", "raw_capture": str(RAW.relative_to(ROOT)),
              "workers": len(runs), "episodes": len(runs) * len(ARMS),
              "per_event_semantic_comparisons": 10 * len(runs) * 2,
              "gates": {"source_lock_stable": True, "unique_fresh_worker_processes": True,
                        "all_three_lifecycle_rules_active": True, "task_goals_and_epistemic_residual_match": True,
                        "all_per_event_canonical_graphs_and_progress_match": True,
                        "all_adopted_primary_states_match_producing_branches": True,
                        "terminal_fixed_point_and_empty_receipts": True,
                        "wire_order_reported_separately": True},
              "timing": summary, "order_diagnostics": order, "receipt_activity": receipts,
              "worker_module_import_ms_median": statistics.median(
                  r["worker_module_import_ns"] for r in runs) / 1e6,
              "limits": ["one existing authored mixed-act task fixture", "one host",
                         "canonical parity does not imply serialized edge-order parity",
                         "no concurrent writer or serving-runtime evidence"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "all_gates_pass": True,
                      "order_diagnostics": order, "analysis": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
