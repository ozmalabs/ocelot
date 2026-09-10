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


# ---- block 322 levers: signed coupling, incidence map, exact vs loopy ----

def test_refine_to_neurons_signed_is_frustrated():
    modes, mean, Wc = _toy_modes()
    coeffs = Wc @ np.ones(Wc.shape[1], dtype=np.float32)
    idx = np.argsort(-np.linalg.norm(modes, axis=0))[:10]
    # positive-only cofiring magnitudes
    coact = (np.abs(np.random.default_rng(2).standard_normal((10, 10)))
             + 0.1).astype(np.float32)
    field, J = lng.refine_to_neurons_signed(modes, coeffs, idx, coact,
                                             n_dom_modes=4)
    assert field.shape == (10,)
    assert J.shape == (10, 10)
    assert np.allclose(J, J.T)
    assert np.allclose(np.diag(J), 0.0)
    # frustration: signed J has BOTH signs (not a pure ferromagnet), unlike the
    # positive cofiring magnitudes it is built from
    off = J[np.triu_indices_from(J, k=1)]
    assert np.any(off > 0) and np.any(off < 0)


@_need_substrate
def test_mode_neuron_factor_graph_builds_and_reads():
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    modes, mean, Wc = _toy_modes(k=6, ff=40)
    coeffs = Wc @ np.ones(Wc.shape[1], dtype=np.float32)
    idx = np.argsort(-np.linalg.norm(modes, axis=0))[:8]
    _, field, _ = lng.refine_to_neurons(modes, coeffs, n_neurons=8)
    s = _native.Substrate()
    mt, ncs, mcs, dom = lng.build_mode_neuron_factor_graph(
        s, ["seeds/can_native_reimplementation.json"], modes, coeffs, idx,
        field, temperature=1.0, mode_field_scale=0.0, neuron_field_scale=1.0,
        incidence_scale=1.0, n_modes=4, discrete_mode="3state")
    assert len(ncs) == 8 and len(mcs) == 4 and len(dom) == 4
    bp = run_loopy_bp(s, mt, combine="max_product")
    state_hat = lng.read_mode_nodes(bp, mcs)
    assert state_hat.shape == (4,)
    assert set(np.unique(state_hat)).issubset({-1.0, 1.0})


@_need_substrate
def test_exact_matches_loopy_on_factor_graph():
    # lever (c): on this bipartite structure, exact MAP and loopy-BP settle
    # the mode-nodes to the same signs (the block-322 finding that the ceiling
    # is structural, not the solver — checked here on a toy for stability).
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    from domains.can_junction_tree import can_network_from_mt, brute_force_map
    modes, mean, Wc = _toy_modes(k=6, ff=40, seed=3)
    coeffs = Wc @ np.ones(Wc.shape[1], dtype=np.float32)
    idx = np.argsort(-np.linalg.norm(modes, axis=0))[:6]
    _, field, _ = lng.refine_to_neurons(modes, coeffs, n_neurons=6)
    s = _native.Substrate()
    mt, ncs, mcs, dom = lng.build_mode_neuron_factor_graph(
        s, ["seeds/can_native_reimplementation.json"], modes, coeffs, idx,
        field, temperature=1.0, mode_field_scale=0.0, neuron_field_scale=1.0,
        incidence_scale=1.0, n_modes=3, discrete_mode="3state")
    bp = run_loopy_bp(s, mt, combine="max_product")
    loopy_modes = lng.read_mode_nodes(bp, mcs)
    net = can_network_from_mt(s, mt)
    bf = brute_force_map(net["nodes"], net["unary"], net["pairwise"],
                         net["vocab"])
    exact_modes = np.array(
        [1.0 if bf["state"][c.value] >= 0 else -1.0 for c in mcs],
        dtype=np.float32)
    # exact and loopy agree on the mode-node signs (structural, not solver-bound)
    assert np.array_equal(loopy_modes, exact_modes)


# ---- block 323 fidelity: fitted incidence + vocab ----------------------

def test_fit_incidence_shapes_and_representability():
    modes, mean, Wc = _toy_modes(k=6, ff=40, seed=5)
    rng = np.random.default_rng(6)
    train_x = rng.standard_normal((30, Wc.shape[1])).astype(np.float32)
    idx = np.argsort(-np.linalg.norm(modes, axis=0))[:8]
    W = lng.fit_incidence(modes, mean, Wc, train_x, idx, n_modes=4, ridge=1.0)
    assert W.shape == (modes.shape[0], 8)          # [k, N]
    # representability: the fitted read reproduces the TRAIN mode signs well
    # (it can memorise train — that is the point of "representable")
    ok = []
    for x in train_x:
        coeffs = Wc @ x
        s = np.where((coeffs @ modes[:, idx]) >= 0, 1.0, -1.0)
        dom = np.argsort(-np.abs(coeffs))[:4]
        ok.append(np.mean(np.sign(W[dom] @ s)
                          == np.where(coeffs[dom] >= 0, 1.0, -1.0)))
    assert np.mean(ok) > 0.75                      # fits train (representable)


@_need_substrate
def test_incidence_override_wires_into_builder():
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    modes, mean, Wc = _toy_modes(k=6, ff=40, seed=7)
    coeffs = Wc @ np.ones(Wc.shape[1], dtype=np.float32)
    idx = np.argsort(-np.linalg.norm(modes, axis=0))[:8]
    _, field, _ = lng.refine_to_neurons(modes, coeffs, n_neurons=8)
    override = np.ones((modes.shape[0], 8), dtype=np.float32) * 0.5
    s = _native.Substrate()
    mt, ncs, mcs, dom = lng.build_mode_neuron_factor_graph(
        s, ["seeds/can_native_reimplementation.json"], modes, coeffs, idx,
        field, temperature=1.0, mode_field_scale=0.0, neuron_field_scale=1.0,
        incidence_scale=1.0, n_modes=4, discrete_mode="3state",
        incidence_override=override)
    # the override is used as the incidence weight: mode<->neuron edges exist
    bp = run_loopy_bp(s, mt, combine="max_product")
    sh = lng.read_mode_nodes(bp, mcs)
    assert sh.shape == (4,)


@_need_substrate
def test_vocab_param_passes_through():
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    modes, mean, Wc = _toy_modes(k=6, ff=40, seed=8)
    coeffs = Wc @ np.ones(Wc.shape[1], dtype=np.float32)
    idx = np.argsort(-np.linalg.norm(modes, axis=0))[:6]
    _, field, _ = lng.refine_to_neurons(modes, coeffs, n_neurons=6)
    for dm, vocab in (("3state", {-1.0, 0.0, 1.0}), ("2state", {-1.0, 1.0})):
        s = _native.Substrate()
        mt, ncs, mcs, dom = lng.build_mode_neuron_factor_graph(
            s, ["seeds/can_native_reimplementation.json"], modes, coeffs, idx,
            field, temperature=1.0, mode_field_scale=0.0, neuron_field_scale=1.0,
            incidence_scale=1.0, n_modes=3, discrete_mode=dm)
        bp = run_loopy_bp(s, mt, combine="max_product")
        for v in bp["final_state"].values():
            assert v in vocab
