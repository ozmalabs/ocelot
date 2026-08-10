"""RUN 39 GATE 0 -- unit sanity for the motor-plan feature extraction
(`scripts/jabberwock_omniglot_run39_motorplan.py`): pure numpy + the Rust `PointSetDist` Term,
no graph, no agent decisions (CLAUDE.md's world-adapter/feature-extraction allowance, same class
as `domains/ink_dynamics.py`). Synthetic two-stroke drawings only -- no real Omniglot files
needed, deterministic.

Covers: order agreement/disagreement under a swapped draw order; direction-polarity flip on a
reversed stroke; the falsy-zero fix on `_pointset_cost` (an identical-stroke match must cost
EXACTLY 0.0, not silently become NaN via a stray `or`); determinism of the whole pipeline.
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

from scripts import jabberwock_omniglot_run39_motorplan as m


@pytest.fixture(scope="module")
def native():
    return srs.Substrate()._inner


# Two simple, well-separated strokes: A = a horizontal segment, B = a vertical segment, both
# starting at the origin -- so the greedy matcher has an unambiguous cheapest assignment.
STROKE_A = np.array([[0.0, 0.0], [0.5, 0.0], [1.0, 0.0]])
STROKE_B = np.array([[0.0, 0.0], [0.0, 0.5], [0.0, 1.0]])
STROKE_A_REVERSED = STROKE_A[::-1].copy()


def test_pointset_cost_identical_is_exact_zero_not_nan(native):
    """THE FALSY-ZERO BUG (run 36's `float(native.evaluate(term, {}) or float('nan'))`):
    an exact-zero distance must stay 0.0, not get silently replaced by NaN via `or`."""
    c = m._pointset_cost(native, STROKE_A, STROKE_A.copy())
    assert c == 0.0
    assert c == c   # not NaN.


def test_greedy_match_full_bijection_two_strokes(native):
    ref = [STROKE_A, STROKE_B]
    other_same_order = [STROKE_A.copy(), STROKE_B.copy()]
    mapping = m.greedy_match(native, ref, other_same_order)
    assert mapping == {0: 0, 1: 1}


def test_greedy_match_swapped_order_still_finds_correct_correspondence(native):
    """The OTHER drawer draws B then A (swapped draw order) -- the greedy matcher must still
    identify draw-position 0 (B-shaped) as canonical id 1, and draw-position 1 (A-shaped) as
    canonical id 0, by SHAPE, not by position."""
    ref = [STROKE_A, STROKE_B]
    other_swapped = [STROKE_B.copy(), STROKE_A.copy()]
    mapping = m.greedy_match(native, ref, other_swapped)
    assert mapping == {0: 1, 1: 0}


def test_order_agreement_same_vs_swapped():
    """Two drawers with the SAME draw order agree exactly; a drawer with a SWAPPED draw order
    disagrees -- the core order-disagreement-detection sanity the launch brief asks for."""
    order_same = (0, 1)
    order_swapped = (1, 0)
    assert m._EQ_SCORE(order_same, order_same) == 1.0
    assert m._EQ_SCORE(order_same, order_swapped) == 0.0
    # relaxed (Kendall) metric: a full 2-element reversal is maximally discordant (tau=1).
    assert m.kendall_tau_normalized(order_same, order_swapped) == 1.0
    assert m.kendall_tau_normalized(order_same, order_same) == 0.0


def test_polarity_flip_on_reversed_stroke():
    """A stroke drawn in REVERSE (same shape, opposite start/end) must flip the polarity bit
    relative to the reference."""
    same_polarity = m.polarity(STROKE_A, STROKE_A.copy())
    reversed_polarity = m.polarity(STROKE_A, STROKE_A_REVERSED)
    assert same_polarity == 1
    assert reversed_polarity == 0
    assert same_polarity != reversed_polarity


def test_sector8_cardinal_directions():
    assert m.sector8(np.array([1.0, 0.0])) == 0     # +x, sector 0 centred on 0 degrees.
    assert m.sector8(np.array([0.0, 1.0])) == 2      # +y, 90 degrees -> sector 2.
    assert m.sector8(np.array([-1.0, 0.0])) == 4     # -x, 180 degrees -> sector 4.
    assert m.sector8(np.array([0.0, -1.0])) == 6     # -y, 270 degrees -> sector 6.


def test_grid_cell_corners_and_center():
    assert m.grid_cell((-1.0, -1.0)) == (0, 0)
    assert m.grid_cell((1.0, 1.0)) == (2, 2)
    assert m.grid_cell((0.0, 0.0)) == (1, 1)


def test_raw_null_excess_perfect_agreement_beats_shuffled_null():
    """A synthetic bucket where every group is UNANIMOUS (perfect real agreement) must score
    RAW=1.0 and, when there is real cross-group variety for the null shuffle to mix in, EXCESS
    strictly above the shuffled floor. 6 groups of size 4, alternating between two distinct
    unanimous values so the shuffled null has genuine variety to draw from (not itself
    trivially 1.0)."""
    rng = np.random.default_rng(0)
    groups = []
    for i in range(6):
        val = "A" if i % 2 == 0 else "B"
        groups.append([val] * 4)
    stat = m.raw_null_excess(groups, m._EQ_SCORE, n_reps=200, rng=rng)
    assert stat["raw"] == 1.0
    assert stat["null"] is not None and stat["null"] < 1.0
    assert stat["excess"] > 0.0
    assert stat["live"] is True


def test_raw_null_excess_random_labels_score_near_null():
    """When group membership carries NO real information (values assigned independent of
    group), RAW should land close to the null floor (small excess) -- the honest negative-
    control counterpart to the perfect-agreement test above."""
    rng = np.random.default_rng(1)
    values = ["A", "B", "C"] * 20
    rng.shuffle(values)
    groups = [values[i:i + 4] for i in range(0, len(values), 4)]
    stat = m.raw_null_excess(groups, m._EQ_SCORE, n_reps=200, rng=np.random.default_rng(2))
    assert stat["excess"] is not None
    assert abs(stat["excess"]) < 0.15   # loose bound -- this is a randomized sanity check.


def test_determinism_of_process_class_pipeline(native, tmp_path):
    """Running the same synthetic two-drawer, two-stroke class twice through
    `greedy_match`+`polarity`+`sector8` yields byte-identical results (no hidden randomness in
    the feature-extraction path itself -- randomness only ever enters via the null's own RNG)."""
    ref = [STROKE_A, STROKE_B]
    other = [STROKE_B.copy(), STROKE_A.copy()]
    m1 = m.greedy_match(native, ref, other)
    m2 = m.greedy_match(native, ref, other)
    assert m1 == m2
    p1 = m.polarity(STROKE_A, STROKE_A_REVERSED)
    p2 = m.polarity(STROKE_A, STROKE_A_REVERSED)
    assert p1 == p2


def test_select_characters_excludes_learn_alphabets():
    """The 5 LEARN alphabets (background[:5]) must never appear in the sampled pool -- the
    launch brief's quarantine requirement."""
    pytest.importorskip("domains.omniglot_world")
    from domains import omniglot_world as ow
    if not ow.alphabets("background"):
        pytest.skip("Omniglot data not present on this machine.")
    learn = set(ow.alphabets("background")[:m.LEARN_ALPHABETS_N])
    alphabets, char_dirs = m.select_characters()
    assert not (set(alphabets) & learn)
    assert len(alphabets) == m.N_ALPHABETS
