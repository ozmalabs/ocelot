"""Legacy embodied-Pareto publication boundary.

The actual comparison and goal-audit faculty is ``cognitive_pareto``. This
module remains for existing motor interfaces; ``embodied_pareto_profile``
bridges its vocabulary into the general relations. New cognition should use
``domains.cognitive_pareto`` directly.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping


def _edge(agent, source, edge_type: str, target) -> None:
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def install_pareto_profile(
    agent,
    owner,
    dimensions: Iterable[Mapping[str, Any]],
    *,
    context: str,
):
    """Publish an objective coordinate system without a scalar utility."""
    rows = tuple(dict(row) for row in dimensions)
    ordinals = [int(row["ordinal"]) for row in rows]
    if len(set(ordinals)) != len(rows):
        raise ValueError("Pareto dimension ordinals must be unique")
    profile = agent.s.add_node("EmbodiedParetoProfile", {
        "context": str(context),
        "epoch": 0.0,
        "dimension_count": float(len(rows)),
        "candidate_count": 0.0,
        "provenance_kind": "unweighted_objective_coordinate_system",
    })
    _edge(agent, owner, "has_embodied_pareto_profile", profile)
    dimensions_by_name = {}
    for row in rows:
        direction = str(row["direction"])
        if direction not in {"maximize", "minimize"}:
            raise ValueError(f"invalid Pareto direction: {direction!r}")
        dimension = agent.s.add_node("EmbodiedParetoDimension", {
            "name": str(row["name"]),
            "ordinal": float(row["ordinal"]),
            "direction": direction,
            "direction_sign": 1.0 if direction == "maximize" else -1.0,
            "unit": str(row.get("unit", "")),
            "hard_boundary": float(row.get("hard_boundary", False)),
        })
        _edge(agent, profile, "has_embodied_pareto_dimension", dimension)
        dimensions_by_name[str(row["name"])] = dimension
    return {
        "profile": profile,
        "dimensions": dimensions_by_name,
        "candidate_count": 0,
    }


def publish_pareto_candidate(
    agent,
    profile_result: dict[str, Any],
    measurements: Mapping[str, float],
    *,
    identity: str,
    verified: bool = True,
):
    """Publish one immutable measured point in an existing profile."""
    dimensions = profile_result["dimensions"]
    if set(measurements) != set(dimensions):
        missing = sorted(set(dimensions) - set(measurements))
        extra = sorted(set(measurements) - set(dimensions))
        raise ValueError(
            f"candidate dimensions are incomplete: missing={missing}, extra={extra}"
        )
    candidate = agent.s.add_node("EmbodiedParetoCandidate", {
        "identity": str(identity),
        "dominated": 0.0,
        "verified": float(verified),
        "provenance_kind": "immutable_measured_objective_point",
    })
    _edge(
        agent,
        profile_result["profile"],
        "has_embodied_pareto_candidate",
        candidate,
    )
    for name, dimension in dimensions.items():
        attrs = agent.s.node(dimension)["attrs"]
        raw_value = float(measurements[name])
        value = agent.s.add_node("EmbodiedParetoValue", {
            "dimension_ordinal": float(attrs["ordinal"]),
            "raw_value": raw_value,
            "signed_value": raw_value * float(attrs["direction_sign"]),
            "verified": float(verified),
        })
        _edge(agent, candidate, "has_embodied_pareto_value", value)
        _edge(agent, value, "measures_embodied_pareto_dimension", dimension)
    profile_result["candidate_count"] += 1
    agent.inner.set_attr(
        profile_result["profile"],
        "candidate_count",
        float(profile_result["candidate_count"]),
    )
    return candidate


def evaluate_pareto_profile(agent, profile_result) -> dict[str, Any]:
    """Request bounded System-2 dominance recognition for a complete profile."""
    profile = profile_result["profile"]
    epoch = float(agent.s.node(profile)["attrs"].get("epoch", 0.0)) + 1.0
    agent.inner.set_attr(profile, "epoch", epoch)
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "area": "cognitive_pareto",
        "enabled": 1.0,
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
    """Read the relational frontier; absence of domination is authoritative."""
    return tuple(
        candidate
        for candidate in agent.inner.neighbours(
            profile_result["profile"],
            "has_embodied_pareto_candidate",
        )
        if not agent.inner.neighbours(
            candidate,
            "is_dominated_by_embodied_candidate",
        )
    )


__all__ = [
    "evaluate_pareto_profile",
    "install_pareto_profile",
    "pareto_frontier",
    "publish_pareto_candidate",
]
