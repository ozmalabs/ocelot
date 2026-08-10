"""Mechanical publication/readback for the general cognitive Pareto faculty.

All decisions live in ``seeds/cognitive_pareto.json``. This module only maps
integer interface data into graph nodes and reads relational results back.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping


def _edge(agent, source, edge_type: str, target) -> None:
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be integer quanta, got {value!r}")
    return value


def install_pareto_profile(
    agent,
    owner,
    dimensions: Iterable[Mapping[str, Any]],
    *,
    context: str,
    goal=None,
):
    """Publish an objective basis, optionally as an audit of a current Goal."""
    rows = tuple(dict(row) for row in dimensions)
    ordinals = [_integer(row["ordinal"], "dimension ordinal") for row in rows]
    if len(set(ordinals)) != len(rows):
        raise ValueError("Pareto dimension ordinals must be unique")
    profile = agent.s.add_node("ParetoProfile", {
        "context": str(context),
        "epoch": 0,
        "dimension_count": len(rows),
        "candidate_count": 0,
        "provenance_kind": "unweighted_objective_coordinate_system",
    })
    _edge(agent, owner, "has_pareto_profile", profile)
    if goal is not None:
        _edge(agent, profile, "audits_goal", goal)
    dimensions_by_name = {}
    for row in rows:
        direction = str(row["direction"])
        if direction not in {"maximize", "minimize"}:
            raise ValueError(f"invalid Pareto direction: {direction!r}")
        dimension = agent.s.add_node("ParetoDimension", {
            "name": str(row["name"]),
            "ordinal": _integer(row["ordinal"], "dimension ordinal"),
            "direction": direction,
            "direction_sign": 1 if direction == "maximize" else -1,
            "unit": str(row.get("unit", "quanta")),
            "hard_boundary": int(bool(row.get("hard_boundary", False))),
        })
        _edge(agent, profile, "has_pareto_dimension", dimension)
        dimensions_by_name[str(row["name"])] = dimension
    return {
        "profile": profile,
        "dimensions": dimensions_by_name,
        "candidate_count": 0,
        "goal": goal,
    }


def publish_pareto_candidate(
    agent,
    profile_result: dict[str, Any],
    measurements: Mapping[str, int],
    *,
    identity: str,
    verified: bool = True,
    incumbent: bool = False,
):
    """Publish one immutable, integer-quantized point."""
    dimensions = profile_result["dimensions"]
    if set(measurements) != set(dimensions):
        missing = sorted(set(dimensions) - set(measurements))
        extra = sorted(set(measurements) - set(dimensions))
        raise ValueError(
            f"candidate dimensions are incomplete: missing={missing}, extra={extra}"
        )
    candidate = agent.s.add_node("ParetoCandidate", {
        "identity": str(identity),
        "dominated": 0,
        "verified": int(bool(verified)),
        "incumbent": int(bool(incumbent)),
        "provenance_kind": "immutable_measured_objective_point",
    })
    _edge(agent, profile_result["profile"], "has_pareto_candidate", candidate)
    if incumbent:
        _edge(
            agent,
            profile_result["profile"],
            "has_incumbent_pareto_candidate",
            candidate,
        )
    for name, dimension in dimensions.items():
        attrs = agent.s.node(dimension)["attrs"]
        raw_value = _integer(measurements[name], f"measurement {name!r}")
        direction_sign = _integer(attrs["direction_sign"], "direction sign")
        value = agent.s.add_node("ParetoValue", {
            "dimension_ordinal": _integer(attrs["ordinal"], "dimension ordinal"),
            "raw_value": raw_value,
            "signed_value": raw_value * direction_sign,
            "verified": int(bool(verified)),
        })
        _edge(agent, candidate, "has_pareto_value", value)
        _edge(agent, value, "measures_pareto_dimension", dimension)
    profile_result["candidate_count"] += 1
    agent.inner.set_attr(
        profile_result["profile"],
        "candidate_count",
        profile_result["candidate_count"],
    )
    return candidate


def evaluate_pareto_profile(agent, profile_result) -> dict[str, Any]:
    """Recruit bounded System 2 to search for dominance counterexamples."""
    profile = profile_result["profile"]
    epoch = int(agent.s.node(profile)["attrs"].get("epoch", 0)) + 1
    agent.inner.set_attr(profile, "epoch", epoch)
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "area": "cognitive_pareto",
        "enabled": 1,
        "provenance_kind": "pareto_relational_evaluation",
    })
    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested",
        "reason": "evaluate_goal_tradeoff_basis",
        "input_epoch": epoch,
        "deadline_epoch": epoch,
    })
    _edge(agent, escalation, "about_context", profile)
    _edge(agent, escalation, "recruits_task_set", task_set)
    return agent.dual_process_tick()


def pareto_frontier(agent, profile_result) -> tuple[Any, ...]:
    return tuple(
        candidate
        for candidate in agent.inner.neighbours(
            profile_result["profile"], "has_pareto_candidate")
        if not agent.inner.neighbours(
            candidate, "is_dominated_by_pareto_candidate")
    )


def goal_revision_requests(agent, profile_result) -> tuple[Any, ...]:
    return tuple(agent.inner.neighbours(
        profile_result["profile"], "has_goal_revision_request"))


__all__ = [
    "evaluate_pareto_profile",
    "goal_revision_requests",
    "install_pareto_profile",
    "pareto_frontier",
    "publish_pareto_candidate",
]
