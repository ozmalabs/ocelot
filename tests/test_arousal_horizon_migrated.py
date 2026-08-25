"""THE PLANNING HORIZON IS DERIVED FROM REGULATION, NOT SET.

Three rungs closed on the same admission: the compression was STIPULATED — a mask
or a budget handed to a rule by a fixture, with nothing saying why stress should
produce either. This is the derivation.

An agent can only plan as far ahead as it can stay regulated, so its projection
budget is the tick at which its own projected arousal would leave its own window
of tolerance. That is not a new computation: it is exactly the escape the
future-manifold audit already performs, run on the arousal dimension with the
window as the allowed tube. No stress coefficient, no tuned rate.

SCOPE, stated precisely because it is easy to overclaim: this seed derives
WINDOW -> HORIZON. The other half of the chain — stressor -> arousal ->
dysregulation -> window narrows — is `arousal_window_coreg`'s, predates this
question, and has its own gates. These tests drive the window directly and do not
re-test it.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))
from substrate.world_adapter import WorldAdapter  # noqa: E402

AROUSAL = [[0.0], [1.0], [2.0], [3.0], [4.0], [5.0], [6.0], [7.0]]
CAPACITY = 8.0


def _agent(half_width):
    a = WorldAdapter(seeds=())
    for sd in ("arousal_window_coreg", "arousal_horizon"):
        a.inner.load_seed_manifest(
            json.load(open(ROOT / "seeds" / f"{sd}.json")), a.agent)
    g = a.s
    who = g.add_node("Agent", {"name": "infant"})
    aff = g.add_node("AffectiveState", {"arousal": 0.0, "dysregulated": 0.0,
                                        "arousal_projection": AROUSAL,
                                        "future_manifold_values": AROUSAL})
    a.inner.add_edge_unchecked(who, "has_affective_state", aff)
    wot = g.add_node("WindowOfTolerance", {"lo": -half_width, "hi": half_width,
                                           "half_width": half_width})
    g.add_edge(who, "has_window", wot)
    cap = g.add_node("ProjectionCapacity", {
        "future_manifold_projection_budget": CAPACITY,
        "future_manifold_physical_horizon": float(len(AROUSAL))})
    g.add_edge(who, "has_projection_capacity", cap)
    pol = g.add_node("ManifoldPolicy", {
        "future_manifold_projection_budget": -1.0,
        "future_manifold_physical_horizon": float(len(AROUSAL))})
    g.add_edge(who, "governs_horizon", pol)
    a.inner.run_rules(1_000_000)
    return a, g, wot, pol


def _horizon(g, pol):
    return float(g.node(pol)["attrs"].get("future_manifold_projection_budget", -1.0))


def test_the_horizon_is_written_by_a_rule_not_by_the_fixture():
    """The fixture hands the policy `-1`, a value no audit can produce. Anything
    else means a rule computed it."""
    _a, g, _w, pol = _agent(4.0)
    assert g.node(pol)["attrs"].get("ah_derived") == 1.0
    assert _horizon(g, pol) > 0.0, "the horizon was never derived"


def test_a_narrower_window_yields_a_shorter_horizon():
    """THE DERIVATION. Monotone, and nothing about stress appears in the rule —
    only the window and the agent's own projected arousal."""
    seen = [(hw, _horizon(*_agent(hw)[1::2])) for hw in (4.0, 3.0, 2.0, 1.0)]
    horizons = [h for _hw, h in seen]
    # the window NARROWS across the sweep, so the horizon must DESCEND
    assert horizons == sorted(horizons, reverse=True), seen
    assert horizons[0] > horizons[-1], f"the window did not move the horizon: {seen}"


def test_a_window_wide_enough_to_never_escape_leaves_the_full_capacity():
    """The ceiling case. `earliest_decisive_tick` is 0 when nothing escapes, and
    0 must read as "the whole capacity is available", never as "no horizon"."""
    _a, g, _w, pol = _agent(64.0)
    assert _horizon(g, pol) == CAPACITY


def test_the_agent_cannot_widen_its_own_horizon_by_wanting_more():
    """WHY THIS DERIVATION MATTERS, and what it resolves.

    `COMPRESSION_MODELS_RESULTS.md` showed temporal compression IS recoverable by
    more budget, which conditioned the earlier "evidence is inert" claim. Once the
    budget is DERIVED, that recovery is no longer something the agent can help
    itself to: raising the physiological capacity does not lengthen the horizon
    while the window stays narrow, because the window binds first.

    So the clinical shape — you cannot reason someone out of dysregulation, but
    regulation restores them — falls out of the derivation instead of being
    stipulated by it."""
    a = WorldAdapter(seeds=())
    for sd in ("arousal_window_coreg", "arousal_horizon"):
        a.inner.load_seed_manifest(
            json.load(open(ROOT / "seeds" / f"{sd}.json")), a.agent)
    g = a.s
    who = g.add_node("Agent", {"name": "infant"})
    aff = g.add_node("AffectiveState", {"arousal": 0.0, "dysregulated": 0.0,
                                        "arousal_projection": AROUSAL,
                                        "future_manifold_values": AROUSAL})
    a.inner.add_edge_unchecked(who, "has_affective_state", aff)
    wot = g.add_node("WindowOfTolerance", {"lo": -1.0, "hi": 1.0, "half_width": 1.0})
    g.add_edge(who, "has_window", wot)
    cap = g.add_node("ProjectionCapacity", {
        "future_manifold_projection_budget": 8.0,
        "future_manifold_physical_horizon": float(len(AROUSAL))})
    g.add_edge(who, "has_projection_capacity", cap)
    pol = g.add_node("ManifoldPolicy", {
        "future_manifold_projection_budget": -1.0,
        "future_manifold_physical_horizon": float(len(AROUSAL))})
    g.add_edge(who, "governs_horizon", pol)
    a.inner.run_rules(1_000_000)
    narrow = _horizon(g, pol)

    g.set_attr(cap, "future_manifold_projection_budget", 64.0)   # more capacity
    a.inner.run_rules(1_000_000)
    assert _horizon(g, pol) == narrow, (
        f"capacity alone lengthened the horizon ({narrow} -> {_horizon(g, pol)}) — "
        f"the window is not binding, and the derivation is not doing its work")

    for hw in (1.0, 8.0):                                        # widen the window
        g.set_attr(wot, "half_width", hw)
        g.set_attr(wot, "lo", -hw)
        g.set_attr(wot, "hi", hw)
        a.inner.run_rules(1_000_000)
    assert _horizon(g, pol) > narrow, (
        "widening the window did not restore the horizon — regulation must be the "
        "thing that recovers it")
