#!/usr/bin/env python3
"""Verify historical gap, amended scoped attribution, and additive counters."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASELINE = ROOT / "evaluation/reports/substrate_frame_topology_cost_attribution_v1_0_scope_audit_gap_20260926.json"
CURRENT = ROOT / "evaluation/reports/substrate_frame_topology_cost_attribution_borrowed_v2_20260926.json"
BASE = ROOT / "evaluation/substrate_capability/frame_topology_cost_attribution_baseline_20260926"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def per_rule_sums(rows):
    out = defaultdict(int)
    for row in rows:
        out[row["metric"]] += int(row["count"])
    return out


def main():
    old, data = json.loads(BASELINE.read_text()), json.loads(CURRENT.read_text())
    baseline_paths = {
        "graph_rs": BASE / "graph.rs", "substrate_rs": BASE / "substrate.rs",
        "rewrite_rs": BASE / "rewrite.rs", "py_rs": BASE / "py.rs",
        "scale_audit_rs": BASE / "scale_audit.rs", "native": BASE / "_native.abi3.so",
        "runner": ROOT / "scripts/archive/substrate_frame_topology_cost_attribution_v1_0_scope_audit_gap.py",
        "base_runner": ROOT / "scripts/substrate_frame_topology_matched_scale_v1.py",
        "protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_FRAME_TOPOLOGY_COST_ATTRIBUTION_PREREG_20260926.md",
        "base_protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_FRAME_TOPOLOGY_MATCHED_SCALE_PREREG_20260926.md",
    }
    baseline_integrity = {key: sha(path) == old["inputs"][key] for key, path in baseline_paths.items()}
    current_paths = {
        "protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_BORROWED_SCOPED_RULES_CONFIRMATION_PREREG_20260926.md",
        "amendment": ROOT / "docs/research/engine_substrate/SUBSTRATE_FRAME_TOPOLOGY_COST_ATTRIBUTION_V1_1_AMENDMENT_20260926.md",
        "base_protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_FRAME_TOPOLOGY_MATCHED_SCALE_PREREG_20260926.md",
        "runner": ROOT / "scripts/substrate_frame_topology_cost_attribution_borrowed_v2.py",
        "base_runner": ROOT / "scripts/substrate_frame_topology_matched_scale_v1.py",
        "graph_rs": ROOT / "runners/dsl/src/graph.rs", "substrate_rs": ROOT / "runners/dsl/src/substrate.rs",
        "rewrite_rs": ROOT / "runners/dsl/src/rewrite.rs", "py_rs": ROOT / "runners/dsl/src/py.rs",
        "scale_audit_rs": ROOT / "runners/dsl/src/scale_audit.rs",
        "native": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
    }
    current_integrity = {key: sha(path) == data["inputs"][key] for key, path in current_paths.items()}
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    current_integrity["rust_source_fingerprint"] = rust_source_fingerprint(str(ROOT)) == data["inputs"]["rust_source_fingerprint"]
    current_integrity["build_record_current"] = not build_is_stale(str(ROOT))

    old_event_rows = sum(1 for row in old["rows"] for pair in row["pairs"] for phase in pair["event"]["phases"] if phase["per_rule"])
    old_full_rows = sum(1 for row in old["rows"] for pair in row["pairs"] for phase in pair["full"]["phases"] if phase["per_rule"])
    old_global_work = all(int(phase["global"].get("cand_enum", 0)) > 0 and int(phase["global"].get("term_evals_total", 0)) > 0
                          for row in old["rows"] for pair in row["pairs"] for phase in pair["event"]["phases"])
    baseline_gap_reproduced = old_event_rows == 0 and old_full_rows == 60 and old_global_work

    summary, conservation = [], []
    semantic = True
    for row in data["rows"]:
        per_topology = {"topology": row["topology"], "pairs": len(row["pairs"])}
        metric_values = defaultdict(list)
        per_rule_pair_values = defaultdict(list)
        for pair in row["pairs"]:
            event, full = pair["event"], pair["full"]
            pair_rule_totals = defaultdict(int)
            semantic &= all(event["phases"][i]["projection"] == full["phases"][i]["projection"] for i in (0, 1))
            semantic &= all(phase["settlement"]["complete"] for phase in event["phases"])
            semantic &= all(phase["status"] == "fixed_point" for phase in full["phases"])
            for arm_name, arm in (("event", event), ("full", full)):
                for phase in arm["phases"]:
                    enum_rows = [x for x in phase["per_rule"] if x["metric"] == "rule_enumerations"]
                    index_names = {int(x["rule_index"]): x["rule_name"] for x in enum_rows}
                    expected = {0: "propagate_on", 2: "observe_on", 3: "observe_off", 4: "propagate_off"}
                    idx_ok = index_names == expected
                    sums = per_rule_sums(phase["per_rule"])
                    global_counts = phase["global"]
                    checks = {
                        "stable_original_rule_indices": idx_ok,
                        "candidate_pair_conservation": sums["candidate_pairs"] == int(global_counts.get("cand_enum", 0)),
                        "candidate_test_conservation": sums["candidate_tests"] == int(global_counts.get("cand_tested", 0)),
                        "where_eval_conservation": sums["where_evaluations"] == int(global_counts.get("where_evals", 0)),
                        "term_eval_conservation": sums["term_evaluations"] == int(global_counts.get("term_evals_total", 0)),
                        "term_unit_conservation": sums["term_units"] == int(global_counts.get("term_units_total", 0)),
                        "rule_enumeration_conservation": sums["rule_enumerations"] == int(global_counts.get("rule_enumerations", 0)),
                    }
                    conservation.append({"topology": row["topology"], "repeat": pair["repeat"], "arm": arm_name,
                                         "phase": len([x for x in conservation if x["topology"] == row["topology"] and x["repeat"] == pair["repeat"] and x["arm"] == arm_name]),
                                         "checks": checks})
                    for metric in ("candidate_pairs", "term_evaluations", "where_evaluations", "rule_enumerations"):
                        metric_values[(arm_name, metric)].append(sums[metric])
                    for record in phase["per_rule"]:
                        pair_rule_totals[(arm_name, record["rule_name"], record["metric"])] += int(record["count"])
            for arm_name in ("event", "full"):
                for rule_name in ("propagate_on", "propagate_off", "observe_on", "observe_off"):
                    for metric in ("candidate_pairs", "term_evaluations", "where_evaluations", "rule_enumerations"):
                        per_rule_pair_values[(arm_name, rule_name, metric)].append(pair_rule_totals[(arm_name, rule_name, metric)])
        for arm_name in ("event", "full"):
            for metric in ("candidate_pairs", "term_evaluations", "where_evaluations", "rule_enumerations"):
                vals = metric_values[(arm_name, metric)]
                if vals:
                    per_topology[f"median_{arm_name}_{metric}"] = sorted(vals)[len(vals)//2]
        per_topology["event_full_candidate_ratio"] = per_topology["median_event_candidate_pairs"] / per_topology["median_full_candidate_pairs"]
        per_topology["event_full_term_eval_ratio"] = per_topology["median_event_term_evaluations"] / per_topology["median_full_term_evaluations"]
        per_topology["per_rule_medians"] = []
        for rule_name in ("propagate_on", "propagate_off", "observe_on", "observe_off"):
            item = {"rule_name": rule_name}
            for arm_name in ("event", "full"):
                for metric in ("candidate_pairs", "term_evaluations", "where_evaluations", "rule_enumerations"):
                    values = sorted(per_rule_pair_values[(arm_name, rule_name, metric)])
                    item[f"median_{arm_name}_{metric}"] = values[len(values)//2]
            item["event_full_candidate_ratio"] = (item["median_event_candidate_pairs"] / item["median_full_candidate_pairs"]
                                                    if item["median_full_candidate_pairs"] else None)
            item["event_full_term_eval_ratio"] = (item["median_event_term_evaluations"] / item["median_full_term_evaluations"]
                                                   if item["median_full_term_evaluations"] else None)
            per_topology["per_rule_medians"].append(item)
        summary.append(per_topology)
    conservation_ok = all(all(x["checks"].values()) for x in conservation)
    all_pass = all(baseline_integrity.values()) and baseline_gap_reproduced and all(current_integrity.values()) and semantic and conservation_ok
    result = {"protocol_id": data["protocol_id"], "baseline_integrity": baseline_integrity,
              "baseline_scope_attribution_gap_reproduced": baseline_gap_reproduced,
              "baseline_per_rule_rows": {"event": old_event_rows, "full": old_full_rows, "event_global_work_nonzero": old_global_work},
              "confirmatory_integrity": current_integrity, "semantic_parity_and_settlement": semantic,
              "per_rule_conservation": conservation_ok, "conservation_checks": conservation,
              "all_gates_pass": all_pass, "topology_summary": summary}
    out = ROOT / "evaluation/reports/substrate_frame_topology_cost_attribution_borrowed_v2_20260926_analysis.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(out), "all_gates_pass": all_pass,
                      "baseline_gap_reproduced": baseline_gap_reproduced,
                      "current_integrity": current_integrity, "semantic_parity": semantic,
                      "per_rule_conservation": conservation_ok, "topology_summary": summary}, indent=2))
    if not all_pass:
        raise SystemExit("baseline or confirmatory analysis gate failed")


if __name__ == "__main__":
    main()
