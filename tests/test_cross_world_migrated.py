"""cross-world life, migrated — ONE seed-booted agent perceives multiple worlds.

The old tests/test_cross_world.py drove `CuriousAgent.live()` over chess and
Conway and asserted three things: (1) the SAME agent code works in both worlds,
(2) the two worlds give the agent DIFFERENT (disjoint) sensed vocabularies, and
(3) the agent's mind ACCUMULATES everything — living in a second world keeps the
first world's senses and adds the second's.

Those three are world-agnostic perception facts and migrate cleanly onto the
`WorldAdapter` over `boot_core`: the SAME adapter ingests world after world via
`ingest()`, its `senses()` accumulates every perceived node type, and instances
from every world coexist in the one shared graph (the `knows` set). No
`CuriousAgent` here.

We demonstrate the mechanism on TWO world pairs:

  • chess → Conway (the original test's pair): disjoint type vocabularies, senses
    accumulate across the swap. These worlds publish `id`-less type nodes, so they
    exercise the `senses()` accumulation half of the fold.
  • number → structure (the `id`-carrying worlds, like the other migrated tests):
    additionally exercises the WorldInstance half — instances from BOTH worlds
    live in the one graph and the agent `knows` all of them.

NOW MIGRATED (the adapter grew `live()`): the boundary-texture and grammar-growth
halves the original test asserted are now expressible WITHOUT `CuriousAgent`,
driving the worlds through `WorldAdapter.live()`:

  • SPECTATOR-vs-ACTOR acts_on texture — `live()` advances a world via its own
    `legal_actions`/`apply_action` and, per ply, registers the `acts_on`
    body-types the world's `interpret_acts_on` reports. Conway reports none (its
    evolution is the world's own dynamics, not the agent's doing) → empty
    `acts_on_set()`; chess reports the moved/captured pieces → a rich one. The
    boundary texture differs structurally between worlds, from the same adapter.
  • GRAMMAR / Γ-production GROWTH — `live()` accumulates `act`→`act` co-occurrence
    over the plies and runs `discover_relations`, which (when the SEEDED salience
    predicate accepts a recurrent temporal-lag pair) reifies it into a new Γ
    production (`meta_productions()`, landing in `grammar_to_json()`) plus an
    asserted `Pattern` node. The DECISION (salience) is the seed; the adapter only
    sequences the world and counts.

NOW ALSO MIGRATED (the adapter grew `observe_structure` / `grow_structural_grammar`):
the original `test_agent_lives_in_conway` (the Γ-growth half) and
`test_conway_agent_discovers_cell_invariants` assert `agent.gamma_dynamic.productions`
grew from observing Conway, with AliveCell/DeadCell as production src-types. In
`CuriousAgent` that growth is the triple-discovery branch of `grow_gamma`: it
counts `(src_type, edge_type, tgt_type)` STRUCTURAL triples (`triple_counts`)
accumulated while observing, and reifies any seen at least
`discovery_triple_threshold` times into a Γ production — the same domain-agnostic
threshold mechanism the adapter already uses for relation-promotion, just over
structural type-triples rather than activity pairs. Conway's cells are id-less
(row/col, no `id`), so `ingest` senses them but never instances them or mirrors
their `adjacent_to` edges; the adapter therefore grew a minimal, ADDITIVE,
decision-free pair of methods — `observe_structure` (count the structural
type-triples between world nodes, incl. id-less ones) and
`grow_structural_grammar` (reify the over-threshold triples via the existing
`_grow_grammar`, the threshold read from the seeded `discovery_triple_threshold`
policy). The DECISION (the threshold) stays graph-resident seed data; the adapter
only counts and reifies. AliveCell/DeadCell then appear as grown src-types and the
agent's Γ grows from observing Conway, with NO `CuriousAgent`.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.worlds import chess_world, conway_world
from domains.number_world import NumberWorld
from domains.structure_world import StructureWorld, structure_world_handle


# --- driving a world purely for STRUCTURAL observation (the Conway Γ-growth) --

def _observe_structure_over(wa: WorldAdapter, world, n_games: int, max_plies: int):
    """Mechanically step a world and feed each state's STRUCTURE to the adapter.
    No decisions — the world's own `legal_actions`/`apply_action` advance it; the
    adapter only counts the structural type-triples it observes."""
    for _ in range(n_games):
        s, ctx = world["reset"]()
        wa.observe_structure(s)
        for _ in range(max_plies):
            actions = world["legal_actions"](s, ctx)
            if not actions:
                break
            s, ctx = world["apply_action"](s, ctx, actions[0])
            wa.observe_structure(s)


# --- driving the dict-of-callables worlds (chess / Conway) -------------------

def _live(wa: WorldAdapter, world, n_steps: int = 4):
    """Mechanically drive a `World` (dict of callables) through the adapter:
    reset → ingest, then step → ingest. No decisions — the world's own
    `legal_actions`/`apply_action` advance it; the adapter only perceives."""
    s, ctx = world["reset"]()
    wa.ingest(s)
    for _ in range(n_steps):
        action = world["legal_actions"](s, ctx)[0]
        s, ctx = world["apply_action"](s, ctx, action)
        wa.ingest(s)


def test_same_adapter_lives_in_chess_and_conway():
    """The SAME adapter code perceives both worlds — and picks up each world's
    own vocabulary. (Replaces the old 'same agent code works in both bodies'.)"""
    chess_wa = WorldAdapter()
    _live(chess_wa, chess_world())
    assert "Square" in chess_wa.senses()
    assert {"WhiteKing", "BlackKing"} <= chess_wa.senses()

    conway_wa = WorldAdapter()
    _live(conway_wa, conway_world(rows=10, cols=10))
    # Conway has exactly two cell types — the agent perceives both.
    assert "AliveCell" in conway_wa.senses()
    assert "DeadCell" in conway_wa.senses()


def test_chess_and_conway_have_disjoint_vocabularies():
    """Different bodies → different sensed vocabularies, from the same adapter.
    (Replaces test_chess_and_conway_agents_have_different_boundary_textures, the
    senses half — the acts_on half is out of scope, see module docstring.)"""
    chess_wa = WorldAdapter()
    _live(chess_wa, chess_world(), n_steps=3)

    conway_wa = WorldAdapter()
    _live(conway_wa, conway_world(rows=10, cols=10), n_steps=3)

    assert chess_wa.senses() & conway_wa.senses() == set(), (
        "chess and Conway shouldn't share sensed types (different vocabularies)"
    )


def test_world_swap_mid_life_accumulates_senses():
    """ONE adapter lives in chess then Conway. Its graph accumulates everything:
    the chess vocabulary survives and the Conway vocabulary is added on top.
    (Direct migration of test_world_swap_mid_life.)"""
    wa = WorldAdapter()
    _live(wa, chess_world(), n_steps=2)
    chess_sensed = set(wa.senses())
    assert "Square" in chess_sensed

    _live(wa, conway_world(rows=8, cols=8), n_steps=2)
    assert chess_sensed <= wa.senses(), \
        "old chess-world senses should still be present after the swap"
    assert "AliveCell" in wa.senses() or "DeadCell" in wa.senses(), \
        "Conway-world senses should be added"


# --- the deeper cross-world point: ONE shared graph of instances -------------

def test_one_agent_accumulates_instances_across_two_worlds():
    """The point of cross-world: the SAME agent perceives multiple worlds and
    accumulates a SHARED graph. Driven on the `id`-carrying worlds so the
    WorldInstance half of the fold is exercised — instances from BOTH the number
    world and the structure world coexist, and the agent `knows` all of them."""
    wa = WorldAdapter()

    # World 1: walk a number line.
    nw = NumberWorld(max_n=14)
    sub, ctx = nw.reset()
    wa.ingest(sub)
    for _ in range(10):
        sub, ctx = nw.apply_action(ctx, ("count_up",))
        wa.ingest(sub)
    number_senses = set(wa.senses())
    n_numbers = len(wa.instances("Number"))
    knows_after_number = len(wa.inner.neighbours(wa.agent, "knows"))
    assert n_numbers >= 8, f"should have perceived number instances; got {n_numbers}"
    assert "Number" in number_senses

    # World 2: a structure world (sets / functions / elements).
    handle = structure_world_handle(StructureWorld(), None)
    sub, ctx = handle["reset"]()
    wa.ingest(sub)
    for _ in range(8):
        sub, ctx = handle["apply_action"](sub, ctx, ("focus_next",))
        wa.ingest(sub)

    # The first world's vocabulary survives; the second's is added.
    assert number_senses <= wa.senses(), "number senses should survive the swap"
    assert {"MathSet", "Function", "Element"} <= wa.senses(), \
        "structure-world senses should be added"

    # Instances from BOTH worlds coexist in the one shared graph.
    assert len(wa.instances("Number")) == n_numbers, \
        "number instances should persist after living in a second world"
    assert len(wa.instances("MathSet")) > 0, "structure instances should be present"

    # The agent `knows` strictly more after perceiving the second world (the
    # shared graph grew — both worlds' instances are in the one knows-set).
    knows_after_structure = len(wa.inner.neighbours(wa.agent, "knows"))
    assert knows_after_structure > knows_after_number, \
        "the shared knows-set should grow as the agent perceives a second world"


# --- boundary texture: SPECTATOR (Conway) vs ACTOR (chess) acts_on -----------
# (migrates the acts_on half of test_conway_world_is_spectator and
# test_chess_and_conway_agents_have_different_boundary_textures, now that
# WorldAdapter.live() drives a world and registers acts_on per ply.)


def test_conway_lived_is_a_spectator_world():
    """`live()` drives Conway by its own callables; Conway's `interpret_acts_on`
    reports nothing (its evolution is the world's own dynamics, not the agent's
    doing), so the boundary's `acts_on_set()` stays EMPTY — the spectator-world
    texture. (Migration of test_conway_world_is_spectator.)"""
    wa = WorldAdapter()
    wa.live(conway_world(rows=10, cols=10), n_games=4, max_plies=30)
    # The agent still senses Conway's vocabulary — it observes, it just can't act.
    assert "AliveCell" in wa.senses()
    assert "DeadCell" in wa.senses()
    assert wa.acts_on_set() == set(), (
        f"spectator world shouldn't have acts_on relations; got {wa.acts_on_set()}"
    )


def test_chess_and_conway_have_different_acts_on_textures():
    """Different bodies → different boundary textures, from the SAME adapter
    code: chess (an ACTOR world) registers a rich `acts_on` over the pieces it
    moves/captures; Conway (a SPECTATOR world) registers none. (Migration of the
    acts_on half of test_chess_and_conway_agents_have_different_boundary_textures.)"""
    chess_wa = WorldAdapter()
    chess_wa.live(chess_world(), n_games=3, max_plies=30)

    conway_wa = WorldAdapter()
    conway_wa.live(conway_world(rows=10, cols=10), n_games=3, max_plies=30)

    # chess acts on its pieces; Conway acts on nothing.
    assert len(chess_wa.acts_on_set()) > 0, "chess should act on the pieces it moves"
    assert len(conway_wa.acts_on_set()) == 0, "Conway is a spectator — no acts_on"
    # The acts_on set is drawn from chess's own (disjoint) vocabulary.
    assert chess_wa.acts_on_set() <= chess_wa.senses()
    assert chess_wa.acts_on_set() & conway_wa.senses() == set(), (
        "chess's acts_on body-types shouldn't appear in Conway's vocabulary"
    )


# --- grammar growth: living a world grows Γ via discovery ---------------------
# (migrates the gamma-growth half of test_agent_lives_in_conway, now that
# live() accumulates act->act co-occurrence and runs discover_relations, which
# reifies salient temporal-lag pairs into new Γ productions + Pattern nodes.
# Driven on chess, the ACTOR world that publishes typed acts_on activity — the
# adapter's relation-promotion needs typed activity to discover over, which
# Conway (a spectator) does not produce. Conway's CELL-TRANSITION Γ_dynamic
# growth is the out-of-scope compositional mechanism; see the module docstring.)


def test_living_chess_grows_the_grammar():
    """Living in chess for enough plies accumulates recurrent `act`→`act`
    co-occurrence; `live()`'s closing `discover_relations` promotes the salient
    pairs into new Γ productions (`meta_productions`) that LAND in the grammar,
    each with an asserted `Pattern` node. (Migration of the Γ-growth assertion
    of test_agent_lives_in_conway — `gamma_dynamic.productions > 0` — onto the
    adapter's relation-promotion path.)"""
    wa = WorldAdapter()
    wa.live(chess_world(), n_games=8, max_plies=40)

    grown = wa.meta_productions()
    assert len(grown) > 0, "living the world should grow Γ productions via discovery"

    # Every grown relation is a real production in the agent's grammar.
    grammar = wa.inner.grammar_to_json()
    prod_edges = {p.get("edge_type") for p in grammar.get("productions", [])}
    assert grown <= prod_edges, "every grown meta-production should land in the grammar"

    # Each growth asserts a temporal-lag Pattern node, one per grown relation, and
    # its src/tgt are body-types drawn from the world the agent lived in.
    patterns = wa.patterns()
    assert len(patterns) == len(grown)
    assert all(p["shape"] == "temporal_lag" for p in patterns)
    vocab = wa.senses()
    assert all(p["from_type"] in vocab and p["to_type"] in vocab for p in patterns), \
        "discovered patterns should relate body-types from the lived world"


def test_grammar_growth_and_spectator_texture_are_world_specific():
    """Ties the two migrated halves together: an ACTOR world (chess) BOTH grows
    Γ over its own vocabulary AND registers a non-empty acts_on; a SPECTATOR
    world (Conway) does NEITHER — empty acts_on and no grown patterns — from the
    same adapter code. The boundary texture and the grown grammar are both
    world-specific.

    (Conway's discovery growing nothing is the adapter's relation-promotion
    correctly finding no salient typed activity in a spectator world; Conway's
    actual Γ_dynamic CELL-transition growth is the out-of-scope compositional
    mechanism — see the module docstring.)"""
    chess_wa = WorldAdapter()
    chess_wa.live(chess_world(), n_games=8, max_plies=40)
    chess_pat_types = {p["from_type"] for p in chess_wa.patterns()} | \
                      {p["to_type"] for p in chess_wa.patterns()}

    conway_wa = WorldAdapter()
    conway_wa.live(conway_world(rows=10, cols=10), n_games=8, max_plies=40)

    # Chess: an actor world — grows Γ over its OWN vocabulary, and acts on it.
    assert len(chess_wa.meta_productions()) > 0
    assert len(chess_wa.acts_on_set()) > 0
    assert chess_pat_types and chess_pat_types <= chess_wa.senses()

    # Conway: a spectator world — no typed activity to discover over, nothing to
    # act on. The texture differs even though the same adapter lived in both.
    assert conway_wa.meta_productions() == set()
    assert conway_wa.patterns() == []
    assert conway_wa.acts_on_set() == set()

    # The grown chess patterns are disjoint from Conway's vocabulary entirely.
    assert chess_pat_types & conway_wa.senses() == set(), (
        "chess-grown patterns shouldn't touch Conway's (disjoint) vocabulary"
    )


# --- Conway STRUCTURAL Γ-growth: observing Conway grows the grammar -----------
# (migrates the Γ-growth half of test_agent_lives_in_conway and all of
# test_conway_agent_discovers_cell_invariants — the `gamma_dynamic.productions`
# growth with AliveCell/DeadCell as production src-types — onto the adapter's
# structural-triple discovery: observe_structure counts (src_type, edge_type,
# tgt_type) triples between Conway's id-less cells, grow_structural_grammar
# reifies the over-threshold ones into Γ productions, the threshold read from the
# seeded discovery_triple_threshold policy.)


def test_observing_conway_grows_the_grammar():
    """Observing Conway accumulates recurrent structural type-triples (cells
    `adjacent_to` cells); `grow_structural_grammar` reifies the over-threshold
    ones into new Γ productions — Γ grows with no win signal and no acts_on.
    (Migration of test_agent_lives_in_conway's `gamma_dynamic.productions > 0`.)"""
    wa = WorldAdapter()
    _observe_structure_over(wa, conway_world(rows=10, cols=10),
                            n_games=4, max_plies=30)
    # Conway has exactly two cell types — the agent perceives both.
    assert "AliveCell" in wa.senses()
    assert "DeadCell" in wa.senses()
    # Γ grows from observing Conway's structure.
    grown = wa.grow_structural_grammar()
    assert len(wa.meta_productions()) > 0, \
        "observing Conway should grow Γ productions via structural discovery"
    # Every grown production is a real edge type in the agent's grammar.
    grammar = wa.inner.grammar_to_json()
    prod_edges = {p.get("edge_type") for p in grammar.get("productions", [])}
    assert wa.meta_productions() <= prod_edges, \
        "every grown structural production should land in the grammar"
    # Each growth asserts a structural Pattern node, one per grown relation.
    patterns = wa.patterns()
    assert len(patterns) == len(wa.meta_productions())
    assert all(p["shape"] == "structural_triple" for p in patterns)
    assert grown <= wa.senses()


def test_conway_structural_growth_discovers_cell_invariants():
    """The grown productions have AliveCell and/or DeadCell as src-types: the
    agent discovers the cell types as the structure it now models. (Direct
    migration of test_conway_agent_discovers_cell_invariants — the original
    asserted `{p.src.type for p in gamma_dynamic.productions}` contains AliveCell
    or DeadCell.)"""
    wa = WorldAdapter()
    _observe_structure_over(wa, conway_world(rows=12, cols=12),
                            n_games=5, max_plies=40)
    src_types = wa.grow_structural_grammar()
    assert "AliveCell" in src_types or "DeadCell" in src_types, \
        "cell types should appear as src-types in the grown productions"
    # The grown structure relates Conway's own (disjoint) cell vocabulary.
    pat_types = {p["from_type"] for p in wa.patterns()} | \
                {p["to_type"] for p in wa.patterns()}
    assert pat_types <= wa.senses()
    assert pat_types & {"AliveCell", "DeadCell"}, \
        "discovered patterns should relate Conway's cell types"
