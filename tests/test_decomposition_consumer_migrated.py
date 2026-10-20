"""Execution gates for decomposition_consumer (P1.A2)."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "decomposition_consumer.json"
GENERATOR = ROOT / "scripts" / "gen_decomposition_consumer_seed.py"

for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _fresh(seeds=("decomposition_consumer",), *, enabled=False):
    agent = WorldAdapter(seeds=seeds)
    policies = agent.s.nodes("DecompositionConsumerPolicy")
    assert len(policies) == 1
    if enabled:
        agent.s.set_attr(policies[0], "enabled", 1.0)
    return agent


def _setup_axis_with_keys(agent, keys, *, add_decomposition_edge=True):
    ax = agent.s.add_node("CapabilityAxis", {
        "is_axis": 1.0,
        "saturation": 0.2,
        "shortfall": 0.7,
        "mf_stall": 0,
        "capability_keys": list(keys),
    })
    key_nodes = []
    for name in keys:
        ck = agent.s.add_node("CapKey", {"name": name})
        _edge(agent, ax, "requires_key", ck)
        key_nodes.append(ck)
    mi = agent.s.add_node("Impasse", {
        "order": 3,
        "acted_order": 2 if not add_decomposition_edge else 3,
        "kind": "escalation",
        "resolved": False,
    })
    _edge(agent, mi, "about_axis", ax)
    if add_decomposition_edge:
        _edge(agent, mi, "needs_decomposition", ax)
    return mi, ax, key_nodes


def test_generator_reproduces_committed_seed_exactly():
    before = SEED.read_bytes()
    subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert SEED.read_bytes() == before


def test_disabled_policy_does_nothing():
    agent = _fresh(enabled=False)
    mi, ax, _ = _setup_axis_with_keys(agent, ["alpha", "beta", "gamma"])

    agent.tick()

    assert agent.s.neighbours(ax, "decomposes_into") == []
    assert "dc_handled" not in agent.s.node(mi)["attrs"]


def test_three_keys_partition_into_three_distinct_child_axes_and_dedup():
    agent = _fresh(enabled=True)
    parent_keys = ["alpha", "beta", "gamma"]
    mi, ax, key_nodes = _setup_axis_with_keys(agent, parent_keys)

    assert agent.tick() > 0

    children = agent.s.neighbours(ax, "decomposes_into")
    assert len(children) == 3

    decomposed_keys = set()
    for child in children:
        attrs = agent.s.node(child)["attrs"]
        assert attrs["is_axis"] == 1.0
        assert attrs["subskill"] == 1.0
        assert attrs["shortfall"] == pytest.approx(0.6)
        assert attrs["decomposed_key"] in parent_keys
        assert list(attrs["capability_keys"]) == [attrs["decomposed_key"]]
        assert list(attrs["capability_keys"]) != parent_keys
        decomposed_keys.add(attrs["decomposed_key"])
        req_keys = agent.s.neighbours(child, "requires_key")
        assert len(req_keys) == 1
        assert agent.s.node(req_keys[0])["attrs"]["name"] == attrs["decomposed_key"]

    assert decomposed_keys == {"alpha", "beta", "gamma"}
    mi_attrs = agent.s.node(mi)["attrs"]
    assert mi_attrs["dc_handled"] == 1
    assert mi_attrs["dc_outcome"] == "partitioned"

    # Re-ticking must not mint duplicate children.
    assert agent.tick() == 0
    assert len(agent.s.neighbours(ax, "decomposes_into")) == 3


def test_single_key_records_no_partition_and_mints_zero_children():
    agent = _fresh(enabled=True)
    mi, ax, _ = _setup_axis_with_keys(agent, ["only_one_key"])

    assert agent.tick() > 0

    assert agent.s.neighbours(ax, "decomposes_into") == []
    mi_attrs = agent.s.node(mi)["attrs"]
    assert mi_attrs["dc_handled"] == 1
    assert mi_attrs["dc_outcome"] == "no_partition"


def test_child_saturations_aggregate_into_child_mean_saturation():
    agent = _fresh(enabled=True)
    _, ax, _ = _setup_axis_with_keys(agent, ["k1", "k2", "k3"])

    assert agent.tick() > 0
    children = agent.s.neighbours(ax, "decomposes_into")
    assert len(children) == 3

    for child, sat in zip(children, (0.2, 0.4, 0.6)):
        agent.s.set_attr(child, "saturation", sat)

    assert agent.tick() > 0
    assert agent.s.node(ax)["attrs"]["child_mean_saturation"] == pytest.approx(0.4)


def test_integration_with_impasse_escalation_order3_reframe():
    agent = _fresh(seeds=("impasse_escalation", "decomposition_consumer"), enabled=True)
    mi, ax, _ = _setup_axis_with_keys(
        agent, ["seg_boundary", "track_identity", "predict_motion"],
        add_decomposition_edge=False,
    )
    op = agent.s.add_node("Operator", {"name": "op_default", "metric": "purity"})
    _edge(agent, ax, "investigated_by", op)

    assert agent.tick() > 0

    # order3_reframe fired and added needs_decomposition -> decomposition_consumer partitioned ax
    assert agent.s.neighbours(mi, "needs_decomposition") == [ax]
    mi_attrs = agent.s.node(mi)["attrs"]
    assert mi_attrs["acted_order"] == 3
    assert mi_attrs["dc_handled"] == 1
    assert mi_attrs["dc_outcome"] == "partitioned"

    children = agent.s.neighbours(ax, "decomposes_into")
    assert len(children) == 3
    for child in children:
        assert agent.s.neighbours(child, "investigated_by") == [op]
