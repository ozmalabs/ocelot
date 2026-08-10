from __future__ import annotations

import pytest

from domains.embodied_graph_transducer import (
    GraphBoundaryCardinalityError,
    add_unchecked_edge,
    basic_sensor_state_attrs,
    neighbour_rows,
    pose_attrs,
    stamp_attrs,
    unique_neighbour,
    unique_node,
)


class _Graph:
    def __init__(self) -> None:
        self.rows = {}

    def nodes(self, node_type):
        return [
            node for node, row in self.rows.items()
            if row["type"] == node_type
        ]

    def node(self, node):
        return self.rows[node]


class _Inner:
    def __init__(self, graph) -> None:
        self.graph = graph
        self.edges = []

    def add_edge_unchecked(self, source, edge_type, target, attrs):
        self.edges.append((source, edge_type, target, attrs))

    def neighbours(self, source, edge_type):
        return [
            target
            for edge_source, edge_name, target, _ in self.edges
            if edge_source == source and edge_name == edge_type
        ]

    def set_attr(self, node, key, value):
        self.graph.rows[node]["attrs"][key] = value


class _Agent:
    def __init__(self) -> None:
        self.s = _Graph()
        self.inner = _Inner(self.s)


def _node(agent, name, node_type, **attrs):
    agent.s.rows[name] = {"type": node_type, "attrs": attrs}
    return name


def test_edge_lookup_and_reporting_are_mechanical():
    agent = _Agent()
    episode = _node(agent, "episode", "Episode")
    later = _node(
        agent,
        "later",
        "Trial",
        status="issued",
        epoch=1.0,
        ordinal=2.0,
        token="b",
    )
    earlier = _node(
        agent,
        "earlier",
        "Trial",
        status="closed",
        epoch=0.0,
        ordinal=1.0,
        token="a",
    )
    add_unchecked_edge(agent, episode, "has_trial", later)
    add_unchecked_edge(agent, episode, "has_trial", earlier)

    assert unique_node(agent, "Episode") == episode
    assert unique_neighbour(
        agent,
        episode,
        "has_trial",
        attrs={"status": "issued", "epoch": 1},
        description="issued trials",
    ) == later
    assert neighbour_rows(
        agent,
        episode,
        "has_trial",
        fields=("token", "ordinal"),
    ) == [
        {"token": "a", "ordinal": 1.0},
        {"token": "b", "ordinal": 2.0},
    ]


def test_unique_boundaries_reject_missing_or_ambiguous_graph_output():
    agent = _Agent()
    episode = _node(agent, "episode", "Episode")
    with pytest.raises(GraphBoundaryCardinalityError):
        unique_node(agent, "Policy")
    with pytest.raises(GraphBoundaryCardinalityError):
        unique_neighbour(
            agent,
            episode,
            "has_trial",
            attrs={"status": "issued"},
            description="issued trials",
        )


def test_pose_and_state_stamping_only_copy_declared_sensor_values():
    agent = _Agent()
    episode = _node(agent, "episode", "Episode")
    observation = {
        "base_position": (1.0, 2.0, 3.0),
        "base_orientation_xyzw": (0.0, 0.0, 0.0, 1.0),
        "sensor_requires_inference": 1.0,
    }
    assert pose_attrs(observation, "pre") == {
        "pre_x": 1.0,
        "pre_y": 2.0,
        "pre_z": 3.0,
        "pre_qx": 0.0,
        "pre_qy": 0.0,
        "pre_qz": 0.0,
        "pre_qw": 1.0,
    }
    attrs = basic_sensor_state_attrs(observation, state_seq=7)
    stamp_attrs(agent, episode, attrs)
    assert agent.s.node(episode)["attrs"]["state_seq"] == 7.0
    assert agent.s.node(episode)["attrs"]["state_x"] == 1.0
    assert agent.s.node(episode)["attrs"]["sensor_requires_inference"] == 1.0
