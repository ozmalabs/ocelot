"""Native finite-SCM backdoor adjustment conformance fixtures."""
from domains.engine_provenance import engine_preamble

engine_preamble()

from substrate_rs import Lit, Substrate, Term  # noqa: E402


def _native(model, query, intervention, assignments, cap=16):
    term = Term(
        "SCMIntervene", model=Lit(model), query=Lit(query), intervention=Lit(intervention),
        exogenous_assignments=Lit(assignments), assignment_cap=Lit(cap),
    )
    return term.evaluate({}, Substrate())


def _positivity_confounder_model():
    x_rows = [
        {"inputs": {"U": 0, "V": 0}, "value": 0},
        {"inputs": {"U": 0, "V": 1}, "value": 1},
        {"inputs": {"U": 1, "V": 0}, "value": 1},
        {"inputs": {"U": 1, "V": 1}, "value": 0},
    ]
    y_rows = [{"inputs": {"U": 0}, "value": 0}, {"inputs": {"U": 1}, "value": 1}]
    return {
        "variables": [{"id": "X", "domain": [0, 1]}, {"id": "Y", "domain": [0, 1]}],
        "exogenous": [{"id": "U", "domain": [0, 1]}, {"id": "V", "domain": [0, 1]}],
        "equations": [
            {"target": "X", "parents": [], "exogenous": ["U", "V"], "rows": x_rows},
            {"target": "Y", "parents": [], "exogenous": ["U"], "rows": y_rows},
        ],
        "source_ids": ["mechanism-confounded"], "source_epoch": 3,
    }


def _collider_model():
    return {
        "variables": [{"id": "X", "domain": [0, 1]}, {"id": "Y", "domain": [0, 1]},
                      {"id": "C", "domain": [0, 1]}],
        "exogenous": [],
        "equations": [
            {"target": "X", "parents": [], "exogenous": [], "rows": [{"inputs": {}, "value": 0}]},
            {"target": "Y", "parents": [], "exogenous": [], "rows": [{"inputs": {}, "value": 1}]},
            {"target": "C", "parents": ["X", "Y"], "exogenous": [], "rows": [
                {"inputs": {"X": 0, "Y": 0}, "value": 0},
                {"inputs": {"X": 0, "Y": 1}, "value": 1},
                {"inputs": {"X": 1, "Y": 0}, "value": 1},
                {"inputs": {"X": 1, "Y": 1}, "value": 0},
            ]},
        ],
        "source_ids": ["mechanism-collider"], "source_epoch": 4,
    }


def test_backdoor_adjustment_matches_finite_confounder_oracle():
    assignments = [{"U": u, "V": v} for u in (0, 1) for v in (0, 1)]
    result = _native(_positivity_confounder_model(),
                     {"kind": "adjustment", "outcome": "Y", "adjustment": ["U"]},
                     {"X": 1}, assignments)
    assert result["status"] == "identified"
    weighted = {}
    for _stratum, weight, outcome in result["values"]:
        weighted[outcome] = weighted.get(outcome, 0.0) + weight
    assert weighted == {0: 0.5, 1: 0.5}
    assert result["assumptions"] == ["valid_backdoor_adjustment"]


def test_backdoor_rejects_treatment_descendant_collider():
    result = _native(_collider_model(),
                     {"kind": "adjustment", "outcome": "Y", "adjustment": ["C"]},
                     {"X": 0}, [{}])
    assert result["status"] == "unknown"


def test_backdoor_rejects_positivity_failure():
    model = {
        "variables": [{"id": "X", "domain": [0, 1]}, {"id": "Y", "domain": [0, 1]}],
        "exogenous": [{"id": "U", "domain": [0, 1]}],
        "equations": [
            {"target": name, "parents": [], "exogenous": ["U"], "rows": [
                {"inputs": {"U": 0}, "value": 0}, {"inputs": {"U": 1}, "value": 1}]}
            for name in ("X", "Y")
        ],
    }
    result = _native(model, {"kind": "adjustment", "outcome": "Y", "adjustment": ["U"]},
                     {"X": 1}, [{"U": 0}, {"U": 1}])
    assert result["status"] == "unknown"
    assert result["reason"] == "positivity_violation"
