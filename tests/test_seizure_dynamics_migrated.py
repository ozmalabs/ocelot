"""Seizure-dynamics seed: default-OFF safety + the engine reproduces the
standing -> persist/die -> traveling bifurcation FROM the give.

The load-bearing safety test is byte-identity-when-off: adding a pathology
capability to the core cognition engine MUST NOT change normal cognition when
the dial is off. We prove it two ways:
  1. The seizure rule is INERT on the real scheduler graph (no CognitiveArea
     carries a sz_managed_by edge -> the rule never matches) -> the scheduler's
     settlement is byte-identical with the seed loaded vs not.
  2. Even a lattice that IS seizure-managed but has sz_enabled=0 does not move
     any residual (the where-guard blocks the rule).
"""
from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREA_SEED = os.path.join(ROOT, "seeds", "cognitive_areas.json")
SCHEDULER_SEED = os.path.join(ROOT, "seeds", "cognitive_scheduler.json")
SZ_SEED = os.path.join(ROOT, "seeds", "seizure_dynamics.json")


def _load(agent, *paths):
    for p in paths:
        agent.inner.load_seed_manifest(json.load(open(p)), agent.agent)


def _scheduler_scenario(agent):
    """A small real-scheduler scenario: an area with two tasks + a residual +
    a projection, driven to fixpoint. Returns a snapshot of every node's attrs."""
    area = agent.s.add_node("CognitiveArea", {
        "name": "test", "status": "active", "input_epoch": 2,
        "logical_tick": 0, "desired_workers": 1, "effort": 0.0,
        "last_residual_epoch": -1,
    })
    dst = agent.s.add_node("CognitiveArea", {
        "name": "dst", "status": "active", "input_epoch": 1,
        "logical_tick": 0, "desired_workers": 1, "effort": 0.0,
        "last_residual_epoch": -1,
    })
    agent.inner.add_edge_unchecked(area, "projects_to", dst)
    res = agent.s.add_node("Residual", {"epoch": 5})
    agent.inner.add_edge_unchecked(area, "has_residual", res)
    load = agent.s.add_node("AreaLoad", {
        "queued": 3, "failed": 0, "fold_conflicts": 0, "capacity_workers": 2,
    })
    agent.inner.add_edge_unchecked(area, "has_area_load", load)
    for i, (sal, ie) in enumerate([(0.9, 2), (0.2, 2)]):
        t = agent.s.add_node("CognitiveTask", {
            "status": "pending", "kind": "abs_diff_energy", "payload": [i, i + 1],
            "input_epoch": ie, "salience": sal, "logical_time": i, "area": "test",
            "order": 2, "effort": 1,
        })
        agent.inner.add_edge_unchecked(area, "has_task", t)
    agent.inner.run_rules(100000)
    return _snapshot(agent)


def _snapshot(agent):
    snap = {}
    for nid in agent.inner.nodes(None):
        n = agent.s.node(nid)
        snap[repr(nid)] = (n["type"], dict(sorted(n["attrs"].items())))
    return snap


def test_scheduler_settlement_byte_identical_with_seed_present_off():
    """The real scheduler reaches the SAME graph state whether or not the
    seizure seed is loaded (its rule can't match the scheduler's nodes)."""
    a0 = WorldAdapter(seeds=())
    _load(a0, AREA_SEED, SCHEDULER_SEED)
    snap_without = _scheduler_scenario(a0)

    a1 = WorldAdapter(seeds=())
    _load(a1, AREA_SEED, SCHEDULER_SEED, SZ_SEED)   # seizure seed PRESENT (off)
    snap_with = _scheduler_scenario(a1)

    # Same node types and same attrs, node-for-node (ids are assigned in the
    # same order both times since the scenario builds the same nodes).
    assert set(snap_without) == set(snap_with)
    for nid in snap_without:
        assert snap_without[nid][0] == snap_with[nid][0], f"type differs at {nid}"
        assert snap_without[nid][1] == snap_with[nid][1], (
            f"attrs differ at node {nid}: {snap_without[nid][1]} vs {snap_with[nid][1]}"
        )


def _mini_lattice(agent, sz_enabled, alpha=0.5, give=0.0, n=3):
    cfg = agent.s.add_node("SeizureConfig", {
        "sz_enabled": float(sz_enabled), "give": give, "alpha": alpha,
        "g": 0.8, "budget": 0.8, "c_gen": 1.8, "gen_cap": 2.5, "r_max": 60.0,
    })
    ids = {}
    for r in range(n):
        for c in range(n):
            nid = agent.s.add_node("CognitiveArea", {
                "name": f"a_{r}_{c}", "status": "active",
                "residual": 5.0, "next_residual": 5.0, "drive": 0.0,
                "ticking": 1.0, "clocked": 1.0,
            })
            agent.inner.add_edge_unchecked(nid, "sz_managed_by", cfg)
            ids[(r, c)] = nid
    return ids


def test_disabled_flag_moves_no_residual():
    """sz_enabled=0 -> the where-guard blocks the rule -> next_residual stays
    at its initial value (no settlement happens)."""
    agent = WorldAdapter(seeds=())
    _load(agent, AREA_SEED, SZ_SEED)
    ids = _mini_lattice(agent, sz_enabled=0)
    agent.inner.run_rules(100000)
    for nid in ids.values():
        # next_residual untouched (rule inert); residual untouched.
        assert agent.s.node(nid)["attrs"]["next_residual"] == 5.0
        assert agent.s.node(nid)["attrs"]["residual"] == 5.0


def test_enabled_flag_settles_residual():
    """sz_enabled=1 -> the rule fires and writes a DIFFERENT next_residual
    (proves the same seed, same nodes, only the flag decides)."""
    agent = WorldAdapter(seeds=())
    _load(agent, AREA_SEED, SZ_SEED)
    ids = _mini_lattice(agent, sz_enabled=1, give=1.0, alpha=0.0)
    agent.inner.run_rules(100000)
    # With give=1, alpha=0, ticking=1: an overloaded area sheds hard -> next<5.
    center = ids[(1, 1)]
    assert agent.s.node(center)["attrs"]["next_residual"] < 5.0


def test_good_null_alpha_zero_only_dissipates():
    """The anti-plant good null, in miniature: with the positive-feedback gain
    alpha=0, one clock step never RAISES total residual (pure dissipation)."""
    agent = WorldAdapter(seeds=())
    _load(agent, AREA_SEED, SZ_SEED)
    ids = _mini_lattice(agent, sz_enabled=1, give=0.0, alpha=0.0)
    before = sum(agent.s.node(n)["attrs"]["residual"] for n in ids.values())
    agent.inner.run_rules(100000)
    agent.inner.fold_clock_edge()
    after = sum(agent.s.node(n)["attrs"]["residual"] for n in ids.values())
    assert after <= before + 1e-9, "alpha=0 must not regenerate residual"


def test_positive_feedback_can_raise_residual():
    """The mirror: with alpha>0 and give off, overload REGENERATES -- total
    residual can grow across a step (the positive-feedback term is live)."""
    agent = WorldAdapter(seeds=())
    _load(agent, AREA_SEED, SZ_SEED)
    # No ticking this step -> no settle/shed/push; only gen (added every step)
    # can move residual. alpha>0 over threshold -> grows.
    cfg = agent.s.add_node("SeizureConfig", {
        "sz_enabled": 1.0, "give": 0.0, "alpha": 0.5,
        "g": 0.8, "budget": 0.8, "c_gen": 1.8, "gen_cap": 2.5, "r_max": 60.0,
    })
    nid = agent.s.add_node("CognitiveArea", {
        "name": "solo", "status": "active", "residual": 5.0,
        "next_residual": 5.0, "drive": 0.0, "ticking": 0.0, "clocked": 1.0,
    })
    agent.inner.add_edge_unchecked(nid, "sz_managed_by", cfg)
    agent.inner.run_rules(100000)
    agent.inner.fold_clock_edge()
    # gen = 0.5*min(5-1.8, 2.5) = 0.5*2.5 = 1.25 -> residual 5 -> 6.25
    assert agent.s.node(nid)["attrs"]["residual"] > 5.0
