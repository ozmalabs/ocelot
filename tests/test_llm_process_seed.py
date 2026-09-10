"""Block 329000 — tests for process-seed extraction
(`domains/llm_process_seed.py`). The operator/probe fit is pure numpy (always
runs); the substrate transport-settle is gated on `substrate_rs`. Real statement
vectors need the model and are exercised by the block-329 scripts.
"""
from __future__ import annotations

import numpy as np
import pytest

from domains import llm_process_seed as ps


def _have_substrate():
    try:
        import substrate_rs  # noqa: F401
        return True
    except Exception:
        return False


_need_substrate = pytest.mark.skipif(
    not _have_substrate(),
    reason="substrate_rs absent (run with PYTHONPATH=runners/dsl/python)")

SEEDS = ["seeds/can_native_reimplementation.json"]


def _toy_process(d=8, n=60, seed=0):
    """A toy 'negate' geometry: affirmations sit on the + side of a valence
    direction `u`, negations reflect to the - side. WELL-DETERMINED (n >> d) so
    the fitted operator learns the reflection and GENERALISES to held-out
    vectors (not identity-plus-noise)."""
    rng = np.random.default_rng(seed)
    u = rng.standard_normal(d).astype(np.float32)
    u = u / np.linalg.norm(u)
    vecs = {}
    pairs = []
    aff, neg = [], []
    for i in range(n):
        base = rng.standard_normal(d).astype(np.float32)
        base = base - (base @ u) * u            # component orthogonal to u
        v = (base + 2.0 * u).astype(np.float32)   # affirmation: + side
        vn = (base - 3.0 * u).astype(np.float32)  # negation: - side
        a = "aff%d" % i
        ng = "neg%d" % i
        vecs[a] = v
        vecs[ng] = vn
        pairs.append((a, ng))
        aff.append(a); neg.append(ng)
    return vecs, pairs, aff, neg, u


def test_fit_process_operator_shape_and_transforms():
    vecs, pairs, aff, neg, u = _toy_process()
    N = ps.fit_process_operator(vecs, pairs, ridge=1e-3)
    d = len(u)
    assert N.shape == (d, d)
    # N maps an affirmation toward its negation (output near the negation vec)
    pred = N @ vecs["aff0"]
    err = np.linalg.norm(pred - vecs["neg0"]) / (np.linalg.norm(vecs["neg0"]) + 1e-9)
    assert err < 0.5                       # transforms A input -> output region


def test_valence_probe_separates_and_reads_negated():
    vecs, pairs, aff, neg, u = _toy_process()
    p, thresh = ps.fit_valence_probe(vecs, aff, neg)
    # affirmations read NOT-negated, negations read negated
    assert not ps.reads_negated(vecs["aff0"], p, thresh)
    assert ps.reads_negated(vecs["neg0"], p, thresh)


def test_process_operator_applies_to_heldout_toy():
    # fit on A pairs, apply to a HELD-OUT affirmation not in the fit
    vecs, pairs, aff, neg, u = _toy_process(n=8)
    N = ps.fit_process_operator(vecs, pairs, ridge=1e-3)
    p, thresh = ps.fit_valence_probe(vecs, aff, neg)
    rng = np.random.default_rng(99)
    base = rng.standard_normal(len(u)).astype(np.float32)
    base = base - (base @ u) * u
    held = (base + 2.0 * u).astype(np.float32)   # a NEW affirmation (+ side)
    # identity: held affirmation reads not-negated; N(held) reads negated
    assert not ps.reads_negated(held, p, thresh)
    assert ps.reads_negated(N @ held, p, thresh)


@_need_substrate
def test_run_process_substrate_returns_config():
    from substrate_rs import _native
    K = 8
    N = np.eye(32, dtype=np.float32)       # identity transport (full-k)
    inp = np.zeros(32, dtype=np.float32)
    inp[:K] = np.array([1, -1, 1, -1, 1, -1, 1, -1], dtype=np.float32)
    s = _native.Substrate()
    out = ps.run_process_substrate(s, SEEDS, N, inp, n_modes=K)
    assert out.shape == (K,)
    assert set(np.unique(out)).issubset({-1.0, 1.0})
