"""Plan P3b (2026-10-10): declared witnesses + one generic judge.

seeds/self_optimisation.json v1.7.0 replaces the five family judges with
declare_witness_<family> rules and judge_declared_witness_outcome. The
verdict matrix is pinned against the frozen v1.6.0 judges
(tests/fixtures/family_judges_self_optimisation_v1_6_0.json): for every
family, direction, regression count and measure ordering (and for missing
inputs) the new rules write the same outcome as the old ones.
"""
from __future__ import annotations

import itertools
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter   # noqa: E402

_OLD = json.load(open(os.path.join(ROOT, "tests", "fixtures",
                                   "family_judges_self_optimisation_v1_6_0.json")))["rules"]
_NEW = [r for r in json.load(open(os.path.join(ROOT, "seeds", "self_optimisation.json")))["rules"]
        if r["name"].startswith(("declare_witness_", "judge_declared_witness"))]

# family -> (delta markers, exp control attr, exp variant attr, direction attr or None)
_FAMILIES = {
    "knob": ({"knob_edit": 1.0}, "control_reforms", "variant_reforms", "knob_direction"),
    "rule_literal": ({"rule_literal_edit": 1.0}, "control_witness_fires", "variant_witness_fires",
                     "rule_literal_direction"),
    "datum": ({"datum_feedback_edit": 1.0}, "control_belief", "variant_belief", None),
    "shape": ({"shape_mint_edit": 1.0}, "control_belief", "variant_belief", None),
    "performance": ({"performance_objective": 1.0}, None, "avg_turn_ms", None),
}


def _cases():
    out = []
    for fam, (markers, c_attr, v_attr, d_attr) in _FAMILIES.items():
        directions = ["increase_fires", "decrease_fires", None] if d_attr else [None]
        for direction, regs, (c, v) in itertools.product(
                directions, [0, 2, None], [(3, 2), (2, 2), (2, 3), (None, 2), (2, None)]):
            delta = dict(markers)
            exp = {}
            if d_attr and direction is not None:
                delta[d_attr] = direction
            if regs is not None:
                exp["regressions"] = regs
            if fam == "performance":
                if c is not None:
                    delta["baseline_avg_turn_ms"] = float(c)
            elif c is not None:
                exp[c_attr] = c
            if v is not None:
                exp[v_attr] = v
            out.append((fam, delta, exp))
    # a deep-reader delta is exempt from the performance objective
    out.append(("performance_deep_reader", {"performance_objective": 1.0, "deep_reader_edit": 1.0,
                                            "baseline_avg_turn_ms": 5.0},
                {"avg_turn_ms": 1.0, "regressions": 0}))
    # family + performance objective: the family's verdict stands (it ran last)
    for c, v, base, ms in [(3, 2, 5.0, 9.0), (2, 3, 9.0, 5.0), (2, 2, 9.0, 5.0)]:
        out.append(("knob+performance", {"knob_edit": 1.0, "performance_objective": 1.0,
                                         "baseline_avg_turn_ms": base},
                    {"control_reforms": c, "variant_reforms": v, "avg_turn_ms": ms, "regressions": 0}))
    return out


def _outcome(rules, delta_attrs, exp_attrs):
    a = WorldAdapter(seeds=())
    for r in rules:
        a.inner.add_rule(r)
    exp = a.s.add_node("Experiment", dict(exp_attrs, outcome="generic"))
    delta = a.s.add_node("SeedDelta", dict(delta_attrs))
    run = a.s.add_node("Run", {"status": "done"})
    a.inner.add_edge_unchecked(exp, "has_delta", delta)
    a.inner.add_edge_unchecked(exp, "produced", run)
    a.inner.add_edge_unchecked(exp, "analysed", run)
    a.inner.run_rules()
    return a.s.node(exp)["attrs"].get("outcome"), a.s.node(delta)["attrs"]


@pytest.mark.parametrize("fam,delta,exp", _cases(),
                         ids=lambda x: x if isinstance(x, str) else None)
def test_same_verdict_as_the_frozen_family_judges(fam, delta, exp):
    old, _ = _outcome(_OLD, delta, exp)
    new, _ = _outcome(_NEW, delta, exp)
    assert new == old, (fam, delta, exp, old, new)


def test_the_matrix_is_not_vacuous():
    verdicts = {_outcome(_OLD, d, e)[0] for _f, d, e in _cases()}
    assert {"supported", "refuted", "inconclusive", "generic"} <= verdicts


def test_declaration_is_graph_data_and_a_declared_delta_needs_no_marker():
    _, dattrs = _outcome(_NEW, {"knob_edit": 1.0, "knob_direction": "increase_fires"},
                         {"control_reforms": 1, "variant_reforms": 2, "regressions": 0})
    assert dattrs["witness_kind"] == "reforms" and dattrs["witness_direction"] == "increase"
    # a delta that declares its own witness (a future FamilyProgram) is judged without a marker
    out, _ = _outcome(_NEW, {"witness_kind": "custom", "witness_direction": "decrease",
                             "witness_control_attr": "c_x", "witness_control_on": "exp",
                             "witness_variant_attr": "v_x"},
                      {"c_x": 4.0, "v_x": 1.0, "regressions": 0})
    assert out == "supported"
