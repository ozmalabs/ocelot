"""Two agents in a shared chess world.

Both agents act on the SAME substrate (one chess board, one channel, both
visible as AgentMarker nodes). They do NOT share mind_graphs — privacy is
by construction (separate CuriousAgent instances).

**Messages are transient.** Two chess players talk across a board; the words
don't pile up. Each ``send_message`` action produces a Message node that
appears in the substrate for *one* observation cycle (so both agents
observe it) and is gone on the next rebuild. The agent's payload is an
arbitrary Term-tree pulled from its own mind_graph — by default a random
theorem's predicate, but this is a hook the agent's ``message_payload()``
method controls.

The receiving agent observes the Term-tree's nodes as ordinary graph state.
Whether the receiver builds a *model* of those Term-trees (productions
referencing Term.Gte → Term.Count → etc.) emerges from its own discovery.

Implementation notes:

- ``apply_action`` is stateless (returns new state without mutating world).
- World identity exists only so per-agent handles can refer to "the same world."
- Messages live in the *ctx*'s ``current_message`` slot, included in the
  substrate during ``_build`` and discarded on the next ``apply_action``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chess as pc

from domains import chess as cg
from domains.worlds import _chess_piece_type_name
from substrate import term_to_subgraph


_AGENT_MARKER = "AgentMarker"
_CHANNEL = "Channel"
_MESSAGE = "Message"


@dataclass
class SharedChessWorld:
    """The shared world. Holds no mutable game state — that lives in the ctx
    threaded by the driver. The class exists so per-agent handles can refer
    to the same world identity (for agent-id-aware ``legal_actions``)."""

    def reset(self) -> tuple[Any, dict]:
        board = pc.Board()
        substrate, ctx = self._build(board, current_message=None)
        ctx["board"] = board
        ctx["current_message"] = None
        ctx["message_count"] = 0
        return substrate, ctx

    def _build(self, board: pc.Board, current_message: dict | None) -> tuple[Any, dict]:
        """Build a fresh substrate. If ``current_message`` is not None,
        include it as a Message node with optional payload subgraph."""
        s = cg.make_substrate()
        ctx = cg.encode_fen(s, board.fen())
        g = s.graph
        g._insert_node(_AGENT_MARKER, {"id": "A", "role": "white"})
        g._insert_node(_AGENT_MARKER, {"id": "B", "role": "black"})
        channel_id = g._insert_node(_CHANNEL, {})
        if current_message is not None:
            mid = g._insert_node(_MESSAGE, {
                "from": current_message["from"],
                "seq": current_message["seq"],
            })
            g._insert_edge(mid, "in_channel", channel_id)
            payload = current_message.get("payload")
            if payload is not None:
                # Serialize the Term-tree as a subgraph attached via "payload".
                payload_root = term_to_subgraph(payload, g)
                g._insert_edge(mid, "payload", payload_root)
        return s, ctx

    def legal_actions(self, ctx: dict, agent_id: str, agent) -> list:
        """Per-agent legal actions. The acting ``agent`` is passed so we can
        ask it for a message payload (a Term-tree from its mind_graph).

        Speaking is always available; chess moves are only available on the
        agent's chess-turn. The agent decides what it wants to do — including
        choosing to talk forever if its curiosity drive prefers that over
        playing. That's the experiment's observation, not a bug."""
        actions: list = []
        payload = agent.message_payload() if agent is not None else None
        actions.append(("send_message", agent_id, payload))
        board = ctx["board"]
        my_turn = (agent_id == "A" and board.turn == pc.WHITE) or \
                  (agent_id == "B" and board.turn == pc.BLACK)
        if my_turn:
            for move in board.legal_moves:
                actions.append(("move", agent_id, move))
        return actions

    def interpret_acts_on(self, ctx: dict, action) -> list[str]:
        kind = action[0]
        if kind == "move":
            _, _agent_id, move = action
            types: list[str] = []
            board = ctx["board"]
            moved = board.piece_at(move.from_square)
            if moved is not None:
                types.append(_chess_piece_type_name(moved))
            if board.is_capture(move):
                if board.is_en_passant(move):
                    cap_sq = pc.square(pc.square_file(move.to_square),
                                       pc.square_rank(move.from_square))
                    captured = board.piece_at(cap_sq)
                else:
                    captured = board.piece_at(move.to_square)
                if captured is not None:
                    types.append(_chess_piece_type_name(captured))
            return types
        if kind == "send_message":
            return [_CHANNEL, _MESSAGE]
        return []

    def apply_action(self, ctx: dict, action) -> tuple[Any, dict]:
        """Stateless: returns future (substrate, ctx). Messages do NOT persist:
        any previous ``current_message`` is discarded on each call. If this
        action is a ``send_message``, the new message becomes ``current_message``
        and lives only in the substrate built for this turn."""
        new_board = ctx["board"].copy()
        new_count = ctx["message_count"]
        new_message: dict | None = None
        kind = action[0]
        if kind == "move":
            _, _agent_id, move = action
            new_board.push(move)
        elif kind == "send_message":
            _, sender, payload = action
            new_message = {
                "from": sender,
                "payload": payload,
                "seq": new_count,
            }
            new_count += 1
        new_substrate, new_ctx = self._build(new_board, new_message)
        new_ctx["board"] = new_board
        new_ctx["current_message"] = new_message
        new_ctx["message_count"] = new_count
        return new_substrate, new_ctx


def make_world_handle(world: SharedChessWorld, agent_id: str, agent) -> dict:
    """Per-agent view of the shared world. Binds the ``agent`` reference so
    the world can ask it for a message payload at action-enumeration time."""
    def reset():
        return world.reset()

    def legal_actions(s, ctx):
        return world.legal_actions(ctx, agent_id, agent)

    def apply_action(s, ctx, action):
        return world.apply_action(ctx, action)

    def interpret_acts_on(s, ctx, action):
        return world.interpret_acts_on(ctx, action)

    return {
        "name": f"shared_chess[{agent_id}]",
        "reset": reset,
        "legal_actions": legal_actions,
        "apply_action": apply_action,
        "interpret_acts_on": interpret_acts_on,
    }


def run_two_agents(agent_a, agent_b,
                   n_games: int = 2,
                   max_plies: int = 40,
                   grow_every_game: int = 1) -> tuple[SharedChessWorld, dict]:
    """Drive two CuriousAgent instances through alternating life in a shared
    chess world. Each agent maintains its own mind_graph; neither reads the
    other's; transient messages flow through the world's substrate one tick
    at a time.

    Returns ``(world, final_ctx)`` for inspection.
    """
    world = SharedChessWorld()
    handle_a = make_world_handle(world, "A", agent_a)
    handle_b = make_world_handle(world, "B", agent_b)

    final_ctx: dict = {}
    for _ in range(n_games):
        substrate, ctx = handle_a["reset"]()
        agent_a.observe(substrate)
        agent_b.observe(substrate)
        for ply in range(max_plies):
            # Strict alternation: each ply, the next agent gets to act.
            # Their legal actions may or may not include chess moves,
            # depending on whose chess turn it is. Both can always speak.
            acting_agent_id = "A" if ply % 2 == 0 else "B"
            acting = agent_a if acting_agent_id == "A" else agent_b
            acting_handle = handle_a if acting_agent_id == "A" else handle_b
            actions = acting_handle["legal_actions"](substrate, ctx)
            if not actions:
                break
            action = acting.choose_action(substrate, ctx, actions, acting_handle)
            touched = acting_handle["interpret_acts_on"](substrate, ctx, action)
            for t in touched:
                acting._register_relation(t, "acts_on")
            acting._record_activity("act", touched)
            substrate, ctx = acting_handle["apply_action"](substrate, ctx, action)
            agent_a.observe(substrate)
            agent_b.observe(substrate)
        final_ctx = ctx

        for ag in (agent_a, agent_b):
            ag.n_games += 1
            if ag.n_games % grow_every_game == 0:
                ag.grow_gamma()
                ag.discover_relations()
                ag.check_theorems()
                ag.discover_theorems()
    return world, final_ctx
