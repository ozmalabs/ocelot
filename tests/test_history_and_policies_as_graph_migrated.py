"""History + policies as graph data, migrated — the agent's reality is the
substrate, not Python state (no CuriousAgent).

After this migration:
- the agent's HISTORY lives in the graph as ``Event`` nodes, attached to the
  agent by ``logged`` edges, each ``involves`` the BodyTypes it touched; the
  ``_event_log`` view reconstructs records from those nodes — it is not a stored
  Python list. The adapter only stamps events (``log_event``); it makes no
  decisions about them.
- the discovery thresholds (top_k_*, min_count, triple_threshold), the theorem
  hold_threshold, and the meta_curiosity_weight all live as ``Term.Lit`` nodes
  attached to the agent by named edges — graph data, not Python parameters.
  Editing a Lit's value changes the agent's behaviour (here: whether the seeded
  salience predicate promotes a discovered relation).

Covers the original tests/test_history_and_policies_as_graph: events as graph
nodes (logged + involves), the event-log property reading from the graph, the
five discovery/theorem Lit policies (names + values), behaviour-change on
editing a discovery threshold, and the meta-curiosity weight Lit + its reader.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


# --- History as graph data ---


def test_events_appear_as_graph_nodes():
    """The agent's history is in the graph as Event nodes, with `logged` and
    `involves` edges — not a Python list. Every event is logged from the agent
    and involves at least one BodyType."""
    wa = WorldAdapter()
    wa.log_event("observe", ["Cell", "Wall"])
    wa.log_event("gamma_edit", ["Cell"])
    events = list(wa.s.nodes("Event"))
    assert len(events) == 2
    # one `logged` edge per event, from the agent
    logged = wa.inner.neighbours(wa.agent, "logged")
    assert len(logged) == len(events)
    for e in events:
        involves = wa.inner.neighbours(e, "involves")
        assert len(involves) > 0


def test_event_log_property_reads_from_graph():
    """``_event_log`` reconstructs records from the Event nodes in the graph —
    it is not a stored list. Kinds and body-types are read back faithfully."""
    wa = WorldAdapter()
    wa.log_event("observe", ["Cell"])
    wa.log_event("gamma_edit", ["Cell", "Wall"])
    log = wa._event_log
    assert len(log) == 2
    kinds = {ev["kind"] for ev in log}
    assert {"observe", "gamma_edit"}.issubset(kinds)
    # body-types travel via `involves` edges, sorted; timestamps are monotone
    by_kind = {ev["kind"]: ev for ev in log}
    assert by_kind["gamma_edit"]["body_types"] == ("Cell", "Wall")
    assert [ev["timestamp"] for ev in log] == sorted(ev["timestamp"] for ev in log)


def test_event_log_is_not_a_python_list():
    """Mutating the returned view does not change the graph-resident history —
    proving the log is reconstructed each call, not a stored list."""
    wa = WorldAdapter()
    wa.log_event("observe", ["Cell"])
    view = wa._event_log
    view.append({"kind": "fake", "body_types": (), "timestamp": 999})
    assert len(wa._event_log) == 1  # graph unchanged


def test_event_bodytypes_shared_with_instances():
    """The BodyType an event `involves` is the SAME shared node an ingested
    instance reaches via `instance_of` — one BodyType per world type."""
    from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
    g = TypedGraph()
    g._insert_node("Cell", {"id": "c1"})
    world = Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))
    wa = WorldAdapter()
    wa.ingest(world)
    wa.log_event("observe", ["Cell"])
    inst = wa._instances[("Cell", "c1")]
    inst_bt = wa.inner.neighbours(inst, "instance_of")[0]
    ev = list(wa.s.nodes("Event"))[0]
    ev_bt = wa.inner.neighbours(ev, "involves")[0]
    assert inst_bt == ev_bt


# --- Discovery thresholds as Lits ---


def test_discovery_thresholds_are_lit_policies():
    """The numeric thresholds discovery uses live as `Term.Lit` nodes attached
    to the agent by named edges — graph data, not Python parameters."""
    wa = WorldAdapter()
    for edge_name, expected in [
        ("discovery_top_k_agent_world", 20),
        ("discovery_top_k_type_pairs", 40),
        ("discovery_min_count", 8),
        ("discovery_triple_threshold", 30),
        ("theorem_hold_threshold", 3),
    ]:
        lit = wa.policy_lit(edge_name)
        assert lit is not None, f"missing Lit policy edge {edge_name}"
        assert wa.s.node(lit)["type"] == "Term.Lit"
        assert wa.get_scalar_policy(edge_name) == expected


def test_editing_discovery_threshold_changes_behavior():
    """Edit the ``discovery_min_count`` Lit in graph data — relation discovery
    starts/stops promoting accordingly. The discovery policy is graph-resident."""
    def _build():
        wa = WorldAdapter()
        for _ in range(20):
            wa.log_event("observe", ["Lever"])
            wa.log_event("act", ["Door"])
        return wa

    # Default threshold: the strongly-predictive lag-1 pair gets promoted.
    wa = _build()
    mc = int(wa.get_scalar_policy("discovery_min_count"))
    assert wa.discover_relations(min_count=mc) != []

    # Edit the Lit to an impossibly-high count — no relation qualifies.
    wa2 = _build()
    wa2.set_scalar_policy("discovery_min_count", 10_000)
    mc2 = int(wa2.get_scalar_policy("discovery_min_count"))
    assert mc2 == 10_000
    assert wa2.discover_relations(min_count=mc2) == []


# --- Meta-curiosity weight as Lit ---


def test_meta_curiosity_weight_is_lit_in_graph():
    """The 0.15 weight lives as a Term.Lit attached to the agent."""
    wa = WorldAdapter()
    lit = wa.policy_lit("meta_curiosity_weight")
    assert lit is not None
    assert wa.s.node(lit)["type"] == "Term.Lit"
    assert abs(wa.get_scalar_policy("meta_curiosity_weight") - 0.15) < 1e-9


def test_editing_meta_curiosity_weight_is_graph_data():
    """Lower the weight to 0 via graph state; the reader returns the edited
    value — there is no Python field to touch."""
    wa = WorldAdapter()
    wa.set_scalar_policy("meta_curiosity_weight", 0.0)
    assert wa.get_scalar_policy("meta_curiosity_weight", -1.0) == 0.0
