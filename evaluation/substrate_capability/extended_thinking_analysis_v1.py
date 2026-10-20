"""Pre-registered paired analysis for extended_thinking_heldout_v1 reports."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> dict:
    if n <= 0:
        return {"rate": None, "lower": None, "upper": None, "n": 0, "successes": int(successes)}
    p = successes / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return {"rate": p, "lower": max(0.0, centre - half), "upper": min(1.0, centre + half),
            "n": n, "successes": int(successes)}


def exact_mcnemar(on: list[bool], off: list[bool]) -> dict:
    if len(on) != len(off):
        raise ValueError("paired arms must have equal length")
    b = sum(bool(a) and not bool(c) for a, c in zip(on, off))
    c = sum(not bool(a) and bool(d) for a, d in zip(on, off))
    n = b + c
    if n == 0:
        p = 1.0
    else:
        tail = sum(math.comb(n, k) for k in range(min(b, c) + 1)) / (2 ** n)
        p = min(1.0, 2.0 * tail)
    return {"on_only": b, "off_only": c, "discordant": n, "p_two_sided": p}


def _paired(rows, family):
    return [r for r in rows if r["family"] == family]


def analyze(report: dict) -> dict:
    rows = report["rows"]
    by_family = {}
    for family in ("A", "B", "control_a", "control_b_value_noise", "control_b_quadratic"):
        selected = _paired(rows, family)
        on = [bool(r["et_on"]["first"]["solved"]) for r in selected]
        off = [bool(r["et_off"]["first"]["solved"]) for r in selected]
        by_family[family] = {
            "et_on_solve_rate": wilson(sum(on), len(on)),
            "et_off_solve_rate": wilson(sum(off), len(off)),
            "paired_gain": (sum(on) - sum(off)) / len(on) if on else None,
            "mcnemar": exact_mcnemar(on, off),
        }

    def control_rows():
        return [r for r in rows if r["family"].startswith("control")]
    controls = control_rows()
    on_false = [bool(r["et_on"]["first"].get("false_accept")) for r in controls]
    off_false = [bool(r["et_off"]["first"].get("false_accept")) for r in controls]
    false_on = wilson(sum(on_false), len(on_false))
    false_off = wilson(sum(off_false), len(off_false))
    H3 = bool(false_on["rate"] is not None and false_on["rate"] <= 0.05
              and false_on["upper"] <= 0.10 and false_on["rate"] <= false_off["rate"] + 0.02)

    a_solved = [r for r in _paired(rows, "A") if r["et_on"]["first"]["solved"]]
    a_repeat = [r["et_on"]["second"]["steps"] < r["et_on"]["first"]["steps"] for r in a_solved]
    b_solved = [r for r in _paired(rows, "B") if r["et_on"]["first"]["solved"]]
    b_repeat = [r["et_on"]["second"]["steps"] == 0 for r in b_solved]
    a_repeat_rate = wilson(sum(a_repeat), len(a_repeat))
    b_repeat_rate = wilson(sum(b_repeat), len(b_repeat))

    all_results = [r[arm][visit] for r in rows for arm in ("et_on", "et_off") for visit in ("first", "second")]
    no_unfunded_steps = all(int(x.get("applied_steps", 0)) <= int(x.get("approved_requests", 0)) for x in all_results)
    spend = sum(float(x.get("budget_spent", 0.0)) for x in all_results)
    funding = sum(float(r["et_on"]["first"].get("funding_upper_bound", 0.0)) for r in rows)
    H5 = no_unfunded_steps and spend <= funding

    h1_gain = by_family["A"]["paired_gain"]
    h2_gain = by_family["B"]["paired_gain"]
    H1 = bool(h1_gain is not None and h1_gain >= 0.5 and by_family["A"]["mcnemar"]["p_two_sided"] < 0.01)
    H2 = bool(h2_gain is not None and h2_gain >= 0.5 and by_family["B"]["mcnemar"]["p_two_sided"] < 0.01)
    H4a = bool(a_repeat_rate["rate"] is not None and a_repeat_rate["rate"] >= 0.90)
    H4b = bool(b_repeat_rate["rate"] is not None and b_repeat_rate["rate"] >= 0.95)
    return {
        "protocol": report.get("protocol"), "prereg_hash": report.get("prereg_hash"),
        "draw_range": [report.get("first"), report.get("end")], "by_family": by_family,
        "controls_false_accept": {"et_on": false_on, "et_off": false_off},
        "second_encounter": {"family_a_steps_reduced": a_repeat_rate,
                              "family_b_zero_steps": b_repeat_rate},
        "budget": {"applied_steps_le_approved_requests": no_unfunded_steps,
                   "spend": spend, "funding_upper_bound": funding},
        "hypotheses": {
            "H1_family_a_gain_and_mcnemar": {"pass": H1},
            "H2_family_b_gain_and_mcnemar": {"pass": H2},
            "H3_control_false_accept_guard": {"pass": H3},
            "H4_second_encounter_cache": {"pass": H4a and H4b,
                "family_a_pass": H4a, "family_b_pass": H4b},
            "H5_budget_accounting": {"pass": H5},
        },
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        raise SystemExit("usage: extended_thinking_analysis_v1.py <heldout_report.json>")
    src = Path(argv[0])
    result = analyze(json.loads(src.read_text()))
    out = src.with_name(src.stem + "_analysis.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
