"""Tests for two Rust-native primitives added to the rule engine's PyO3
surface (`substrate_rs._native.Substrate`):

* `remove_rule(rule_idx)` — tombstones a rule slot installed by
  `add_rule`. The rule never matches/fires again in `apply_rule_once` /
  `run_rules` / `tick`, but the slot is NOT compacted out: `rule_idx`
  values handed out by `add_rule` stay valid forever (self-modification
  code that cached a `RuleIdx` keeps working), and `rule_count()` keeps
  counting the slot. Double-remove and an out-of-range index are both
  safe no-ops (`False`, never a panic).
* `graph_diff(dict_a, dict_b)` — a pure, JSON-level structural diff
  between two `graph_to_dict()`-shaped dicts. Node identity is the node
  `id` (stable across a `graph_to_dict` / `graph_from_dict` round-trip,
  so a parent agent's pre-dispatch snapshot and a dispatched child's
  final graph are id-aligned); edge identity is the structural
  `(src, type, tgt)` triple. `nodes_changed` entries carry only the
  attr keys that actually differ.

See the semantics documented on `Substrate::remove_rule` and
`persist::graph_diff` in `runners/dsl/src/substrate.rs` /
`runners/dsl/src/persist.rs` for the full contract; this file exercises
both from the actual installed `substrate_rs` extension, matching the
existing low-level-native test style (see
`tests/test_conflict_detection.py`, `tests/test_rust_engine_ext_7c.py`).
"""
from __future__ import annotations

import copy

import pytest

native = pytest.importorskip("substrate_rs._native")
ext = pytest.importorskip("substrate_rs.ext")


def _open_substrate(node_types, edge_types):
    """A fresh native Substrate with a fully permissive grammar over the
    given node/edge type vocabulary, so `add_node` / `add_edge` (the
    checked, admissibility-gated path) accept anything in that
    vocabulary. Mirrors `tests/test_conflict_detection.py`'s
    `_fresh_substrate()`."""
    s = native.Substrate()
    for src_t in node_types:
        for tgt_t in node_types:
            for et in edge_types:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


# ---------------------------------------------------------------------------
# remove_rule
# ---------------------------------------------------------------------------


def test_remove_rule_fires_before_not_after():
    """A rule fires while active; after `remove_rule`, the identical
    admissible binding no longer fires it — removal isn't "consume the
    match once", it's "this rule is gone"."""
    s = _open_substrate(["Trigger", "Target", "Minted"], ["triggers"])
    a = s.add_node("Trigger", {})
    b = s.add_node("Target", {})
    s.add_edge(a, "triggers", b, {})

    idx = ext.add_rule(
        s,
        name="mint_on_trigger",
        match_edges=[("src", "triggers", "tgt")],
        effects=[ext.AddNode("m", "Minted", {})],
    )

    # Fires while active.
    assert ext.apply_rule_once(s, idx) is True
    assert len(s.nodes("Minted")) == 1

    # First remove_rule call reports success.
    assert s.remove_rule(idx) is True

    # Never fires again, even though the very same admissible binding
    # (a -[triggers]-> b) is still sitting in the graph.
    assert ext.apply_rule_once(s, idx) is False
    assert len(s.nodes("Minted")) == 1, "no new node minted by a removed rule"


def test_remove_rule_double_remove_and_bad_index_are_safe():
    s = _open_substrate(["N"], ["E"])
    idx = ext.add_rule(s, name="noop", match_edges=[("x", "E", "y")], effects=[])
    assert isinstance(idx, int)

    assert s.remove_rule(idx) is True
    # Second call on the same index is a safe, idempotent no-op — no panic.
    assert s.remove_rule(idx) is False
    # Out-of-range index: safe, no panic, reports failure.
    assert s.remove_rule(idx + 999) is False


def test_remove_rule_leaves_other_rules_unaffected():
    """Removing one rule must not disturb any sibling rule's matching or
    firing — `run_rules`'s dirty/fixed-point machinery must still reach
    every live rule."""
    s = _open_substrate(["N"], ["A", "B"])
    n1 = s.add_node("N", {})
    n2 = s.add_node("N", {})
    s.add_edge(n1, "A", n2, {})
    s.add_edge(n1, "B", n2, {})

    idx_a = ext.add_rule(
        s, name="rule_A", match_edges=[("x", "A", "y")],
        effects=[ext.AddNode("m", "MintedA", {})],
    )
    ext.add_rule(
        s, name="rule_B", match_edges=[("x", "B", "y")],
        effects=[ext.AddNode("m", "MintedB", {})],
    )

    assert s.remove_rule(idx_a) is True

    ext.run_rules(s, max_steps=100)
    assert len(s.nodes("MintedA")) == 0, "removed rule_A must not fire"
    assert len(s.nodes("MintedB")) == 1, "sibling rule_B must still fire normally"


def test_remove_rule_does_not_shrink_rule_count():
    """The slot is tombstoned, not compacted: `rule_count()` (the index
    space `add_rule` hands out) is unchanged by removal, and every
    surviving rule keeps the exact index it always had."""
    s = _open_substrate(["N"], ["A", "B"])
    idx_a = ext.add_rule(s, name="rule_A", match_edges=[("x", "A", "y")], effects=[])
    idx_b = ext.add_rule(s, name="rule_B", match_edges=[("x", "B", "y")], effects=[])
    assert ext.rule_count(s) == 2

    assert s.remove_rule(idx_a) is True
    assert ext.rule_count(s) == 2, "remove_rule must not shrink/reindex the rule store"

    # rule_B's index is untouched by rule_A's removal.
    n1 = s.add_node("N", {})
    n2 = s.add_node("N", {})
    s.add_edge(n1, "B", n2, {})
    assert ext.apply_rule_once(s, idx_b) is True, "rule_B's index must still resolve to rule_B"


# ---------------------------------------------------------------------------
# graph_diff
# ---------------------------------------------------------------------------


def test_graph_diff_identical_graphs_is_empty():
    s = _open_substrate(["Cell"], ["adjacent_to"])
    a = s.add_node("Cell", {"score": 1.0})
    b = s.add_node("Cell", {})
    s.add_edge(a, "adjacent_to", b, {})
    d = s.graph_to_dict()

    diff = native.Substrate.graph_diff(d, d)
    assert diff["nodes_added"] == []
    assert diff["nodes_removed"] == []
    assert diff["nodes_changed"] == []
    assert diff["edges_added"] == []
    assert diff["edges_removed"] == []


def test_graph_diff_all_categories():
    """Exercises every category in one pass: an added node, a removed
    node, a changed node (only the touched attr keys reported), an
    added edge, and a removed edge. `dict_b` is built by mutating a
    deep copy of `dict_a` at the JSON level — the exact contract
    `graph_diff` documents (two `graph_to_dict()`-shaped dicts), and
    the natural shape of "parent snapshot vs. dispatched child's final
    graph"."""
    s = _open_substrate(["Cell"], ["adjacent_to", "touches"])
    a_nid = s.add_node("Cell", {"score": 1.0, "stable": 9, "will_go": True})
    b_nid = s.add_node("Cell", {})
    doomed_nid = s.add_node("Cell", {})
    s.add_edge(a_nid, "adjacent_to", b_nid, {})
    a, b, doomed = a_nid.value, b_nid.value, doomed_nid.value
    dict_a = s.graph_to_dict()

    dict_b = copy.deepcopy(dict_a)

    # nodes_added: a fresh id not present in dict_a.
    new_id = dict_b["next_id"]
    dict_b["nodes"].append({"id": new_id, "type": "Cell", "attrs": {}})

    # nodes_removed: drop `doomed`.
    dict_b["nodes"] = [n for n in dict_b["nodes"] if n["id"] != doomed]

    # nodes_changed: on `a`, change `score`, drop `will_go`, add
    # `new_key` — leave `stable` untouched so it must NOT show up in
    # either side of the diff (only changed keys are reported).
    for n in dict_b["nodes"]:
        if n["id"] == a:
            n["attrs"]["score"] = 2.0
            del n["attrs"]["will_go"]
            n["attrs"]["new_key"] = "hi"

    # edges: remove the adjacent_to edge, add a touches edge on the same
    # endpoints (different type -> a distinct identity, not a "changed" edge).
    dict_b["edges"] = [
        e for e in dict_b["edges"]
        if not (e["src"] == a and e["type"] == "adjacent_to" and e["tgt"] == b)
    ]
    dict_b["edges"].append({"src": a, "type": "touches", "tgt": b, "attrs": {}})

    diff = native.Substrate.graph_diff(dict_a, dict_b)

    assert [n["id"] for n in diff["nodes_added"]] == [new_id]
    assert diff["nodes_added"][0]["type"] == "Cell"

    assert diff["nodes_removed"] == [doomed]

    assert len(diff["nodes_changed"]) == 1
    changed = diff["nodes_changed"][0]
    assert changed["id"] == a
    assert changed["attrs_before"] == {"score": 1.0, "will_go": True}
    assert changed["attrs_after"] == {"score": 2.0, "new_key": "hi"}
    assert "stable" not in changed["attrs_before"]
    assert "stable" not in changed["attrs_after"]

    assert diff["edges_removed"] == [{"src": a, "type": "adjacent_to", "tgt": b}]
    assert diff["edges_added"] == [{"src": a, "type": "touches", "tgt": b}]


def test_graph_diff_bad_shape_raises_instead_of_crashing():
    ok = {"next_id": 0, "nodes": [], "edges": []}
    bad = {"next_id": 0, "nodes": "not-a-list", "edges": []}
    with pytest.raises(Exception):
        native.Substrate.graph_diff(bad, ok)
    with pytest.raises(Exception):
        native.Substrate.graph_diff(ok, bad)
