"""Phase 1a acceptance: Conway substrate matches a numpy oracle for N generations.

Multiple seed patterns exercise different parts of the Γ:
- blinker (period-2 oscillator)
- block (still life)
- glider (translation by (1,1) every 4 gens)
- random fill (exercises all four productions)
"""
from __future__ import annotations

import random

import numpy as np
import pytest

from domains import conway


def life_like_step_oracle(board: np.ndarray, birth: set[int], survival: set[int]) -> np.ndarray:
    """Numpy reference for any Bn/Sn Life-like CA. Dead boundary (zero-pad)."""
    h, w = board.shape
    padded = np.zeros((h + 2, w + 2), dtype=np.int8)
    padded[1:-1, 1:-1] = board.astype(np.int8)
    nbrs = np.zeros((h, w), dtype=np.int8)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nbrs += padded[1 + dr:1 + dr + h, 1 + dc:1 + dc + w]
    survive_mask = np.zeros_like(nbrs, dtype=bool)
    for n in survival:
        survive_mask |= (nbrs == n)
    birth_mask = np.zeros_like(nbrs, dtype=bool)
    for n in birth:
        birth_mask |= (nbrs == n)
    return (board & survive_mask) | (~board & birth_mask)


def conway_step_oracle(board: np.ndarray) -> np.ndarray:
    return life_like_step_oracle(board, birth={3}, survival={2, 3})


def _board_to_np(board: list[list[int]]) -> np.ndarray:
    return np.array(board, dtype=bool)


def _np_to_board(arr: np.ndarray) -> list[list[int]]:
    return [[int(x) for x in row] for row in arr]


def _run_substrate(initial: list[list[int]], generations: int) -> list[list[list[int]]]:
    s = conway.make_substrate()
    conway.encode_board(s, initial)
    history = [conway.decode_board(s, len(initial), len(initial[0]))]
    for _ in range(generations):
        conway.step(s)
        history.append(conway.decode_board(s, len(initial), len(initial[0])))
    return history


def _run_oracle(initial: list[list[int]], generations: int) -> list[np.ndarray]:
    board = _board_to_np(initial)
    history = [board.copy()]
    for _ in range(generations):
        board = conway_step_oracle(board)
        history.append(board.copy())
    return history


def _assert_matches(substrate_hist, oracle_hist):
    assert len(substrate_hist) == len(oracle_hist)
    for gen, (sub, orc) in enumerate(zip(substrate_hist, oracle_hist)):
        sub_np = np.array(sub, dtype=bool)
        if not np.array_equal(sub_np, orc):
            diff = np.argwhere(sub_np != orc)
            pytest.fail(f"Mismatch at generation {gen}; "
                        f"first divergence at {diff[0].tolist()} "
                        f"(substrate={int(sub_np[tuple(diff[0])])}, "
                        f"oracle={int(orc[tuple(diff[0])])})")


def test_blinker_period_2():
    # vertical blinker, oscillates to horizontal and back
    board = [[0] * 5 for _ in range(5)]
    board[1][2] = board[2][2] = board[3][2] = 1
    sub_hist = _run_substrate(board, generations=20)
    orc_hist = _run_oracle(board, generations=20)
    _assert_matches(sub_hist, orc_hist)


def test_block_still_life():
    board = [[0] * 5 for _ in range(5)]
    board[1][1] = board[1][2] = board[2][1] = board[2][2] = 1
    sub_hist = _run_substrate(board, generations=50)
    orc_hist = _run_oracle(board, generations=50)
    _assert_matches(sub_hist, orc_hist)
    # block is invariant
    for gen in sub_hist:
        assert sum(sum(row) for row in gen) == 4


def test_glider_translates():
    # Standard glider in the top-left of a 16x16 board
    board = [[0] * 16 for _ in range(16)]
    board[1][2] = 1
    board[2][3] = 1
    board[3][1] = board[3][2] = board[3][3] = 1
    sub_hist = _run_substrate(board, generations=40)
    orc_hist = _run_oracle(board, generations=40)
    _assert_matches(sub_hist, orc_hist)


def test_random_fill_1000_generations():
    """Phase 1a acceptance: 1000 generations on random 16x16 must match oracle every step."""
    rng = random.Random(1337)
    board = [[rng.randint(0, 1) for _ in range(16)] for _ in range(16)]
    sub_hist = _run_substrate(board, generations=1000)
    orc_hist = _run_oracle(board, generations=1000)
    _assert_matches(sub_hist, orc_hist)


def test_state_density_falls_to_steady():
    """Sanity: a random 16x16 typically decays to a near-stable density in <1000 gens."""
    rng = random.Random(99)
    board = [[rng.randint(0, 1) for _ in range(16)] for _ in range(16)]
    sub_hist = _run_substrate(board, generations=1000)
    final_density = sum(sum(row) for row in sub_hist[-1]) / (16 * 16)
    # Conway-on-finite-grid typically lands on still lifes / oscillators; density should be modest
    assert final_density < 0.5


def _run_substrate_with_grammar(initial, generations, grammar_fn):
    s = conway.make_substrate(grammar_fn)
    conway.encode_board(s, initial)
    history = [conway.decode_board(s, len(initial), len(initial[0]))]
    for _ in range(generations):
        conway.step(s)
        history.append(conway.decode_board(s, len(initial), len(initial[0])))
    return history


def test_highlife_matches_oracle():
    """B36/S23 — same substrate, different Γ. Proves rule-change is Γ-only."""
    rng = random.Random(2024)
    board = [[rng.randint(0, 1) for _ in range(16)] for _ in range(16)]
    sub_hist = _run_substrate_with_grammar(board, 200, conway.highlife_grammar)
    np_board = _board_to_np(board)
    orc_hist = [np_board.copy()]
    for _ in range(200):
        np_board = life_like_step_oracle(np_board, birth={3, 6}, survival={2, 3})
        orc_hist.append(np_board.copy())
    _assert_matches(sub_hist, orc_hist)


def test_seeds_matches_oracle():
    """B2/S — every alive cell dies; explosive growth."""
    rng = random.Random(11)
    board = [[0] * 16 for _ in range(16)]
    for _ in range(8):
        board[rng.randrange(16)][rng.randrange(16)] = 1
    sub_hist = _run_substrate_with_grammar(board, 50, conway.seeds_grammar)
    np_board = _board_to_np(board)
    orc_hist = [np_board.copy()]
    for _ in range(50):
        np_board = life_like_step_oracle(np_board, birth={2}, survival=set())
        orc_hist.append(np_board.copy())
    _assert_matches(sub_hist, orc_hist)


def test_live_grammar_swap_mid_run():
    """Headline claim: swap Γ on a running substrate; same board continues under new rule."""
    rng = random.Random(7)
    board = [[rng.randint(0, 1) for _ in range(12)] for _ in range(12)]
    s = conway.make_substrate(conway.conway_grammar)
    conway.encode_board(s, board)
    # 20 gens under Conway
    for _ in range(20):
        conway.step(s)
    state_after_conway = conway.decode_board(s, 12, 12)
    # SWAP Γ — substrate state untouched
    conway.swap_grammar(s, conway.highlife_grammar())
    # 20 more gens under HighLife
    for _ in range(20):
        conway.step(s)
    state_after_swap = conway.decode_board(s, 12, 12)
    # Independent oracle path: run the same prefix under Conway, then suffix under HighLife
    np_board = _board_to_np(board)
    for _ in range(20):
        np_board = life_like_step_oracle(np_board, birth={3}, survival={2, 3})
    assert _np_to_board(np_board) == state_after_conway
    for _ in range(20):
        np_board = life_like_step_oracle(np_board, birth={3, 6}, survival={2, 3})
    assert _np_to_board(np_board) == state_after_swap
