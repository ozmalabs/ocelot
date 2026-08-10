"""Γ_meta core, slice C — Γ_dynamic grown from observing a real chess world via
live self-play, on the seed-booted WorldAdapter.

The autopoietic loop (live_gamma): reset -> observe -> step -> observe -> grow,
no goal, no reward. Acceptance is NOT "plays good chess" — it is that the agent
DISCOVERS its taxonomy by experience (productions for every piece type), infers
genuine chess invariants (pawns never on their impossible rank), grows monotone,
and its boundary (senses/models/acts_on) is a gradient (Squares are sensed +
modeled but never acted on; pieces are acted on). No game outcome is consumed.

Completes test_curious_agent (with the slice-A structural + slice-B engine
twins); after this the hull (CuriousAgent) can burn.
"""
from __future__ import annotations

import inspect

import pytest

pytest.importorskip("substrate_rs")
pytest.importorskip("chess")

from substrate import Attr, In, Lit, SetT
from substrate.world_adapter import WorldAdapter


def _agent():
    a = WorldAdapter()
    a.boot_gamma_meta()
    return a


def test_grows_gamma_from_observation():
    a = _agent()
    a.live_gamma(n_games=4, max_plies=40, grow_every_game=1)
    assert len(a.gamma_dynamic.productions) > 0
    assert a.n_observations > 0
    assert all(p.provenance.startswith("discovered:")
               for p in a.gamma_dynamic.productions)


def test_discovers_all_piece_types():
    a = _agent()
    a.live_gamma(n_games=8, max_plies=50, grow_every_game=2)
    src_types = {p.src.type for p in a.gamma_dynamic.productions}
    expected = {
        "WhiteKing", "WhiteQueen", "WhiteRook", "WhiteBishop", "WhiteKnight",
        "WhitePawn", "BlackKing", "BlackQueen", "BlackRook", "BlackBishop",
        "BlackKnight", "BlackPawn"}
    assert not (expected - src_types), f"missing: {expected - src_types}"


def test_quality_is_monotone_non_decreasing():
    a = _agent()
    qualities = [a.quality_of_gamma()]
    for _ in range(4):
        a.live_gamma(n_games=1, max_plies=40, grow_every_game=1)
        qualities.append(a.quality_of_gamma())
    diffs = [b - x for x, b in zip(qualities, qualities[1:])]
    assert all(d >= 0 for d in diffs), f"quality regressed: {qualities}"
    assert qualities[-1] > qualities[0], "no learning observed"


def test_discovers_chess_invariants_about_pawns():
    a = _agent()
    a.live_gamma(n_games=8, max_plies=50, grow_every_game=2)

    def rank_set(src_type):
        for p in a.gamma_dynamic.productions:
            if p.src.type != src_type or not isinstance(p.where, In):
                continue
            m = p.where.member
            if isinstance(m, Attr) and m.key == "rank" \
                    and isinstance(p.where.container, SetT):
                return {it.value for it in p.where.container.items
                        if isinstance(it, Lit)}
        return None

    wp = rank_set("WhitePawn")
    assert wp is not None and 0 not in wp, f"white pawn on rank 0: {wp}"
    bp = rank_set("BlackPawn")
    assert bp is not None and 7 not in bp, f"black pawn on rank 7: {bp}"


def test_boundary_relations_are_subsets_of_senses():
    a = _agent()
    a.live_gamma(n_games=5, max_plies=40, grow_every_game=2)
    sensed, modeled, acted = a.senses(), a.models_set(), a.acts_on_set()
    assert sensed
    assert modeled <= sensed, f"modeled not subset: {modeled - sensed}"
    assert acted <= sensed, f"acts_on not subset: {acted - sensed}"


def test_boundary_is_a_gradient_not_a_partition():
    a = _agent()
    a.live_gamma(n_games=6, max_plies=50, grow_every_game=2)
    assert "Square" in a.senses()
    assert "Square" in a.models_set()
    assert "Square" not in a.acts_on_set(), "the agent doesn't move squares"
    piece_acts = {t for t in a.acts_on_set() if any(
        x in t for x in ("Pawn", "Knight", "Bishop", "Rook", "Queen", "King"))}
    assert piece_acts, f"no piece-types acted on: {a.acts_on_set()}"


def test_boundary_edges_visible_in_mind_graph():
    a = _agent()
    a.live_gamma(n_games=3, max_plies=30, grow_every_game=1)
    agent_nodes = [n for n in a.s.nodes("Agent")]
    assert a.agent in agent_nodes
    assert [n for n in a.s.nodes("BodyType")]
    assert list(a.inner.neighbours(a.agent, "senses"))
    assert list(a.inner.neighbours(a.agent, "models"))
    assert list(a.inner.neighbours(a.agent, "acts_on"))


def test_no_win_signal_in_the_growth_path():
    """The curious growth path must not consume game outcomes — that's what
    distinguishes curiosity from a reward learner. Scan the Γ-core methods'
    source for forbidden outcome identifiers."""
    import ast
    import textwrap
    forbidden = {"result", "is_checkmate", "is_game_over", "outcome", "reward"}
    src = "\n".join(textwrap.dedent(inspect.getsource(m)) for m in (
        WorldAdapter.live_gamma, WorldAdapter.observe_gamma,
        WorldAdapter.grow_gamma))
    offenders = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            offenders.append(node.attr)
        if isinstance(node, ast.Name) and node.id in forbidden:
            offenders.append(node.id)
    assert not offenders, f"growth path uses outcome identifiers: {offenders}"
