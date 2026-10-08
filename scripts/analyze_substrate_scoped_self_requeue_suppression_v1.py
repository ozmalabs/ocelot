#!/usr/bin/env python3
"""Independently verify guarded self-requeue suppression measurements."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_scoped_self_requeue_suppression_v1_20260926.json"
BASE_RAW = ROOT / "evaluation/reports/substrate_scoped_notification_requeue_attribution_v1_20260926.json"
BASE_ANALYSIS = BASE_RAW.with_name(BASE_RAW.stem + "_analysis.json")
OUT = RAW.with_name(RAW.stem + "_analysis.json")

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def median(xs): return statistics.median(xs)

def main():
    import sys
    sys.path.insert(0, str(ROOT))
    from domains.engine_provenance import rust_source_fingerprint

    data = json.loads(RAW.read_text())
    base_analysis = json.loads(BASE_ANALYSIS.read_text())
    baseline = json.loads(BASE_RAW.read_text())
    paths = {"protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_SELF_REQUEUE_SUPPRESSION_PREREG_20260926.md",
        "runner": ROOT / "scripts/substrate_scoped_self_requeue_suppression_v1.py",
        "baseline_raw": BASE_RAW, "baseline_analysis": BASE_ANALYSIS,
        "runner_source": ROOT / "scripts/substrate_scoped_notification_requeue_attribution_v1.py",
        "native": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"}
    integrity = {name: sha(path) == data["inputs"][name] for name, path in paths.items()}
    integrity["rust_source_fingerprint"] = rust_source_fingerprint(str(ROOT)) == data["inputs"]["rust_source_fingerprint"]
    integrity["baseline_analysis_gates"] = bool(base_analysis["all_gates_pass"])
    summaries, all_gates = [], all(integrity.values())
    source_rows = {(r["topology"], r["frame_count"]): r for r in baseline["rows"]}
    for row in data["rows"]:
        source = source_rows[(row["topology"], row["frame_count"])]
        measures = {key: [] for key in ("turns", "no_progress_turns", "notifications", "self_requeues",
            "suppressed_self_enqueues", "duplicate_suppressions", "candidates", "term_evaluations", "wall_ns")}
        baseline_measures = {key: [] for key in ("turns", "candidates", "term_evaluations", "wall_ns")}
        per_rep_ok = []
        for rep, source_rep in zip(row["repetitions"], source["repetitions"]):
            ok = all(rep["gates"].values()) and all(source_rep["gates"].values())
            for phase in rep["intervention"]["phases"]:
                turns = phase["turn_records"]
                audit = phase["audit"]
                ok &= phase["turns"] == len(turns)
                ok &= phase["notification_entries"] == sum(t["notification_entries"] for t in turns)
                ok &= phase["self_requeues"] == sum(t["self_requeues"] for t in turns)
                ok &= phase["suppressed_self_enqueues"] == sum(t["suppressed_self_enqueues"] for t in turns)
                ok &= phase["duplicate_suppressions"] == sum(t["duplicate_suppressions"] for t in turns)
                ok &= sum(t["counter_delta"]["cand_enum"] for t in turns) == audit["cand_enum"]
                ok &= sum(t["counter_delta"]["term_evals_total"] for t in turns) == audit["term_evals_total"]
            ie, be = rep["intervention"], rep["baseline"]
            for i in range(2):
                measures["turns"].append(ie["phases"][i]["turns"])
                measures["no_progress_turns"].append(sum(t["progress_steps"] == 0 for t in ie["phases"][i]["turn_records"]))
                measures["notifications"].append(ie["phases"][i]["notification_entries"])
                measures["self_requeues"].append(ie["phases"][i]["self_requeues"])
                measures["suppressed_self_enqueues"].append(ie["phases"][i]["suppressed_self_enqueues"])
                measures["duplicate_suppressions"].append(ie["phases"][i]["duplicate_suppressions"])
                measures["candidates"].append(ie["phases"][i]["audit"]["cand_enum"])
                measures["term_evaluations"].append(ie["phases"][i]["audit"]["term_evals_total"])
                measures["wall_ns"].append(ie["phases"][i]["wall_ns"])
                baseline_measures["turns"].append(be["phases"][i]["turns"])
                baseline_measures["candidates"].append(be["phases"][i]["audit"]["cand_enum"])
                baseline_measures["term_evaluations"].append(be["phases"][i]["audit"]["term_evals_total"])
                baseline_measures["wall_ns"].append(be["phases"][i]["wall_ns"])
            per_rep_ok.append(bool(ok))
        summary = {"topology": row["topology"], "frame_count": row["frame_count"],
            "repetitions": len(row["repetitions"]), "all_repetitions_pass": all(per_rep_ok),
            "baseline_medians": {k: median(v) for k, v in baseline_measures.items()},
            "intervention_medians": {k: median(v) for k, v in measures.items()},
            "median_turn_reduction": median(baseline_measures["turns"]) - median(measures["turns"]),
            "median_candidate_reduction": median(baseline_measures["candidates"]) - median(measures["candidates"]),
            "median_term_evaluation_reduction": median(baseline_measures["term_evaluations"]) - median(measures["term_evaluations"]),
            "baseline_median_wall_ns": median(baseline_measures["wall_ns"]),
            "wall_ratio": median(measures["wall_ns"]) / median(baseline_measures["wall_ns"]) if median(baseline_measures["wall_ns"]) else None}
        summaries.append(summary); all_gates &= summary["all_repetitions_pass"]
    control = data["controls"]["ownership_change"]
    control_gate = bool(control["gate"] and control["event_self_requeues"] > 0 and
                        control["event_suppressed_self_enqueues"] == 0 and control["parity"])
    delayed = data["controls"]["delayed_writer"]
    delayed_gate = bool(delayed["gate"] and delayed["suppressed_sequence"] == [0, 1, 0] and
        delayed["b_turn_notifies_a"] and delayed["event_complete"] and
        delayed["full_status"] == "fixed_point" and delayed["event_projection"] ==
        delayed["baseline_projection"] == delayed["full_projection"])
    result = {"protocol_id": data["protocol_id"], "integrity": integrity,
        "ownership_change_control_pass": control_gate, "delayed_writer_control_pass": delayed_gate,
        "all_gates_pass": bool(all_gates and control_gate and delayed_gate),
        "rows": summaries}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT), "all_gates_pass": result["all_gates_pass"],
        "integrity": integrity, "ownership_change_control_pass": control_gate,
        "delayed_writer_control_pass": delayed_gate,
        "rows": summaries}, indent=2))
    if not result["all_gates_pass"]: raise SystemExit("intervention analysis gate failed")

if __name__ == "__main__": main()
