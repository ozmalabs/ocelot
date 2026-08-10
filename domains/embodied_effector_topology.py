"""Mechanical, name-free effector topology for arbitrary body plans.

This module is a transducer, not a controller.  It publishes immutable plant
facts into the graph and never decides which effectors should be coactivated.
Those decisions belong to graph rules and verified physical receipts.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Any, Iterable, Mapping


def _edge(agent, source, edge_type: str, target) -> None:
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _mechanical_graph(
    body_signature: Iterable[tuple[Any, ...]],
) -> tuple[dict[int, int], dict[int, set[int]]]:
    """Decode only topology already present in a name-free shape signature."""
    actuator_joint: dict[int, int] = {}
    parent_by_joint: dict[int, int] = {}
    for relation in body_signature:
        if not relation:
            continue
        if relation[0] == "actuator" and len(relation) >= 3:
            actuator = _integer(relation[1])
            joint = _integer(relation[2])
            if actuator is not None and joint is not None:
                actuator_joint[actuator] = joint
        elif relation[0] == "link" and len(relation) >= 3:
            joint = _integer(relation[1])
            parent = _integer(relation[2])
            if joint is not None and parent is not None:
                parent_by_joint[joint] = parent

    adjacency: dict[int, set[int]] = {
        joint: set() for joint in parent_by_joint
    }
    for joint, parent in parent_by_joint.items():
        if parent < 0:
            continue
        adjacency.setdefault(joint, set()).add(parent)
        adjacency.setdefault(parent, set()).add(joint)
    return actuator_joint, adjacency


def _mechanical_local_features(
    body_signature: Iterable[tuple[Any, ...]],
    actuator_joint: Mapping[int, int],
    adjacency: Mapping[int, set[int]],
) -> dict[int, tuple[int, int, int, int, int]]:
    """Decode name-free joint depth, degree and integer actuator axis class."""
    parent_by_joint: dict[int, int] = {}
    axis_by_actuator: dict[int, tuple[int, int, int]] = {}
    for relation in body_signature:
        if not relation:
            continue
        if relation[0] == "link" and len(relation) >= 3:
            joint = _integer(relation[1])
            parent = _integer(relation[2])
            if joint is not None and parent is not None:
                parent_by_joint[joint] = parent
        elif relation[0] == "actuator" and len(relation) >= 9:
            actuator = _integer(relation[1])
            numerators = tuple(_integer(relation[index]) for index in (3, 5, 7))
            if actuator is not None and all(value is not None for value in numerators):
                axis_by_actuator[actuator] = tuple(
                    0 if value == 0 else (1 if value > 0 else -1)
                    for value in numerators
                )

    depth_cache = {-1: 0}

    def depth(joint: int) -> int:
        trail = []
        cursor = joint
        while cursor not in depth_cache and cursor in parent_by_joint:
            trail.append(cursor)
            cursor = parent_by_joint[cursor]
        value = depth_cache.get(cursor, 0)
        for member in reversed(trail):
            value += 1
            depth_cache[member] = value
        return depth_cache.get(joint, 0)

    return {
        actuator: (
            depth(joint),
            len(adjacency.get(joint, ())),
            *axis_by_actuator.get(actuator, (0, 0, 0)),
        )
        for actuator, joint in actuator_joint.items()
    }


def _path_length(
    adjacency: Mapping[int, set[int]],
    source: int | None,
    target: int | None,
) -> int | None:
    if source is None or target is None:
        return None
    if source == target:
        return 0
    frontier = deque(((source, 0),))
    visited = {source}
    while frontier:
        node, distance = frontier.popleft()
        for neighbour in adjacency.get(node, ()):
            if neighbour == target:
                return distance + 1
            if neighbour not in visited:
                visited.add(neighbour)
                frontier.append((neighbour, distance + 1))
    return None


def install_name_free_effector_topology(
    agent,
    episode,
    options: Iterable[Mapping[str, Any]],
    body_signature: Iterable[tuple[Any, ...]] = (),
    *,
    learning_enabled: bool = True,
) -> dict[str, Any]:
    """Publish effectors and pairwise mechanical relations into ``agent``.

    Optional world facts such as ``mount_ordinal`` and ``hard_coupling_id`` are
    copied mechanically.  In their absence, actuator ordinals and the body
    relation graph provide a conservative topology.  No anatomical names or
    task roles cross this boundary.
    """
    option_rows = tuple(dict(option) for option in options)
    signature = tuple(tuple(row) for row in body_signature)
    actuator_joint, adjacency = _mechanical_graph(signature)
    local_features = _mechanical_local_features(
        signature,
        actuator_joint,
        adjacency,
    )
    topology = agent.s.add_node("EmbodiedEffectorTopology", {
        "effector_count": float(len(option_rows)),
        "relation_count": 0.0,
        "body_relation_count": float(len(signature)),
        "learning_enabled": float(learning_enabled),
        "provenance_kind": "mechanical_name_free_boundary",
    })
    _edge(agent, episode, "has_embodied_effector_topology", topology)

    # Some plants expose primitive commands (one option per effector direction),
    # while others expose already-combined command vectors.  An optional
    # ``effector_commands`` row makes that wiring explicit without assigning
    # semantic names. The latter must produce one effector per physical channel,
    # not one fictitious effector per Cartesian command token.
    channel_rows: dict[int, dict[str, Any]] = {}
    for option in option_rows:
        commands = option.get("effector_commands")
        if isinstance(commands, (tuple, list)):
            for command in commands:
                if not isinstance(command, (tuple, list)) or len(command) < 2:
                    continue
                channel = _integer(command[0])
                if channel is not None:
                    channel_rows.setdefault(channel, {
                        "token": f"opaque_effector:{channel}",
                        "actuator_group": channel,
                        "mount_ordinal": channel,
                        "command_polarity": 0.0,
                        "tonic_default": 0.0,
                    })
    effector_rows = (
        tuple(channel_rows[key] for key in sorted(channel_rows))
        if channel_rows
        else option_rows
    )
    agent.inner.set_attr(topology, "effector_count", float(len(effector_rows)))

    effectors = []
    by_token: dict[str, tuple[Any, ...]] = {}
    by_channel = {}
    for ordinal, option in enumerate(effector_rows):
        vector = option.get("vector")
        vector_mount = (
            _integer(vector[0])
            if isinstance(vector, (tuple, list)) and vector
            else None
        )
        vector_polarity = (
            float(vector[1])
            if isinstance(vector, (tuple, list))
            and len(vector) > 1
            and isinstance(vector[1], (int, float))
            and not isinstance(vector[1], bool)
            else 0.0
        )
        channel = _integer(option.get("actuator_group"))
        mount = _integer(option.get("mount_ordinal"))
        if mount is None:
            mount = actuator_joint.get(
                vector_mount if vector_mount is not None else ordinal
            )
        if mount is None:
            mount = vector_mount
        feature_channel = channel if channel is not None else ordinal
        mount_depth, mount_degree, axis_x, axis_y, axis_z = local_features.get(
            feature_channel,
            (0, 0, 0, 0, 0),
        )
        effector = agent.s.add_node("EmbodiedEffector", {
            "token": str(option["token"]),
            "ordinal": float(ordinal),
            "channel_ordinal": float(channel if channel is not None else -1),
            "mount_ordinal": float(mount if mount is not None else -1),
            "command_polarity": float(
                option.get("command_polarity", vector_polarity)
            ),
            "tonic_default": float(option.get("tonic_default", 0.0)),
            "hard_coupling_id": str(option.get("hard_coupling_id", "")),
            "mount_depth": float(mount_depth),
            "mount_degree": float(mount_degree),
            "axis_x_class": float(axis_x),
            "axis_y_class": float(axis_y),
            "axis_z_class": float(axis_z),
            "provenance_kind": "mechanical_effector_fact",
        })
        _edge(agent, topology, "has_embodied_effector", effector)
        effectors.append(effector)
        by_token[str(option["token"])] = (effector,)
        by_channel[channel if channel is not None else ordinal] = effector

    if channel_rows:
        by_token = {}
        for option in option_rows:
            members = []
            for command in option.get("effector_commands", ()):
                channel = _integer(command[0])
                magnitude = command[1]
                if (
                    channel in by_channel
                    and isinstance(magnitude, (int, float))
                    and not isinstance(magnitude, bool)
                    and float(magnitude) != 0.0
                ):
                    members.append(by_channel[channel])
            by_token[str(option["token"])] = tuple(dict.fromkeys(members))

    relation_count = 0
    for left, right in combinations(effectors, 2):
        left_attrs = agent.s.node(left)["attrs"]
        right_attrs = agent.s.node(right)["attrs"]
        same_channel = (
            left_attrs["channel_ordinal"] >= 0.0
            and left_attrs["channel_ordinal"]
            == right_attrs["channel_ordinal"]
        )
        hard_id = left_attrs["hard_coupling_id"]
        declared_hard = bool(
            hard_id and hard_id == right_attrs["hard_coupling_id"]
        )
        left_mount = _integer(left_attrs["mount_ordinal"])
        right_mount = _integer(right_attrs["mount_ordinal"])
        distance = _path_length(adjacency, left_mount, right_mount)
        # The fast sheet represents segmental locality, not the Cartesian
        # product of a body. One graph edge is the topology-defined unit of
        # adjacency (not a tuned distance threshold); distal coordination is
        # composed by higher assemblies. Plants without a published linkage
        # graph conservatively retain all channel hypotheses.
        if (
            adjacency
            and not same_channel
            and not declared_hard
            and (distance is None or distance > 1)
        ):
            continue
        relation = agent.s.add_node("EmbodiedEffectorRelation", {
            "ordinal": float(relation_count),
            "same_command_channel": float(same_channel),
            "declared_hard_coupling": float(declared_hard),
            "mechanical_path_known": float(distance is not None),
            "mechanical_path_length": float(
                distance if distance is not None else len(signature)
            ),
            "same_mount": float(
                left_mount is not None and left_mount == right_mount
            ),
            "command_polarity_product": float(
                left_attrs["command_polarity"]
                * right_attrs["command_polarity"]
            ),
            "provenance_kind": "mechanical_pair_relation",
        })
        _edge(agent, topology, "has_embodied_effector_relation", relation)
        _edge(agent, relation, "has_embodied_effector_source", left)
        _edge(agent, relation, "has_embodied_effector_target", right)
        relation_count += 1
    agent.inner.set_attr(topology, "relation_count", float(relation_count))
    return {
        "topology": topology,
        "effectors": tuple(effectors),
        "by_token": by_token,
        "relation_count": relation_count,
    }


def bind_effector_models(agent, topology_result, models_by_token) -> None:
    """Mechanically bind domain action models to their opaque effectors."""
    for token, model in models_by_token.items():
        effectors = topology_result["by_token"].get(str(token), ())
        for effector in effectors:
            _edge(agent, model, "models_embodied_effector", effector)


__all__ = [
    "bind_effector_models",
    "install_name_free_effector_topology",
]
