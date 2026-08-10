"""RUN 49 -- unit gates for `domains/motor_verdict.py` (the MOTOR-PROGRAM VERDICT: a held-Term
distance over stroke-interior/motor structure, fused into -- never replacing -- the whole-shape
continuous SC+TPS verdict, per RUN 37A's supplement law).

Covers (per the RUN 49 launch brief): (1) `motor_distance` on synthetic glyphs -- the SAME shape
drawn with a DIFFERENT stroke program (or stroke order/count) scores a LARGE `m`; the identical
program scores a small (zero) `m`; a stroke-count mismatch is handled honestly (not a crash, not
silently imputed); (2) the spread-matched + frozen `w_m`/`lam` mechanics (`derive_w_m` reproduces
`deform_metric.derive_w_aff`'s own formula on a single-existing-term ensemble; the SUPPLEMENT
invariant -- `lam=0.0` recovers `argmin(geo_scores)` alone, BYTE-IDENTICAL); (3) the greedy
stroke-matcher's falsy-zero fix (a genuine ZERO-cost match must not be dropped -- `gate0.
greedy_match` is reused, not re-implemented, so this is a regression guard on the REUSE, not a
new fix); (4) a held-Term source audit (no Python argmin/argmax/sort-by-score, no minting); (5)
the seed-write guard -- `seeds/stroke_shapes.json` must be provably unchanged before and after
this entire test module runs (belt-and-suspenders, per this run's own launch brief, on top of
`tests/conftest.py`'s session-wide `OZMA_SEED_PERSIST_DISABLED` autouse guard).

All synthetic (no real DigiLeTs/UCI files needed), deterministic.
"""
from __future__ import annotations

import hashlib
import inspect
import os
import re

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

from domains import abs_read as ar
from domains import committed_shape as cs
from domains import deform_metric as dm
from domains import motor_plan as mp
from domains import motor_verdict as mv
from scripts import jabberwock_omniglot_run39_motorplan as gate0

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# A tiny, fast, deterministic edge set -- NOT fit from any real population (this module never
# fits edges; a caller always hands in an already-frozen dict, see `glyph_motor_program`'s own
# docstring). Mirrors `tests/test_committed_shape_migrated.py`'s own small-fixed-grid convention.
EDGES = {"tol_deg": 15.0, "level_edges": [-180.0, -90.0, -30.0, 30.0, 90.0, 180.0],
          "delta_edges": [-360.0, -60.0, 0.0, 60.0, 360.0]}
SEGMENTS = 8
MAX_KNOTS = 16


def _md5(path: str):
    if not os.path.exists(path):
        return None
    return hashlib.md5(open(path, "rb").read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def _seed_guard():
    """Belt-and-suspenders (this run's own launch brief): assert
    `seeds/stroke_shapes.json` is byte-identical before and after this ENTIRE module runs, on
    top of `tests/conftest.py`'s session-wide `OZMA_SEED_PERSIST_DISABLED` guard -- this module
    mints nothing (source-audited below) so this should be trivially true; the assertion makes
    that fact load-bearing rather than assumed."""
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after, "seeds/stroke_shapes.json changed across test_motor_verdict_migrated.py"


@pytest.fixture(scope="module")
def native():
    return srs.Substrate()._inner


def _prog(strokes, native_ignored=None):
    return mv.glyph_motor_program(strokes, edges=EDGES, segments=SEGMENTS, max_knots=MAX_KNOTS)


# A right-angle "L"-ish stroke (line then a sharp turn) vs. a smooth arc -- distinct fine
# programs at this edge set (line/arc token kinds differ), used throughout as the two "different
# program" primitives.
_LINE_THEN_TURN = [[0, 0], [1, 0], [2, 0], [2, 1], [2, 2]]
_SMOOTH_ARC = [[0, 0], [0.3, 0.95], [1.0, 1.3], [1.9, 0.95], [2.2, 0.0]]


# ===================================================================================== #
# GATE 1 -- motor_distance on synthetics.
# ===================================================================================== #
def test_identical_glyph_scores_zero_motor_distance(native):
    """The SAME strokes (same program, same pen-up channel, same count) against themselves ->
    m == 0.0 exactly -- every one of the three components must independently vanish."""
    strokes = [np.asarray(_LINE_THEN_TURN, dtype=float), np.asarray(_SMOOTH_ARC, dtype=float)]
    prog = _prog(strokes)
    r = mv.motor_distance(native, prog, prog)
    assert r["program"] == pytest.approx(0.0, abs=1e-9)
    assert r["pen_up"] == pytest.approx(0.0, abs=1e-9)
    assert r["count"] == pytest.approx(0.0, abs=1e-9)
    assert r["m"] == pytest.approx(0.0, abs=1e-9)


def test_different_stroke_program_scores_large_motor_distance(native):
    """Two glyphs with the SAME stroke count and similar spatial placement/start position, but
    one draws a straight-then-turn stroke where the other draws a smooth arc in that slot -- a
    genuinely different MOTOR PROGRAM in an aligned slot. `m` must be strictly larger than the
    identical-program case, and the PROGRAM component specifically must be > 0 (it is the only
    component that can see a token-content difference when start/count agree)."""
    a = [np.asarray(_LINE_THEN_TURN, dtype=float), np.asarray([[5, 5], [5, 6]], dtype=float)]
    b = [np.asarray(_SMOOTH_ARC, dtype=float), np.asarray([[5, 5], [5, 6]], dtype=float)]
    prog_a, prog_b = _prog(a), _prog(b)
    same = mv.motor_distance(native, prog_a, prog_a)
    diff = mv.motor_distance(native, prog_a, prog_b)
    assert diff["program"] > 0.0
    assert diff["m"] > same["m"]


def test_reordered_strokes_score_larger_than_same_order(native):
    """The identical two strokes, drawn in the OPPOSITE order, must score a larger (or equal, in
    a degenerate all-symmetric case) motor distance than the same order -- start position and/or
    transitions see the reordering even when the spatial correspondence still recovers the right
    shape-twin per stroke (mirrors `test_motor_supplement_migrated.py`'s own reordered-
    correspondence precedent)."""
    s1 = np.asarray(_LINE_THEN_TURN, dtype=float)
    s2 = np.asarray([[5, 5], [6, 5], [7, 6], [8, 8]], dtype=float)
    forward = _prog([s1, s2])
    reversed_ = _prog([s2, s1])
    same_order = mv.motor_distance(native, forward, forward)
    diff_order = mv.motor_distance(native, forward, reversed_)
    assert diff_order["m"] >= same_order["m"]


def test_count_mismatch_is_handled_honestly_never_a_crash(native):
    """A stroke-count mismatch must be REFLECTED in `count` (and, via the unmatched-slot penalty,
    in `program`), never silently ignored and never a crash. `pen_up` degrades honestly through
    `motor_plan_agreement`'s own count-mismatch skip (start_agree alone)."""
    a = _prog([np.asarray(_LINE_THEN_TURN, dtype=float)])
    b = _prog([np.asarray(_LINE_THEN_TURN, dtype=float),
               np.asarray([[9, 9], [9, 10]], dtype=float)])
    r = mv.motor_distance(native, a, b)
    assert r["n_a"] == 1 and r["n_b"] == 2
    assert r["count"] == pytest.approx(0.5)
    assert r["program"] > 0.0, "the unmatched second stroke must penalize PROGRAM too"
    assert 0.0 <= r["m"] <= 1.0
    assert r["pen_up_detail"]["skip_reason"] == "count_mismatch"


def test_both_empty_glyphs_do_not_crash():
    """Two glyphs with zero usable strokes (degenerate input) -- `glyph_motor_program` must
    return an honest `n_strokes=0`, never raise."""
    prog = mv.glyph_motor_program([], edges=EDGES, segments=SEGMENTS, max_knots=MAX_KNOTS)
    assert prog["n_strokes"] == 0
    assert prog["fine_tokens"] == []
    assert prog["norm_xy"] == []


def test_motor_distance_bounded_when_both_glyphs_empty(native):
    empty = mv.glyph_motor_program([], edges=EDGES, segments=SEGMENTS, max_knots=MAX_KNOTS)
    r = mv.motor_distance(native, empty, empty)
    assert 0.0 <= r["m"] <= 1.0


def test_degenerate_single_point_stroke_yields_empty_token(native):
    """A single-point stroke (`<2` points) must tokenize to `(EMPTY_TOKEN,)`, never a crash --
    `stroke_fine_tokens`'s own documented degenerate floor."""
    tok = mv.stroke_fine_tokens([[0.0, 0.0]], tol_deg=EDGES["tol_deg"],
                                 level_edges=EDGES["level_edges"],
                                 delta_edges=EDGES["delta_edges"], segments=SEGMENTS,
                                 max_knots=MAX_KNOTS)
    assert tok == (mv.EMPTY_TOKEN,)


def test_motor_distance_always_bounded_0_1(native):
    rng = np.random.default_rng(20260706)
    for _ in range(20):
        n1, n2 = rng.integers(1, 4), rng.integers(1, 4)
        a = [np.cumsum(rng.normal(size=(rng.integers(3, 8), 2)), axis=0) for _ in range(n1)]
        b = [np.cumsum(rng.normal(size=(rng.integers(3, 8), 2)), axis=0) for _ in range(n2)]
        r = mv.motor_distance(native, _prog(a), _prog(b))
        assert 0.0 <= r["m"] <= 1.0 + 1e-9, r


# ===================================================================================== #
# GATE 2 -- the greedy matcher's falsy-zero fix, exercised through this module's own reuse.
# ===================================================================================== #
def test_greedy_matcher_keeps_a_genuine_zero_cost_match(native):
    """A query stroke IDENTICAL (zero `PointSetDist`) to one candidate stroke must still be
    matched to it -- the falsy-zero bug (`v or nan` would have discarded a real zero-cost pair,
    treating it as `nan`/missing). `gate0.greedy_match` already carries the fix
    (`float(v) if v is not None else float("nan")`) at its source; this test regression-guards
    THIS module's own reuse of it (imported, never re-implemented -- see the source audit
    below)."""
    ident = np.asarray(_LINE_THEN_TURN, dtype=float)
    other = np.asarray([[9, 9], [9, 10], [9, 11]], dtype=float)
    norm = gate0.normalize_glyph_xy([ident, other])
    mapping = gate0.greedy_match(native, norm, norm)
    assert mapping == {0: 0, 1: 1}, "an exact self-match must map every stroke to itself"


# ===================================================================================== #
# GATE 3 -- spread-matched w_m + lambda fusion mechanics (RUN 44b protocol).
# ===================================================================================== #
def test_derive_w_m_matches_deform_metric_formula_on_one_existing_term():
    spread_geo, spread_m = 0.42, 0.07
    w_m = mv.derive_w_m(spread_geo, spread_m)
    expected = dm.derive_w_aff(spread_geo, spread_geo, spread_geo, spread_m)
    assert w_m == pytest.approx(expected)
    assert w_m == pytest.approx(spread_geo / spread_m)


def test_spread_of_scores_is_mean_of_per_episode_std():
    per_episode = [[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]]
    expected = float(np.mean([np.std([1.0, 2.0, 3.0]), np.std([0.0, 0.0, 0.0])]))
    assert mv.spread_of_scores(per_episode) == pytest.approx(expected)


def test_spread_of_scores_ignores_degenerate_single_candidate_episodes():
    assert mv.spread_of_scores([[5.0], [1.0, 2.0]]) == pytest.approx(np.std([1.0, 2.0]))


def test_lambda_zero_recovers_continuous_only_argmin_exactly(native):
    """The SUPPLEMENT invariant (RUN 37A's law): `lam=0.0` must be BYTE-IDENTICAL to
    `argmin(geo_scores)` alone, regardless of how strong/weak the motor evidence is."""
    geo_scores = [1.0, 2.0, 0.5, 1.5]
    m_scores = [1.0, 0.0, 1.0, 0.0]     # candidate 2 (best geo) has the WORST motor agreement.
    winner = mv.fused_argmin(native, geo_scores, m_scores, w_m=10.0, lam=0.0)
    bare_pairs = [(g, i) for i, g in enumerate(geo_scores)]
    expected = int(native.evaluate(ar._argmin_pairs_term(bare_pairs), {})[1])
    assert winner == expected == 2


def test_large_lambda_can_flip_a_close_call(native):
    geo_scores = [1.00, 1.05]
    m_scores = [1.0, 0.0]     # candidate 1 has better (lower) motor distance.
    w_m = 1.0
    assert mv.fused_argmin(native, geo_scores, m_scores, w_m, lam=0.0) == 0
    assert mv.fused_argmin(native, geo_scores, m_scores, w_m, lam=1.0) == 1


def test_fused_score_pairs_lambda_zero_equals_bare_geo_scores():
    geo_scores = [3.0, 1.0, 2.0]
    m_scores = [0.9, 0.1, 0.5]
    pairs = mv.fused_score_pairs(geo_scores, m_scores, w_m=5.0, lam=0.0)
    assert [p[0] for p in pairs] == geo_scores


# ===================================================================================== #
# GATE 4 -- held-Term source audit (no Python argmin/argmax/sort-by-score, no minting).
# ===================================================================================== #
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SORT_RE = re.compile(r"\bsorted\(|\.sort\(", re.IGNORECASE)


def _code_only(mod) -> str:
    return re.sub(r'""".*?"""', "", inspect.getsource(mod), flags=re.DOTALL)


def test_motor_verdict_no_python_ranking_decisions():
    src = _code_only(mv)
    assert not _BANNED_CALL_RE.search(src), (
        "motor_verdict.py must not rank candidates via Python argmin/argmax -- "
        "fused_argmin is a held Argmin Term")
    assert not _MINMAX_KEY_RE.search(src), (
        "motor_verdict.py must not use Python's builtin min()/max() ranked by a key-function")
    assert not _SORT_RE.search(src), (
        "motor_verdict.py must not sort candidates by a continuous score in Python")


def test_motor_verdict_mints_nothing():
    src = _code_only(mv)
    forbidden = ["teach(", "add_node(", "add_edge(", "run_rules(", "decode_ink("]
    hits = [tok for tok in forbidden if tok in src]
    assert not hits, f"motor_verdict.py must mint nothing -- found: {hits}"


def test_motor_verdict_reuses_gate0_and_committed_shape_not_reimplemented():
    src = _code_only(mv)
    assert "from scripts import jabberwock_omniglot_run39_motorplan as gate0" in src
    assert "from domains import committed_shape as cs" in src
    assert "from domains import motor_plan as mp" in src
    assert "from domains import deform_metric as dm" in src
    for name in ("def normalize_glyph_xy(", "def grid_cell(", "def sector8(",
                 "def greedy_match(", "def _token_edit_distance(", "def motor_plan_agreement(",
                 "def derive_w_aff("):
        assert name not in src, (
            f"motor_verdict.py must not re-define {name.strip('def (')} -- reuse the existing "
            f"module's own copy verbatim")


def test_motor_verdict_denoises_nothing():
    """Real-pen-data convention (module docstring): no `denoise_path_global` call -- that
    instrument targets the mousewriting Bresenham artifact, absent from real pen corpora
    (`OMNIGLOT_ARC.md` Addendum 2)."""
    src = _code_only(mv)
    assert "denoise" not in src.lower()
