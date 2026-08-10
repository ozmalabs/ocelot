"""Strict parity: Python Conway and Rust Conway must produce
**bit-identical** boards step-for-step on the same starting state.

This is the strongest possible parity test for the engine — the
domain involves Filter / Neighbours / Count / TypeOf / Eq / In / Not /
SetT and many admissibility probes per step. If anything in the eval
path or in the admissibility checker drifts between backends, the
boards diverge within a few steps.
"""
from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def domains():
    """Late-bind both domains so the test is skipped cleanly when
    substrate_rs isn't installed."""
    pytest.importorskip("substrate_rs")
    from domains import conway as py_conway
    from domains_rs import conway as rs_conway
    return py_conway, rs_conway


@pytest.mark.parametrize("board_name,steps", [
    ("glider", 8),
    ("r_pentomino", 12),
])
def test_python_and_rust_conway_match_step_for_step(domains, board_name, steps):
    py_conway, rs_conway = domains
    # Same starting board on both engines.
    board_fn = getattr(rs_conway, f"{board_name}_board")
    starting = board_fn(20, 20)

    py_sub = py_conway.make_substrate()
    py_conway.encode_board(py_sub, [row[:] for row in starting])

    rs_sub = rs_conway.make_substrate()
    rs_conway.encode_board(rs_sub, [row[:] for row in starting])

    for i in range(steps):
        py_changed = py_conway.step(py_sub)
        rs_changed = rs_conway.step(rs_sub)
        assert py_changed == rs_changed, (
            f"step {i + 1}: change count diverged "
            f"(python={py_changed}, rust={rs_changed})"
        )
        py_board = py_conway.decode_board(py_sub, 20, 20)
        rs_board = rs_conway.decode_board(rs_sub, 20, 20)
        assert py_board == rs_board, (
            f"step {i + 1}: boards diverged on pattern '{board_name}'"
        )


def test_conway_grammar_size_matches(domains):
    """Both engines hold the same Γ — same number of productions,
    same provenance labels."""
    py_conway, rs_conway = domains
    py_sub = py_conway.make_substrate()
    rs_sub = rs_conway.make_substrate()
    rs_grammar = rs_sub.grammar_to_json()
    rs_provs = sorted(p["provenance"] for p in rs_grammar["productions"])
    py_provs = sorted(p.provenance for p in py_sub.checker.grammar.productions)
    # Rust adds the 4 structural adjacency productions; Python doesn't
    # (it bypasses Γ for adjacency). Filter those out for a fair
    # comparison of the *transition* grammar.
    rs_transition = [p for p in rs_provs if not p.startswith("Conway:adj_")]
    assert rs_transition == py_provs


def test_changed_count_matches_after_arbitrary_steps(domains):
    """Sanity check on a larger board run through more steps —
    accumulate total flip count and verify identical totals."""
    py_conway, rs_conway = domains
    board = py_conway_random_board(seed=42, rows=25, cols=25)
    py_sub = py_conway.make_substrate()
    py_conway.encode_board(py_sub, [row[:] for row in board])
    rs_sub = rs_conway.make_substrate()
    rs_conway.encode_board(rs_sub, [row[:] for row in board])
    py_total = sum(py_conway.step(py_sub) for _ in range(15))
    rs_total = sum(rs_conway.step(rs_sub) for _ in range(15))
    assert py_total == rs_total


def py_conway_random_board(seed: int, rows: int, cols: int) -> list[list[int]]:
    """Deterministic random board so both engines see the same input."""
    import random
    rng = random.Random(seed)
    return [[1 if rng.random() < 0.25 else 0 for _ in range(cols)] for _ in range(rows)]
