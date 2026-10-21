"""E3 finite-SCM contract and native evaluator fixtures."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from domains.engine_provenance import engine_preamble

engine_preamble()

from substrate_rs import Lit, Substrate, Term  # noqa: E402


def _native(model, query, intervention, assignments, cap=16):
    term = Term(
        "SCMIntervene",
        model=Lit(model),
        query=Lit(query),
        intervention=Lit(intervention),
        exogenous_assignments=Lit(assignments),
        assignment_cap=Lit(cap),
    )
    return term.evaluate({}, Substrate())


def _common_cause_model():
    rows = [{"inputs": {"U": 0}, "value": 0}, {"inputs": {"U": 1}, "value": 1}]
    return {
        "variables": [{"id": "X", "domain": [0, 1]}, {"id": "Y", "domain": [0, 1]}],
        "exogenous": [{"id": "U", "domain": [0, 1]}],
        "equations": [
            {"target": name, "parents": [], "exogenous": ["U"], "rows": rows}
            for name in ("X", "Y")
        ],
        "source_ids": ["mechanism-1"],
        "source_epoch": 7,
    }


def _run_seeded_request(*, enabled=1.0, remaining=1.0, model_epoch=7, query_epoch=7, approved=True):
    root = Path(__file__).resolve().parents[1]
    seed = json.loads((root / "seeds/scm_reasoning.json").read_text())
    substrate = Substrate()
    agent = substrate.add_node("Agent", {})
    substrate.load_seed_manifest(seed, agent)
    policy = substrate.nodes("ScmReasoningPolicy")[0]
    substrate.set_attr(policy, "enabled", enabled)
    substrate.set_attr(policy, "remaining", remaining)
    model = substrate.add_node("ScmModel", {
        "snapshot": _common_cause_model() | {"source_epoch": model_epoch},
        "source_epoch": model_epoch,
        "model_hash": "sha256:fixture-model",
    })
    query = substrate.add_node("ScmQuery", {
        "kind": "effect",
        "outcome": "Y",
        "intervention": {"X": 1},
        "exogenous_assignments": [{"U": 0}, {"U": 1}],
        "assignment_cap": 16,
        "scm_status": "pending",
        "funding_approved": approved,
        "source_epoch": query_epoch,
    })
    substrate.add_edge(query, "uses_scm_model", model)
    substrate._inner.run_rules()
    return substrate, policy, model, query


def _do_y_for_common_cause(x_value, u_values=(0, 1)):
    """SCM X := U, Y := U; do(X) cuts U -> X but leaves Y := U."""
    return [u for u in u_values]


def _condition_y_for_x(x_value, population=((0, 0, 0), (1, 1, 1))):
    rows = [(u, x, y) for u, x, y in population if x == x_value]
    return [y for _u, _x, y in rows]


def _ancestors(graph, nodes):
    parents = {node: set() for node in graph}
    for source, target in graph:
        parents.setdefault(target, set()).add(source)
    result = set(nodes)
    todo = list(nodes)
    while todo:
        for parent in parents.get(todo.pop(), ()):
            if parent not in result:
                result.add(parent)
                todo.append(parent)
    return result, parents


def _d_separated(graph, left, right, conditioned):
    ancestral, parents = _ancestors(graph, {left, right, *conditioned})
    undirected = {node: set() for node in ancestral}
    for source, target in graph:
        if source in ancestral and target in ancestral:
            undirected[source].add(target)
            undirected[target].add(source)
    for child in ancestral:
        for a in parents.get(child, ()):
            for b in parents.get(child, ()):
                if a != b and a in ancestral and b in ancestral:
                    undirected[a].add(b)
                    undirected[b].add(a)
    blocked = set(conditioned)
    seen, todo = {left}, [left]
    while todo:
        current = todo.pop()
        for neighbor in undirected.get(current, ()):
            if neighbor not in blocked and neighbor not in seen:
                seen.add(neighbor)
                todo.append(neighbor)
    return right not in seen


def _valid_backdoor_set(graph, treatment, outcome, adjustment):
    descendants = set()
    frontier = [treatment]
    while frontier:
        source = frontier.pop()
        for a, b in graph:
            if a == source and b not in descendants:
                descendants.add(b)
                frontier.append(b)
    if set(adjustment) & descendants:
        return False
    backdoor_graph = [(a, b) for a, b in graph if a != treatment]
    return _d_separated(backdoor_graph, treatment, outcome, set(adjustment))


def _standardized_risk(rows, treatment, adjustment):
    strata = sorted({row[0] for row in rows})
    total = len(rows)
    risks = {}
    for x_value in (0, 1):
        value = 0.0
        for z in strata:
            stratum = [row for row in rows if row[0] == z]
            selected = [row for row in stratum if row[1] == x_value]
            if not selected:
                return None
            weight = len(stratum) / total
            value += weight * sum(row[2] for row in selected) / len(selected)
        risks[x_value] = value
    return risks


def _finite_do(model, intervention):
    if model.get("cyclic") or not model.get("complete_equations"):
        return {"status": "unknown", "reason": "unsupported_or_incomplete_model"}
    values = []
    for exogenous in model["exogenous_assignments"]:
        # This fixture's equations are X := U and Y := U. The intervention
        # replaces X's equation but leaves Y's mechanism and the same U intact.
        row = {"X": intervention.get("X", exogenous["U"]), "Y": exogenous["U"]}
        values.append(row)
    return {"status": "identified", "values": values,
            "assumptions": ["uniform_exogenous_assignments"]}


def test_do_differs_from_conditioning():
    conditioned = _condition_y_for_x(1)
    intervened = _do_y_for_common_cause(1)
    assert sum(conditioned) / len(conditioned) == 1.0
    assert sum(intervened) / len(intervened) == 0.5


def test_confounder_adjustment_matches_oracle():
    # Rows are (U, X, Y), with strong confounding but no within-U treatment
    # effect. The known interventional oracle has risk 0.5 under either X.
    rows = (
        [(0, 0, 0)] * 36 + [(0, 0, 1)] * 9
        + [(0, 1, 0)] * 4 + [(0, 1, 1)] * 1
        + [(1, 0, 0)] * 1 + [(1, 0, 1)] * 4
        + [(1, 1, 0)] * 9 + [(1, 1, 1)] * 36
    )
    graph = [("U", "X"), ("U", "Y"), ("X", "Y")]
    assert _valid_backdoor_set(graph, "X", "Y", {"U"})
    risks = _standardized_risk(rows, "X", {"U"})
    assert risks == {0: 0.5, 1: 0.5}
    assert risks[1] - risks[0] == 0.0


def test_collider_not_adjusted():
    graph = [("X", "C"), ("Y", "C")]
    assert _valid_backdoor_set(graph, "X", "Y", set())
    assert not _valid_backdoor_set(graph, "X", "Y", {"C"})


def test_no_identification_returns_unknown():
    cyclic = {"cyclic": True, "complete_equations": True,
              "exogenous_assignments": [{"U": 0}, {"U": 1}]}
    assert _finite_do(cyclic, {"X": 1})["status"] == "unknown"

    rows = [(0, 0, 0), (0, 0, 1), (1, 1, 0), (1, 1, 1)]
    assert _standardized_risk(rows, treatment="X", adjustment={"U"}) is None


def test_live_graph_unchanged():
    live = {
        "epoch": 7,
        "causal_facts": [{"source": "U", "target": "X", "kind": "observation"}],
        "mechanisms": [{"id": "m-x-u", "parents": ["U"], "target": "X"}],
        "observations": [{"X": 1, "Y": 1}],
    }
    before = deepcopy(live)
    detached = deepcopy(live)
    detached_model = {"complete_equations": True,
                      "exogenous_assignments": [{"U": 0}, {"U": 1}]}
    result = _finite_do(detached_model, {"X": 1})
    assert result["status"] == "identified"
    assert live == before


def test_native_do_differs_from_conditioning():
    model = _common_cause_model()
    assignments = [{"U": 0}, {"U": 1}]
    intervention = {"X": 1}
    effect = _native(model, {"kind": "effect", "outcome": "Y"}, intervention, assignments)
    condition = _native(model, {"kind": "condition", "outcome": "Y"}, intervention, assignments)
    assert effect["status"] == condition["status"] == "identified"
    assert effect["values"] == [0, 1]
    assert condition["values"] == [1]
    assert effect["assumptions"] == ["uniform_exogenous_assignments"]
    assert effect["source_ids"] == ["mechanism-1"] and effect["source_epoch"] == 7


def test_native_counterfactual_reuses_shared_exogenous_assignment():
    result = _native(_common_cause_model(), {"kind": "unit_counterfactual", "outcome": "Y"},
                     {"X": 1}, [{"U": 0}, {"U": 1}])
    assert result["values"] == [
        {"factual": 0, "counterfactual": 0},
        {"factual": 1, "counterfactual": 1},
    ]


def test_native_scm_abstains_on_cycles_empty_assignments_and_bounds():
    cyclic = {
        "variables": [{"id": "X", "domain": [0, 1]}, {"id": "Y", "domain": [0, 1]}],
        "exogenous": [],
        "equations": [
            {"target": "X", "parents": ["Y"], "exogenous": [], "rows": [
                {"inputs": {"Y": 0}, "value": 0}, {"inputs": {"Y": 1}, "value": 1}]},
            {"target": "Y", "parents": ["X"], "exogenous": [], "rows": [
                {"inputs": {"X": 0}, "value": 0}, {"inputs": {"X": 1}, "value": 1}]},
        ],
    }
    query = {"kind": "effect", "outcome": "Y"}
    assert _native(cyclic, query, {"X": 1}, []).get("status") == "unknown"
    assert _native(_common_cause_model(), query, {"X": 1}, []).get("status") == "unknown"
    assert _native(_common_cause_model(), query, {"X": 1}, [{"U": 0}, {"U": 1}], 1).get("status") == "unknown"
    assert _native(None, query, {"X": 1}, [{"U": 0}]).get("status") == "invalid"


def test_source_model_epoch_invalidates():
    substrate, policy, model, query = _run_seeded_request(model_epoch=8, query_epoch=7)
    assert substrate.node(query)["attrs"]["scm_status"] == "unknown"
    assert substrate.node(query)["attrs"]["scm_reason"] == "source_model_epoch_mismatch"
    assert "scm_result" not in substrate.node(query)["attrs"]
    assert substrate.node(policy)["attrs"]["remaining"] == 1.0


def test_query_budget_bound():
    substrate, policy, _model, query = _run_seeded_request(remaining=0.0)
    attrs = substrate.node(query)["attrs"]
    assert attrs["scm_status"] == "pending"
    assert "scm_result" not in attrs
    assert substrate.node(policy)["attrs"]["remaining"] == 0.0


def test_scm_seed_is_default_off():
    substrate, policy, _model, query = _run_seeded_request(enabled=0.0)
    assert substrate.node(query)["attrs"]["scm_status"] == "pending"
    assert "scm_result" not in substrate.node(query)["attrs"]
    assert substrate.node(policy)["attrs"]["remaining"] == 1.0


def test_scm_query_requires_one_explicit_funding_approval():
    substrate, policy, _model, query = _run_seeded_request(approved=False)
    assert substrate.node(query)["attrs"]["scm_status"] == "pending"
    assert "scm_result" not in substrate.node(query)["attrs"]
    assert substrate.node(policy)["attrs"]["remaining"] == 1.0


def test_detached_result_not_observed():
    substrate, policy, _model, query = _run_seeded_request()
    attrs = substrate.node(query)["attrs"]
    assert attrs["scm_status"] == "evaluated"
    assert attrs["model_hash_used"] == "sha256:fixture-model"
    assert attrs["evaluated_source_epoch"] == 7
    assert attrs["scm_result"]["status"] == "identified"
    assert substrate.node(policy)["attrs"]["remaining"] == 0.0
    assert substrate.nodes("Observation") == []
    assert "observed" not in attrs
