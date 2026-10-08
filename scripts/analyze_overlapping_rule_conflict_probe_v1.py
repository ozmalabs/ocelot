#!/usr/bin/env python3
"""Independent analysis for overlapping rule conflict and cycle behavior."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/overlapping_rule_conflict_probe_v1_20260928.json"
OUT = ROOT / "evaluation/reports/overlapping_rule_conflict_probe_v1_analysis_20260928.json"
ORDERS = ("A_then_B", "B_then_A")
DETECTION = (False, True)


def main() -> None:
    d = json.loads(RAW.read_text())
    runs = d["runs"]
    gates = {
        "three_workers": len(runs) == 3,
        "locked_inputs_match": all(r["started_inputs"] == d["locked_inputs"] for r in runs),
        "four_cells_each": all(len(r["cells"]) == 4 for r in runs),
        "all_order_detection_cells": all(
            {(c["order"], c["detect_cycles"]) for c in r["cells"]} == {(o, d_) for o in ORDERS for d_ in DETECTION}
            for r in runs
        ),
    }
    expected = {}
    signatures = []
    for r in runs:
        sig = {}
        for c in r["cells"]:
            key = (c["order"], c["detect_cycles"])
            final_value = 2 if c["order"] == "A_then_B" else 1
            expected[key] = (final_value, "repeated_graph_state" if c["detect_cycles"] else "progress_budget_reached")
            status = c["termination"]["status"]
            gates[f"correct_{c['order']}_{'cycle' if c['detect_cycles'] else 'budget'}_worker_{r['worker_id']}"] = (
                c["final_accepted"] == final_value and status == expected[key][1]
                and c["termination"]["cycle_detection_enabled"] == c["detect_cycles"]
                and c["callback_count"] > 0 and all(x == "same" for x in c["callback_arguments"])
            )
            sig[f"{key[0]}:{key[1]}"] = {"status": status, "final": c["final_accepted"],
                                          "progress_steps": c["termination"]["progress_steps"],
                                          "passes": c["termination"]["passes_completed"],
                                          "callbacks": c["callback_count"]}
        signatures.append(sig)
    gates["replicated_worker_signatures"] = signatures[0] == signatures[1] == signatures[2]
    report = {
        "analysis": "Overlapping rule conflict probe v1",
        "all_gates_pass": all(gates.values()), "gates": gates,
        "cells": signatures[0],
        "interpretation": "Conflicting overlapping rules do not converge to one insertion-order-independent fixed point. With cycle detection the engine reports a repeated graph state; without it the step budget stops the loop. The last writer in each completed pass determines the observed value.",
        "limitations": [
            "One graph binding and two deterministic rules only.",
            "Cycle detection fingerprints graph state; external callback side effects or other pending state may not be represented by that fingerprint.",
            "This is not a general confluence or rewrite-system termination classification.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": report["all_gates_pass"], "gates": gates,
                      "cells": report["cells"], "analysis": str(OUT.relative_to(ROOT))}, indent=2))
    if not report["all_gates_pass"]: raise SystemExit("conflict probe gate failed")


if __name__ == "__main__": main()
