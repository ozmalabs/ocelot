#!/usr/bin/env python3
"""Independent analysis for compensation order and simultaneous transition panel."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/compensation_order_simultaneous_transitions_v1_20260928.json"
OUT = ROOT / "evaluation/reports/compensation_order_simultaneous_transitions_v1_analysis_20260928.json"
MODES = ("compensating_attr", "retractable_edge")
ORDERS = ("positive_first", "compensator_first")
PHASES = ("A_initial_all_negative", "B_establish_frame0_positive", "C_simultaneous_opposite_transitions")


def expected(mode: str, phase: str):
    if mode == "compensating_attr":
        vals = {PHASES[0]: [0, 0, 0], PHASES[1]: [1, 0, 0], PHASES[2]: [0, 1, 0]}[phase]
        return [{"frame": i, "revision": rev, "accepted_attr": vals[i], "accepted_edge": False}
                for i, rev in enumerate({PHASES[0]: ["0:r0", "1:r0", "2:r0"], PHASES[1]: ["0:r1", "1:r0", "2:r0"], PHASES[2]: ["0:r2", "1:r1", "2:r0"]}[phase])]
    edges = {PHASES[0]: [False, False, False], PHASES[1]: [True, False, False], PHASES[2]: [False, True, False]}[phase]
    revs = {PHASES[0]: ["0:r0", "1:r0", "2:r0"], PHASES[1]: ["0:r1", "1:r0", "2:r0"], PHASES[2]: ["0:r2", "1:r1", "2:r0"]}[phase]
    return [{"frame": i, "revision": revs[i], "accepted_attr": None, "accepted_edge": edges[i]}
            for i in range(3)]


def main() -> None:
    d = json.loads(RAW.read_text())
    runs = d["runs"]
    gates = {
        "three_workers": len(runs) == 3,
        "locked_inputs_match": all(r["started_inputs"] == d["locked_inputs"] for r in runs),
        "four_cells_each": all(len(r["cells"]) == 4 for r in runs),
        "all_modes_orders_phases_present": all(
            {(c["mode"], c["rule_order"]) for c in r["cells"]} == {(m, o) for m in MODES for o in ORDERS}
            and all(tuple(p["phase"] for p in c["phases"]) == PHASES for c in r["cells"])
            for r in runs
        ),
    }
    expected_outputs = True
    worker_consistency = True
    insertion_order_parity = True
    signatures = []
    for run in runs:
        by_cell = {(c["mode"], c["rule_order"]): c for c in run["cells"]}
        for (mode, order), cell in by_cell.items():
            for phase in cell["phases"]:
                expected_outputs &= phase["frames"] == expected(mode, phase["phase"])
                event_values = {}
                for call in phase["callback_log"]:
                    event_values.setdefault(call["frame"], set()).add(call["value"])
                wanted = {0: "0", 1: "1", 2: "0"} if phase["phase"] == PHASES[2] else None
                if wanted:
                    expected_outputs &= all(i in event_values and event_values[i] == {v} for i, v in wanted.items())
        sig = {}
        for mode in MODES:
            a, b = by_cell[(mode, "positive_first")], by_cell[(mode, "compensator_first")]
            insertion_order_parity &= [p["frames"] for p in a["phases"]] == [p["frames"] for p in b["phases"]]
            sig[mode] = {(order): [p["frames"] for p in by_cell[(mode, order)]["phases"]] for order in ORDERS}
        signatures.append(sig)
    worker_consistency = signatures[0] == signatures[1] == signatures[2]
    gates["expected_phase_states"] = expected_outputs
    gates["rule_order_invariant_projection"] = insertion_order_parity
    gates["replicated_across_workers"] = worker_consistency
    by_mode = {}
    for mode in MODES:
        by_mode[mode] = {}
        for order in ORDERS:
            by_mode[mode][order] = {
                phase: [next(c for c in r["cells"] if c["mode"] == mode and c["rule_order"] == order)["phases"][i]["callback_count"] for r in runs]
                for i, phase in enumerate(PHASES)
            }
    report = {
        "analysis": "Compensation order and simultaneous transitions v1",
        "all_gates_pass": all(gates.values()), "gates": gates,
        "callback_counts_by_mode_and_order": by_mode,
        "interpretation": "Both explicit compensator representations converge to the same frame projection under reversed rule insertion order for the tested independent simultaneous transitions.",
        "limitations": [
            "Only independent frame matches with mutually exclusive positive/negative predicates are tested.",
            "This does not establish order independence for overlapping rules that write conflicting values.",
            "This remains explicit compensation logic; no automatic truth maintenance is tested.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": report["all_gates_pass"], "gates": gates,
                      "callback_counts_by_mode_and_order": by_mode,
                      "analysis": str(OUT.relative_to(ROOT))}, indent=2))
    if not report["all_gates_pass"]:
        raise SystemExit("one or more transition/order gates failed")


if __name__ == "__main__": main()
