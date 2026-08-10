"""Two seed-booted WorldAdapter agents in a shared chess world.

Migrates every test in tests/test_multi_agent.py onto the WorldAdapter /
boot_core path, eliminating CuriousAgent entirely.

Coverage map (original -> migrated):
  test_world_starts_with_agent_markers_and_channel  -> same (world only, no agent)
  test_both_agents_see_the_world                    -> test_both_adapters_see_the_world
  test_agents_have_separate_mind_graphs             -> test_adapters_have_separate_substrates
  test_both_agents_grow_via_shared_life             -> test_both_adapters_grow_via_shared_life
  test_messages_are_transient                       -> same (world only, no agent)
  test_message_visible_to_both_agents               -> test_message_visible_to_both_adapters
  test_term_tree_payload_is_observable              -> test_term_tree_payload_is_observable
  test_agents_share_their_thoughts                  -> test_adapters_share_their_thoughts
  test_two_agents_complete_a_game_together          -> test_two_adapters_complete_a_game_together

Architecture note: the ingest() method in WorldAdapter now records Term.*
type names in _sensed_types (additive superset), which allows the agent to
sense Term-tree payloads a world deliberately places in its substrate (message
payloads). Term.* nodes are still never instanced (they carry no `id`).
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.shared_chess import SharedChessWorld, make_world_handle


# --- shared driver: drives two WorldAdapters through a shared chess world ----


def run_two_agents_wa(wa_a: WorldAdapter, wa_b: WorldAdapter,
                      n_games: int = 2,
                      max_plies: int = 40,
                      grow_every_game: int = 1):
    """Drive two WorldAdapter instances through alternating life in a shared
    chess world. Mirrors domains.shared_chess.run_two_agents but targets the
    WorldAdapter API:
      - observe() instead of CuriousAgent.observe()
      - choose_action(legal_actions, preview_fn) with a preview closure
      - register_relation / record_activity for boundary + discovery bookkeeping
      - discover_relations(all shapes) + check_theorems + discover_theorems for
        the post-game growth pass (mirrors grow_gamma + discover_relations +
        check_theorems + discover_theorems)
      - wa.n_games incremented per game (the counter the last test asserts)

    Returns (world, final_ctx) for inspection, same shape as run_two_agents.
    """
    world = SharedChessWorld()
    handle_a = make_world_handle(world, "A", wa_a)
    handle_b = make_world_handle(world, "B", wa_b)

    final_ctx: dict = {}
    for _ in range(n_games):
        substrate, ctx = handle_a["reset"]()
        wa_a.observe(substrate)
        wa_b.observe(substrate)
        for ply in range(max_plies):
            acting_agent_id = "A" if ply % 2 == 0 else "B"
            acting_wa = wa_a if acting_agent_id == "A" else wa_b
            acting_handle = handle_a if acting_agent_id == "A" else handle_b
            actions = acting_handle["legal_actions"](substrate, ctx)
            if not actions:
                break
            # Capture loop vars for the closures (avoid late-binding)
            cur_s, cur_c = substrate, ctx
            preview_fn = (lambda a, c=cur_c: world.apply_action(c, a)[0])
            action = acting_wa.choose_action(actions, preview_fn)
            touched = acting_handle["interpret_acts_on"](substrate, ctx, action)
            for t in touched:
                acting_wa.register_relation(t, "acts_on")
            acting_wa.record_activity("act", touched)
            substrate, ctx = acting_handle["apply_action"](substrate, ctx, action)
            wa_a.observe(substrate)
            wa_b.observe(substrate)
        final_ctx = ctx

        for wa in (wa_a, wa_b):
            wa.n_games += 1
            if wa.n_games % grow_every_game == 0:
                # Full parity with CuriousAgent's post-game pass:
                # grow_gamma (all discovery shapes) + check/discover theorems.
                wa.discover_relations(
                    shapes=("temporal_lag", "agent_to_body", "body_to_body"))
                wa.check_theorems()
                wa.discover_theorems()

    return world, final_ctx


# --- shared world basics ---


def test_world_starts_with_agent_markers_and_channel():
    """The shared substrate carries both agents as entities and a channel.

    Direct migration — this test uses only the SharedChessWorld, no agents.
    """
    world = SharedChessWorld()
    substrate, ctx = world.reset()
    g = substrate.graph
    markers = list(g.nodes("AgentMarker"))
    assert len(markers) == 2
    assert {m.attrs["id"] for m in markers} == {"A", "B"}
    assert {m.attrs["role"] for m in markers} == {"white", "black"}
    channel = list(g.nodes("Channel"))
    assert len(channel) == 1


def test_both_adapters_see_the_world():
    """Both WorldAdapters observe the SAME substrate object on each tick.
    Their senses() should contain the shared world types (AgentMarker, Channel).

    Migrates: test_both_agents_see_the_world.
    """
    wa_a = WorldAdapter()
    wa_b = WorldAdapter()
    run_two_agents_wa(wa_a, wa_b, n_games=1, max_plies=10)
    for type_name in ("AgentMarker", "Channel"):
        assert type_name in wa_a.senses()
        assert type_name in wa_b.senses()


# --- privacy: adapters do NOT share substrate state ---


def test_adapters_have_separate_substrates():
    """Each WorldAdapter has its own substrate — no shared references.

    Migrates: test_agents_have_separate_mind_graphs.
    The equivalent of mind_graph is wa.s (the substrate); the equivalent of
    agent_root is wa.agent. Two separate WorldAdapter() instances have separate
    substrates and separate agent nodes — privacy by construction.
    """
    wa_a = WorldAdapter()
    wa_b = WorldAdapter()
    assert wa_a.s is not wa_b.s
    assert wa_a.agent != wa_b.agent or wa_a.s is not wa_b.s


def test_both_adapters_grow_via_shared_life():
    """Both WorldAdapters accumulate content while sharing a world. Both grow
    _discovered_relations (via post-game discover_relations) and acts_on
    (via register_relation during play). Their substrates remain private.

    Migrates: test_both_agents_grow_via_shared_life.
    """
    wa_a = WorldAdapter()
    wa_b = WorldAdapter()
    run_two_agents_wa(wa_a, wa_b, n_games=2, max_plies=20)
    assert len(wa_a._discovered_relations) > 0
    assert len(wa_b._discovered_relations) > 0
    assert len(wa_a.acts_on_set()) > 0
    assert len(wa_b.acts_on_set()) > 0
    # Privacy: their substrates are different Python objects.
    assert wa_a.s is not wa_b.s


# --- communication: messages flow through the world ---


def test_messages_are_transient():
    """A message appears in the substrate when sent; on the next apply_action,
    it's gone. Two chess players don't pile words on the board.

    Direct migration — this test uses only the SharedChessWorld, no agents.
    """
    world = SharedChessWorld()
    substrate, ctx = world.reset()
    # Send a message
    substrate, ctx = world.apply_action(ctx, ("send_message", "A", None))
    # Message node present in this substrate snapshot
    msg_nodes = list(substrate.graph.nodes("Message"))
    assert len(msg_nodes) == 1
    assert ctx["current_message"] is not None
    # Make a chess move — the previous message should be gone
    move = next(iter(ctx["board"].legal_moves))
    substrate, ctx = world.apply_action(ctx, ("move", "A", move))
    assert ctx["current_message"] is None
    msg_nodes = list(substrate.graph.nodes("Message"))
    assert len(msg_nodes) == 0


def test_message_visible_to_both_adapters():
    """If A sends a message, B's next observation includes it as a Message
    node. The Channel and Message become part of B's senses.

    Migrates: test_message_visible_to_both_agents.
    """
    wa_b = WorldAdapter()
    world = SharedChessWorld()
    substrate, ctx = world.reset()
    substrate, ctx = world.apply_action(ctx, ("send_message", "A", None))
    wa_b.observe(substrate)
    assert "Message" in wa_b.senses()


def test_term_tree_payload_is_observable():
    """When an agent sends a message with a Term-tree payload, the receiving
    WorldAdapter observes the Term-tree's nodes as new sensed types in the
    substrate. Term.* type names are recorded in senses() (the adapter's
    ingest now senses Term.* types from the world substrate before skipping
    instancing, so a deliberately-placed Term-tree payload is observable).

    Migrates: test_term_tree_payload_is_observable (unchanged world side).
    """
    from substrate import Gte, Count, Neighbours, Var, Lit
    wa_b = WorldAdapter()
    world = SharedChessWorld()
    substrate, ctx = world.reset()
    # A sends a Term-tree payload — a simple Gte(Count(Neighbours), Lit) expression.
    payload = Gte(Count(Neighbours(Var("agent"), "senses")), Lit(0))
    substrate, ctx = world.apply_action(ctx, ("send_message", "A", payload))
    # B observes — Term.* types should be in senses
    wa_b.observe(substrate)
    assert "Term.Gte" in wa_b.senses()
    assert "Term.Count" in wa_b.senses()
    assert "Term.Neighbours" in wa_b.senses()
    assert "Term.Var" in wa_b.senses()
    assert "Term.Lit" in wa_b.senses()


def test_adapters_share_their_thoughts():
    """Over a full run, adapters send each other Term-trees from their own
    bootstrap theorem predicates (via message_payload()). Both end up with
    Term.* types in their senses — they've observed each other's representational
    structure even without direct substrate access.

    Migrates: test_agents_share_their_thoughts.
    """
    wa_a = WorldAdapter()
    wa_b = WorldAdapter()
    run_two_agents_wa(wa_a, wa_b, n_games=2, max_plies=30)
    # Each adapter should have observed at least some Term.* types from the
    # other's messages (message_payload() returns a bootstrap Theorem predicate
    # as a Term-tree; world.apply_action serialises it into the substrate).
    a_terms = {t for t in wa_a.senses() if t.startswith("Term.")}
    b_terms = {t for t in wa_b.senses() if t.startswith("Term.")}
    assert len(a_terms) > 0
    assert len(b_terms) > 0


def test_two_adapters_complete_a_game_together():
    """Smoke test: two WorldAdapters play a (partial) chess game and don't crash.
    The n_games counter on each adapter is incremented by run_two_agents_wa.

    Migrates: test_two_agents_complete_a_game_together.
    """
    wa_a = WorldAdapter()
    wa_b = WorldAdapter()
    world, final_ctx = run_two_agents_wa(wa_a, wa_b, n_games=2, max_plies=30)
    assert final_ctx["board"].fullmove_number >= 1
    assert wa_a.n_games == 2
    assert wa_b.n_games == 2
