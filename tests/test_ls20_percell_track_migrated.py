"""RUNG 222000 continuation gate — the GENERAL object-tracking per-cell model.

The base 222000 live half returned the pre-registered null (whole-frame colour
selector cannot isolate the real ls20 avatar). This adds object permanence: the
object is the connected figure blob that moved, tracked across frames; the
per-action shift is the whole-object centroid displacement, stored in the graph;
prediction translates the tracked object. Gated on synthetic dense move+trail
scenes (the honest twin of the real ls20 mechanic) before the live number.
"""
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_percell import Percell, score_prediction  # noqa: E402
from worlds.arc_ls20_percell_track import LiveObjectTracker  # noqa: E402

_H = _W = 64
_AV = [(0, 0, 9), (0, 1, 9), (1, 0, 11), (1, 1, 12), (2, 0, 9), (0, 2, 11), (1, 2, 12), (2, 1, 9)]
_DIRS = {"move_up": (-1, 0), "move_down": (1, 0), "move_left": (0, -1), "move_right": (0, 1)}


def _base():
    g = np.full((_H, _W), 4, dtype=np.int32)
    g[10:54, 10:54] = 3                 # nested local play-field
    g[2, 2] = 9; g[2, 3] = 11; g[60, 60] = 12   # static figure structure (contamination)
    return g


def _frame(pos):
    g = _base(); r0, c0 = pos
    for (dr, dc, v) in _AV:
        g[r0 + dr, c0 + dc] = v
    return g


def _world_next(pos, action, trail):
    dr, dc = _DIRS[action]; nxt = (pos[0] + dr, pos[1] + dc)
    g = _frame(nxt)
    if trail:
        g[pos[0] + 2, pos[1] + 1] = 11
    return g, nxt


def _run(trail, steps=60, shift_mode="centroid"):
    ag = Percell(); trk = LiveObjectTracker(ag, cap=200, n_field=2, shift_mode=shift_mode)
    pos = (30, 30); prev = _frame(pos)
    learned, pers = [], []
    for step in range(steps):
        action = list(_DIRS)[step % 4]
        had = (ag.hypothesis(action) is not None) and (trk.obj is not None)
        pred = trk.predict(prev, action)
        cur, pos = _world_next(pos, action, trail)
        if not (13 < pos[0] < 49 and 13 < pos[1] < 49):
            pos = (30, 30); cur = _frame(pos)
        if had:
            learned.append(score_prediction(prev, cur, pred)["f1_strict"])
            pers.append(score_prediction(prev, cur, prev.copy())["f1_strict"])
        trk.observe(prev, cur, action)
        prev = cur
    return ag, learned, pers


def test_tracker_rigid_move_is_exact_and_beats_persistence():
    ag, learned, pers = _run(trail=False)
    assert np.mean(learned) > 0.99, f"rigid move must predict exactly, got {np.mean(learned)}"
    assert np.mean(pers) == 0.0, "persistence scores 0 change-set F1"
    # the discovered per-action shift is the TRUE unit translation (not the object extent)
    for a, (dr, dc) in _DIRS.items():
        h = ag.hypothesis(a)
        assert (h["dr"], h["dc"]) == (dr, dc), f"{a}: learned shift {(h['dr'], h['dc'])} != {(dr, dc)}"


def test_tracker_with_trail_beats_persistence_honest_residual():
    _ag, learned, pers = _run(trail=True)
    m = float(np.mean(learned))
    assert m > 0.7, f"tracked model must beat persistence substantially, got {m}"
    assert np.mean(pers) == 0.0
    # the trail/consume dynamic is the honest residual: not exact, but far above the null
    assert m < 1.0, "a rigid-translate model cannot perfectly predict a trail/consume dynamic"


def test_tracker_shift_stored_in_graph_not_python():
    """The per-action shift lives in a graph Hypothesis (read via agent.hypothesis),
    not a Python dict — graph-native model, mechanical tracking."""
    ag, _l, _p = _run(trail=False, steps=12)
    h = ag.hypothesis("move_right")
    assert h is not None and h["key"] == "shift:0:1"
    assert h["conf"] >= 2.0, "the shift hypothesis is confirmed by re-observation"


def test_wrong_shift_estimator_scores_below_bar_so_exact_is_earned():
    """INSTRUMENT TEETH (pre-committed G-track-teeth). The exact rigid strict-F1
    (>0.99) is EARNED, not a permissive-metric artifact: the WRONG shift estimator
    (extent-not-displacement — the bug caught in validation, which read the object's
    edge gap instead of its centroid displacement) scores strict-F1 BELOW the
    pre-committed low bar (0.5) on the SAME rigid scene the centroid estimator aces.
    A metric that could not tell the two apart would be toothless."""
    ag_bad, learned_bad, _p = _run(trail=False, shift_mode="extent")
    m_bad = float(np.mean(learned_bad))
    assert m_bad < 0.5, f"a wrong (extent) shift estimator must score < 0.5, got {m_bad}"
    # the extent estimator over-reports the shift as the object's extent, not 1
    bad_shifts = {a: (ag_bad.hypothesis(a)["dr"], ag_bad.hypothesis(a)["dc"]) for a in _DIRS}
    assert any(abs(dr) > 1 or abs(dc) > 1 for (dr, dc) in bad_shifts.values()), \
        f"the extent bug must over-report the shift magnitude, got {bad_shifts}"
    # and the CORRECT estimator, on the identical scene, is exact — the teeth bite
    ag_ok, learned_ok, _ = _run(trail=False, shift_mode="centroid")
    assert float(np.mean(learned_ok)) > 0.99 > m_bad, "the exact number is earned by the estimator"
