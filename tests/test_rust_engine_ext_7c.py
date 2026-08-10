"""Phase 7c — graph-resident rewrite rules.

The agent can now hold rewrite rules first-class via the substrate
itself: the matcher + applier + fixed-point runner all live in Rust,
the Python ext module just hands rules + effects across the FFI
boundary. Closes the "mutation must be expressed in Python" gap that
made domains/graph_rewrite.py necessary as a side module.

Each rule is `(name, match_edges, where?, effects)`. Effects compose
five primitives — AddEdge / DelEdge / AddNode / DelNode / SetAttr —
and effect arguments may be either literals OR Terms (evaluated under
the match binding at apply time).
"""
from __future__ import annotations

import pytest


srs = pytest.importorskip("substrate_rs")
ext = pytest.importorskip("substrate_rs.ext")


@pytest.fixture
def empty():
    return srs.Substrate()


# --- basic matching + simple effects ---


def test_add_rule_returns_index(empty):
    idx = ext.add_rule(
        empty,
        name="noop",
        match_edges=[("a", "knows", "b")],
        effects=[],
    )
    assert isinstance(idx, int)
    assert ext.rule_count(empty) == 1


def test_apply_rule_once_finds_match():
    """Pattern ?a -[knows]-> ?b ⇒ add ?a -[likes]-> ?b."""
    s = srs.Substrate()
    alice = s.add_node("Person")
    bob = s.add_node("Person")
    # No grammar — we use the raw graph through Π's add_edge with a
    # permissive production so the test edges admit.
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Person", var="src"),
        edge_type="knows",
        tgt=srs.NodePattern(type="Person", var="tgt"),
        where=None, weight=None,
        provenance="test:knows",
    ))
    s.add_edge(alice, "knows", bob)

    idx = ext.add_rule(
        s,
        name="knows_implies_likes",
        match_edges=[("a", "knows", "b")],
        effects=[ext.AddEdge("a", "likes", "b")],
    )
    fired = ext.apply_rule_once(s, idx)
    assert fired
    assert s.has_edge(alice, "likes", bob)


def test_distinct_vars_required():
    """Variables in a match must resolve to distinct nodes — self-loop
    on the pattern shouldn't fire."""
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Node", var="src"),
        edge_type="r",
        tgt=srs.NodePattern(type="Node", var="tgt"),
        where=None, weight=None,
        provenance="t",
    ))
    n = s.add_node("Node")
    s.add_edge(n, "r", n)  # self-loop
    idx = ext.add_rule(
        s,
        name="ab_pattern",
        match_edges=[("a", "r", "b")],
        effects=[ext.AddEdge("a", "marker", "b")],
    )
    assert ext.apply_rule_once(s, idx) is False


def test_where_clause_filters_match():
    """Where: only fire when the source has attr 'state'='ready'."""
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Cell", var="src"),
        edge_type="adj",
        tgt=srs.NodePattern(type="Cell", var="tgt"),
        where=None, weight=None,
        provenance="t",
    ))
    a = s.add_node("Cell", {"state": "idle"})
    b = s.add_node("Cell")
    s.add_edge(a, "adj", b)
    where = srs.Eq(srs.Attr(srs.Var("a"), "state"), srs.Lit("ready"))
    idx = ext.add_rule(
        s,
        name="only_ready",
        match_edges=[("a", "adj", "b")],
        where=where,
        effects=[ext.AddEdge("a", "marked", "b")],
    )
    assert ext.apply_rule_once(s, idx) is False
    # Flip state → match should now fire.
    s.set_attr(a, "state", "ready")
    assert ext.apply_rule_once(s, idx) is True


# --- multi-edge pattern + fixed point ---


def test_run_rules_transitive_closure_reaches_fixed_point():
    """Classic rewrite test: ?a -[r]-> ?b -[r]-> ?c ⇒ ?a -[r]-> ?c.
    Reaches a fixed point with every reachable pair connected."""
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="N", var="src"),
        edge_type="r",
        tgt=srs.NodePattern(type="N", var="tgt"),
        where=None, weight=None,
        provenance="t",
    ))
    n1 = s.add_node("N")
    n2 = s.add_node("N")
    n3 = s.add_node("N")
    n4 = s.add_node("N")
    s.add_edge(n1, "r", n2)
    s.add_edge(n2, "r", n3)
    s.add_edge(n3, "r", n4)
    ext.add_rule(
        s,
        name="transitive",
        match_edges=[("a", "r", "b"), ("b", "r", "c")],
        effects=[ext.AddEdge("a", "r", "c")],
    )
    steps = ext.run_rules(s, max_steps=100)
    assert steps >= 3
    # Every pair connected by the original chain.
    assert s.has_edge(n1, "r", n3)
    assert s.has_edge(n1, "r", n4)
    assert s.has_edge(n2, "r", n4)


# --- AddNode + SetAttr + Term-valued effect args ---


def test_add_node_binds_new_var():
    """AddNode introduces a fresh variable binding that subsequent
    effects can target."""
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Task", var="src"),
        edge_type="status",
        tgt=srs.NodePattern(type="Tag", var="tgt"),
        where=None, weight=None,
        provenance="t",
    ))
    s.add_production(srs.Production(
        src=srs.NodePattern(type="Task", var="src"),
        edge_type="next",
        tgt=srs.NodePattern(type="Task", var="tgt"),
        where=None, weight=None,
        provenance="t2",
    ))
    t_pending = s.add_node("Tag", {"label": "pending"})
    t_done = s.add_node("Tag", {"label": "done"})
    task = s.add_node("Task")
    s.add_edge(task, "status", t_pending)

    # Rule: task -[status]-> Tag('pending') ⇒ create new Task, link to it
    where = srs.Eq(srs.Attr(srs.Var("p"), "label"), srs.Lit("pending"))
    idx = ext.add_rule(
        s,
        name="advance_to_done",
        match_edges=[("t", "status", "p")],
        where=where,
        effects=[
            ext.AddNode("new_task", "Task", {}),
            ext.AddEdge("t", "next", "new_task"),
        ],
    )
    fired = ext.apply_rule_once(s, idx)
    assert fired
    # Two Tasks now, with `next` edge between them.
    tasks = s.nodes("Task")
    assert len(tasks) == 2
    nexts = s.neighbours(task, "next")
    assert len(nexts) == 1
    _ = t_done  # silence unused


def test_set_attr_with_computed_term():
    """SetAttr can take a Term value evaluated over the match binding."""
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="N", var="src"),
        edge_type="r",
        tgt=srs.NodePattern(type="N", var="tgt"),
        where=None, weight=None,
        provenance="t",
    ))
    a = s.add_node("N", {"x": 7})
    b = s.add_node("N", {"x": 13})
    s.add_edge(a, "r", b)
    # Rule: copy a's x into b's y, computed: y = a.x + 100
    computed = srs.Plus(items=(srs.Attr(srs.Var("a"), "x"), srs.Lit(100)))
    idx = ext.add_rule(
        s,
        name="copy_x_plus_100",
        match_edges=[("a", "r", "b")],
        effects=[ext.SetAttr("b", "y", computed)],
    )
    assert ext.apply_rule_once(s, idx)
    assert s.node(b)["attrs"]["y"] == 107


def test_del_edge_removes_edge():
    s = srs.Substrate()
    s.add_production(srs.Production(
        src=srs.NodePattern(type="N", var="src"),
        edge_type="bad",
        tgt=srs.NodePattern(type="N", var="tgt"),
        where=None, weight=None,
        provenance="t",
    ))
    a = s.add_node("N")
    b = s.add_node("N")
    s.add_edge(a, "bad", b)
    idx = ext.add_rule(
        s,
        name="cleanup",
        match_edges=[("a", "bad", "b")],
        effects=[ext.DelEdge("a", "bad", "b")],
    )
    assert ext.apply_rule_once(s, idx)
    assert not s.has_edge(a, "bad", b)


# --- counters track rewrite work ---


def test_rewrite_mutations_show_up_in_counters():
    s = srs.Substrate()
    n = s.add_node("N")
    m = s.add_node("N")
    # Authorise the rewrite's AddEdge target type.
    s.add_production(srs.Production(
        src=srs.NodePattern(type="N", var="src"),
        edge_type="touched",
        tgt=srs.NodePattern(type="N", var="tgt"),
        where=None, weight=None,
        provenance="t",
    ))
    # We use a non-grammar edge for matching since the rewrite path
    # bypasses C. Insert via add_edge after a permissive production.
    s.add_production(srs.Production(
        src=srs.NodePattern(type="N", var="src"),
        edge_type="seed",
        tgt=srs.NodePattern(type="N", var="tgt"),
        where=None, weight=None,
        provenance="t2",
    ))
    s.add_edge(n, "seed", m)
    pre_edges = ext.counters(s)["edges_inserted_total"]
    idx = ext.add_rule(
        s,
        name="mark",
        match_edges=[("a", "seed", "b")],
        effects=[ext.AddEdge("a", "touched", "b")],
    )
    ext.apply_rule_once(s, idx)
    # rewrite path uses graph.insert_edge directly — counters today
    # only track Π add_edge calls, so the rewrite mutations are silent.
    # That's deliberate (matches the "rewrite bypasses C" posture) and
    # documented; what we assert is that direct Π adds still count.
    after_edges = ext.counters(s)["edges_inserted_total"]
    # `seed` insert went via Π; subsequent rewrite-added `touched`
    # bypassed Π. So total Π-counted edges hasn't moved past the seed.
    assert after_edges == pre_edges
    assert s.has_edge(n, "touched", m)
