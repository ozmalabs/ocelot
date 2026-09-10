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


# ---- block 324: between-layer transport aperture -----------------------

def test_fit_transport_shapes_and_reproduces_train():
    rng = np.random.default_rng(11)
    # a genuine linear transition C1 = C0 @ A^T (+ small noise) is recoverable
    k0, k1, N = 6, 5, 40
    C0 = rng.standard_normal((N, k0)).astype(np.float32)
    A = rng.standard_normal((k1, k0)).astype(np.float32)
    C1 = (C0 @ A.T + 0.01 * rng.standard_normal((N, k1))).astype(np.float32)
    T = lng.fit_transport(C0, C1, ridge=1e-3)
    assert T.shape == (k1, k0)
    # reproduces the training transition well (sign covariance high)
    pred = C0 @ T.T
    assert np.mean(np.sign(pred) == np.sign(C1)) > 0.9


@_need_substrate
def test_build_transport_factor_graph_and_read():
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    rng = np.random.default_rng(12)
    k = 32                              # T is full k x k (indexed by mode id)
    T = rng.standard_normal((k, k)).astype(np.float32)
    coeffs0 = rng.standard_normal(k).astype(np.float32)
    s = _native.Substrate()
    mt, n0, n1, dom0, dom1 = lng.build_transport_factor_graph(
        s, ["seeds/can_native_reimplementation.json"], T, coeffs0,
        n_modes0=6, n_modes1=5, temperature=1.0, discrete_mode="3state",
        bidirectional=True)
    assert len(n0) == 6 and len(n1) == 5
    bp = run_loopy_bp(s, mt, combine="max_product")
    sh = lng.read_transport_modes(bp, n1)
    assert sh.shape == (5,)
    assert set(np.unique(sh)).issubset({-1.0, 1.0})


@_need_substrate
def test_transport_l0_field_drives_l1_through_transport():
    # a strong single L0 mode with a strong positive transport edge to one L1
    # mode should drive that L1 mode-node positive (self-field 0 -> only the
    # transport can set it): confirms the transport edge carries the signal.
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    k = 32
    T = np.zeros((k, k), dtype=np.float32)
    T[0, 0] = 3.0                       # L0 mode 0 --(+)--> L1 mode 0
    coeffs0 = np.zeros(k, dtype=np.float32)
    coeffs0[0] = 5.0                    # L0 mode 0 strongly ON (+)
    s = _native.Substrate()
    mt, n0, n1, dom0, dom1 = lng.build_transport_factor_graph(
        s, ["seeds/can_native_reimplementation.json"], T, coeffs0,
        n_modes0=4, n_modes1=4, temperature=1.0, field_scale=1.0,
        transport_scale=1.0, discrete_mode="3state", bidirectional=True)
    bp = run_loopy_bp(s, mt, combine="max_product")
    sh = lng.read_transport_modes(bp, n1)
    assert sh[0] == 1.0                 # L1 mode 0 driven positive via transport


# ---- block 325: multi-hop transport chain ------------------------------

@_need_substrate
def test_build_chain_factor_graph_structure():
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    rng = np.random.default_rng(20)
    k, nm = 32, 6
    Ts = [rng.standard_normal((k, k)).astype(np.float32) for _ in range(3)]
    coeffs0 = rng.standard_normal(k).astype(np.float32)
    s = _native.Substrate()
    mt, layer_nodes = lng.build_chain_factor_graph(
        s, ["seeds/can_native_reimplementation.json"], Ts, coeffs0,
        n_modes=nm, temperature=1.0, discrete_mode="3state")
    assert len(layer_nodes) == len(Ts) + 1          # n_hops + 1 layers
    for nodes in layer_nodes:
        assert len(nodes) == nm
    bp = run_loopy_bp(s, mt, combine="max_product")
    # every layer is readable
    for nodes in layer_nodes:
        sh = lng.read_transport_modes(bp, nodes)
        assert sh.shape == (nm,)


@_need_substrate
def test_chain_transport_propagates_a_clamped_bit_forward():
    # a diagonal +transport chain should carry a clamped +bit at layer 0 forward
    # to the same mode at every deeper layer (feed-forward settle-and-clamp).
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    k, nm, hops = 32, 4, 3
    T = np.zeros((k, k), dtype=np.float32)
    for m in range(nm):
        T[m, m] = 3.0                    # identity-ish positive transport
    cur = np.zeros(k, dtype=np.float32)
    cur[0] = 5.0                         # mode 0 ON at layer 0
    states = [1.0]
    for hop in range(hops):
        c0 = np.zeros(k, dtype=np.float32)
        c0[:nm] = cur[:nm]
        s = _native.Substrate()
        mt, ln = lng.build_chain_factor_graph(
            s, ["seeds/can_native_reimplementation.json"], [T], c0,
            n_modes=nm, temperature=1.0, discrete_mode="3state")
        bp = run_loopy_bp(s, mt, combine="max_product")
        sh = lng.read_transport_modes(bp, ln[1])
        states.append(sh[0])
        cur = np.zeros(k, dtype=np.float32)
        cur[:nm] = sh                    # feed settled states forward
    # mode 0 stays positive through the whole feed-forward chain
    assert all(v == 1.0 for v in states)


# ---- block 326: transport fidelity (settle-aware fit + edge asymmetry) --

def test_fit_transport_settle_aware_shape():
    rng = np.random.default_rng(30)
    k0, k1, N = 32, 32, 40
    C0 = rng.standard_normal((N, k0)).astype(np.float32)
    A = rng.standard_normal((k1, k0)).astype(np.float32)
    C1 = (C0 @ A.T).astype(np.float32)
    T = lng.fit_transport_settle_aware(C0, C1, ridge=10.0, n_modes=8)
    assert T.shape == (k1, k0)


@_need_substrate
def test_back_scale_wires_asymmetric_edges():
    # back_scale reweights the reverse Ising edge; the graph must still build
    # and settle (BP needs the reverse channel present, so back_scale>0).
    from substrate_rs import _native
    from domains.can_native_bp import run_loopy_bp
    k = 32
    T = np.zeros((k, k), dtype=np.float32)
    T[0, 0] = 3.0
    coeffs0 = np.zeros(k, dtype=np.float32); coeffs0[0] = 5.0
    s = _native.Substrate()
    mt, ln = lng.build_chain_factor_graph(
        s, ["seeds/can_native_reimplementation.json"], [T], coeffs0,
        n_modes=4, temperature=1.0, discrete_mode="3state", back_scale=0.1)
    bp = run_loopy_bp(s, mt, combine="max_product")
    sh = lng.read_transport_modes(bp, ln[1])
    assert sh.shape == (4,)
    assert sh[0] == 1.0                 # forward transport still drives mode 0
