"""RUN 35 GATE 0 -- unit sanity for `domains/stroke_programs.py` (the per-stroke program
tokenizer). Synthetic geometry only, no LEARN/eval data, no seeds, no codebook mutation --
mirrors `domains/mouse_model.py`/`domains/ink_dynamics.py`'s own "world-adapter feature
extractor" test style (`tests/test_mouse_model_migrated.py` etc.).

HONEST NOTE (found while pre-registering these fixtures, before any real-data number was
computed): a sharp line-to-arc corner, resampled at only `segments=8` (7 usable per-segment
turn values), does NOT show as a clean second ARC run -- the corner's curvature smears across
2-3 resampled segments as an increasing sequence, which `promote_ramps` correctly (and
intentionally, per its own monotonic-run rule) reads as a RAMP, not a second constant-level ARC.
This is a real, expected property of coarse per-stroke segmentation (a "hook" IS a change-point,
but at this grain the change is itself gradual over a couple of steps) -- the line+arc fixture
below asserts the CHANGE-POINT is found (exactly two tokens, first is `line`) without demanding
the second token's specific kind, which is the literal, honestly-observed behaviour.
"""
from __future__ import annotations

import numpy as np
import substrate_rs as srs

from domains import stroke_programs as sp

LEVEL_EDGES = list(np.linspace(-180.0, 180.0, 13))     # a plain 12-bin reference grid --
DELTA_EDGES = [-360.0, -60.0, -20.0, 0.0, 20.0, 60.0, 360.0]   # fixed, test-local (not cited
                                                                # from any real run) so these
                                                                # tests are self-contained.
TOL_DEG = 1.0
SEGMENTS = 8
MAX_KNOTS = 16


def _tokenize(points: list) -> dict:
    s = srs.Substrate()
    seq = sp.stroke_turn_sequence(s, points, segments=SEGMENTS, max_knots=MAX_KNOTS)
    return sp.tokenize_turn_sequence(seq, TOL_DEG, LEVEL_EDGES, DELTA_EDGES)


def _circle_points(radius: float = 10.0, n: int = 80) -> list:
    theta = np.linspace(0.0, 2 * np.pi, n)
    return np.stack([radius * np.cos(theta), radius * np.sin(theta)], axis=1).tolist()


def _line_points(length: float = 10.0, n: int = 40) -> list:
    return np.stack([np.linspace(0.0, length, n), np.zeros(n)], axis=1).tolist()


def _line_then_arc_points() -> list:
    line_pts = np.stack([np.linspace(0.0, 4.0, 40), np.zeros(40)], axis=1)
    theta2 = np.linspace(-np.pi / 2, 0.0, 200)
    cx, cy = 4.0, 3.0
    arc_pts = np.stack([cx + 3.0 * np.sin(theta2 + np.pi / 2),
                        cy - 3.0 * np.cos(theta2 + np.pi / 2)], axis=1)
    arc_pts = arc_pts - arc_pts[0] + line_pts[-1]
    return np.concatenate([line_pts, arc_pts[1:]], axis=0).tolist()


def _spiral_points(n: int = 60) -> list:
    """A turtle walk whose per-step turn increases LINEARLY (0.5 -> 4.0 degrees) -- a clean,
    monotonic curvature ramp by construction."""
    heading = 0.0
    pos = np.array([0.0, 0.0])
    pts = [pos.copy()]
    for i in range(n):
        dtheta = 0.5 + 3.5 * (i / float(n - 1))
        heading += dtheta
        rad = np.radians(heading)
        pos = pos + np.array([np.cos(rad), np.sin(rad)])
        pts.append(pos.copy())
    return np.array(pts).tolist()


def test_circle_is_one_arc_token():
    res = _tokenize(_circle_points())
    assert len(res["tokens"]) == 1, res
    assert res["tokens"][0]["kind"] == "arc", res
    assert res["coarse"] == "A"


def test_line_is_one_line_token():
    res = _tokenize(_line_points())
    assert len(res["tokens"]) == 1, res
    assert res["tokens"][0]["kind"] == "line", res
    assert res["coarse"] == "L"


def test_line_then_arc_is_a_changepoint():
    res = _tokenize(_line_then_arc_points())
    assert len(res["tokens"]) == 2, res
    assert res["tokens"][0]["kind"] == "line", res
    assert res["tokens"][1]["kind"] in ("arc", "ramp"), res
    assert res["coarse"].startswith("L-"), res


def test_spiral_is_a_ramp_token():
    res = _tokenize(_spiral_points())
    assert any(t["kind"] == "ramp" for t in res["tokens"]), res
    assert "R" in res["coarse"], res


def test_determinism():
    pts = _line_then_arc_points()
    r1 = _tokenize(pts)
    r2 = _tokenize(pts)
    assert r1["fine"] == r2["fine"]
    assert r1["coarse"] == r2["coarse"]


def test_empty_stroke_is_honest_not_a_crash():
    res = _tokenize([[0.0, 0.0], [0.0, 0.0]])   # degenerate: <2 usable knots.
    assert res["fine"] == "∅"
    assert res["coarse"] == "∅"


def test_bin_index_matches_bin_occupancy_semantics():
    edges = [0.0, 1.0, 2.0, 3.0]
    assert sp.bin_index(-5.0, edges) == 0      # below range -> clamp to first bin.
    assert sp.bin_index(0.0, edges) == 0
    assert sp.bin_index(0.5, edges) == 0
    assert sp.bin_index(1.0, edges) == 1
    assert sp.bin_index(2.999, edges) == 2
    assert sp.bin_index(3.0, edges) == 2       # above range -> clamp to last bin.
    assert sp.bin_index(100.0, edges) == 2


def test_tol_deg_from_edges_is_half_median_bin_width():
    edges = [0.0, 2.0, 4.0, 6.0, 8.0]   # uniform width-2 bins.
    assert abs(sp.tol_deg_from_edges(edges) - 1.0) < 1e-9


def test_gather_delta_edges_falls_back_gracefully_on_sparse_input():
    edges = sp.gather_delta_edges([5.0])   # a single observation -- degenerate, must not crash.
    assert len(edges) >= 2
    assert all(edges[i] < edges[i + 1] for i in range(len(edges) - 1))
