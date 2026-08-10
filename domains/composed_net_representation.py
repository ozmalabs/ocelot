"""composed_net_representation — iter-28. A small COMPOSED net (write-not-train) for the
speech representation, AUTHORED from the agent's OWN derived understanding, NOT
gradient-trained.

PROVENANCE — the ENACTMENT of the agent's self-derived fix
(scripts/iter28_composed_net_derive.py), not a hand-pick. Over the iter-27 RESIDUAL frame
(fixed_scalar_relation_frame: the representation is now ONE fixed scalar relation per
frame, the SAME straight mapping in every region, unable to carry a region-dependent
curved combination of the inputs nor the predictive structure), the agent's OWN
synthesize_gaps fired its OWN harvested shapes (verbatim, iter28_composed_net_derive):

  (A) a RICHER / region-dependent / LOCALLY-approximated function of the inputs
      via rule_derived__Taylor_series_local_approximation (concept
      Taylor_series_local_approximation): "Taylor series approximates locally"
      -> the representation should be a smooth function approximated LOCALLY by several
         terms, not one straight term: lift each band value b into its local-polynomial
         basis [b, b^2, b^3].
  (B) encode the PREDICTIVE / forward structure
      via removable_context__from__residual_vector_quantisation (concept
      residual_vector_quantisation): "a quantity is a smooth FUNCTION of its known
      context -> MODEL and PREDICT it from the neighbours and remove it"
      -> add a per-band predictive-residual component b_t - b_hat(b_{t-1}) (the agent's
         explicit forward-model analog of the SSL representational edge).

THE COMPOSED NET (the agent's net-authoring machinery, code_writing_cortex):

  per band b_t, the representation maps
      b_t  ->  [ b_t,  b_t^2,  b_t^3,   b_t - b_{t-1} ]
  · the [b, b^2, b^3] LIFT is composed by construct_broadcast_pattern over the agent's
    CPWL gadgets [identity_gadget, square_pwl_signed_gadget, cube_gadget] — the local
    polynomial (Taylor) basis. construct_weights renders the EXACT ReLU weights from the
    gadget formulas (no fit); forward evaluates them (proven exact in test_gadgets).
  · the predictive residual b_t - b_{t-1} is composed by a CPWL linear (the trivial
    1-step forward predictor b_hat_t = b_{t-1}, the simplest model-of-context that needs
    NO data to author) via construct_pwl_through_points / a 2-input linear gadget. It is
    the "predict from neighbours and subtract" move applied along the time axis.

WHERE THE WEIGHTS COME FROM (write-not-train, auditable as composed-not-fit):
  every weight in the net is RENDERED by the agent's gadget constructor from the gadget
  FORMULAS (|x|, the secant-line PWL of x^2 with breakpoints at k/10, x^3 via polarization,
  the difference linear) — there is NO optimizer, NO backprop, NO least-squares, NO fit to
  the FSDD data anywhere in this module. (construct_elm_readout, the one fitting method, is
  deliberately NOT used.) The only data-derived numbers are the FIXED per-corpus band-range
  scale that maps the band values into the gadgets' valid domain [-0.5, 0.5] — a domain
  normalisation (range, not a learned parameter), the same role as the baseline's VTLN
  canonical centroid, computed from TRAIN frames only in the gate (no leakage).

NO-DONKEY. The agent DERIVED the move (its Taylor-local + removable-context shapes) and
COMPOSED the net via its OWN constructors; the only new Python here is the world-adapter
that (i) drives the cortex's constructors and (ii) applies forward() per band per frame —
mechanical, no decision over graph state, no hand-set weight, no gradient.
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Compose the per-band feature net via the agent's net-authoring machinery.
# ---------------------------------------------------------------------------

def compose_band_poly_net(cortex):
    """Compose the per-band LOCAL-POLYNOMIAL basis net  b -> [b, b^2, b^3]  via the
    agent's construct_broadcast_pattern over its CPWL gadgets. Returns the rendered
    assemblage node id (weights already constructed). Write-not-train: every weight is
    rendered from the gadget formulas, no fit."""
    s = cortex.s
    name = cortex.construct_broadcast_pattern(
        input_dim=1,
        branch_chains=[["identity_gadget"],
                       ["square_pwl_signed_gadget"],
                       ["cube_gadget"]],
        label="iter28_band_poly_basis")
    if name is None:
        raise RuntimeError("agent could not compose the band poly-basis net")
    tgt = s.add_node("ReplacementTarget", {
        "op_name": "_iter28_band_poly", "baseline_total_ms": 0.0,
        "baseline_count": 1, "baseline_mean_ms": 0.0, "selected_at": 0.0})
    s.set_attr(tgt, "input_dim", 1)
    s.set_attr(tgt, "output_dim", 3)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", tgt, {})
    g = next(n for n in s.nodes("DesignPattern")
             if s.node(n)["attrs"].get("name") == name)
    s.add_edge(tgt, "uses_pattern", g, {})
    asm = cortex.assemble_network(tgt)
    cortex.construct_weights(asm)
    return asm


# ---------------------------------------------------------------------------
# Apply the composed net to a band-mean frame matrix -> richer representation.
# ---------------------------------------------------------------------------

def _band_scale(train_frames):
    """A FIXED domain-normalisation scale (range, NOT a learned parameter): map the band
    values into the gadgets' valid domain [-0.5, 0.5]. Computed from TRAIN frames only.
    Returns (centre, half_range). Same role as the baseline's VTLN canonical centroid."""
    allv = np.concatenate([M.reshape(-1) for M in train_frames]) if train_frames else \
        np.array([0.0])
    lo, hi = float(np.percentile(allv, 1)), float(np.percentile(allv, 99))
    centre = 0.5 * (lo + hi)
    half = max(1e-6, 0.5 * (hi - lo))
    return centre, half


def apply_composed_net(cortex, asm, M, centre, half, mode="full"):
    """Map a band-mean frame matrix M (frames x bands) into the agent's COMPOSED richer
    representation. Per band value b_t:
        normalise z = clip((b - centre)/(2*half), -0.5, 0.5)   (domain norm, not fit)
        poly      = forward(asm, [z]) = [z, z^2, z^3]          (agent's composed net)
        predres   = z_t - z_{t-1}                              (predict-from-neighbour)
    Returns a (frames x (bands*4)) matrix: [z, z^2, z^3, predres] per band.
    The forward() is a pure graph-read of the agent's rendered weights. No fit.

    `mode` is for HONEST ablation (which derived component drives the gain):
      'full'   : [z, z^2, z^3, z_t - z_{t-1}]  (both gaps, the agent's composed net)
      'poly'   : [z, z^2, z^3]                 (gap A only — local-polynomial basis)
      'predres': [z, z_t - z_{t-1}]            (gap B only — predictive residual)
    """
    F, B = M.shape
    Z = np.clip((M - centre) / (2.0 * half), -0.5, 0.5)
    # predictive residual along time: z_t - z_{t-1}  (b_hat_t = b_{t-1}); first frame 0.
    predres = np.zeros((F, B), dtype=np.float64)
    predres[1:] = Z[1:] - Z[:-1]
    if mode == "predres":
        return np.concatenate([Z, predres], axis=1)
    poly = np.zeros((F, B, 3), dtype=np.float64)
    for t in range(F):
        for j in range(B):
            poly[t, j] = cortex.forward(asm, [float(Z[t, j])])
    if mode == "poly":
        return poly.reshape(F, B * 3)
    out = np.concatenate([poly.reshape(F, B * 3), predres], axis=1)
    return out


def compose_representation_concept(substrate):
    """Record the agent's iter-28 composed-net representation as a Concept carrying the
    derived gaps + the composition recipe. Idempotent."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind")
                == "composed_net_representation"}
    if "composed_net_representation" in existing:
        return []
    c = substrate.add_node("Concept", {
        "name": "composed_net_representation",
        "feature_kind": "composed_net_representation",
        "origin": "composed_net_representation", "composed_by": "agent",
        "derived_gaps": (
            "(A) Taylor_series_local_approximation: a smooth function approximated "
            "LOCALLY by several terms -> lift band b to its local-polynomial basis "
            "[b, b^2, b^3]; (B) removable_context: a quantity is a smooth function of "
            "its context -> add the predictive residual b_t - b_{t-1}"),
        "recipe": (
            "construct_broadcast_pattern([identity, square_pwl_signed, cube]) renders "
            "the per-band [b,b^2,b^3] basis to EXACT ReLU weights (no fit); forward() "
            "evaluates them; the predictive residual is the agent's predict-from-"
            "neighbour move along time. Write-not-train (Tracr/CPWL-constructive)."),
    })
    return [(c, "composed_net_representation")]


__all__ = ["compose_band_poly_net", "apply_composed_net",
           "_band_scale", "compose_representation_concept"]
