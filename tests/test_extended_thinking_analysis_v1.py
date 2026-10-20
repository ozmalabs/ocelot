from __future__ import annotations

from evaluation.substrate_capability.extended_thinking_analysis_v1 import analyze, exact_mcnemar, wilson


def _row(family, solved_on, solved_off, first_steps=2, second_steps=1):
    def arm(solved, first, second):
        return {"first": {"solved": solved, "steps": first, "budget_spent": 1.0,
                           "approved_requests": 1, "applied_steps": 1,
                           "funding_upper_bound": 96.0, "false_accept": False},
                "second": {"solved": solved, "steps": second, "budget_spent": 0.0,
                            "approved_requests": 0, "applied_steps": 0}}
    on = arm(solved_on, first_steps, second_steps)
    off = arm(solved_off, 0, 0)
    if family.startswith("control"):
        on["first"]["false_accept"] = False
        off["first"]["false_accept"] = False
    return {"family": family, "et_on": on, "et_off": off}


def test_exact_mcnemar_and_wilson_helpers():
    assert exact_mcnemar([True] * 10, [False] * 10)["p_two_sided"] < 0.01
    interval = wilson(0, 10)
    assert interval["rate"] == 0.0 and interval["upper"] > 0.0


def test_analysis_applies_the_preregistered_decision_rules():
    rows = []
    for family in ("A", "B"):
        second_steps = 1 if family == "A" else 0
        rows.extend(_row(family, True, False, first_steps=2, second_steps=second_steps) for _ in range(20))
    for family in ("control_a", "control_b_value_noise", "control_b_quadratic"):
        rows.extend(_row(family, False, False) for _ in range(40))
    report = {"protocol": "extended_thinking_heldout_v1", "prereg_hash": "deadbeef",
              "first": 0, "end": 20, "rows": rows}
    result = analyze(report)
    assert all(x["pass"] for x in result["hypotheses"].values())
