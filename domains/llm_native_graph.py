"""Block 321000 — the recovered structure as a NATIVE GRAPH, and the test of
whether it is one.

The prior blocks (318-320) recovered the FFN's structure into an intermediate
representation: SVD modes + a coefficient map + per-position selection, executed
by the same numpy substrate doing the same matmul shapes. That is an IR — the
model's computation in the model's coordinates, factored cheaply. It is NOT a
native graph.

The user's framing for what a native graph is: *an edge is literally a node at a
different APERTURE*. There is one aperture-invariant object; "node" vs "edge" is
a movable readout, not a property baked into the thing. The recovered structure
is a native graph IFF it is APERTURE-COVARIANT: the same object read at the mode
aperture, refined to the coactivation-edge aperture and propagated on the
SUBSTRATE'S OWN belief propagation (`can_native_bp.run_loopy_bp`, an Ising/
Boltzmann graphical model — NOT numpy matmul replay), reproduces the SAME
outcome. If it does, the cognition was never in the model's coordinates — it
lived in the aperture-invariant object, and the weights were one aperture's
encoding. That is substrate independence, demonstrated.

This module has two sides, bridged by an on-disk export because the two
substrates live in different Python environments:
  * EXPORT (model side, /applications venv): fit the mode structure and write
    the per-layer {modes, coefficient map, mean} + held-out coefficients to a
    npz. Needs the model; see `export_mode_structure`.
  * REFINE + PROPAGATE (substrate side, tree python3 with substrate_rs): build
    the Ising graph for one mode-refinement and run the substrate's own BP;
    read the settled state back up to the mode aperture. Needs substrate_rs;
    see `build_ising_refinement`, `read_back_modes`.

The aperture-covariance measure lives in
`scripts/llm_native_graph_measure.py`; the pre-reg / results are in
`docs/research/psychology_affect/NATIVE_GRAPH_APERTURE_PREREG.md` /
`_RESULTS.md`. Protected CAN internals (`can_native_bp.py`,
`can_junction_tree.py`, `model_reader.py`, `can_ops.rs`) are READ-ONLY here —
this module builds TO their interface, mints no new node/edge types, and never
touches the `.so`.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# EXPORT side (model / venv): fit the mode structure, write held-out coeffs.
# ---------------------------------------------------------------------------

def export_mode_structure(model, train_ids, heldout_ids, out_path, *,
                          layer, k=32, ridge=1.0, all_positions=True,
                          n_neurons=24):
    """Fit the mode-grain router (block 318/320) and export, for ONE layer, the
    objects the aperture test needs:
      modes   [k, ff]  — the SVD activation modes (the recovered units).
      mean    [ff]     — corpus mean activation.
      Wc      [k, d]   — input -> mode-coefficient map.
      ho_x    [H, d]   — held-out last-token MLP inputs at this layer.
      ho_coef [H, k]   — held-out true mode coefficients (mean-removed proj).
      neuron_idx [N]   — the top-loading neurons this layer refines into.
      coact_J [N, N]   — the neurons' COFIRING coupling (block 313 coactivation
                         graph) over neuron_idx — a basis with REAL edges, for
                         the coactivation refinement (the orthogonal mode Gram
                         has ~none).
    All numpy, written to `out_path` (npz). Runs in the model venv."""
    from . import llm_structure_recovery as lsr
    R = lsr.fit_mode_router(model, train_ids, k=k, ridge=ridge,
                            all_positions=all_positions)
    modes = R.modes[layer]
    mean = R.mean[layer]
    Wc = R.Wc[layer]
    # the neurons this layer refines into = top mode-loading columns
    col_norm = np.linalg.norm(modes, axis=0)
    neuron_idx = np.argsort(-col_norm)[:n_neurons].astype(np.int64)
    # coactivation coupling over those neurons (real cofiring edges)
    G = lsr.fit_coactivation_graph(model, train_ids, per_query_frac=0.1,
                                   pool_frac=0.6)
    cof = G.cofire.get(layer, {})
    N = len(neuron_idx)
    coact_J = np.zeros((N, N), dtype=np.float32)
    pos = {int(n): p for p, n in enumerate(neuron_idx)}
    for a_p, a in enumerate(neuron_idx):
        for partner, c in cof.get(int(a), {}).items():
            b_p = pos.get(int(partner))
            if b_p is not None:
                coact_J[a_p, b_p] = float(c)
    ho_x = []
    ho_coef = []
    for ids in heldout_ids:
        ios = lsr._ffn_io(model, ids)
        xg, act = ios[layer]
        ho_x.append(xg.astype(np.float32))
        ho_coef.append(((act - mean) @ modes.T).astype(np.float32))
    tr_x = []
    tr_coef = []
    for ids in train_ids:
        ios = lsr._ffn_io(model, ids)
        xg, act = ios[layer]
        tr_x.append(xg.astype(np.float32))
        tr_coef.append(((act - mean) @ modes.T).astype(np.float32))
    np.savez(out_path,
             modes=modes.astype(np.float32),
             mean=mean.astype(np.float32),
             Wc=Wc.astype(np.float32),
             ho_x=np.stack(ho_x),
             ho_coef=np.stack(ho_coef),
             tr_x=np.stack(tr_x),
             tr_coef=np.stack(tr_coef),
             neuron_idx=neuron_idx,
             coact_J=coact_J,
             layer=np.int64(layer))
    return out_path


# ---------------------------------------------------------------------------
# The two aperture readings of the SAME recovered object.
# ---------------------------------------------------------------------------

def coarse_mode_state(modes, mean, Wc, x):
    """MODE APERTURE (nodes = modes). For a query input x, the coefficient of
    each mode is c_m = Wc[m]·x; the mode's binary state is sign(c_m). Returns
    (coeffs [k], states [k] in {-1,+1})."""
    coeffs = Wc @ x
    states = np.where(coeffs >= 0, 1.0, -1.0)
    return coeffs.astype(np.float32), states.astype(np.float32)


def refine_to_neurons(modes, coeffs, *, n_neurons=16):
    """Open the layer's mode aperture one notch to the NEURON aperture. Select
    the neurons the modes most load on (top |·| of the mode matrix column
    norms), and derive the Ising graph PURELY from the recovered modes:
      field_i = (Σ_m coeffs[m]·modes[m,i])   — the modes' predicted drive to
                neuron i for THIS query (the reconstructed activation's centred
                part).
      J_ij    = Σ_m modes[m,i]·modes[m,j]     — the modes' Gram over neurons:
                neurons that co-load on the same modes are coupled. This is the
                mode structure READ AT THE NEURON APERTURE — the "edge" is the
                mode seen finer.
    Returns (neuron_idx [N], field [N], J [N,N]).

    NOTE (block 321 finding): the SVD modes are ~orthogonal by construction, so
    their Gram over a neuron subset is near-diagonal — J_off ≈ 0 and this
    refinement has essentially NO edges (an orthogonal factorisation is
    coordinate structure, not graph structure). Use `refine_to_neurons_coact`
    for the coactivation-coupled refinement, which has real edges."""
    col_norm = np.linalg.norm(modes, axis=0)          # [ff]
    neuron_idx = np.argsort(-col_norm)[:n_neurons]
    M = modes[:, neuron_idx]                           # [k, N]
    field = (coeffs @ M).astype(np.float32)            # [N]
    J = (M.T @ M).astype(np.float32)                   # [N, N] Gram
    np.fill_diagonal(J, 0.0)                           # no self-coupling
    return neuron_idx, field, J


def refine_to_neurons_coact(modes, coeffs, neuron_idx, coact_J, *,
                            symmetrize=True):
    """Coactivation-coupled refinement. Same field as `refine_to_neurons`
    (the modes' predicted drive), but the coupling J comes from the neurons'
    actual COFIRING structure (block 313's coactivation graph) restricted to
    `neuron_idx` — a basis with REAL edges, unlike the orthogonal mode Gram.
    `coact_J` is the [N, N] cofire-count coupling for these neurons.
    Returns (field [N], J [N,N])."""
    M = modes[:, neuron_idx]                           # [k, N]
    field = (coeffs @ M).astype(np.float32)            # [N]
    J = np.asarray(coact_J, dtype=np.float32).copy()
    if symmetrize:
        J = 0.5 * (J + J.T)
    np.fill_diagonal(J, 0.0)
    return field, J


def refine_to_neurons_signed(modes, coeffs, neuron_idx, coact_J, *,
                             n_dom_modes=8):
    """SIGNED / FRUSTRATED refinement (block 322 lever a). Block 321's
    coactivation coupling was dense and POSITIVE, so the Ising settle collapsed
    to a ferromagnetic consensus that erased the mode structure. Here the edge
    MAGNITUDE is the real cofiring (dense edges) but the edge SIGN is the
    neurons' AGREEMENT on the dominant modes: neurons that load the SAME way on
    the query's active modes couple POSITIVELY (want the same state), neurons
    that load OPPOSITELY couple NEGATIVELY (want opposite states) — frustration
    that prevents consensus collapse and, if the modes' geometry is the real
    graph, should make the settle re-express the mode reading.

      sign_ij = sign( Σ_{m in dominant} coeffs[m] · modes[m,i] · modes[m,j] )
      J_ij    = sign_ij · |coact_J_ij|

    `n_dom_modes` = how many top-|coeff| modes define the agreement sign.
    Returns (field [N], J [N,N])."""
    M = modes[:, neuron_idx]                           # [k, N]
    field = (coeffs @ M).astype(np.float32)            # [N]
    dom = np.argsort(-np.abs(coeffs))[:n_dom_modes]
    Md = M[dom]                                         # [d, N]
    cd = coeffs[dom]                                    # [d]
    # agreement matrix: neurons i,j signed by co-loading on the active modes
    agree = (Md * cd[:, None]).T @ Md                  # [N, N]
    sign = np.sign(agree).astype(np.float32)
    mag = np.abs(np.asarray(coact_J, dtype=np.float32))
    mag = 0.5 * (mag + mag.T)
    J = (sign * mag).astype(np.float32)
    np.fill_diagonal(J, 0.0)
    return field, J


def build_mode_neuron_factor_graph(substrate, seed_paths, modes, coeffs,
                                   neuron_idx, field, *, temperature=1.0,
                                   mode_field_scale=1.0, neuron_field_scale=1.0,
                                   incidence_scale=1.0, n_modes=None,
                                   discrete_mode="3state",
                                   incidence_override=None):
    """Lever (b): the INCIDENCE MAP made explicit as a BIPARTITE factor graph.

    Block 321/322a read the mode back by PROJECTING settled neurons onto the
    modes — a lossy read that assumed mode = flat neuron-support. Here the mode
    is a FIRST-CLASS node coupled to its neuron-variables by the incidence
    (`modes[m,i]` — the mode's loading on neuron i). The mode-node's OWN settled
    state IS the mode reading, no projection: node ⇄ edge are the same object at
    two apertures, joined by the incidence.

    Structure:
      neuron nodes  N of them, external_field = field_i (the query drive).
      mode nodes    n_modes of them, external_field = coeffs[m] (the coarse
                    coefficient — the mode's own drive).
      incidence edges  mode_m —causal_influence— neuron_i, weight =
                    modes[m, idx_i]·incidence_scale. A mode and a neuron that
                    load together want the same state; opposite loading frustrates.
    Returns (mt, neuron_concepts [N], mode_concepts [n_modes]).
    Runs in tree python3 (substrate_rs)."""
    import json
    from substrate.seed_loader import engine_rules_only
    for path in seed_paths:
        substrate.load_seed_manifest(engine_rules_only(json.load(open(path))))
    if n_modes is None:
        n_modes = modes.shape[0]
    dom = np.argsort(-np.abs(coeffs))[:n_modes]
    M = modes[:, neuron_idx]                            # [k, N]
    mt = substrate.add_node("Microtheory",
                            {"temperature": float(temperature),
                             "discrete_mode": discrete_mode})
    neuron_concepts = []
    for i in range(len(neuron_idx)):
        c = substrate.add_node("Concept", {
            "external_field": float(field[i] * neuron_field_scale),
            "identity_field": 0.0, "state": 0.0})
        substrate.add_edge(mt, "has_concept", c, {})
        neuron_concepts.append(c)
    mode_concepts = []
    for m in dom:
        c = substrate.add_node("Concept", {
            "external_field": float(coeffs[m] * mode_field_scale),
            "identity_field": 0.0, "state": 0.0})
        substrate.add_edge(mt, "has_concept", c, {})
        mode_concepts.append(c)
    # incidence edges (bidirectional causal_influence, weight = loading, OR the
    # fitted incidence W_inc[mode, neuron] when `incidence_override` is given
    # (block 323 lever 1 — the incidence fit to reproduce the mode reading)).
    for mi, m in enumerate(dom):
        for ni in range(len(neuron_idx)):
            if incidence_override is not None:
                w = float(incidence_override[m, ni] * incidence_scale)
            else:
                w = float(M[m, ni] * incidence_scale)
            if w == 0.0:
                continue
            substrate.add_edge(mode_concepts[mi], "causal_influence",
                               neuron_concepts[ni], {"weight": w})
            substrate.add_edge(neuron_concepts[ni], "causal_influence",
                               mode_concepts[mi], {"weight": w})
    return mt, neuron_concepts, mode_concepts, dom


def read_mode_nodes(bp_result, mode_concepts):
    """Read the mode-aperture state DIRECTLY off the mode nodes' settled state
    (no projection) — the incidence-map reading. Returns state_hat [n_modes] in
    {-1,+1} (0 mapped to +1 as the degenerate tie)."""
    fs = bp_result["final_state"]
    out = []
    for c in mode_concepts:
        cid = c.value if hasattr(c, "value") else int(c)
        s = float(fs.get(cid, 0.0))
        out.append(1.0 if s >= 0 else -1.0)
    return np.asarray(out, dtype=np.float32)


def export_chain_structure(model, train_ids, heldout_ids, out_path, *,
                           layers, k=32, ridge=1.0, all_positions=True):
    """Block 325: export the mode coefficients across a CHAIN of layers (a list
    of layer indices, e.g. [10,11,12,13,14]) for every train + held-out query,
    so per-hop transports T_i: coeffs_{L_i} -> coeffs_{L_{i+1}} can be fit and
    the chain settled as one graph. Writes tr_c[layer], ho_c[layer] as a stacked
    array [n_layers, N, k]."""
    from . import llm_structure_recovery as lsr
    R = lsr.fit_mode_router(model, train_ids, k=k, ridge=ridge,
                            all_positions=all_positions)
    layers = list(layers)

    def coeffs_at(ids, L):
        xg, act = lsr._ffn_io(model, ids)[L]
        return ((act - R.mean[L]) @ R.modes[L].T).astype(np.float32)

    tr_c = np.stack([np.stack([coeffs_at(ids, L) for ids in train_ids])
                     for L in layers])          # [n_layers, N_train, k]
    ho_c = np.stack([np.stack([coeffs_at(ids, L) for ids in heldout_ids])
                     for L in layers])          # [n_layers, N_ho, k]
    np.savez(out_path,
             tr_c=tr_c, ho_c=ho_c,
             layers=np.asarray(layers, dtype=np.int64))
    return out_path


def build_chain_factor_graph(substrate, seed_paths, transports, coeffs0, *,
                             n_modes=8, temperature=1.0, field_scale=1.0,
                             transport_scale=1.0, discrete_mode="3state"):
    """Block 325: the MULTI-HOP transport chain as ONE substrate factor graph.
    A column of `n_modes` mode-nodes per layer in the chain; the FIRST layer's
    nodes carry the known input (external_field = coeffs0[m]); every deeper
    layer's nodes have NO self-field and are driven only through the transport
    edges. `transports` is a list of per-hop maps T_i [k, k] (hop i couples
    layer i's nodes to layer i+1's). Edges are bidirectional (undirected Ising).
    Returns (mt, layer_nodes) where layer_nodes[i] is the list of that layer's
    mode-node concepts (mode ids 0..n_modes-1)."""
    import json
    from substrate.seed_loader import engine_rules_only
    for path in seed_paths:
        substrate.load_seed_manifest(engine_rules_only(json.load(open(path))))
    n_layers = len(transports) + 1
    mt = substrate.add_node("Microtheory",
                            {"temperature": float(temperature),
                             "discrete_mode": discrete_mode})
    layer_nodes = []
    for li in range(n_layers):
        nodes = []
        for m in range(n_modes):
            fld = float(coeffs0[m] * field_scale) if li == 0 else 0.0
            c = substrate.add_node("Concept", {
                "external_field": fld, "identity_field": 0.0, "state": 0.0})
            substrate.add_edge(mt, "has_concept", c, {})
            nodes.append(c)
        layer_nodes.append(nodes)
    for hop, T in enumerate(transports):
        src, dst = layer_nodes[hop], layer_nodes[hop + 1]
        for m1 in range(n_modes):
            for m0 in range(n_modes):
                w = float(T[m1, m0] * transport_scale)
                if w == 0.0:
                    continue
                substrate.add_edge(src[m0], "causal_influence", dst[m1],
                                   {"weight": w})
                substrate.add_edge(dst[m1], "causal_influence", src[m0],
                                   {"weight": w})
    return mt, layer_nodes


def export_transport_structure(model, train_ids, heldout_ids, out_path, *,
                               layer, k=32, ridge=1.0, all_positions=True):
    """Block 324: export the BETWEEN-LAYER transport structure for adjacent
    layers (layer, layer+1). Fits a mode router (all layers) once and writes,
    for L and L+1: modes, mean, Wc; and per-query (train + held-out) the TRUE
    mode coefficients at BOTH layers. The transport map T: coeffs_L ->
    coeffs_{L+1} is fit downstream (`fit_transport`) on the train coefficients.
    This is the recovered TRANSPORT incidence — how the mode configuration at L
    maps to the mode configuration at L+1, the between-layer aperture."""
    from . import llm_structure_recovery as lsr
    R = lsr.fit_mode_router(model, train_ids, k=k, ridge=ridge,
                            all_positions=all_positions)
    L0, L1 = layer, layer + 1

    def coeffs_at(ids, L):
        xg, act = lsr._ffn_io(model, ids)[L]
        return ((act - R.mean[L]) @ R.modes[L].T).astype(np.float32)

    tr_c0 = np.stack([coeffs_at(ids, L0) for ids in train_ids])
    tr_c1 = np.stack([coeffs_at(ids, L1) for ids in train_ids])
    ho_c0 = np.stack([coeffs_at(ids, L0) for ids in heldout_ids])
    ho_c1 = np.stack([coeffs_at(ids, L1) for ids in heldout_ids])
    np.savez(out_path,
             modes_L0=R.modes[L0].astype(np.float32),
             modes_L1=R.modes[L1].astype(np.float32),
             mean_L0=R.mean[L0].astype(np.float32),
             mean_L1=R.mean[L1].astype(np.float32),
             Wc_L0=R.Wc[L0].astype(np.float32),
             Wc_L1=R.Wc[L1].astype(np.float32),
             tr_c0=tr_c0, tr_c1=tr_c1, ho_c0=ho_c0, ho_c1=ho_c1,
             layer=np.int64(L0))
    return out_path


def fit_transport(tr_c0, tr_c1, *, ridge=1.0):
    """Fit the between-layer TRANSPORT map T: coeffs_L -> coeffs_{L+1} by ridge
    regression on train coefficients. T is the recovered transport incidence.
    Returns T [k1, k0] (coeffs_L1 ≈ T @ coeffs_L0)."""
    C0 = np.asarray(tr_c0, dtype=np.float32)          # [N, k0]
    C1 = np.asarray(tr_c1, dtype=np.float32)          # [N, k1]
    k0 = C0.shape[1]
    A = C0.T @ C0 + ridge * np.eye(k0, dtype=np.float32)
    T = np.linalg.solve(A, C0.T @ C1).T.astype(np.float32)   # [k1, k0]
    return T


def build_transport_factor_graph(substrate, seed_paths, T, coeffs0, *,
                                  n_modes0=8, n_modes1=8, temperature=1.0,
                                  field_scale=1.0, transport_scale=1.0,
                                  discrete_mode="3state", bidirectional=False):
    """Block 324: the BETWEEN-LAYER TRANSPORT aperture as a bipartite factor
    graph on the substrate. L-mode-nodes carry the KNOWN input configuration
    (external_field = coeffs0[m], the mode config at layer L); L+1-mode-nodes
    have NO self-field (state 0) and must be driven ONLY through the transport
    edges, weight T[m1, m0] (the recovered transport incidence). The settled
    L+1-mode-node states are the transported mode reading — if they match the
    true layer-L+1 mode config, the between-layer transition is aperture-
    covariant on the substrate's own message-passing.

    `n_modes0/1` = how many dominant L / L+1 mode-nodes to instantiate (by
    |coeffs0| for L; the top L+1 rows of T's targets). `T` MUST be the full
    k×k transport (indexed by mode id), since `dom0` holds mode ids into the
    original coefficient vector. Returns
    (mt, nodes_L0, nodes_L1, dom0, dom1)."""
    import json
    from substrate.seed_loader import engine_rules_only
    for path in seed_paths:
        substrate.load_seed_manifest(engine_rules_only(json.load(open(path))))
    dom0 = np.argsort(-np.abs(coeffs0))[:n_modes0]
    dom1 = np.arange(n_modes1)                          # first n_modes1 L+1 modes
    mt = substrate.add_node("Microtheory",
                            {"temperature": float(temperature),
                             "discrete_mode": discrete_mode})
    nodes_L0 = []
    for m in dom0:
        c = substrate.add_node("Concept", {
            "external_field": float(coeffs0[m] * field_scale),
            "identity_field": 0.0, "state": 0.0})
        substrate.add_edge(mt, "has_concept", c, {})
        nodes_L0.append(c)
    nodes_L1 = []
    for _ in dom1:
        c = substrate.add_node("Concept", {
            "external_field": 0.0, "identity_field": 0.0, "state": 0.0})
        substrate.add_edge(mt, "has_concept", c, {})
        nodes_L1.append(c)
    # transport edges: L0-mode m0 -> L1-mode m1 with weight T[m1, m0]
    for i1, m1 in enumerate(dom1):
        for i0, m0 in enumerate(dom0):
            w = float(T[m1, m0] * transport_scale)
            if w == 0.0:
                continue
            substrate.add_edge(nodes_L0[i0], "causal_influence",
                               nodes_L1[i1], {"weight": w})
            if bidirectional:
                substrate.add_edge(nodes_L1[i1], "causal_influence",
                                   nodes_L0[i0], {"weight": w})
    return mt, nodes_L0, nodes_L1, dom0, dom1


def read_transport_modes(bp_result, nodes_L1):
    """Read the settled L+1 mode-node states (the transported reading). Returns
    state_hat [n_modes1] in {-1,+1}."""
    fs = bp_result["final_state"]
    out = []
    for c in nodes_L1:
        cid = c.value if hasattr(c, "value") else int(c)
        s = float(fs.get(cid, 0.0))
        out.append(1.0 if s >= 0 else -1.0)
    return np.asarray(out, dtype=np.float32)


def fit_incidence(modes, mean, Wc, train_x, neuron_idx, *, n_modes=None,
                  ridge=1.0, neuron_field_scale=1.0):
    """Block 323 lever 1: FIT the incidence weights so the mode-node settle
    REPRODUCES the mode reading, instead of taking raw loadings `modes[m,i]`.

    The mode-node (self-field 0) settles by the sign of the message it receives
    from its neurons: sign(Σ_i W_inc[m,i]·s_i), where s_i is neuron i's settled
    state (≈ sign(field_i) in the field-driven regime). We fit W_inc[m,·] by
    ridge regression on TRAIN so that Σ_i W_inc[m,i]·s_i^(train) matches the
    true mode coefficient coeffs[m]^(train) — a per-mode linear read-out from
    the neuron states to the mode value. Frozen after fit; still a RECOVERED
    incidence (learned from train activations, never held-out).

    Returns W_inc [k, N] to hand to `build_mode_neuron_factor_graph` via
    `incidence_override`."""
    if n_modes is None:
        n_modes = modes.shape[0]
    N = len(neuron_idx)
    # per-train-query neuron states (sign of the modes' predicted drive) and
    # true mode coefficients
    S = []      # [T, N] neuron states
    C = []      # [T, k] true coeffs
    for x in train_x:
        coeffs = Wc @ x
        M = modes[:, neuron_idx]                     # [k, N]
        field = coeffs @ M                           # [N] predicted drive
        S.append(np.where(field * neuron_field_scale >= 0, 1.0, -1.0))
        C.append(coeffs)
    S = np.asarray(S, dtype=np.float32)              # [T, N]
    C = np.asarray(C, dtype=np.float32)              # [T, k]
    # ridge: neuron states -> mode coefficient, per mode (shared design matrix)
    A = S.T @ S + ridge * np.eye(N, dtype=np.float32)
    W = np.linalg.solve(A, S.T @ C).T.astype(np.float32)   # [k, N]
    return W




def read_back_modes(modes, neuron_idx, settled_state):
    """Read the settled NEURON-aperture state back UP to the mode aperture:
    project the settled state onto each mode (restricted to the refined
    neurons) — ĉ_m = Σ_i modes[m, idx_i]·s_i — and take sign. Returns
    (coeff_hat [k], state_hat [k] in {-1,+1})."""
    M = modes[:, neuron_idx]                           # [k, N]
    s = np.asarray([settled_state[i] for i in range(len(neuron_idx))],
                   dtype=np.float32)
    coeff_hat = (M @ s).astype(np.float32)             # [k]
    state_hat = np.where(coeff_hat >= 0, 1.0, -1.0).astype(np.float32)
    return coeff_hat, state_hat


# ---------------------------------------------------------------------------
# REFINE + PROPAGATE side (substrate / tree python3 with substrate_rs).
# ---------------------------------------------------------------------------

def build_ising_refinement(substrate, seed_paths, field, J, *,
                           temperature=1.0, field_scale=1.0, j_scale=1.0,
                           discrete_mode="3state"):
    """Build the CAN substrate Ising graph for one mode-refinement: a
    Microtheory with N Concept nodes (external_field = field_i) coupled by
    causal_influence edges (weight = J_ij). Returns (mt, [concept NodeIDs in
    neuron order]). Builds TO the protected substrate interface; mints no new
    types. Runs in tree python3 (substrate_rs)."""
    import json
    from substrate.seed_loader import engine_rules_only
    for path in seed_paths:
        substrate.load_seed_manifest(engine_rules_only(json.load(open(path))))
    mt = substrate.add_node("Microtheory",
                            {"temperature": float(temperature),
                             "discrete_mode": discrete_mode})
    N = len(field)
    concepts = []
    for i in range(N):
        c = substrate.add_node("Concept", {
            "external_field": float(field[i] * field_scale),
            "identity_field": 0.0,
            "state": 0.0,
        })
        substrate.add_edge(mt, "has_concept", c, {})
        concepts.append(c)
    for i in range(N):
        for jj in range(N):
            if i == jj:
                continue
            w = float(J[i, jj] * j_scale)
            if w == 0.0:
                continue
            substrate.add_edge(concepts[i], "causal_influence", concepts[jj],
                               {"weight": w})
    return mt, concepts


def settled_state_array(bp_result, concepts):
    """Map run_loopy_bp's {node_id -> state} onto a neuron-ordered dict
    {position -> state} using the concept NodeID order."""
    fs = bp_result["final_state"]
    out = {}
    for pos, c in enumerate(concepts):
        cid = c.value if hasattr(c, "value") else int(c)
        out[pos] = float(fs.get(cid, 0.0))
    return out
