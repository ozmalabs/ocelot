#!/usr/bin/env python3
"""Independent gate, integrity, and native-work aggregation for topology probe."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evaluation/reports/substrate_frame_topology_local_candidates_v3_20260926.json"
BASELINE = ROOT / "evaluation/substrate_capability/frame_topology_cost_attribution_baseline_20260926"
sys.path.insert(0, str(ROOT))
from domains.engine_provenance import rust_source_fingerprint  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values):
    return statistics.median(values)


def sum_phase(arm, phase_index, key):
    if key == "wall_ns":
        return sum(int(p[key]) for p in arm["phases"])
    return sum(int(p["audit"].get(key, 0)) for p in arm["phases"])


def main():
    data = json.loads(REPORT.read_text())
    paths = {
        "protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_LOCAL_CANDIDATE_PREREG_20260926.md",
        "runner": ROOT / "scripts/substrate_frame_topology_local_candidates_v3.py",
        "graph_rs": ROOT / "runners/dsl/src/graph.rs",
        "substrate_rs": ROOT / "runners/dsl/src/substrate.rs",
        "rewrite_rs": ROOT / "runners/dsl/src/rewrite.rs",
        "py_rs": ROOT / "runners/dsl/src/py.rs",
        "scale_audit_rs": ROOT / "runners/dsl/src/scale_audit.rs",
        "native": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
    }
    integrity = {key: sha(path) == data["inputs"][key] for key, path in paths.items()}
    integrity["rust_source_fingerprint"] = rust_source_fingerprint(str(ROOT)) == data["inputs"]["rust_source_fingerprint"]
    summaries, gate_values = [], []
    all_cardinality = True
    for row in data["rows"]:
        topology, n = row["topology"], int(row["frame_count"])
        reps = row["repetitions"]
        per_rep_gates = []
        measures = {"event_wall_ms": [], "full_wall_ms": [], "event_candidates": [], "full_candidates": [],
                    "event_term_evaluations": [], "full_term_evaluations": [], "event_term_units": [],
                    "full_term_units": [], "event_progress_steps": [], "full_progress_steps": [],
                    "event_scoped_turns": [], "event_enqueues": []}
        for rep in reps:
            event, full, omission = rep["event"], rep["full"], rep["omission"]
            expected = event["frame_ids"]
            cardinality = (int(row["node_count"]) == 2 * n and int(row["dependency_edge_count"]) == n - 1
                           and int(row["rule_count"]) == 4 and len(event["edges"]) == n - 1
                           and event["edges"] == full["edges"])
            checks = {
                "matched_cardinality_and_topology": cardinality,
                "full_fixed_point_both_phases": all(p["status"] == "fixed_point" for p in full["phases"]),
                "event_settled_both_phases": all(p["complete"] for p in event["phases"]),
                "exact_event_full_state_parity": all(event["phases"][i]["projection"] == full["phases"][i]["projection"] for i in range(2)),
                "all_frame_owners_notified": all(p["affected_owners"] == expected for p in event["phases"]),
                "omitted_leaf_stays_unobserved": omission["phases"][0]["projection"]["states"][-1] == 1 and omission["phases"][0]["projection"]["observed"][-1] is False and omission["phases"][0]["projection"] != full["phases"][0]["projection"],
                "audit_counters_recorded": all(set(("cand_enum", "term_evals_total", "term_units_total")) <= set(p["audit"]) for arm in (event, full) for p in arm["phases"]),
                "event_uses_local_and_mt_seed_paths": all(p["audit"]["scoped_local_rule_matches"] > 0 and p["audit"]["scoped_mt_seeded_rule_matches"] > 0 and p["audit"]["scoped_full_fallback_rule_matches"] == 0 for p in event["phases"]),
                "full_arm_has_no_scoped_path_counts": all(p["audit"]["scoped_local_rule_matches"] == 0 and p["audit"]["scoped_mt_seeded_rule_matches"] == 0 and p["audit"]["scoped_full_fallback_rule_matches"] == 0 for p in full["phases"]),
                "no_event_cap_or_deferred_work": all(not p["cap_hit"] and not p["deferred_pending"] for p in event["phases"]),
            }
            per_rep_gates.append(checks); gate_values.extend(checks.values()); all_cardinality &= cardinality
            measures["event_wall_ms"].append(sum_phase(event, 0, "wall_ns") / 1e6)
            measures["full_wall_ms"].append(sum_phase(full, 0, "wall_ns") / 1e6)
            for target, key in (("event_candidates", "cand_enum"), ("full_candidates", "cand_enum"),
                                ("event_term_evaluations", "term_evals_total"), ("full_term_evaluations", "term_evals_total"),
                                ("event_term_units", "term_units_total"), ("full_term_units", "term_units_total")):
                arm = event if target.startswith("event") else full
                measures[target].append(sum_phase(arm, 0, key))
            measures["event_progress_steps"].append(sum(int(p["progress_steps"]) for p in event["phases"]))
            measures["full_progress_steps"].append(sum(int(p["progress_steps"]) for p in full["phases"]))
            measures["event_scoped_turns"].append(sum(int(p["turns"]) for p in event["phases"]))
            measures["event_enqueues"].append(sum(int(p["enqueues"]) for p in event["phases"]))
        med = {key: median(values) for key, values in measures.items()}
        summaries.append({
            "topology": topology, "frame_count": n, "repetitions": len(reps),
            "all_gates_pass": all(all(c.values()) for c in per_rep_gates),
            **{f"median_{key}": value for key, value in med.items()},
            "event_full_candidate_ratio": med["event_candidates"] / med["full_candidates"] if med["full_candidates"] else None,
            "event_full_term_evaluation_ratio": med["event_term_evaluations"] / med["full_term_evaluations"] if med["full_term_evaluations"] else None,
            "event_full_term_unit_ratio": med["event_term_units"] / med["full_term_units"] if med["full_term_units"] else None,
            "event_full_wall_ratio": med["event_wall_ms"] / med["full_wall_ms"] if med["full_wall_ms"] else None,
            "repeat_gates": per_rep_gates,
        })
    controls = data["focused_controls"]
    focused_checks = {
        "order_sensitive_exact_state_and_step": controls["order_sensitive"]["full"]["concept"] == controls["order_sensitive"]["scoped"]["concept"]
            and controls["order_sensitive"]["full"]["concept"].get("selected") is not None
            and controls["order_sensitive"]["scoped"]["concept"].get("selected") is not None
            and controls["order_sensitive"]["full"]["steps"] == controls["order_sensitive"]["scoped"]["steps"] == 1,
        "order_sensitive_uses_local_path": controls["order_sensitive"]["scoped"]["path_counters"]["scoped_local_rule_matches"] > 0
            and controls["order_sensitive"]["scoped"]["path_counters"]["scoped_full_fallback_rule_matches"] == 0,
        "deleted_reuse_falls_back_with_parity": controls["deleted_type_reuse"]["scoped"]["deleted_edge"] is True
            and controls["deleted_type_reuse"]["scoped"]["edge_reinserted"] is True
            and controls["deleted_type_reuse"]["full"]["concept"] == controls["deleted_type_reuse"]["scoped"]["concept"]
            and controls["deleted_type_reuse"]["scoped"]["path_counters"]["scoped_full_fallback_rule_matches"] > 0
            and controls["deleted_type_reuse"]["scoped"]["path_counters"]["scoped_local_rule_matches"] == 0,
        "multi_edge_falls_back_with_parity": controls["multi_edge_fallback"]["full"]["concept"] == controls["multi_edge_fallback"]["scoped"]["concept"]
            and controls["multi_edge_fallback"]["scoped"]["path_counters"]["scoped_full_fallback_rule_matches"] > 0
            and controls["multi_edge_fallback"]["scoped"]["path_counters"]["scoped_local_rule_matches"] == 0,
    }
    all_pass = all(integrity.values()) and all_cardinality and all(gate_values) and all(focused_checks.values())
    result = {"protocol_id": data["protocol_id"], "integrity": integrity, "all_cardinalities_match": all_cardinality,
              "all_gates_pass": all_pass, "focused_control_checks": focused_checks, "rows": summaries}
    out = REPORT.with_name("substrate_frame_topology_local_candidates_v3_20260926_analysis.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    compact = [{k: r[k] for k in ("topology", "frame_count", "all_gates_pass", "median_event_candidates", "median_full_candidates", "event_full_candidate_ratio", "event_full_term_evaluation_ratio", "event_full_wall_ratio", "median_event_scoped_turns")} for r in summaries]
    print(json.dumps({"analysis": str(out), "all_gates_pass": all_pass, "integrity": integrity,
                      "focused_control_checks": focused_checks, "rows": compact}, indent=2))
    if not all_pass:
        raise SystemExit("integrity or independent topology gate failed")


if __name__ == "__main__":
    main()
