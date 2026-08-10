"""Phase 1b acceptance: GammaLearner converges to B3/S23 from observations alone."""
from __future__ import annotations

import random

import numpy as np
import pytest

from domains import conway
from substrate import GammaLearner, extract_observations
from tests.test_conway import life_like_step_oracle


def _board(rng: random.Random, density: float, size: int = 16) -> list[list[int]]:
    return [[1 if rng.random() < density else 0 for _ in range(size)] for _ in range(size)]


def _conway_transition(before: list[list[int]]) -> list[list[int]]:
    arr = np.array(before, dtype=bool)
    nxt = life_like_step_oracle(arr, birth={3}, survival={2, 3})
    return [[int(x) for x in row] for row in nxt]


def _mixed_corpus(rng: random.Random, n_boards: int = 24, size: int = 16
                  ) -> list[tuple[list[list[int]], list[list[int]]]]:
    """Boards across a range of densities so the learner sees all (src_type, n) cases."""
    densities = [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85]
    out = []
    for _ in range(n_boards):
        d = rng.choice(densities)
        before = _board(rng, d, size)
        after = _conway_transition(before)
        out.append((before, after))
    return out


def _held_out_observations(rng: random.Random, n_boards: int = 40, size: int = 16
                           ) -> list[tuple[str, int, str]]:
    obs: list[tuple[str, int, str]] = []
    for _ in range(n_boards):
        before = _board(rng, 0.35, size)
        after = _conway_transition(before)
        obs.extend(extract_observations(before, after))
    return obs


def test_learner_converges_within_budget():
    """Starting from empty Γ, accuracy on held-out reaches ≥99% within 5000 observations."""
    train_rng = random.Random(1234)
    test_rng = random.Random(5678)
    learner = GammaLearner()
    held_out = _held_out_observations(test_rng, n_boards=40)
    corpus = _mixed_corpus(train_rng, n_boards=24)

    flat: list[tuple[str, int, str]] = []
    for before, after in corpus:
        flat.extend(extract_observations(before, after))

    converged_at: int | None = None
    for i, (src_type, n, next_type) in enumerate(flat, start=1):
        learner.observe(src_type, n, next_type)
        if i % 64 == 0:
            acc = learner.accuracy(held_out)
            if acc >= 0.99 and converged_at is None:
                converged_at = i
                break

    assert converged_at is not None, (
        f"learner did not reach 99% accuracy within {len(flat)} observations; "
        f"current acc={learner.accuracy(held_out):.3f}"
    )
    assert converged_at <= 5000, f"converged at {converged_at} obs (budget 5000)"


def test_learned_grammar_matches_conway_table():
    """After enough observations, the learned (src_type, n) → next_type table equals Conway's."""
    rng = random.Random(99)
    learner = GammaLearner()
    corpus = _mixed_corpus(rng, n_boards=40)
    for before, after in corpus:
        learner.observe_transition(before, after)

    # Conway: B3/S23
    for src_type in ("AliveCell", "DeadCell"):
        for n in range(9):
            if src_type == "AliveCell":
                expected = "AliveCell" if n in {2, 3} else "DeadCell"
            else:
                expected = "AliveCell" if n == 3 else "DeadCell"
            if learner.predict(src_type, n) is None:
                continue  # not yet observed — allowed; test_converges_within_budget guards coverage
            assert learner.predict(src_type, n) == expected, \
                f"({src_type}, n={n}): predicted {learner.predict(src_type, n)}, expected {expected}"

    # Every (src_type, n) Conway uses should be covered by the corpus
    uncovered = [(s, n) for s in ("AliveCell", "DeadCell") for n in range(9)
                 if learner.predict(s, n) is None]
    assert uncovered == [], f"Conway table not fully covered: missing {uncovered}"


def test_learned_grammar_runs_in_substrate():
    """Plug the learned Γ into the substrate, run forward, compare to oracle."""
    rng = random.Random(42)
    learner = GammaLearner()
    for before, after in _mixed_corpus(rng, n_boards=40):
        learner.observe_transition(before, after)

    test_board = _board(random.Random(7), 0.35, size=16)
    s = conway.make_substrate(lambda: learner.grammar)
    conway.encode_board(s, test_board)
    sub_hist = [conway.decode_board(s, 16, 16)]
    for _ in range(20):
        conway.step(s)
        sub_hist.append(conway.decode_board(s, 16, 16))

    arr = np.array(test_board, dtype=bool)
    orc_hist = [arr.copy()]
    for _ in range(20):
        arr = life_like_step_oracle(arr, birth={3}, survival={2, 3})
        orc_hist.append(arr.copy())

    for gen, (sub, orc) in enumerate(zip(sub_hist, orc_hist)):
        sub_np = np.array(sub, dtype=bool)
        if not np.array_equal(sub_np, orc):
            diff = np.argwhere(sub_np != orc)
            pytest.fail(f"gen {gen}: learned-Γ substrate diverges from Conway oracle at {diff[0].tolist()}")


def test_edit_log_records_adds():
    """Each new (src_type, tgt_type) decision should produce an 'add' edit."""
    learner = GammaLearner()
    learner.observe("DeadCell", 3, "AliveCell")
    learner.observe("DeadCell", 3, "AliveCell")  # repeat — no edit
    learner.observe("AliveCell", 2, "AliveCell")  # different (src, tgt) — new add
    ops = [e.op for e in learner.edit_log]
    assert ops == ["add", "add"]
    src_tgt = [(e.src_type, e.tgt_type) for e in learner.edit_log]
    assert ("DeadCell", "AliveCell") in src_tgt
    assert ("AliveCell", "AliveCell") in src_tgt
