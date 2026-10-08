#!/usr/bin/env python3
"""Independent checks for positive-to-negative external effect compensation."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/external_effect_compensation_probe_v1_20260928.json"
OUT = ROOT / "evaluation/reports/external_effect_compensation_probe_v1_analysis_20260928.json"
PHASES = ["initial_negative_r0", "positive_revision_r1", "external_only_negative_flip", "negative_revision_r2"]
MODES = ["sticky_attr", "compensating_attr", "retractable_edge"]


def main() -> None:
    d = json.loads(RAW.read_text())
    runs = d["runs"]
    gates = {
        "three_workers": len(runs) == 3,
        "locked_inputs_match": all(r["started_inputs"] == d["locked_inputs"] for r in runs),
        "all_arms_and_phases_present": all(
            {a["mode"] for a in r["arms"]} == set(MODES)
            and all([p["phase"] for p in a["phases"]] == PHASES for a in r["arms"])
            for r in runs
        ),
    }
    signatures = []
    expected_final = {"sticky_attr": {"accepted_attr": 1, "accepted_edge": False},
                      "compensating_attr": {"accepted_attr": 0, "accepted_edge": False},
                      "retractable_edge": {"accepted_attr": None, "accepted_edge": False}}
    for r in runs:
        by_mode = {a["mode"]: a for a in r["arms"]}
        sig = {}
        for mode, arm in by_mode.items():
            p = {x["phase"]: x for x in arm["phases"]}
            sig[mode] = [{k: p[name][k] for k in ("revision", "progress", "callback_count", "markers")}
                         for name in PHASES]
        signatures.append(sig)
    gates["identical_worker_behavior"] = signatures[0] == signatures[1] == signatures[2]
    gates["positive_revision_commits_effect"] = all(
        (a["mode"] == "retractable_edge" and a["phases"][1]["markers"]["accepted_edge"])
        or (a["mode"] != "retractable_edge" and a["phases"][1]["markers"]["accepted_attr"] == 1)
        for r in runs for a in r["arms"]
    )
    gates["external_only_flip_does_not_recheck_or_correct"] = all(
        a["phases"][2]["callback_count"] == 0
        and a["phases"][2]["markers"] == a["phases"][1]["markers"]
        for r in runs for a in r["arms"]
    )
    gates["negative_revision_rechecks_resource"] = all(
        a["phases"][3]["callback_count"] > 0
        and all(c["value"] == "0" for c in a["phases"][3]["callback_log"])
        for r in runs for a in r["arms"]
    )
    gates["final_state_matches_strategy"] = all(
        a["phases"][3]["markers"] == expected_final[a["mode"]]
        for r in runs for a in r["arms"]
    )
    mode_summary = {}
    for mode in MODES:
        arms = [next(a for a in r["arms"] if a["mode"] == mode) for r in runs]
        mode_summary[mode] = {
            "phase_markers_by_worker": [[p["markers"] for p in a["phases"]] for a in arms],
            "callback_counts_by_worker": [[p["callback_count"] for p in a["phases"]] for a in arms],
            "resource_hashes_by_worker": [[p["resource_sha256"] for p in a["phases"]] for a in arms],
        }
    report = {
        "analysis": "External effect compensation probe v1",
        "all_gates_pass": all(gates.values()), "gates": gates,
        "strategies": mode_summary,
        "interpretation": "Resource-only changes do not re-evaluate a settled predicate. After an explicit revision update, the sticky rule leaves its prior positive attr; an authored false-case rule can set an explicit negative value or delete an edge. These are explicit compensation strategies, not automatic truth maintenance.",
        "limitations": [
            "One rule binding and fixed four-phase resource sequence per arm.",
            "No DelAttr effect was exercised; edge deletion and explicit value compensation are the supported representations tested.",
            "No effects are automatically retracted when a predicate becomes false.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": report["all_gates_pass"], "gates": gates,
                      "strategies": {k: v["phase_markers_by_worker"][0] for k, v in mode_summary.items()},
                      "analysis": str(OUT.relative_to(ROOT))}, indent=2))
    if not report["all_gates_pass"]:
        raise SystemExit("one or more compensation gates failed")


if __name__ == "__main__":
    main()
