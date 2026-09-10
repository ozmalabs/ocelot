"""Block 321000 — tests for the native-graph aperture bridge
(`domains/llm_native_graph.py`). The aperture READINGS (coarse/refine/read-back)
are pure numpy and always run. The SUBSTRATE-BP round-trip is gated on
`substrate_rs` being importable (PYTHONPATH=runners/dsl/python). The full
model-side export is not tested here (needs the model, /applications venv);
that path is exercised by the block-321 export + measure scripts.
"""
from __future__ import annotations

import numpy as np
import pytest

from domains import llm_native_graph as lng


def _have_substrate():
    try:
        import substrate_rs  # noqa: F401
        return True
    except Exception:
        return False


_need_substrate = pytest.mark.skipif(
    not _have_substrate(),
    reason="substrate_rs absent (run with PYTHONPATH=runners/dsl/python)")


def _toy_modes(k=6, ff=40, seed=0):
    rng = np.random.default_rng(seed)
    # orthonormal-ish modes (as SVD would give)
    A = rng.standard_normal((ff, k)).astype(np.float32)
    Q, _ = np.linalg.qr(A)
    modes = Q[:, :k].T.astype(np.float32)     # [k, ff], rows ~orthonormal
    mean = rng.standard_normal(ff).astype(np.float32) * 0.1
    Wc = rng.standard_normal((k, 24)).astype(np.float32)
    return modes, mean, Wc


# ---- pure-numpy aperture readings (always run) -------------------------

def test_coarse_mode_state_shapes_and_signs():
    modes, mean, Wc = _toy_modes()
    x = np.ones(Wc.shape[1], dtype=np.float32)
    coeffs, states = lng.coarse_mode_state(modes, mean, Wc, x)
    assert coeffs.shape == (modes.shape[0],)
    assert states.shape == (modes.shape[0],)
    assert set(np.unique(states)).issubset({-1.0, 1.0})
    assert np.allclose(np.sign(np.where(coeffs >= 0, 1, -1)), states)


def test_refine_to_neurons_shapes():
    modes, mean, Wc = _toy_modes()
    coeffs = Wc @ np.ones(Wc.shape[1], dtype=np.float32)
    idx, field, J = lng.refine_to_neurons(modes, coeffs, n_neurons=12)
    assert idx.shape == (12,)
    assert field.shape == (12,)
    assert J.shape == (12, 12)
    assert np.allclose(np.diag(J), 0.0)          # no self-coupling
    assert np.allclose(J, J.T)                    # Gram is symmetric


def test_refine_to_neurons_coact_uses_given_coupling():
    modes, mean, Wc = _toy_modes()
    coeffs = Wc @ np.ones(Wc.shape[1], dtype=np.float32)
    idx = np.argsort(-np.linalg.norm(modes, axis=0))[:10]
    coact = np.abs(np.random.default_rng(1).standard_normal((10, 10))
                   ).astype(np.float32)
    field, J = lng.refine_to_neurons_coact(modes, coeffs, idx, coact)
    assert field.shape == (10,)
    assert J.shape == (10, 10)
    assert np.allclose(np.diag(J), 0.0)
    assert np.allclose(J, J.T)                    # symmetrised


def test_read_back_modes_roundtrip_shapes():
    modes, mean, Wc = _toy_modes()
    idx = np.arange(12)
    settled = {i: (1.0 if i % 2 == 0 else -1.0) for i in range(12)}
    coeff_hat, state_hat = lng.read_back_modes(modes, idx, settled)
    assert coeff_hat.shape == (modes.shape[0],)
    assert state_hat.shape == (modes.shape[0],)
    assert set(np.unique(state_hat)).issubset({-1.0, 1.0})


# ---- substrate-BP round trip (gated on substrate_rs) -------------------

@_need_substrate
def test_build_ising_and_settle_roundtrip():
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    modes, mean, Wc = _toy_modes()
    coeffs = Wc @ np.ones(Wc.shape[1], dtype=np.float32)
    idx, field, J = lng.refine_to_neurons(modes, coeffs, n_neurons=8)
    s = _native.Substrate()
    mt, concepts = lng.build_ising_refinement(
        s, ["seeds/can_native_reimplementation.json"], field, J,
        temperature=1.0, discrete_mode="3state")
    assert len(concepts) == 8
    bp = run_loopy_bp(s, mt, combine="max_product")
    settled = lng.settled_state_array(bp, concepts)
    assert set(settled.keys()) == set(range(8))
    for v in settled.values():
        assert v in (-1.0, 0.0, 1.0)              # 3state vocab
    # read-back is well-formed
    coeff_hat, state_hat = lng.read_back_modes(modes, idx, settled)
    assert state_hat.shape == (modes.shape[0],)


@_need_substrate
def test_strong_field_dominates_settle():
    # a decisive field should pin the settle to its sign (sanity on the
    # substrate Ising unary term via this module's builder)
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    field = np.array([5.0, -5.0, 5.0, -5.0], dtype=np.float32)
    J = np.zeros((4, 4), dtype=np.float32)         # no coupling
    s = _native.Substrate()
    mt, concepts = lng.build_ising_refinement(
        s, ["seeds/can_native_reimplementation.json"], field, J,
        temperature=1.0, discrete_mode="3state")
    bp = run_loopy_bp(s, mt, combine="max_product")
    settled = lng.settled_state_array(bp, concepts)
    assert [settled[i] for i in range(4)] == [1.0, -1.0, 1.0, -1.0]
