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
    np.savez(out_path,
             modes=modes.astype(np.float32),
             mean=mean.astype(np.float32),
             Wc=Wc.astype(np.float32),
             ho_x=np.stack(ho_x),
             ho_coef=np.stack(ho_coef),
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
                                   discrete_mode="3state"):
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
    # incidence edges (bidirectional causal_influence, weight = loading)
    for mi, m in enumerate(dom):
        for ni in range(len(neuron_idx)):
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
