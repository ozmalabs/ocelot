#!/usr/bin/env python3
"""Independent gates and scaling summary for the v1.1 scoped invalidation panel."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/resource_version_scoped_invalidation_v1_2_20260928.json"
OUT = ROOT / "evaluation/reports/resource_version_scoped_invalidation_v1_2_analysis_20260928.json"
SIZES = (4, 16, 64)


def main() -> None:
    d = json.loads(RAW.read_text())
    runs = d["runs"]
    gates = {
        "three_workers": len(runs) == 3,
        "locked_inputs_match": all(r["started_inputs"] == d["locked_inputs"] for r in runs),
        "six_cells_each": all(len(r["cells"]) == 6 for r in runs),
        "sizes_and_arms_complete": all(
            {(c["n_frames"], c["arm"]) for c in r["cells"]}
            == {(n, a) for n in SIZES for a in ("global", "scoped")}
            for r in runs
        ),
        "wildcard_access_observed": all(c["static_access"]["reads_any"] for r in runs for c in r["cells"]),
        "initial_and_external_only_reject": all(
            not any(f["accepted"] for f in c["initial"]["frames"])
            and not any(f["accepted"] for f in c["external_only"]["frames"])
            and c["external_only"]["callback_count"] == 0
            and c["external_only"]["progress"] == 0
            for r in runs for c in r["cells"]
        ),
        "revision_update_accepts_only_frame_zero": all(
            [f["accepted"] for f in c["frames"]] == [True] + [False] * (c["n_frames"] - 1)
            and c["frames"][0]["revision"] == "r0_v1"
            for r in runs for c in r["cells"]
        ),
    }
    paired_parity = True
    work_advantage = True
    size_summary = []
    for n in SIZES:
        paired = []
        global_calls, scoped_calls = [], []
        global_ns, scoped_ns = [], []
        for run in runs:
            by_arm = {c["arm"]: c for c in run["cells"] if c["n_frames"] == n}
            g, s = by_arm["global"], by_arm["scoped"]
            paired_parity &= g["frames"] == s["frames"]
            gc, sc = g["revision_update"]["callback_count"], s["revision_update"]["callback_count"]
            global_calls.append(gc); scoped_calls.append(sc)
            global_ns.append(g["revision_update"]["elapsed_ns"])
            scoped_ns.append(s["revision_update"]["elapsed_ns"])
            paired.append({"worker": run["worker_id"], "global_callbacks": gc, "scoped_callbacks": sc,
                           "global_ns": global_ns[-1], "scoped_ns": scoped_ns[-1]})
        if n >= 16:
            work_advantage &= all(sc < gc for gc, sc in zip(global_calls, scoped_calls))
        size_summary.append({"n_frames": n, "replicates": paired,
                             "callback_count_global": global_calls,
                             "callback_count_scoped": scoped_calls,
                             "timing_status": "descriptive only"})
    gates["paired_final_graph_projection_parity"] = paired_parity
    gates["scoped_callback_work_lower_at_n16_and_n64"] = work_advantage
    report = {
        "analysis": "Resource-version scoped invalidation v1.1",
        "all_preregistered_gates_pass": all(gates.values()), "gates": gates,
        "size_summary": size_summary,
        "interpretation": "An explicit graph revision update makes the selected predicate eligible for evaluation. Caller-selected microtheory scoping preserves this fixture's final projection while reducing external callback work as the number of independent frames grows. This does not establish automatic resource watchers or natural frame locality.",
        "limitations": [
            "The scope is explicitly supplied by the caller; no owner/event queue automatically maps resource changes to Microtheories.",
            "Callback counts measure this one rule and callback shape; seeded CAN rules were present to admit real Microtheory nodes but did not define the measured predicate.",
            "Wall times are descriptive and are not used as a speedup gate.",
            "Already asserted graph effects are monotonic; this probe only starts from rejected matches and does not test retraction.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_preregistered_gates_pass": report["all_preregistered_gates_pass"],
                      "gates": gates, "size_summary": size_summary,
                      "analysis": str(OUT.relative_to(ROOT))}, indent=2))
    if not report["all_preregistered_gates_pass"]:
        raise SystemExit("one or more v1.1 panel gates failed")


if __name__ == "__main__":
    main()
