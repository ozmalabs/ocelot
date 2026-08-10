"""Pure host-boundary transduction helpers for embodied experiments.

These functions only copy simulator observations into graph attributes or
read graph-authored outputs back out.  They do not rank actions, retain policy
state, infer outcomes, or learn.  Those operations belong to Rust graph rules.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import math
from typing import Any

from .sensorimotor_transducer import sensed_orientation, sensed_vector


class GraphBoundaryCardinalityError(RuntimeError):
    """A graph output boundary did not contain exactly one expected node."""


def add_unchecked_edge(
    agent: Any,
    source: Any,
    edge_type: str,
    target: Any,
) -> None:
    """Insert a graph-authored experiment edge across binding versions."""
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def unique_node(agent: Any, node_type: str) -> Any:
    """Return the sole node of ``node_type`` or reject an ambiguous boundary."""
    nodes = list(agent.s.nodes(node_type))
    if len(nodes) != 1:
        raise GraphBoundaryCardinalityError(
            f"expected one {node_type}, found {len(nodes)}"
        )
    return nodes[0]


def matching_neighbours(
    agent: Any,
    source: Any,
    edge_type: str,
    *,
    attrs: Mapping[str, Any],
) -> list[Any]:
    """Mechanically filter adjacent nodes by exact graph attributes."""
    return [
        node
        for node in agent.inner.neighbours(source, edge_type)
        if all(
            agent.s.node(node)["attrs"].get(key) == value
            for key, value in attrs.items()
        )
    ]


def unique_neighbour(
    agent: Any,
    source: Any,
    edge_type: str,
    *,
    attrs: Mapping[str, Any],
    description: str,
) -> Any:
    """Return one matching graph output without selecting among candidates."""
    matches = matching_neighbours(
        agent,
        source,
        edge_type,
        attrs=attrs,
    )
    if len(matches) != 1:
        raise GraphBoundaryCardinalityError(
            f"graph authored {len(matches)} {description}"
        )
    return matches[0]


def pose_attrs(observation: Mapping[str, Any], prefix: str) -> dict[str, float]:
    """Flatten the declared sensed position/quaternion into graph attributes."""
    position = sensed_vector(dict(observation), "position")
    quaternion = sensed_orientation(dict(observation))
    return {
        f"{prefix}_x": float(position[0]),
        f"{prefix}_y": float(position[1]),
        f"{prefix}_z": float(position[2]),
        f"{prefix}_qx": float(quaternion[0]),
        f"{prefix}_qy": float(quaternion[1]),
        f"{prefix}_qz": float(quaternion[2]),
        f"{prefix}_qw": float(quaternion[3]),
    }


def basic_sensor_state_attrs(
    observation: Mapping[str, Any],
    *,
    state_seq: int,
) -> dict[str, float]:
    """Build the common raw pose/sample envelope used by body runners."""
    return {
        "has_sensor_state": 1.0,
        "sensor_requires_inference": float(
            observation.get("sensor_requires_inference", 0.0)
        ),
        **pose_attrs(observation, "state"),
        "state_seq": float(state_seq),
    }


def stamp_attrs(
    agent: Any,
    node: Any,
    attrs: Mapping[str, Any],
) -> None:
    """Copy already-shaped host values onto a graph node."""
    for key, value in attrs.items():
        agent.inner.set_attr(node, key, value)


def neighbour_rows(
    agent: Any,
    source: Any,
    edge_type: str,
    *,
    fields: Iterable[str],
    sort_fields: Sequence[str] = ("ordinal",),
) -> list[dict[str, Any]]:
    """Read a stable projection of graph rows for reporting only."""
    field_names = tuple(fields)
    rows = [
        {
            key: agent.s.node(node)["attrs"].get(key)
            for key in field_names
        }
        for node in agent.inner.neighbours(source, edge_type)
    ]
    return sorted(
        rows,
        key=lambda row: tuple(
            (0, float(row[key]))
            if isinstance(row.get(key), (int, float))
            else (1, str(row.get(key, "")))
            for key in sort_fields
        ),
    )


def enact_graph_force_request(
    agent: Any,
    episode: Any,
    world: Any,
    observation: Mapping[str, Any],
    *,
    prefix: str,
) -> dict[str, Any] | None:
    """Mechanically translate one graph-authored normalized force request.

    The graph owns request timing, direction, magnitude and duration. This
    boundary merely validates the unique pending request, converts body
    weights to newtons, enacts it, and acknowledges the sequence number.
    """
    attrs = agent.s.node(episode)["attrs"]
    requested = float(attrs.get(f"{prefix}_challenge_request_seq", 0.0))
    applied = float(attrs.get(f"{prefix}_challenge_applied_seq", 0.0))
    if requested <= applied:
        return None
    current_request = float(attrs.get("request_seq", 0.0))
    if requested != current_request:
        raise GraphBoundaryCardinalityError(
            f"{prefix} force request {requested} does not match current "
            f"motor request {current_request}"
        )
    external_authority = float(
        attrs.get(f"{prefix}_external_impulse_authority", 1.0)
    )
    if external_authority <= 0.0:
        agent.inner.set_attr(
            episode,
            f"{prefix}_challenge_applied_seq",
            requested,
        )
        return {
            "request_seq": requested,
            "challenge_ordinal": float(
                attrs.get(f"{prefix}_active_challenge_ordinal", -1.0)
            ),
            "force_body_weights": [0.0, 0.0, 0.0],
            "force_newtons": [0.0, 0.0, 0.0],
            "frames": 0,
        }
    direction = tuple(
        float(attrs.get(f"{prefix}_force_{axis}_body_weights", 0.0))
        for axis in ("x", "y", "z")
    )
    if not all(math.isfinite(value) for value in direction):
        raise ValueError(f"{prefix} force request is not finite")
    frames_value = attrs.get(f"{prefix}_force_frames", 0.0)
    if (
        isinstance(frames_value, bool)
        or not isinstance(frames_value, (int, float))
        or int(frames_value) != frames_value
        or frames_value < 1
    ):
        raise ValueError(f"{prefix} force frame count is invalid")
    body_weight = (
        float(observation["body_mass"])
        * float(observation["gravity_acceleration"])
    )
    force_newtons = tuple(value * body_weight for value in direction)
    world.apply_force_pulse(force_newtons, frames=int(frames_value))
    agent.inner.set_attr(
        episode,
        f"{prefix}_challenge_applied_seq",
        requested,
    )
    return {
        "request_seq": requested,
        "challenge_ordinal": float(
            attrs.get(f"{prefix}_active_challenge_ordinal", -1.0)
        ),
        "force_body_weights": list(direction),
        "force_newtons": list(force_newtons),
        "frames": int(frames_value),
    }


__all__ = [
    "GraphBoundaryCardinalityError",
    "add_unchecked_edge",
    "basic_sensor_state_attrs",
    "enact_graph_force_request",
    "matching_neighbours",
    "neighbour_rows",
    "pose_attrs",
    "stamp_attrs",
    "unique_neighbour",
    "unique_node",
]
