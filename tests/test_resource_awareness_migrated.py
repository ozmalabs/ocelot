"""Per-action self-attribute signed-delta EMAs — emergent resource awareness,
migrated. The bookkeeping (mirroring the agent's own `my_*` self-state onto the
agent node, the decision-time snapshot, the per-(action, attr) signed-delta
EMA) runs in the WorldAdapter; the bidirectionality test and delta-sum are
mechanical readouts over graph data; the scarcity VALUE of a resource is the
SEEDED `resource_value_term` (read via EvalSubgraph). No CuriousAgent.

Covers tests/test_resource_awareness:
  • attack consistently lowering ammo → negative ammo delta EMA;
  • a pickup consistently raising health → positive health delta EMA;
  • symmetric (positional) movement → delta EMA near zero;
  • action_self_attr_delta_sum combining bidirectional resource attrs, with a
    positional attr excluded by name pattern;
  • monotonic-only counters (kill_count) excluded — not bidirectional;
  • an untracked action returns 0.
PLUS the seeded scarcity value (resource_value_term) on a materialised Resource.

The original copied the world's self-AgentMarker attrs onto agent_root inside
observe(); here set_self_attrs is the adapter's mechanical equivalent. The
agent's `my_world_id = "me"` selection is the I/O choice of which marker is the
self — modelled by reading that marker's scalar attrs as my_*.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def _self_attrs(ammo, health):
    """The self-marker's scalar attrs, as the adapter would read them off the
    world node whose id == the agent's self-id ('me'), keyed my_*."""
    return {"my_ammo_bin": float(ammo), "my_health_bin": float(health)}


def _delta(wa, action, attr_ema):
    return wa.s.node(wa._action_stat_nodes[action])["attrs"].get(attr_ema, 0.0)


def test_attack_accumulates_negative_ammo_delta():
    """If attack consistently lowers ammo, the per-(attack, ammo_bin)
    signed-delta EMA accumulates negative."""
    wa = WorldAdapter()
    for i in range(1000):
        pre, post = 1000 - i, 999 - i
        wa.set_self_attrs(_self_attrs(pre, 3))
        wa.last_my_attrs_at_decision = {"my_ammo_bin": float(pre), "my_health_bin": 3.0}
        wa.set_self_attrs(_self_attrs(post, 3))
        wa.record_self_attr_deltas("attack")
    delta = _delta(wa, "attack", "delta_my_ammo_bin_ema")
    assert delta < -0.5, f"expected consistent ammo loss; got {delta}"


def test_pickup_accumulates_positive_armor_delta():
    """If an action consistently raises an attr, the signed delta EMA
    becomes positive."""
    wa = WorldAdapter()
    for _ in range(1000):
        wa.set_self_attrs(_self_attrs(10, 1))
        wa.last_my_attrs_at_decision = {"my_ammo_bin": 10.0, "my_health_bin": 1.0}
        wa.set_self_attrs(_self_attrs(10, 3))   # health gained
        wa.record_self_attr_deltas("pickup_health")
    delta = _delta(wa, "pickup_health", "delta_my_health_bin_ema")
    assert delta > 0.5, f"expected consistent health gain; got {delta}"


def test_symmetric_movement_averages_near_zero():
    """An attr that goes up and down equally (positional movement)
    yields a signed-delta EMA near zero."""
    wa = WorldAdapter()
    for i in range(1000):
        a_pre = 5 if i % 2 == 0 else 6
        a_post = 6 if i % 2 == 0 else 5
        wa.set_self_attrs(_self_attrs(a_pre, 3))
        wa.last_my_attrs_at_decision = {"my_ammo_bin": float(a_pre), "my_health_bin": 3.0}
        wa.set_self_attrs(_self_attrs(a_post, 3))
        wa.record_self_attr_deltas("walk")
    delta = _delta(wa, "walk", "delta_my_ammo_bin_ema")
    assert abs(delta) < 0.2, f"symmetric movement should average to zero; got {delta}"


def test_action_self_attr_delta_sum_combines_attrs():
    """The delta-sum sums signed-delta EMAs across attrs the agent has
    observed are bidirectional resources. Both ammo and health qualify when
    ONE action raises them and ANOTHER lowers them. Positional attrs are
    excluded by name pattern."""
    wa = WorldAdapter()
    # Establish bidirectionality: ammo and health both have at least one
    # action with a positive delta and one with a negative.
    pickup = wa._ensure_action_stat("pickup")
    wa.inner.set_attr(pickup, "delta_my_ammo_bin_ema", +2.0)
    wa.inner.set_attr(pickup, "delta_my_health_bin_ema", +1.0)
    damage = wa._ensure_action_stat("take_damage")
    wa.inner.set_attr(damage, "delta_my_health_bin_ema", -1.0)
    # The action under test.
    nid = wa._ensure_action_stat("test")
    wa.inner.set_attr(nid, "delta_my_ammo_bin_ema", -1.0)
    wa.inner.set_attr(nid, "delta_my_health_bin_ema", +0.5)
    wa.inner.set_attr(nid, "delta_my_x_bin_ema", 0.0)   # positional, excluded
    total = wa.action_self_attr_delta_sum("test")
    # ammo (-1.0) + health (+0.5) = -0.5; x_bin excluded.
    assert abs(total - (-0.5)) < 1e-9


def test_monotonic_counters_excluded_as_resources():
    """An attr that only ever increases (kill_count) doesn't qualify as a
    resource — no action ever shows a negative delta, so it fails the
    bidirectionality test and is skipped."""
    wa = WorldAdapter()
    a1 = wa._ensure_action_stat("attack")
    wa.inner.set_attr(a1, "delta_my_kill_count_ema", +0.5)
    a2 = wa._ensure_action_stat("noop")
    wa.inner.set_attr(a2, "delta_my_kill_count_ema", +0.1)
    # kill_count only ever increases — not bidirectional.
    resources = wa._bidirectional_resource_attrs()
    assert "kill_count" not in resources
    # Sum is 0 because no bidirectional resource exists.
    assert wa.action_self_attr_delta_sum("attack") == 0.0


def test_untracked_action_returns_zero():
    wa = WorldAdapter()
    assert wa.action_self_attr_delta_sum("never_done") == 0.0


def test_resource_scarcity_value_is_the_seeded_term():
    """A materialised Resource's scarcity value is the SEEDED
    resource_value_term: 1 - current/observed_max — read via EvalSubgraph,
    not reimplemented in the adapter."""
    wa = WorldAdapter()
    wa.ensure_resource("my_ammo_bin", 10.0)   # observed_max = 10
    wa.ensure_resource("my_ammo_bin", 3.0)    # depletes to 3; max stays 10
    assert abs(wa.resource_scarcity("my_ammo_bin") - 0.7) < 1e-9   # 1 - 3/10
    # full resource → zero scarcity.
    wa.ensure_resource("my_health_bin", 5.0)
    assert abs(wa.resource_scarcity("my_health_bin") - 0.0) < 1e-9
    # untracked resource → 0.0.
    assert wa.resource_scarcity("my_unknown") == 0.0
