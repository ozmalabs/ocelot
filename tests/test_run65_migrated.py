"""Unit tests for RUN 65 ligature-strip operationalizations. donkey=0; no seed writes.

Verifies the strip transforms do what the pre-registration claims (before spending compute):
  1. endpoint_trim strips the right ARC-LENGTH fraction at each end.
  2. baseline estimate + connector strip removes a near-baseline low-curvature end connector,
     keeps the high body.
  3. predict-residual: a synthetic char = smooth connector + tall spike -> connector predicted
     (low residual, dropped), core = spike (high residual, kept).
  4. bank + query are stripped by the SAME callable (identical output on identical input).
  5. seed-guard md5 helper reads the seed unchanged.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import scripts.jabberwock_realwordread_run65 as r65


def _arc_len(strokes):
    P, sid = r65._concat(strokes)
    return float(r65._arclen_cum(P, sid)[-1]) if len(P) else 0.0


def test_endpoint_trim_strips_right_fraction():
    # A single straight stroke, unit-spaced along x: arc length = 99 over 100 points.
    P = np.stack([np.arange(100.0), np.zeros(100)], axis=1)
    strokes = [P]
    L0 = _arc_len(strokes)
    for f in (0.10, 0.20, 0.25):
        kept = r65.strip_endpoint_trim(strokes, f)
        Lk = _arc_len(kept)
        # kept arc length should be ~ (1 - 2f) * L0.
        assert abs(Lk - (1 - 2 * f) * L0) <= 1.5, (f, Lk, (1 - 2 * f) * L0)
    # f=0 is identity.
    assert abs(_arc_len(r65.strip_endpoint_trim(strokes, 0.0)) - L0) < 1e-6


def test_endpoint_trim_guards_short_char():
    # too-short char cannot be trimmed -> returned unchanged.
    strokes = [np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])]
    out = r65.strip_endpoint_trim(strokes, 0.25)
    assert sum(len(s) for s in out) == 3


def test_baseline_connector_strips_end_connector_keeps_body():
    # A char that: rises into a tall body (well above baseline -- kept regardless), then EXITS along
    # a long flat near-baseline low-curvature LIGATURE. The exit ligature must be stripped, body
    # kept. Body has enough ABOVE-baseline points to survive the MIN_KEEP guard.
    tx = np.linspace(0, 2.0, 16)
    body = np.stack([tx, 6.0 - np.abs(tx - 1.0) * 6.0], axis=1)      # tall tent, apex y=6, feet y=0
    ligature = np.stack([np.linspace(2.0, 8.0, 30), np.zeros(30)], axis=1)          # flat baseline
    strokes = [np.vstack([body, ligature])]
    kept = r65.strip_baseline_connector(strokes)
    P, _ = r65._concat(kept)
    # the tall apex (y ~ 6) survives; most of the flat baseline tail is gone.
    assert P[:, 1].max() > 4.0
    assert len(P) < len(body) + len(ligature)          # something was stripped
    # the number of near-baseline (y~0) points dropped substantially.
    n_flat_before = int(np.sum(np.abs(np.vstack([body, ligature])[:, 1]) < 0.5))
    n_flat_after = int(np.sum(np.abs(P[:, 1]) < 0.5))
    assert n_flat_after < n_flat_before


def test_predict_residual_keeps_spike_drops_connector():
    # entry->exit is a straight baseline connector; a tall spike in the middle is the CORE.
    left = np.stack([np.linspace(0, 4, 20), np.zeros(20)], axis=1)     # near connector line
    # a WIDE tall core (8 points well above the connector line) so it survives the MIN_KEEP guard.
    sx = np.linspace(4.0, 6.0, 8)
    spike = np.stack([sx, 8.0 - np.abs(sx - 5.0) * 2.0], axis=1)       # far from connector line
    right = np.stack([np.linspace(6, 10, 20), np.zeros(20)], axis=1)   # near connector line
    strokes = [np.vstack([left, spike, right])]
    kept = r65.strip_predict_residual(strokes, thresh_frac=0.15)
    P, _ = r65._concat(kept)
    # the spike core survived; the flat connector points are mostly gone.
    assert P[:, 1].max() > 5.0
    assert int(np.sum(np.abs(P[:, 1]) < 0.5)) <= 6        # near-baseline connector largely dropped
    assert int(np.sum(P[:, 1] > 3.0)) >= 4                # the high-residual core is kept


def test_bank_and_query_stripped_identically():
    # the SAME callable must produce identical output on identical strokes (bank vs query parity).
    rng = np.random.default_rng(0)
    strokes = [rng.normal(size=(40, 2)).cumsum(axis=0)]
    for op_id, transform in r65._op_table():
        a = transform([s.copy() for s in strokes])
        b = transform([s.copy() for s in strokes])
        assert len(a) == len(b), op_id
        for sa, sb in zip(a, b):
            assert np.allclose(sa, sb), op_id


def test_op_table_has_control_first():
    ops = r65._op_table()
    assert ops[0][0] == "endpoint_trim_f0.00"
    ids = [o[0] for o in ops]
    assert "baseline_connector" in ids
    assert any(i.startswith("predict_residual") for i in ids)


def test_seed_guard_reads_unchanged():
    md5 = r65._seed_guard("test")
    assert r65._seed_guard("test", md5) == md5


def test_f0_is_identity():
    rng = np.random.default_rng(1)
    strokes = [rng.normal(size=(30, 2)).cumsum(axis=0)]
    out = r65.strip_endpoint_trim(strokes, 0.0)
    P0, _ = r65._concat(strokes)
    P1, _ = r65._concat(out)
    assert np.allclose(P0, P1)
