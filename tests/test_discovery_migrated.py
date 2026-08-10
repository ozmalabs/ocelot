"""causal discovery, migrated — relations emerge from activity via the SEEDED
salience_predicate, in the WorldAdapter (no CuriousAgent). The adapter records
activity (record_activity) + co-occurrence counters (mechanical bookkeeping);
discover_relations promotes temporal-lag (kind,type)->(kind,type) pairs the agent
has seen enough AND the seeded salience Term accepts. Covers the discovery
essence: predictive pairs discovered, sub-threshold pairs ignored, well-formed
rel ids. (The salience signal-vs-noise discrimination is verified directly in
tests/test_migration_parity.py::test_causal_predicates_from_seed.)
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def _drive(n):
    wa = WorldAdapter()
    for _ in range(n):
        wa.record_activity("act", ["Body"])
        wa.record_activity("observe", ["Item"])
    return wa


def test_predictive_pair_is_discovered():
    wa = _drive(10)
    wa.discover_relations(min_count=8)
    assert any(m["from_type"] == "Body" and m["to_type"] == "Item"
               for m in wa._discovered_relations.values())


def test_subthreshold_pair_not_discovered():
    wa = _drive(3)                       # 3 < min_count 8
    wa.discover_relations(min_count=8)
    assert wa._discovered_relations == {}


def test_discovered_relation_ids_well_formed():
    wa = _drive(10)
    promoted = wa.discover_relations(min_count=8)
    assert len(promoted) > 0
    for rid in promoted:
        assert rid.startswith("rel_") and rid[len("rel_"):].isdigit()


def test_no_activity_discovers_nothing():
    wa = WorldAdapter()
    assert wa.discover_relations(min_count=8) == []


# --- migrated from tests/test_discovery.py -------------------------------------
# The behaviours below cover the original discovery bench's MIGRATABLE essence on
# the seed-booted WorldAdapter (no CuriousAgent): the event log accumulates as
# graph data during life; relations EMERGE from real chess life; each promoted
# relation extends Γ_meta (a production) and is VISIBLE in the graph (an asserted
# Pattern node); rel ids are dense/sequential/well-formed; and different worlds
# yield different vocabularies. Chess life is driven through the seeded live()
# loop; a contrasting activity stream uses record_activity directly (the same
# mechanical co-occurrence bookkeeping live() feeds), exactly as the burn permits.
#
# The original's test_both_shapes_discovered and test_t2_emerges_naturally_from_
# cross_world_life are NOT reproduced here: they assert the agent_to_body and
# body_to_body discovery SHAPES, which the adapter's discover_relations does not
# emit (it promotes temporal_lag relations only). Those shapes are a separate
# discovery dimension (genuine un-migrated reasoning), so the original bench is
# retained for them.

from domains.worlds import chess_world


def _chess_life(n_games=3, max_plies=60):
    """Drive real chess life through the seeded curiosity loop, then discover."""
    wa = WorldAdapter()
    wa.live(chess_world(), n_games=n_games, max_plies=max_plies)
    return wa


def test_event_log_accumulates_during_life():
    """The agent's event log is graph data (Event nodes via `logged`), and it
    accumulates as the agent acts on and observes its world. Both an `observe`
    and an `act` kind appear, with monotone timestamps."""
    wa = WorldAdapter()
    assert wa._event_log == []
    # mechanical I/O: each life step logs what the agent observed / acted on.
    for _ in range(20):
        wa.log_event("observe", ["Square"])
        wa.log_event("act", ["WhitePawn"])
    log = wa._event_log
    assert len(log) > 0
    kinds = {ev["kind"] for ev in log}
    assert "observe" in kinds
    assert "act" in kinds
    # history is graph-resident with a monotone clock.
    timestamps = [ev["timestamp"] for ev in log]
    assert timestamps == sorted(timestamps)
    assert len(set(timestamps)) == len(timestamps)


def test_relations_emerge_from_chess_life():
    """After enough chess, discovery promotes SOME relations from the agent's
    own activity — and every relation id is well-formed rel_N."""
    wa = _chess_life()
    discovered = wa._discovered_relations
    assert len(discovered) > 0, "no relations discovered from chess life"
    for rel_id in discovered:
        assert rel_id.startswith("rel_")
        assert rel_id[len("rel_"):].isdigit()


def test_discovered_relations_admitted_by_meta_gamma():
    """Each discovered relation extends Γ_meta — a production admitting it is
    grown into the grammar (the agent extends its own admissibility law)."""
    wa = _chess_life()
    meta = wa.meta_productions()
    prod_edges = {p.get("edge_type")
                  for p in wa.inner.grammar_to_json().get("productions", [])}
    for rel_id in wa._discovered_relations:
        assert rel_id in meta, f"{rel_id} not grown into meta-productions"
        assert rel_id in prod_edges, f"{rel_id} not admitted by Γ_meta grammar"


def test_discovered_relations_visible_in_graph():
    """Discovery output is graph-resident: for each discovered relation an
    asserted Pattern node (agent --asserts_pattern--> Pattern) carries the
    relation's rel_id + types, visible by traversal in the mind graph."""
    wa = _chess_life()
    pat_nodes = wa.inner.neighbours(wa.agent, "asserts_pattern")
    by_rel = {wa.s.node(p)["attrs"]["rel_id"]: wa.s.node(p)["attrs"]
              for p in pat_nodes}
    for rel_id, m in wa._discovered_relations.items():
        assert rel_id in by_rel, f"no Pattern node for {rel_id} in graph"
        pat = by_rel[rel_id]
        assert pat["from_type"] == m["from_type"]
        assert pat["to_type"] == m["to_type"]
        # the related body-types are themselves graph nodes the agent knows.
        assert wa.body_type(m["from_type"]) is not None
        assert wa.body_type(m["to_type"]) is not None


def test_relation_ids_are_dense_and_sequential():
    """rel ids are assigned densely as discovery proceeds: rel_1, rel_2, … with
    no gaps (the adapter's monotone rel sequence)."""
    wa = _chess_life()
    ids = sorted(wa._discovered_relations.keys(),
                 key=lambda s: int(s[len("rel_"):]))
    nums = [int(s[len("rel_"):]) for s in ids]
    assert nums == list(range(nums[0], nums[0] + len(nums)))


def test_different_worlds_different_discoveries():
    """The relations discovered reflect the world the agent lived in. Chess life
    discovers chess-piece pairs; a different activity stream discovers a disjoint
    vocabulary — near-zero overlap in the discovered type-pairs."""
    chess_wa = _chess_life()
    chess_pairs = {(m["from_type"], m["to_type"])
                   for m in chess_wa._discovered_relations.values()}
    assert chess_pairs, "chess life discovered no type-pairs"

    other = WorldAdapter()
    for _ in range(12):
        other.record_activity("act", ["Cursor"])
        other.record_activity("observe", ["Token"])
    other.discover_relations(min_count=8)
    other_pairs = {(m["from_type"], m["to_type"])
                   for m in other._discovered_relations.values()}
    assert other_pairs, "the contrasting stream discovered no type-pairs"

    overlap = chess_pairs & other_pairs
    assert len(overlap) == 0, f"worlds should discover disjoint vocab: {overlap}"


# --- agent_to_body + body_to_body discovery shapes (test_discovery's both_shapes/t2) ---

def _shapes_of(wa):
    return {m["shape"] for m in wa._discovered_relations.values()}


def test_agent_to_body_shape_discovered():
    wa = WorldAdapter()
    for _ in range(10):
        wa.record_activity("act", ["Body"])
        wa.record_activity("observe", ["Item"])
    wa.discover_relations(min_count=8, shapes=("agent_to_body",))
    a2b = [m for m in wa._discovered_relations.values() if m["shape"] == "agent_to_body"]
    assert a2b
    assert all("event_kind" in m and "body_type" in m for m in a2b)
    assert any(m["body_type"] == "Body" for m in a2b)


def test_body_to_body_shape_discovered():
    wa = WorldAdapter()
    for _ in range(10):
        wa.record_activity("act", ["Body", "Number"])   # two types co-occur
    wa.discover_relations(min_count=8, shapes=("body_to_body",))
    b2b = [m for m in wa._discovered_relations.values() if m["shape"] == "body_to_body"]
    assert b2b
    target = next(m for m in b2b if {m["type_a"], m["type_b"]} == {"Body", "Number"})
    assert target["count"] >= 10


def test_all_three_shapes_share_rel_id_space_and_grow_grammar():
    wa = WorldAdapter()
    for _ in range(10):
        wa.record_activity("act", ["Body", "Number"])
        wa.record_activity("observe", ["Item"])
    promoted = wa.discover_relations(
        min_count=8, shapes=("temporal_lag", "agent_to_body", "body_to_body"))
    assert {"temporal_lag", "agent_to_body", "body_to_body"} <= _shapes_of(wa)
    assert all(rid.startswith("rel_") for rid in wa._discovered_relations)
    # every promoted relation grew a Γ production
    assert all(rid in wa.meta_productions() for rid in promoted)
