"""Block 329000 — extract an LLM's PROCESS as CAN graph dynamics.

Tier 3 of the extraction direction (after knowledge 327, concept 328). A PROCESS
is a PROCEDURE the LLM runs — a transformation of an input configuration into an
output configuration — extracted as graph DYNAMICS (a transport operator over
substrate nodes, connecting to the transport arc 324-326) and applied to inputs
it never saw. The bar rises from held-out TRANSFER (328) to held-out
APPLICATION: extract the process from context A, apply it to context-B inputs it
never saw, and check the substrate produces the correct TRANSFORMED output by
the process's DYNAMICS, not stored input->output pairs.

Process studied: `negate` — carry an affirmation's representation to its
negation. Two parts, both fit on A and applied to held-out B:
  TRANSPORT operator N — a linear map (fit on A affirmation->negation vector
    pairs) that IS the process in the LLM's representation.
  VALENCE probe p — a direction (fit on A) that reads whether a representation
    is "affirmed" (+) or "negated" (-). The APPLICATION readout: apply N to a
    held-out B affirmation, does the output read as NEGATED under p?

On the substrate the process runs as a TRANSPORT factor graph (block 324/325):
input mode-nodes clamped by the affirmation config, transport edges = N,
settle, read the output config. No new grammar — the transport is causal_influence
edges over existing Concept nodes (read-only, built-to). No LLM at query time.

CONSTRAINT: this module installs NO new rewrite rules / Gamma productions — a
process is expressed as a transport-operator + BP settle over the existing
Concept / causal_influence types, keeping the protected seed grammar untouched.
torch/model appear only at fit time (offline).
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# EXTRACT (model side): contextual statement vectors + the process operator N.
# ---------------------------------------------------------------------------

def statement_vectors(model, tokenizer, statements, *, layer=12):
    """Contextual vector per statement = the last-token post-attention-norm
    input at `layer` (the representation the rest of the arc showed is
    meaningful). Returns {statement: vec[d]}."""
    from . import llm_structure_recovery as lsr
    out = {}
    for s in statements:
        ids = tokenizer(s, return_tensors="pt")["input_ids"][0].tolist()
        xgs = lsr._ffn_io_all(model, ids)
        out[s] = xgs[layer][-1].astype(np.float32)
    return out


def fit_process_operator(vecs, pairs_A, *, ridge=1.0):
    """Fit the process transport N on context-A (input, output) statement pairs:
    N maps the input representation to the output representation (ridge). N is
    the extracted PROCESS — frozen, applied to unseen B inputs. Returns N [d,d]."""
    X = np.stack([vecs[i] for i, o in pairs_A if i in vecs and o in vecs])
    Y = np.stack([vecs[o] for i, o in pairs_A if i in vecs and o in vecs])
    d = X.shape[1]
    A = X.T @ X + ridge * np.eye(d, dtype=np.float32)
    N = np.linalg.solve(A, X.T @ Y).T.astype(np.float32)
    return N


def fit_valence_probe(vecs, affirmed, negated):
    """Fit a linear valence direction p (fit on A) that reads a representation
    as affirmed (+) vs negated (-): the difference of class means, normalised.
    Used to CHECK the process output (does N(affirmation) read as negated?).
    Returns (p[d], threshold)."""
    A = np.stack([vecs[w] for w in affirmed if w in vecs])
    Ng = np.stack([vecs[w] for w in negated if w in vecs])
    p = (A.mean(0) - Ng.mean(0)).astype(np.float32)
    p = p / (np.linalg.norm(p) + 1e-9)
    thresh = float(0.5 * (A @ p).mean() + 0.5 * (Ng @ p).mean())
    return p, thresh


def reads_negated(vec, p, thresh):
    """Under the valence probe, does `vec` read as NEGATED (below threshold)?"""
    return float(vec @ p) < thresh


# ---------------------------------------------------------------------------
# SUBSTRATE dynamics: run the process as a transport factor graph + settle.
# ---------------------------------------------------------------------------

def run_process_substrate(substrate, seed_paths, N, input_coeffs, *,
                          n_modes=8, temperature=1.0, transport_scale=1.0):
    """Run the extracted process on the substrate as a TRANSPORT settle (block
    324/325 mechanism, no new grammar): a column of input mode-nodes clamped by
    `input_coeffs`, a column of output mode-nodes (self-field 0) driven only
    through transport edges = N, settle on the substrate's own BP, return the
    output mode-node states [n_modes]. This is the process executed as graph
    dynamics — reused from the transport arc so `build_chain_factor_graph` is
    the single native mechanism."""
    from . import llm_native_graph as lng
    from domains.can_native_bp import run_loopy_bp
    s = substrate
    mt, layer_nodes = lng.build_chain_factor_graph(
        s, seed_paths, [N], input_coeffs, n_modes=n_modes,
        temperature=temperature, field_scale=1.0,
        transport_scale=transport_scale, discrete_mode="3state")
    bp = run_loopy_bp(s, mt, combine="max_product")
    return lng.read_transport_modes(bp, layer_nodes[1])
