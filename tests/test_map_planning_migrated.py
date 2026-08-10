"""map planning, migrated — locus tracking + BFS planning over the mirrored
instance map, run on the seed-booted agent via the WorldAdapter (no
CuriousAgent).

Covers the migratable behaviours of tests/test_map_planning.py:
  • locus tracked from at_location edges (observe_locus);
  • (locus, orientation, action) -> next_locus transition counts;
  • BFS planner returns the next-hop toward the nearest under-saturated
    instance (direct neighbour, through a saturated chain, none-in-horizon,
    no-neighbours), saturation read via the SEEDED saturation_predicate;
  • modal next-locus (most-common, self-loop, orientation-conditioned);
  • the planner is edge-type-agnostic (a social `interacted_with` map plans
    the same way).

The map = the mirrored SpatialLocation + adjacent_to instance graph the adapter
already builds in `ingest`; the planner BFS is pure graph traversal (mechanical,
adapter); the saturation VALUE that ranks instances is the seeded predicate.

The self-loop test (`test_self_loop_penalty_*`) is covered to its actual (weak)
assertion — `choose_action` runs given a learned self-loop history and returns a
legal action; the transition DATA is tracked by the adapter. The scorer-BIAS
channel itself (folding the self-loop count into the action score) is part of the
full CuriousAgent scorer that the curiosity-core seed simplified to
q/novelty/asym_count — un-migrated decision surface the parity gate pins, beyond
what the bench asserts.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world_with_body_at(loc_id, topo):
    """A Doom-like world substrate: a Body --at_location--> a SpatialLocation,
    plus the full known location topology (adjacent_to edges)."""
    g = TypedGraph()
    body_id = g._insert_node("Body", {})
    loc_nids = {}
    for nid in topo["locs"]:
        loc_nids[nid] = g._insert_node("SpatialLocation", {"id": nid})
    for a, b in topo["edges"]:
        g._insert_edge(loc_nids[a], "adjacent_to", loc_nids[b])
    g._insert_edge(body_id, "at_location", loc_nids[loc_id])
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def test_locus_tracked_from_at_location_edge():
    wa = WorldAdapter()
    wa.observe_locus(_world_with_body_at("A", {"locs": ["A"], "edges": []}))
    assert wa.current_locus_wi == wa._instances[("SpatialLocation", "A")]


def test_transition_count_recorded_on_locus_change():
    wa = WorldAdapter()
    topo = {"locs": ["A", "B"], "edges": [("A", "B")]}
    wa.observe_locus(_world_with_body_at("A", topo))
    wa.note_action("forward", ())
    wa.observe_locus(_world_with_body_at("B", topo))
    a_wi = wa._instances[("SpatialLocation", "A")]
    b_wi = wa._instances[("SpatialLocation", "B")]
    inner = wa._locus_transition_counts.get((a_wi, (), "forward"))
    assert inner is not None
    assert inner.get(b_wi) == 1


def test_planner_returns_neighbour_when_neighbour_is_unsaturated():
    wa = WorldAdapter()
    topo = {"locs": ["A", "B"], "edges": [("A", "B")]}
    wa.observe_locus(_world_with_body_at("A", topo))
    a_wi = wa._instances[("SpatialLocation", "A")]
    b_wi = wa._instances[("SpatialLocation", "B")]
    wa.saturate_instance(a_wi)  # leave B unsaturated
    assert wa.is_instance_saturated(a_wi)
    assert not wa.is_instance_saturated(b_wi)
    assert wa.plan_next_step(a_wi, horizon=5) == b_wi


def test_planner_finds_far_unsaturated_through_chain():
    wa = WorldAdapter()
    topo = {"locs": ["A", "B", "C", "D"],
            "edges": [("A", "B"), ("B", "C"), ("C", "D")]}
    wa.observe_locus(_world_with_body_at("A", topo))
    a_wi = wa._instances[("SpatialLocation", "A")]
    b_wi = wa._instances[("SpatialLocation", "B")]
    c_wi = wa._instances[("SpatialLocation", "C")]
    d_wi = wa._instances[("SpatialLocation", "D")]
    for sat in (a_wi, b_wi, c_wi):
        wa.saturate_instance(sat)
    assert not wa.is_instance_saturated(d_wi)
    assert wa.plan_next_step(a_wi, horizon=5) == b_wi  # first hop on A->B->C->D


def test_planner_returns_none_when_nothing_unsaturated_in_horizon():
    wa = WorldAdapter()
    topo = {"locs": ["A", "B"], "edges": [("A", "B")]}
    wa.observe_locus(_world_with_body_at("A", topo))
    a_wi = wa._instances[("SpatialLocation", "A")]
    b_wi = wa._instances[("SpatialLocation", "B")]
    wa.saturate_instance(a_wi)
    wa.saturate_instance(b_wi)
    assert wa.plan_next_step(a_wi, horizon=5) is None


def test_planner_returns_none_with_no_locus_neighbours():
    wa = WorldAdapter()
    wa.observe_locus(_world_with_body_at("A", {"locs": ["A"], "edges": []}))
    a_wi = wa._instances[("SpatialLocation", "A")]
    assert wa.plan_next_step(a_wi, horizon=5) is None


def test_modal_next_locus_lookup():
    wa = WorldAdapter()
    topo = {"locs": ["A", "B", "C"], "edges": [("A", "B"), ("A", "C")]}
    for _ in range(3):
        wa.observe_locus(_world_with_body_at("A", topo))
        wa.note_action("forward", ())
        wa.observe_locus(_world_with_body_at("B", topo))
    wa.observe_locus(_world_with_body_at("A", topo))
    wa.note_action("forward", ())
    wa.observe_locus(_world_with_body_at("C", topo))
    a_wi = wa._instances[("SpatialLocation", "A")]
    b_wi = wa._instances[("SpatialLocation", "B")]
    assert wa.modal_next_locus(a_wi, (), "forward") == b_wi


def test_self_loop_transitions_recorded_so_planner_sees_failed_actions():
    """An action that keeps the locus the same (walking into a wall) records a
    (locus, orientation, action) -> same_locus transition; the modal next is the
    self-loop when it dominates — so the planner won't be fooled into boosting an
    action that historically moved the agent but currently doesn't."""
    wa = WorldAdapter()
    topo = {"locs": ["A", "B"], "edges": [("A", "B")]}
    for _ in range(4):           # forward stays at A (hits wall)
        wa.observe_locus(_world_with_body_at("A", topo))
        wa.note_action("forward", ())
        wa.observe_locus(_world_with_body_at("A", topo))
    wa.observe_locus(_world_with_body_at("A", topo))   # 1x moves to B
    wa.note_action("forward", ())
    wa.observe_locus(_world_with_body_at("B", topo))
    a_wi = wa._instances[("SpatialLocation", "A")]
    assert wa.modal_next_locus(a_wi, (), "forward") == a_wi  # A (4) beats B (1)


def test_modal_next_distinguishes_by_orientation():
    """Same action from same locus gives different next-loci under different
    orientations — the heart of the orientation fix."""
    wa = WorldAdapter()
    topo = {"locs": ["A", "N", "S"], "edges": [("A", "N"), ("A", "S")]}
    for _ in range(3):           # facing north: forward -> N
        wa.observe_locus(_world_with_body_at("A", topo))
        wa.note_action("forward", (("my_angle_bin", 0),))
        wa.observe_locus(_world_with_body_at("N", topo))
    for _ in range(3):           # facing south: forward -> S
        wa.observe_locus(_world_with_body_at("A", topo))
        wa.note_action("forward", (("my_angle_bin", 4),))
        wa.observe_locus(_world_with_body_at("S", topo))
    a_wi = wa._instances[("SpatialLocation", "A")]
    n_wi = wa._instances[("SpatialLocation", "N")]
    s_wi = wa._instances[("SpatialLocation", "S")]
    assert wa.modal_next_locus(a_wi, (("my_angle_bin", 0),), "forward") == n_wi
    assert wa.modal_next_locus(a_wi, (("my_angle_bin", 4),), "forward") == s_wi


def test_planning_works_for_any_edge_type():
    """The planner is general: a social map with `interacted_with` edges supports
    the same next-hop planning (no edge type is privileged)."""
    wa = WorldAdapter()
    g = TypedGraph()
    body = g._insert_node("Body", {})
    a = g._insert_node("AgentMarker", {"id": "X"})
    b = g._insert_node("AgentMarker", {"id": "Y"})
    g._insert_edge(a, "interacted_with", b)
    g._insert_edge(body, "at_location", a)
    wa.observe_locus(Substrate(graph=g, checker=ConsistencyChecker(Grammar([]))))
    a_wi = wa._instances[("AgentMarker", "X")]
    b_wi = wa._instances[("AgentMarker", "Y")]
    wa.saturate_instance(a_wi)  # leave Y unsaturated
    assert wa.plan_next_step(a_wi, horizon=5) == b_wi


def test_self_loop_penalty_choose_action_runs_with_learned_history():
    """test_self_loop_penalty_pushes_against_ineffective_actions, migrated.

    The original asserts only `chosen in actions` ("not strict, but doesn't
    crash") — i.e. choose_action runs given a learned self-loop history. The
    self-loop transition DATA is tracked by the adapter (_locus_transition_counts
    via observe_locus + note_action); choose_action then returns a legal action.

    The scorer-BIAS channel (folding the self-loop count into the action score)
    is part of the full CuriousAgent scorer that the curiosity-core seed
    simplified to q/novelty/asym_count — it is NOT in the migrated seeded
    action_score_term (which the parity gate pins). So the bias itself is
    un-migrated decision surface; this covers exactly what the bench asserts."""
    topo = {"locs": ["A", "B"], "edges": [("A", "B")]}
    wa = WorldAdapter()
    # forward self-loops at A (stays put) repeatedly — learned ineffective here
    for _ in range(10):
        wa.observe_locus(_world_with_body_at("A", topo))
        wa.note_action("forward", ())
        wa.observe_locus(_world_with_body_at("A", topo))
    a_wi = wa._instances[("SpatialLocation", "A")]
    # the self-loop transition was recorded
    assert wa._locus_transition_counts.get((a_wi, (), "forward"), {}).get(a_wi, 0) > 0
    actions = [("forward",), ("turn_left",)]
    chosen = wa.choose_action(actions, lambda a: _world_with_body_at("A", topo))
    assert chosen in actions
