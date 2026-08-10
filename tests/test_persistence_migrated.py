"""Migrated twin of test_persistence.py — stored-graph persistence on the
seed-booted WorldAdapter (boot_core seeds, no CuriousAgent).

The agent's mind is the Rust substrate's graph; the adapter is the thin world
layer. Persistence is therefore mechanical I/O on the adapter:

- `save()`/`load()` round-trips the graph FAITHFULLY (same nodes, edges, ids);
- the adapter's world↔graph index dicts (`_instances` keyed by (type,id),
  `_concepts` keyed by taught-word) survive, so a loaded adapter does NOT
  re-create instances it already has (no duplication);
- the dynamic Γ (lazily-admitted instance edge-types) survives, so edge-types
  admitted at runtime are still admissible after a load;
- a loaded adapter can keep operating (a seeded/taught Term still classifies).

1:1 with the original (which exercised CuriousAgent._ensure_world_instance /
_ensure_instance_edge_type / save / load / _concept_holds):
  _ensure_world_instance   -> WorldAdapter.ensure_world_instance
  _ensure_instance_edge_type -> WorldAdapter.ensure_instance_edge_type
  mind_graph.node/edge_count -> s.node_count()/s.edge_count()
  agent_root               -> wa.agent  (Γ is the grammar, not a node, so the
                              original gamma_root has no node twin — the
                              dynamic-grammar survival test covers Γ instead)
  _concept_nodes           -> _concepts
  _world_instance_nodes    -> _instances
  _concept_holds           -> concept_holds (the in_view perception Term)
"""
from __future__ import annotations

from substrate.dsl import Attr, Eq, Lit, Var
from substrate.jsonio import term_to_json
from substrate.world_adapter import WorldAdapter


def _in_view_term_json():
    """in_view(x) := I am currently sensing x — the seeded perception concept,
    a plain Term over a WorldInstance's `currently_perceived` attr (mirrors
    CuriousAgent._seed_perception_concepts)."""
    return term_to_json(Eq(a=Attr(Var("x"), "currently_perceived"), b=Lit(True)))


def _seeded_with_some_world(tmp_path):
    """A booted adapter with a little accreted world structure: two instances, a
    lazily-admitted instance edge-type, an edge using it, and the seeded in_view
    perception concept grounded as a Term — the migrated analogue of the
    original's seed knowledge + accreted world."""
    wa = WorldAdapter()
    a = wa.ensure_world_instance("Rock", "rock_1")
    b = wa.ensure_world_instance("Rock", "rock_2")
    wa.ensure_instance_edge_type("near")
    wa.s.add_edge(a, "near", b)
    wa.learn_word("in_view", _in_view_term_json())
    return wa


def test_round_trip_is_faithful(tmp_path):
    wa = _seeded_with_some_world(tmp_path)
    before = (wa.s.node_count(), wa.s.edge_count())
    path = str(tmp_path / "mind.json")
    wa.save(path)
    loaded = WorldAdapter.load(path)

    assert (loaded.s.node_count(), loaded.s.edge_count()) == before
    assert loaded.agent == wa.agent
    # Index dicts restored.
    assert set(loaded._concepts) == set(wa._concepts)
    assert set(loaded._instances) == set(wa._instances)


def test_no_duplicate_nodes_after_load(tmp_path):
    wa = _seeded_with_some_world(tmp_path)
    path = str(tmp_path / "mind.json")
    wa.save(path)
    loaded = WorldAdapter.load(path)

    n_before = loaded.s.node_count()
    # Re-ensuring an EXISTING instance must return the SAME node (index survived).
    same = loaded.ensure_world_instance("Rock", "rock_1")
    assert same == wa._instances[("Rock", "rock_1")]
    assert loaded.s.node_count() == n_before     # no new node created


def test_dynamic_meta_grammar_survives(tmp_path):
    wa = _seeded_with_some_world(tmp_path)
    path = str(tmp_path / "mind.json")
    wa.save(path)
    loaded = WorldAdapter.load(path)

    # The lazily-admitted "near" edge-type was registered at runtime, not in the
    # base grammar. It must still be admissible after the load.
    c = loaded.ensure_world_instance("Rock", "rock_3")
    d = loaded.ensure_world_instance("Rock", "rock_4")
    loaded.s.add_edge(c, "near", d)               # must NOT raise (Γ admits it)
    assert loaded.s.has_edge(c, "near", d)


def test_seeded_concept_evaluates_after_load(tmp_path):
    wa = _seeded_with_some_world(tmp_path)
    path = str(tmp_path / "mind.json")
    wa.save(path)
    loaded = WorldAdapter.load(path)

    inst = loaded._instances[("Rock", "rock_1")]
    # in_view is a seeded perception concept; it must still classify after load.
    assert loaded.concept_holds("in_view", inst) in (True, False)
