"""State-conditional action affinity discovery, migrated — runs in the
WorldAdapter (no CuriousAgent). Covers tests/test_action_affinities:

Per-instance per-action freshening stats accumulate during
``record_action_freshening`` (attributed to the WorldInstances in view at the
last observe). ``discover_action_affinities`` aggregates them per BodyType and
promotes ``typical_best_action`` when one action's mean freshening is meaningfully
ahead of the runner-up. The promoted affinity lives on the BodyType node as graph
data the scorer can read at decision time — context-dependent action preference,
not a Python heuristic.

The mechanism is map-agnostic: the same promotion works for spatial locations,
social categories, or any BodyType the agent learns about.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world(node_specs, edges=()):
    g = TypedGraph()
    nids = []
    for typ, attrs in node_specs:
        nids.append(g._insert_node(typ, attrs))
    for s, et, t in edges:
        g._insert_edge(nids[s], et, nids[t])
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def test_per_instance_stats_accumulate_on_record():
    """When the adapter records an action's freshening, it is attributed back
    to each WorldInstance in view this tick — both the cumulative count and the
    EMA update."""
    wa = WorldAdapter()
    wa.observe(_world([("AgentMarker", {"id": "x"})]))
    wa.record_action_freshening("forward", frontier_after=3)
    wi_id = wa._instances[("AgentMarker", "x")]
    attrs = wa.s.node(wi_id)["attrs"]
    assert attrs.get("act_forward_n") == 1
    # EMA receives the first observation weighted by alpha (0.01 * 3 = 0.03).
    assert attrs.get("act_forward_freshening_ema", 0) > 0


def test_discover_promotes_clear_winner():
    """When several instances of the same type all show one action yielding much
    higher freshening than others, discovery promotes that action as the
    BodyType's typical_best_action."""
    wa = WorldAdapter()
    for nid in ("A", "B", "C"):
        wa.observe(_world([("SpatialLocation", {"id": nid})]))
        # forward consistently yields high freshening (5), others low (0).
        # Enough iterations for EMA to converge (alpha=0.01 -> ~700 ticks).
        for _ in range(700):
            wa.record_action_freshening("forward", 5)
            wa.record_action_freshening("turn_left", 0)
            wa.record_action_freshening("turn_right", 0)
    affinities = wa.discover_action_affinities()
    sl_promotions = [t for t in affinities if t[0] == "SpatialLocation"]
    assert len(sl_promotions) == 1
    _name, best, mean = sl_promotions[0]
    assert best == "forward"
    assert mean >= 4.0


def test_discover_does_not_promote_when_margin_too_small():
    """If the leader's mean freshening is only marginally higher than the
    runner-up, no promotion happens — the agent doesn't lock in on noise."""
    wa = WorldAdapter()
    for nid in ("A", "B"):
        wa.observe(_world([("SpatialLocation", {"id": nid})]))
        for _ in range(700):
            wa.record_action_freshening("forward", 2)
            wa.record_action_freshening("turn_left", 2)
    sl_promotions = [t for t in wa.discover_action_affinities() if t[0] == "SpatialLocation"]
    assert sl_promotions == []


def test_typical_best_action_stored_as_graph_data():
    """The promoted affinity lives on the BodyType node — graph data the agent
    can read at decision time and other passes can inspect."""
    wa = WorldAdapter()
    for nid in ("A", "B"):
        wa.observe(_world([("SpatialLocation", {"id": nid})]))
        for _ in range(700):
            wa.record_action_freshening("forward", 8)
            wa.record_action_freshening("noop", 0)
    wa.discover_action_affinities()
    bt_id = wa.body_type("SpatialLocation")
    attrs = wa.s.node(bt_id)["attrs"]
    assert attrs.get("typical_best_action") == "forward"
    assert attrs.get("typical_best_action_mean_freshening", 0) >= 6.0


def test_affinity_promotion_is_idempotent():
    """Running discovery twice without new evidence reports no new promotions —
    the BodyType.typical_best_action is unchanged."""
    wa = WorldAdapter()
    for nid in ("A", "B"):
        wa.observe(_world([("SpatialLocation", {"id": nid})]))
        for _ in range(700):
            wa.record_action_freshening("forward", 8)
            wa.record_action_freshening("noop", 0)
    wa.discover_action_affinities()
    second = wa.discover_action_affinities()
    assert second == [], \
        "second pass should report no new promotions when leader hasn't changed"


def test_min_samples_floor_prevents_noisy_promotion():
    """With only one observation per action, the affinity discovery must not
    promote — the sample size is below the min_samples floor."""
    wa = WorldAdapter()
    wa.observe(_world([("SpatialLocation", {"id": "A"})]))
    wa.record_action_freshening("forward", 100)
    wa.record_action_freshening("noop", 0)
    sl = [t for t in wa.discover_action_affinities() if t[0] == "SpatialLocation"]
    assert sl == []


def test_works_across_multiple_instances_of_a_type():
    """All instances of a BodyType pool their per-instance freshening, so the
    type-level promotion fires when they share the same action preference."""
    wa = WorldAdapter()
    sub = _world(
        [
            ("SpatialLocation", {"id": "A"}),
            ("SpatialLocation", {"id": "B"}),
            ("SpatialLocation", {"id": "C"}),
        ],
        edges=[(0, "adjacent_to", 2), (1, "adjacent_to", 2)],
    )
    wa.observe(sub)
    # Give A, B, C many "forward" successes — enough ticks for EMA convergence.
    for _ in range(700):
        wa.record_action_freshening("forward", 5)
        wa.record_action_freshening("turn_left", 0)
    promoted_types = {t[0] for t in wa.discover_action_affinities()}
    assert "SpatialLocation" in promoted_types


def test_record_action_outcome_observed_does_both():
    """The combined entry point records the global ActionStat (running sums)
    AND the per-instance freshening in one call."""
    wa = WorldAdapter()
    wa.observe(_world([("SpatialLocation", {"id": "A"})]))
    wa.record_action_outcome_observed("forward", novelty_delta=2, frontier_after=4)
    # global ActionStat updated
    stat = wa.action_stat("forward")
    assert stat["n"] == 1 and stat["novelty_sum"] == 2
    # per-instance freshening attributed to the in-view instance
    wi_id = wa._instances[("SpatialLocation", "A")]
    iattrs = wa.s.node(wi_id)["attrs"]
    assert iattrs.get("act_forward_n") == 1
    assert iattrs.get("act_forward_freshening_ema", 0) > 0


def test_scorer_reads_substrate_after_affinity_training():
    """Once an affinity is promoted, choose_action over a substrate with
    SpatialLocations runs without crashing and returns a legal action — the
    promotion is graph data the seeded scorer can read at decision time."""
    wa = WorldAdapter()
    for nid in ("A", "B"):
        wa.observe(_world([("SpatialLocation", {"id": nid})]))
        for _ in range(700):
            wa.record_action_freshening("forward", 8)
            wa.record_action_freshening("noop", 0)
    wa.discover_action_affinities()
    sub = _world([
        ("SpatialLocation", {"id": "X"}),
        ("SpatialLocation", {"id": "Y"}),
    ])
    wa.observe(sub)
    actions = ["forward", "noop", "turn_left"]
    chosen = wa.choose_action(actions, lambda a: sub)
    assert chosen in actions
