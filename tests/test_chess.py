"""Phase 2a acceptance: pseudo-legal-move enumeration via Γ matches python-chess.

Special-move handling (castling, EP, promotion choice) and the check filter come in
Phase 2b. This test compares against python-chess's ``pseudo_legal_moves`` after
filtering out castling and en-passant on both sides — our Γ doesn't yet generate
those, and stripping them lets the substrate's basic move logic stand on its own.
"""
from __future__ import annotations

import random

import chess as pc
import pytest

from domains import chess as cg


# --- helpers ---


def _expected_moves(board: pc.Board) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for m in board.pseudo_legal_moves:
        if board.is_castling(m):
            continue
        if board.is_en_passant(m):
            continue
        out.add((m.from_square, m.to_square))
    return out


def _our_moves(fen: str) -> set[tuple[int, int]]:
    s = cg.make_substrate()
    ctx = cg.encode_fen(s, fen)
    return cg.enumerate_moves(s, ctx)


def _random_position(seed: int, max_plies: int = 30) -> pc.Board:
    rng = random.Random(seed)
    board = pc.Board()
    plies = rng.randint(4, max_plies)
    for _ in range(plies):
        if board.is_game_over():
            break
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(rng.choice(moves))
    return board


# --- FEN round-trip ---


def test_starting_position_round_trip():
    fen = pc.STARTING_FEN
    s = cg.make_substrate()
    cg.encode_fen(s, fen)
    assert cg.decode_fen(s) == fen


def test_mid_game_round_trip():
    fens = [
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
        "r3k2r/pppq1ppp/2np1n2/2b1p1B1/2B1P1b1/2NP1N2/PPPQ1PPP/R3K2R w KQkq - 6 8",
    ]
    for fen in fens:
        s = cg.make_substrate()
        cg.encode_fen(s, fen)
        assert cg.decode_fen(s) == fen, f"round-trip failed for: {fen}"


# --- legal-move parity ---


def test_starting_position_moves_match_python_chess():
    expected = _expected_moves(pc.Board())
    assert _our_moves(pc.STARTING_FEN) == expected


def test_kiwipete_moves_match_python_chess():
    """Kiwipete is a standard perft position with rich move variety."""
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = pc.Board(fen)
    expected = _expected_moves(board)
    actual = _our_moves(fen)
    missing = expected - actual
    extra = actual - expected
    assert not missing and not extra, (
        f"missing {len(missing)} moves: {[pc.Move(*m).uci() for m in list(missing)[:6]]}; "
        f"extra {len(extra)}: {[pc.Move(*m).uci() for m in list(extra)[:6]]}"
    )


@pytest.mark.parametrize("seed", list(range(50)))
def test_random_positions_pseudo_legal_parity(seed: int):
    board = _random_position(seed)
    fen = board.fen()
    expected = _expected_moves(board)
    actual = _our_moves(fen)
    missing = expected - actual
    extra = actual - expected
    if missing or extra:
        pytest.fail(
            f"seed={seed} fen={fen}\n"
            f"missing {len(missing)}: {[pc.Move(*m).uci() for m in list(missing)[:6]]}\n"
            f"extra   {len(extra)}: {[pc.Move(*m).uci() for m in list(extra)[:6]]}"
        )


# --- full legal-move parity (Wave 2b: check filter + castling/EP/promotion) ---


@pytest.mark.parametrize("seed", list(range(20)))
def test_random_positions_full_legal_parity(seed: int):
    board = _random_position(seed)
    fen = board.fen()
    expected = set(board.legal_moves)
    s = cg.make_substrate()
    ctx = cg.encode_fen(s, fen)
    actual = set(cg.enumerate_legal_moves(s, ctx))
    assert actual == expected, f"seed={seed} fen={fen}: differ"


# --- move application ---


def test_apply_move_round_trip():
    """Push 30 random plies; after each, substrate FEN matches python-chess FEN."""
    rng = random.Random(11)
    s = cg.make_substrate()
    fen = pc.STARTING_FEN
    ctx = cg.encode_fen(s, fen)
    board = ctx["board"]
    for _ in range(30):
        moves = list(board.legal_moves)
        if not moves:
            break
        m = rng.choice(moves)
        s, ctx = cg.apply_move(s, ctx, m)
        board = ctx["board"]
        assert cg.decode_fen(s) == board.fen()


# --- material eval ---


def test_starting_position_eval_is_zero():
    table = cg.material_table(cg.material_grammar())
    assert cg.evaluate(pc.Board(), table) == 0


def test_extracts_centipawns_from_gamma():
    table = cg.material_table(cg.material_grammar())
    assert table["WhitePawn"] == 100
    assert table["WhiteQueen"] == 900
    assert table["BlackKnight"] == 320


def test_material_eval_responds_to_grammar_edit():
    """Edit a piece value in Γ; eval reflects the new value immediately."""
    from substrate import Grammar, Lit, Production
    g = cg.material_grammar()
    # Asymmetric edit: make White's queen worth 5000 cp.
    new_prods = []
    for p in g.productions:
        if p.provenance == "value:WhiteQueen":
            new_prods.append(Production(
                src=p.src, edge_type=p.edge_type, tgt=p.tgt,
                weight=Lit(5000),
                provenance=p.provenance,
            ))
        else:
            new_prods.append(p)
    new_g = Grammar(new_prods)
    table = cg.material_table(new_g)
    assert table["WhiteQueen"] == 5000
    # Starting position: each side has its queen; eval = 5000 (white) - 900 (black) = 4100
    assert cg.evaluate(pc.Board(), table) == 4100
    # Position with only white queen vs lone black king:
    only_queen = pc.Board("4k3/8/8/8/8/8/8/4K2Q w - - 0 1")
    assert cg.evaluate(only_queen, table) == 5000


# --- engine vs random ---


def _play_game(white_strategy, black_strategy, max_plies: int = 200) -> pc.Board:
    board = pc.Board()
    for _ in range(max_plies):
        if board.is_game_over():
            break
        move = white_strategy(board) if board.turn == pc.WHITE else black_strategy(board)
        if move is None:
            break
        board.push(move)
    return board


def _engine_strategy(depth: int):
    table = cg.material_table(cg.material_grammar())
    def strat(board: pc.Board) -> pc.Move | None:
        move, _ = cg.choose_move(board, depth=depth, table=table)
        return move
    return strat


def _random_strategy(seed: int):
    rng = random.Random(seed)
    def strat(board: pc.Board) -> pc.Move | None:
        moves = list(board.legal_moves)
        return rng.choice(moves) if moves else None
    return strat


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_engine_beats_random(seed: int):
    """Depth-3 engine with material eval should beat random in every game."""
    final = _play_game(_engine_strategy(depth=3), _random_strategy(seed), max_plies=200)
    table = cg.material_table(cg.material_grammar())
    material = cg.evaluate(final, table)
    result = final.result()
    # Engine plays White. Acceptance: White wins, or game still ongoing with
    # White ahead by ≥ 300 centipawns (a rook+).
    ok = result == "1-0" or (result == "*" and material >= 300)
    assert ok, f"seed={seed} result={result} material={material} fen={final.fen()}"
