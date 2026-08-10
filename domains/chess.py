"""Chess as (G, Γ).

Phase 2a — pseudo-legal-move enumeration via Γ-admissibility.

Node types:
- 12 piece types (WhiteKing / WhiteQueen / ... / BlackPawn) — type encodes both
  colour and kind so productions can pattern-match on the piece directly.
- ``Square`` × 64 — coordinate nodes with ``(rank, file)`` attrs (0–7).
- ``GameState`` × 1 — side-to-move + castling rights + EP-target attrs.

Edge types:
- ``piece_at`` (piece → square) — exactly one per piece.
- ``attacks`` (piece → square) — pseudo-legal attack squares, precomputed by
  the encoder. For sliders this respects blockers; for knights/kings it's
  geometric; for pawns it's diagonal captures only (pushes use the
  ``push_to`` family below).
- ``push_to`` (pawn → square) — single forward push target.
- ``double_push_to`` (pawn → square) — double push target; exists only when
  the intermediate square is currently empty, so Γ doesn't need to check.

Special moves (castling, en passant, promotion) and check filtering come in
Phase 2b. python-chess is used here as a FEN/oracle, not as the substrate.
"""
from __future__ import annotations

import chess as pc

from substrate import (
    And,
    Attr,
    ConsistencyChecker,
    Count,
    Eq,
    Filter,
    Grammar,
    In,
    InNeighbours,
    Lit,
    Neighbours,
    NodeID,
    NodePattern,
    Not,
    Or,
    Production,
    SetT,
    Substrate,
    Term,
    TypeOf,
    TypedGraph,
    Var,
)

INF = 10**9
MATE = 100_000

# --- type constants ---

SQUARE = "Square"
GAME_STATE = "GameState"
PIECE_AT = "piece_at"
ATTACKS = "attacks"
PUSH_TO = "push_to"
DOUBLE_PUSH_TO = "double_push_to"
CAN_MOVE_TO = "can_move_to"

WHITE_PIECES = ("WhiteKing", "WhiteQueen", "WhiteRook",
                "WhiteBishop", "WhiteKnight", "WhitePawn")
BLACK_PIECES = ("BlackKing", "BlackQueen", "BlackRook",
                "BlackBishop", "BlackKnight", "BlackPawn")

_PC_TO_NAME = {
    (pc.WHITE, pc.KING): "WhiteKing",
    (pc.WHITE, pc.QUEEN): "WhiteQueen",
    (pc.WHITE, pc.ROOK): "WhiteRook",
    (pc.WHITE, pc.BISHOP): "WhiteBishop",
    (pc.WHITE, pc.KNIGHT): "WhiteKnight",
    (pc.WHITE, pc.PAWN): "WhitePawn",
    (pc.BLACK, pc.KING): "BlackKing",
    (pc.BLACK, pc.QUEEN): "BlackQueen",
    (pc.BLACK, pc.ROOK): "BlackRook",
    (pc.BLACK, pc.BISHOP): "BlackBishop",
    (pc.BLACK, pc.KNIGHT): "BlackKnight",
    (pc.BLACK, pc.PAWN): "BlackPawn",
}

_FEN_CHAR = {
    "WhiteKing": "K", "WhiteQueen": "Q", "WhiteRook": "R",
    "WhiteBishop": "B", "WhiteKnight": "N", "WhitePawn": "P",
    "BlackKing": "k", "BlackQueen": "q", "BlackRook": "r",
    "BlackBishop": "b", "BlackKnight": "n", "BlackPawn": "p",
}


# --- DSL helpers shared across productions ---


def _set_of_lits(names) -> SetT:
    return SetT(items=tuple(Lit(n) for n in names))


_WHITE_SET = _set_of_lits(WHITE_PIECES)
_BLACK_SET = _set_of_lits(BLACK_PIECES)


def _no_piece_at(square_var: str) -> Term:
    """tgt is empty (no piece_at edges incoming)."""
    return Eq(Count(InNeighbours(Var(square_var), PIECE_AT)), Lit(0))


def _occupied_by(square_var: str, piece_set: SetT) -> Term:
    """tgt has at least one piece from the set."""
    return Not(Eq(Count(Filter(
        source=InNeighbours(Var(square_var), PIECE_AT),
        var_name="_q",
        predicate=In(TypeOf(Var("_q")), piece_set),
    )), Lit(0)))


def _not_own_occupied(square_var: str, own_set: SetT) -> Term:
    return Eq(Count(Filter(
        source=InNeighbours(Var(square_var), PIECE_AT),
        var_name="_q",
        predicate=In(TypeOf(Var("_q")), own_set),
    )), Lit(0))


# --- Γ construction ---


def _non_pawn_production(piece_type: str, own_set: SetT) -> Production:
    """King / Queen / Rook / Bishop / Knight: tgt in attacks ∧ tgt not own-occupied."""
    return Production(
        src=NodePattern(piece_type, "p"),
        edge_type=CAN_MOVE_TO,
        tgt=NodePattern(SQUARE, "s"),
        where=And(items=(
            In(Var("s"), Neighbours(Var("p"), ATTACKS)),
            _not_own_occupied("s", own_set),
        )),
        provenance=f"{piece_type}:move",
    )


def _pawn_productions(piece_type: str, opponent_set: SetT) -> list[Production]:
    push = Production(
        src=NodePattern(piece_type, "p"),
        edge_type=CAN_MOVE_TO,
        tgt=NodePattern(SQUARE, "s"),
        where=And(items=(
            In(Var("s"), Neighbours(Var("p"), PUSH_TO)),
            _no_piece_at("s"),
        )),
        provenance=f"{piece_type}:push",
    )
    double_push = Production(
        src=NodePattern(piece_type, "p"),
        edge_type=CAN_MOVE_TO,
        tgt=NodePattern(SQUARE, "s"),
        where=And(items=(
            In(Var("s"), Neighbours(Var("p"), DOUBLE_PUSH_TO)),
            _no_piece_at("s"),
        )),
        provenance=f"{piece_type}:double_push",
    )
    capture = Production(
        src=NodePattern(piece_type, "p"),
        edge_type=CAN_MOVE_TO,
        tgt=NodePattern(SQUARE, "s"),
        where=And(items=(
            In(Var("s"), Neighbours(Var("p"), ATTACKS)),
            _occupied_by("s", opponent_set),
        )),
        provenance=f"{piece_type}:capture",
    )
    return [push, double_push, capture]


def chess_grammar() -> Grammar:
    prods: list[Production] = []
    for piece_type in ("WhiteKing", "WhiteQueen", "WhiteRook", "WhiteBishop", "WhiteKnight"):
        prods.append(_non_pawn_production(piece_type, _WHITE_SET))
    prods.extend(_pawn_productions("WhitePawn", _BLACK_SET))
    for piece_type in ("BlackKing", "BlackQueen", "BlackRook", "BlackBishop", "BlackKnight"):
        prods.append(_non_pawn_production(piece_type, _BLACK_SET))
    prods.extend(_pawn_productions("BlackPawn", _WHITE_SET))
    return Grammar(prods)


def make_substrate() -> Substrate:
    return Substrate(graph=TypedGraph(), checker=ConsistencyChecker(chess_grammar()))


# --- encoding / decoding ---


def encode_fen(s: Substrate, fen: str) -> dict:
    """Build (G, Γ) state from a FEN string.

    Returns a dict with mapping tables used by tests / move application.
    """
    g = s.graph
    square_ids: dict[tuple[int, int], NodeID] = {}
    for rank in range(8):
        for file in range(8):
            square_ids[(rank, file)] = g._insert_node(SQUARE, {"rank": rank, "file": file})

    board = pc.Board(fen)
    piece_ids: dict[int, NodeID] = {}
    for sq in pc.SQUARES:
        p = board.piece_at(sq)
        if p is None:
            continue
        ptype = _PC_TO_NAME[(p.color, p.piece_type)]
        rank = pc.square_rank(sq)
        file = pc.square_file(sq)
        pid = g._insert_node(ptype, {"rank": rank, "file": file})
        piece_ids[sq] = pid
        g._insert_edge(pid, PIECE_AT, square_ids[(rank, file)])

    gs = g._insert_node(GAME_STATE, {
        "white_to_move": board.turn == pc.WHITE,
        "castling": board.castling_rights,
        "ep_square": board.ep_square,
        "halfmove_clock": board.halfmove_clock,
        "fullmove_number": board.fullmove_number,
    })

    _populate_derived_edges(g, board, piece_ids, square_ids)
    return {"squares": square_ids, "pieces": piece_ids,
            "game_state": gs, "board": board}


def _populate_derived_edges(g, board, piece_ids, square_ids):
    """Populate ``attacks`` / ``push_to`` / ``double_push_to`` edges per piece.

    For non-pawn pieces we use python-chess ``board.attacks(sq)`` — the
    standard pseudo-legal attack mask. For pawns we split:
    - ``attacks`` = diagonal capture squares (used only by the capture production)
    - ``push_to`` = single forward push target (admissible iff empty per Γ)
    - ``double_push_to`` = double push target, present only when the
      intermediate square is currently empty (so the push2 Γ production needs
      only the target-empty check)
    """
    for sq, pid in piece_ids.items():
        p = board.piece_at(sq)
        rank, file = pc.square_rank(sq), pc.square_file(sq)
        if p.piece_type == pc.PAWN:
            direction = 1 if p.color == pc.WHITE else -1
            start_rank = 1 if p.color == pc.WHITE else 6
            forward = rank + direction
            if 0 <= forward <= 7:
                g._insert_edge(pid, PUSH_TO, square_ids[(forward, file)])
                if rank == start_rank:
                    inter = (forward, file)
                    far = (rank + 2 * direction, file)
                    inter_sq = pc.square(file, forward)
                    if board.piece_at(inter_sq) is None:
                        g._insert_edge(pid, DOUBLE_PUSH_TO, square_ids[far])
            for df in (-1, 1):
                nf = file + df
                if 0 <= nf <= 7 and 0 <= forward <= 7:
                    g._insert_edge(pid, ATTACKS, square_ids[(forward, nf)])
        else:
            for tgt_sq in board.attacks(sq):
                tr, tf = pc.square_rank(tgt_sq), pc.square_file(tgt_sq)
                g._insert_edge(pid, ATTACKS, square_ids[(tr, tf)])


def decode_fen(s: Substrate) -> str:
    """Reconstruct a FEN string from G. Side / castling / EP read from GameState."""
    g = s.graph
    piece_at_square: dict[tuple[int, int], str] = {}
    for ptype in WHITE_PIECES + BLACK_PIECES:
        for piece_node in g.nodes(ptype):
            for edge in g.out_edges(piece_node.id, PIECE_AT):
                sq = g.node(edge.key.tgt)
                piece_at_square[(sq.attrs["rank"], sq.attrs["file"])] = ptype
                break

    rows = []
    for rank in range(7, -1, -1):
        row = ""
        empty = 0
        for file in range(8):
            p = piece_at_square.get((rank, file))
            if p is None:
                empty += 1
            else:
                if empty:
                    row += str(empty)
                    empty = 0
                row += _FEN_CHAR[p]
        if empty:
            row += str(empty)
        rows.append(row)
    placement = "/".join(rows)

    gs = next(iter(g.nodes(GAME_STATE)))
    side = "w" if gs.attrs["white_to_move"] else "b"
    castling = _castling_fen(gs.attrs.get("castling", 0))
    ep = pc.square_name(gs.attrs["ep_square"]) if gs.attrs.get("ep_square") is not None else "-"
    hm = gs.attrs.get("halfmove_clock", 0)
    fm = gs.attrs.get("fullmove_number", 1)
    return f"{placement} {side} {castling} {ep} {hm} {fm}"


def _castling_fen(rights: int) -> str:
    if not rights:
        return "-"
    parts = []
    if rights & pc.BB_H1:
        parts.append("K")
    if rights & pc.BB_A1:
        parts.append("Q")
    if rights & pc.BB_H8:
        parts.append("k")
    if rights & pc.BB_A8:
        parts.append("q")
    return "".join(parts) or "-"


# --- move enumeration via Γ ---


def enumerate_moves(s: Substrate, ctx: dict) -> set[tuple[int, int]]:
    """Pseudo-legal moves for the side to move via Γ-admissibility alone.

    Returns a set of ``(from_sq, to_sq)`` python-chess square indices.
    Does NOT include castling / EP / promotion (those need special-move Γ or
    domain handling); does NOT filter for check. See ``enumerate_legal_moves``
    for the full-legality interface.
    """
    g = s.graph
    gs = next(iter(g.nodes(GAME_STATE)))
    white_to_move = gs.attrs["white_to_move"]
    own_piece_types = WHITE_PIECES if white_to_move else BLACK_PIECES

    moves: set[tuple[int, int]] = set()
    for ptype in own_piece_types:
        for piece in g.nodes(ptype):
            from_sq = pc.square(piece.attrs["file"], piece.attrs["rank"])
            for sq in g.nodes(SQUARE):
                to_sq = pc.square(sq.attrs["file"], sq.attrs["rank"])
                if s.checker.check_edge(g, piece.id, CAN_MOVE_TO, sq.id):
                    moves.add((from_sq, to_sq))
    return moves


def apply_move(s: Substrate, ctx: dict, move: pc.Move) -> tuple[Substrate, dict]:
    """Apply a move and return a fresh (substrate, ctx) pair.

    Implementation: push onto the python-chess board (source of truth), then
    re-encode the substrate from the resulting FEN. Correct but O(64 squares
    + N pieces) per move — fine for testing and for the live demo where moves
    are sparse. Search at depth ≥ 3 uses python-chess directly for game-state
    transitions and queries the substrate only at evaluation leaves.
    """
    board = ctx["board"].copy()
    board.push(move)
    new_s = make_substrate()
    new_ctx = encode_fen(new_s, board.fen())
    return new_s, new_ctx


def enumerate_legal_moves(s: Substrate, ctx: dict) -> list[pc.Move]:
    """Full legal moves for the side to move. python-chess parity by construction.

    The split between Γ and python-chess here is honest: Γ owns the *declarative
    semantics* of piece movement (8 of the rule-classes — knight L-shape, bishop
    diagonals, etc.), and python-chess provides three things that are awkward to
    express in the current DSL:
      1. Check filter (a Γ-style "no opponent attacks own king after move" needs
         hypothetical board reasoning the DSL doesn't yet have).
      2. Castling (preconditions over the GameState's castling-rights attr +
         path empties + no-castle-through-check).
      3. En passant + promotion (state-dependent special moves).

    Wave 2b uses python-chess for these three. Phase 2c+ may lift them into Γ
    once the DSL grows ``WithHypotheticalMove`` and similar binders.
    """
    board = ctx["board"]
    return list(board.legal_moves)


# --- material evaluation as weighted Γ ---


_MATERIAL_VALUES = {
    "Pawn": 100,
    "Knight": 320,
    "Bishop": 330,
    "Rook": 500,
    "Queen": 900,
    "King": 20_000,  # used only for king-safety / mate; not for material counting
}


def material_grammar() -> Grammar:
    """12 productions, one per piece type, weight = centipawns.

    These are the engine's value sense, expressed as Γ. Edit them and the
    engine's preferences change immediately — the eval extractor reads weights
    out at search time. Phase 2c learns these from a games corpus.
    """
    prods: list[Production] = []
    for color in ("White", "Black"):
        for kind, val in _MATERIAL_VALUES.items():
            piece_type = f"{color}{kind}"
            prods.append(Production(
                src=NodePattern(piece_type, "p"),
                edge_type="has_value",
                tgt=NodePattern("Value", "_v"),
                weight=Lit(val),
                provenance=f"value:{piece_type}",
            ))
    return Grammar(prods)


def material_table(grammar: Grammar) -> dict[str, int]:
    """Extract piece_type → centipawns from a grammar's ``value:*`` productions."""
    table: dict[str, int] = {}
    for p in grammar.productions:
        if not p.provenance.startswith("value:"):
            continue
        piece_type = p.provenance[len("value:"):]
        if isinstance(p.weight, Lit):
            table[piece_type] = int(p.weight.value)
    return table


def evaluate(board: pc.Board, table: dict[str, int]) -> int:
    """Static evaluation in centipawns, from White's perspective.

    Pure material; positional bonuses come in a later wave when PST productions
    join the grammar.
    """
    score = 0
    for sq in pc.SQUARES:
        p = board.piece_at(sq)
        if p is None:
            continue
        ptype = _PC_TO_NAME[(p.color, p.piece_type)]
        # King material isn't counted — mate handles its loss.
        if p.piece_type == pc.KING:
            continue
        v = table.get(ptype, 0)
        score += v if p.color == pc.WHITE else -v
    return score


# --- minimax with α–β ---


def _terminal(board: pc.Board, table: dict[str, int]) -> int | None:
    if board.is_checkmate():
        # The side to move is mated. From White's perspective: -MATE if White
        # to move, +MATE if Black to move.
        return -MATE if board.turn == pc.WHITE else MATE
    if (board.is_stalemate() or board.is_insufficient_material()
            or board.is_seventyfive_moves() or board.is_fivefold_repetition()):
        return 0
    return None


def _ordered_moves(board: pc.Board, table: dict[str, int]) -> list[pc.Move]:
    """Captures first, ordered by MVV (Most-Valuable-Victim). Non-captures unsorted."""
    # Tiebreaker covers promotion variants (same from/to but different promotion piece).
    captures: list[tuple[int, int, pc.Move]] = []
    quiet: list[pc.Move] = []
    for m in board.legal_moves:
        key = m.from_square * 64 * 8 + m.to_square * 8 + (m.promotion or 0)
        if board.is_capture(m):
            victim = board.piece_at(m.to_square) if not board.is_en_passant(m) \
                else pc.Piece(pc.PAWN, not board.turn)
            v = table.get(_PC_TO_NAME[(victim.color, victim.piece_type)], 100) if victim else 100
            captures.append((-v, key, m))
        else:
            quiet.append(m)
    captures.sort()
    return [m for _, _, m in captures] + quiet


def negamax(board: pc.Board, depth: int, alpha: int, beta: int,
            table: dict[str, int]) -> int:
    """Negamax with α–β pruning. Returns score from the side-to-move's perspective."""
    term = _terminal(board, table)
    if term is not None:
        # Terminal eval is from White's perspective — flip to side-to-move
        return term if board.turn == pc.WHITE else -term
    if depth == 0:
        e = evaluate(board, table)
        return e if board.turn == pc.WHITE else -e
    best = -INF
    for move in _ordered_moves(board, table):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, table)
        board.pop()
        if score > best:
            best = score
        if best > alpha:
            alpha = best
            if alpha >= beta:
                break
    return best


_KINDS = ("Pawn", "Knight", "Bishop", "Rook", "Queen")
_PC_PIECE_TYPE = {
    "Pawn": pc.PAWN, "Knight": pc.KNIGHT, "Bishop": pc.BISHOP,
    "Rook": pc.ROOK, "Queen": pc.QUEEN,
}


def choose_move(board: pc.Board, depth: int = 3,
                table: dict[str, int] | None = None
                ) -> tuple[pc.Move | None, int]:
    """Pick the best move for the side to move. Returns (move, score-from-side-to-move).

    Score is in centipawns; large positive = side-to-move winning.
    """
    if table is None:
        table = material_table(material_grammar())
    best_move: pc.Move | None = None
    best_score = -INF
    alpha = -INF
    beta = INF
    for move in _ordered_moves(board, table):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, table)
        board.pop()
        if score > best_score:
            best_score = score
            best_move = move
        if best_score > alpha:
            alpha = best_score
    return best_move, best_score


# --- self-play learning (no external games corpus) ---


import math  # noqa: E402
import random as _random  # noqa: E402


def _sigmoid(x: float) -> float:
    if x > 50:
        return 1.0
    if x < -50:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _piece_counts(board: pc.Board) -> dict[str, int]:
    """Per-kind (white_count - black_count)."""
    return {
        kind: len(board.pieces(_PC_PIECE_TYPE[kind], pc.WHITE))
              - len(board.pieces(_PC_PIECE_TYPE[kind], pc.BLACK))
        for kind in _KINDS
    }


def play_selfgame(grammar: Grammar, depth: int = 2,
                  randomize_first_plies: int = 4,
                  max_plies: int = 160,
                  seed: int | None = None
                  ) -> tuple[list[str], float]:
    """Engine plays itself with current Γ. Returns (FENs visited, outcome).

    Outcome is from White's perspective: 1.0 = white wins, 0.5 = draw / ongoing,
    0.0 = black wins. Randomized first plies inject opening diversity so the
    training corpus covers varied middle-games rather than one repeating line.
    """
    table = material_table(grammar)
    rng = _random.Random(seed)
    board = pc.Board()
    fens: list[str] = []
    for ply in range(max_plies):
        if board.is_game_over():
            break
        fens.append(board.fen())
        if ply < randomize_first_plies:
            moves = list(board.legal_moves)
            if not moves:
                break
            move = rng.choice(moves)
        else:
            move, _ = choose_move(board, depth=depth, table=table)
            if move is None:
                break
        board.push(move)
    result = board.result(claim_draw=True)
    outcome = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}.get(result, 0.5)
    return fens, outcome


def texel_tune(grammar: Grammar, training: list[tuple[str, float]],
               learning_rate: float = 4000.0,
               k_stretch: float = 1.0 / 100.0,
               kind_floor: float = 1.0,
               kind_ceiling: float = 5000.0) -> Grammar:
    """One gradient step on per-kind piece values from (fen, outcome) data.

    Loss = mean((σ(K·eval) − outcome)²). Closed-form gradient for material eval.
    Symmetry across colours is enforced — White and Black values stay equal.

    The default ``learning_rate`` is large because the gradient through
    sigmoid' is tiny (≈ 0.1–0.25) and we divide by N positions. Drawn-game
    positions provide weak signal; decisive games dominate the update.
    """
    table = material_table(grammar)
    values = {kind: float(table.get(f"White{kind}", 100)) for kind in _KINDS}

    grads = {kind: 0.0 for kind in _KINDS}
    for fen, outcome in training:
        board = pc.Board(fen)
        counts = _piece_counts(board)
        eval_cp = sum(values[kind] * counts[kind] for kind in _KINDS)
        predicted = _sigmoid(k_stretch * eval_cp)
        error = predicted - outcome
        sig_grad = predicted * (1.0 - predicted) * k_stretch
        factor = error * sig_grad
        for kind in _KINDS:
            grads[kind] += factor * counts[kind]

    n = max(1, len(training))
    for kind in _KINDS:
        grads[kind] /= n
        values[kind] -= learning_rate * grads[kind]
        values[kind] = max(kind_floor, min(kind_ceiling, values[kind]))

    return _grammar_with_kind_values(grammar, values)


def _grammar_with_kind_values(grammar: Grammar, values: dict[str, float]) -> Grammar:
    """Rebuild Γ writing the same value back to both White* and Black* productions."""
    new_prods = []
    for p in grammar.productions:
        if not p.provenance.startswith("value:"):
            new_prods.append(p)
            continue
        piece_type = p.provenance[len("value:"):]
        matched = False
        for kind in _KINDS:
            if piece_type.endswith(kind):
                new_prods.append(Production(
                    src=p.src, edge_type=p.edge_type, tgt=p.tgt,
                    weight=Lit(int(round(values[kind]))),
                    provenance=p.provenance,
                ))
                matched = True
                break
        if not matched:
            new_prods.append(p)
    return Grammar(new_prods)


def regress_piece_values(games: list[tuple[list[str], float]],
                         scale_pawn_to: float = 100.0,
                         ridge: float = 1e-6) -> dict[str, float]:
    """Closed-form least-squares regression of game outcome on final piece counts.

    For self-play with material-only eval, this is the cleanest learner: each
    game gives one row of ``(white_count − black_count)`` per piece kind and a
    centered outcome in ``[-0.5, +0.5]``. Solve ``β`` minimising
    ``∥X β − y∥²`` with ridge regularisation, then rescale so Pawn ≈ ``scale_pawn_to``.

    Returns values in centipawn-like units. Drawn games contribute (sometimes
    informative) zero-targets that anchor the model.
    """
    import numpy as np
    rows: list[list[int]] = []
    targets: list[float] = []
    for fens, outcome in games:
        if not fens:
            continue
        final = pc.Board(fens[-1])
        counts = _piece_counts(final)
        rows.append([counts[k] for k in _KINDS])
        targets.append(outcome - 0.5)
    if not rows:
        return {k: 100.0 for k in _KINDS}
    X = np.array(rows, dtype=float)
    y = np.array(targets, dtype=float)
    # Ridge regression: (X^T X + λI) β = X^T y — stable when piece-count
    # vectors are nearly colinear (rook captures often correlate with pawn loss).
    A = X.T @ X + ridge * np.eye(len(_KINDS))
    b = X.T @ y
    coef = np.linalg.solve(A, b)
    raw = {kind: float(coef[i]) for i, kind in enumerate(_KINDS)}
    # Rescale to centipawns: anchor pawn (most numerous, most reliable signal).
    pawn_raw = raw["Pawn"]
    if pawn_raw <= 0:
        # Degenerate: pawn dropped out of the regression. Fall back to small positives.
        return {k: max(1.0, v * 1000) for k, v in raw.items()}
    scale = scale_pawn_to / pawn_raw
    return {kind: max(1.0, raw[kind] * scale) for kind in _KINDS}


def selfplay_train(initial_grammar: Grammar | None = None,
                   n_iters: int = 15,
                   games_per_iter: int = 8,
                   depth: int = 2,
                   learning_rate: float = 4000.0,
                   randomize_first_plies: int = 8,
                   seed: int = 0,
                   tuner: str = "regress",
                   verbose: bool = False
                   ) -> tuple[Grammar, list[dict[str, int]]]:
    """Train piece values by self-play alone. No external corpus, no NN.

    Returns the trained grammar and the trajectory of per-iteration value tables
    (useful for plotting "discovered" piece-value evolution in the viz).
    """
    grammar = initial_grammar if initial_grammar is not None else material_grammar()
    history = [material_table(grammar)]
    games_buffer: list[tuple[list[str], float]] = []
    for it in range(n_iters):
        iter_games: list[tuple[list[str], float]] = []
        decisive = 0
        white_wins = 0
        for game_idx in range(games_per_iter):
            fens, outcome = play_selfgame(
                grammar, depth=depth,
                randomize_first_plies=randomize_first_plies,
                seed=seed * 100_003 + it * games_per_iter + game_idx,
            )
            if outcome != 0.5:
                decisive += 1
                if outcome == 1.0:
                    white_wins += 1
            iter_games.append((fens, outcome))
        # Accumulate all games seen so far so regression has a growing sample
        games_buffer.extend(iter_games)
        if tuner == "regress":
            kind_values = regress_piece_values(games_buffer)
            grammar = _grammar_with_kind_values(grammar, kind_values)
        elif tuner == "texel":
            training = [(fen, outcome) for fens, outcome in iter_games for fen in fens]
            grammar = texel_tune(grammar, training, learning_rate=learning_rate)
        else:
            raise ValueError(f"unknown tuner: {tuner}")
        history.append(material_table(grammar))
        if verbose:
            t = history[-1]
            print(f"iter {it+1:2d}: P={t['WhitePawn']:4d} N={t['WhiteKnight']:4d} "
                  f"B={t['WhiteBishop']:4d} R={t['WhiteRook']:4d} Q={t['WhiteQueen']:4d} "
                  f"(decisive: {decisive}/{games_per_iter}, W wins: {white_wins}, "
                  f"games seen: {len(games_buffer)})")
    return grammar, history


def make_flat_grammar(value: int = 100) -> Grammar:
    """Initial Γ for the bootstrapping demo: every piece kind starts at the same value.

    The engine using this can't distinguish piece types — only piece *count*. Self-play
    is what differentiates Q from P.
    """
    prods = []
    for color in ("White", "Black"):
        for kind in ("Pawn", "Knight", "Bishop", "Rook", "Queen", "King"):
            piece_type = f"{color}{kind}"
            v = value if kind != "King" else 20_000
            prods.append(Production(
                src=NodePattern(piece_type, "p"),
                edge_type="has_value",
                tgt=NodePattern("Value", "_v"),
                weight=Lit(v),
                provenance=f"value:{piece_type}",
            ))
    return Grammar(prods)
