"""coarticulation_predict_remove — the agent FORWARD-BUILDS a richer coarticulation
mechanism for the RESIDUAL the linear flat-mean context-norm could not isolate.
Link-2b of the invariance chain (CMVN -> context-norm -> THIS).

WHY a richer mechanism is needed (the agent's OWN yardstick, not an outside call).
After the agent cut in the linear context-norm (subtract the flat local window mean
per band), its labels-free perception_self_assessment FLIPPED: on the raw quantized
units predict_over_freq fell 5.30 -> 1.26 (now AT the floor) and compress_ratio rose
0.708 -> 0.859 (now OVER the ceiling), so its flagging RULE re-set frontier =
'perception'. And the cross-context invariance RATIO moved the WRONG way
(0.678 -> 0.728). Diagnosis: the flat window MEAN is a DC term — subtracting it
strips the frame's own slow spectral IDENTITY (the band level the chunker's codebook
clusters on) along with the neighbour drift. It over-flattens. So it raised word
PURITY (neighbouring frames collapse together -> cleaner chunk spans) while
DEGRADING the unit stream's own predictability/compressibility and NOT actually
removing the directional coarticulation it targeted.

THE SCIENCE (the agent holds it: speech_production_decomposition.coarticulation).
"Articulators move continuously TOWARD upcoming + AWAY FROM preceding targets, so a
segment's acoustics depend on its NEIGHBOURS." The key word is DIRECTIONAL: the
neighbour influence is a DRIFT across the segment — carryover from the preceding
phone + anticipation of the following one — i.e. a roughly LINEAR ramp in time, not
a flat offset. Flat-mean subtraction removes the ramp's average (a DC term) but
leaves the ramp's SLOPE (the actual coarticulatory drift) AND destroys the frame's
own level. The right move is the inverse: remove the neighbour-PREDICTABLE drift
(the slope-driven trend) and KEEP the frame's own level.

THE AGENT'S MECHANISM — PREDICT-AND-REMOVE (non-linear in the sense that it models
the neighbour structure, not a flat constant). For target frame s with a local
window, the neighbours PREDICT a value at s by the LOCAL LINEAR TREND: the carryover
(left-context mean) ramping toward the anticipation (right-context mean). The
component of band_b(s) the neighbours predict is the trend's value AT s; what they
CANNOT predict is the residual = band_b(s) - that prediction. Subtract ONLY the
neighbour-predicted DRIFT (the deviation of the trend from the frame's own level),
not the frame's level itself:

    leftmu_b(s)  = mean of band_b over the LEFT  context (carryover term)
    rightmu_b(s) = mean of band_b over the RIGHT context (anticipation term)
    drift_b(s)   = (leftmu_b + rightmu_b)/2 - band_b(s)      # what the neighbours
                                                             # pull the frame toward,
                                                             # relative to the frame
    predremove_b(s) = band_b(s) + drift_b(s) * (-(-1))  ... see below

The agent's actual composed Term (clean, all owned primitives):

    nb_b(s)   = ( leftmu_b(s) + rightmu_b(s) ) / 2     # the neighbours' linear
                                                       # prediction at s (carryover
                                                       # + anticipation, averaged)
    out_b(s)  = band_b(s) - k * ( nb_b(s) - band_b(s) )

i.e. PUSH the frame AWAY from where its neighbours pull it, by k times the gap. With
k=0 it is the identity (raw CMVN units, structure preserved); as k grows it
SHARPENS the frame against its coarticulatory drift (un-smears it toward its own
target) WITHOUT removing the frame's DC level — the opposite of flat-mean, which
removes the level and keeps the drift. This SUBTRACTS the neighbour-predictable
component while PRESERVING (indeed restoring) the frame's intrinsic identity, so it
should move the cross-context invariance ratio the RIGHT way WITHOUT flattening the
unit stream (should NOT flip the yardstick to 'perception').

Equivalently out_b(s) = (1+k)*band_b(s) - k*nb_b(s): a high-pass / unsharp-mask over
the temporal context — the deconvolution view of removing a linear smear. (Unsharp
masking is exactly "subtract a blurred copy to undo a blur"; coarticulation IS a
temporal blur of the articulatory target, so the inverse is this high-pass.)

THE COMPOSITION (a graph Term-tree, native eval — no Python arithmetic). The I/O
boundary lays two edges per frame s: `lctx_frame` -> the w left neighbours (s
included), `rctx_frame` -> the w right neighbours (s included). The agent's Term:

    leftmu  = Sum_{g in lctx(s)} band_b(g) / Count(lctx(s))
    rightmu = Sum_{h in rctx(s)} band_b(h) / Count(rctx(s))
    nb      = (leftmu + rightmu) / 2
    out     = band_b(s) - k * (nb - band_b(s))

Primitives: Sum, Count, Div, Minus, Plus, Times, Lit, Attr, Var, Neighbours — ALL
already owned. Same compose move as cmvn_band_term / context_norm_band_term, only
split into left/right context (the directional carryover/anticipation the science
names) plus the high-pass gain.

THE ONE PARAMETER k (the high-pass gain). Mechanism first: a small fixed k. The
accept harness sweeps k ONLY to REPORT the curve honestly (does ANY k move the
invariance ratio the right way while holding the yardstick?) — NOT to tune to a
target. If the curve shows a genuine setpoint (a k where invariance improves and the
yardstick holds), that k is the candidate; if it is sharply sensitive it is flagged
as an L3-drive candidate (setpoint = cross-context invariance under the yardstick
constraint). The linear context-norm needed no drive; whether this richer one does
is an empirical question the harness answers.

HONEST. This is still a LINEAR-trend neighbour model (carryover+anticipation as a
ramp); true coarticulation is non-linear and context-DEPENDENT (the other half of
the Kaldi mine — clustered triphones — which fragments the chunker's alphabet, so
the agent deliberately does NOT take it here). The claim is only that
predict-and-remove subtracts the DIRECTIONAL, neighbour-PREDICTABLE component while
preserving the frame's own structure — a strictly better-shaped instrument than
flat-mean for the residual. The accept harness states whether it actually moves the
ratio + holds the yardstick, or whether it too plateaus. No tuning to force it.
See [[ozma_order_n_concepts]] (tilt/drift science) / [[ozma_agent_writes_its_own_code]]
/ cmvn.py / context_invariant_units.py.
"""
from __future__ import annotations

from substrate_rs import (Attr, Var, Sum, Count, Div, Minus, Plus, Times, Lit,
                          Neighbours)


# The I/O boundary lays these two DIRECTIONAL edges per target frame s:
#   LCTX_EDGE -> s + its w LEFT neighbours  (the carryover / preceding context)
#   RCTX_EDGE -> s + its w RIGHT neighbours (the anticipation / following context)
# The split is the science: carryover and anticipation are the two directional
# coarticulation terms; averaging their means is the linear neighbour prediction.
LCTX_EDGE = "lctx_frame"
RCTX_EDGE = "rctx_frame"


def _band_attr(node: "Var", b: int) -> Attr:
    return Attr(node, f"band{b}")


def _ctx_mean(edge: str, var_inner: str, b: int):
    """mean of band b over a directional context window (left or right)."""
    ctx = Neighbours(Var("s"), edge)
    return Div(a=Sum(source=ctx, var_name=var_inner,
                     value=_band_attr(Var(var_inner), b)),
               b=Count(ctx))


def predict_remove_band_term(b: int, k: float = 0.5):
    """The agent's composed PREDICT-AND-REMOVE Term-tree for ONE band b.
    Evaluated with env {"s": target_frame_node}; returns band b at s with the
    neighbour-predictable coarticulatory drift removed, the frame's own level kept.

        leftmu  = mean band_b over LEFT  context   (carryover)
        rightmu = mean band_b over RIGHT context   (anticipation)
        nb      = (leftmu + rightmu) / 2           (neighbours' linear prediction)
        out     = band_b(s) - k * (nb - band_b(s))

    k = 0 is the identity (CMVN units untouched); k > 0 high-passes the temporal
    context, un-smearing the frame against its coarticulatory drift while
    PRESERVING its DC identity (the opposite of flat-mean context-norm)."""
    leftmu = _ctx_mean(LCTX_EDGE, "g", b)
    rightmu = _ctx_mean(RCTX_EDGE, "h", b)
    nb = Div(a=Plus(items=(leftmu, rightmu)), b=Lit(2.0))   # linear prediction at s
    xs = _band_attr(Var("s"), b)
    drift = Minus(a=nb, b=xs)                               # where neighbours pull s
    return Minus(a=xs, b=Times(items=(Lit(float(k)), drift)))   # push s away from it


def predict_remove_terms(n_bands: int, k: float = 0.5) -> list:
    """The full predict-and-remove transform: one composed Term per band."""
    return [predict_remove_band_term(b, k=k) for b in range(n_bands)]


def compose_coarticulation_predict_remove(substrate, n_bands: int,
                                          k: float = 0.5,
                                          window: int = 2) -> list:
    """The agent composes predict-and-remove and records each per-band Term as a
    Concept (feature_kind=coarticulation_predict_remove) carrying its Term-tree —
    the same authoring move as compose_cmvn / compose_context_invariant.
    Returns [(concept_id, name)]. Idempotent."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind")
                == "coarticulation_predict_remove"}
    created = []
    for b, term in enumerate(predict_remove_terms(n_bands, k=k)):
        name = f"coartpr_band{b}"
        if name in existing:
            continue
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "coarticulation_predict_remove",
            "band": b, "k": float(k), "window": int(window),
            "predicate": term.to_dict(), "origin": "phonology",
            "composed_by": "agent", "mechanism": "predict_and_remove",
            "science": "coarticulation is a DIRECTIONAL drift (carryover from the "
                       "preceding phone + anticipation of the following one) = a "
                       "roughly linear ramp; model the neighbour-predicted value "
                       "(mean of left+right context) and PUSH the frame away from "
                       "it, removing the drift while PRESERVING the frame's own "
                       "level (unlike flat-mean context-norm, which removes the "
                       "level and keeps the drift)"})
        created.append((c, name))
    return created


# ---------------------------------------------------------------------------
# I/O boundary: apply the agent's composed predict-and-remove Term to a
# frames x bands matrix. ONLY Python here — a mechanical translator (matrix ->
# frame graph with directional left/right context windows -> evaluate the agent's
# Term -> matrix). No decisions over graph state. Mirrors apply_context_norm.
# ---------------------------------------------------------------------------

def apply_predict_remove(M, window: int = 2, k: float = 0.5, substrate=None):
    """Apply the agent's composed predict-and-remove Term-tree to one utterance's
    frames x bands matrix; return the transformed matrix (same shape).

    Mechanical I/O translation: lay each row out as a Frame node; for every frame s
    add a `lctx_frame` edge to s + its w LEFT neighbours and a `rctx_frame` edge to
    s + its w RIGHT neighbours. Evaluate the agent's per-band Term natively for
    every (frame, band). The numbers come out of the substrate evaluator, not
    numpy."""
    import numpy as np
    from substrate_rs import Substrate

    M = np.asarray(M, dtype=np.float64)
    n_frames, n_bands = M.shape
    s = substrate if substrate is not None else Substrate()

    frame_ids = []
    for r in range(n_frames):
        attrs = {f"band{b}": float(M[r, b]) for b in range(n_bands)}
        frame_ids.append(s.add_node("Frame", attrs))
    # Lay the DIRECTIONAL context windows (mechanical, signal-derived).
    for r, f in enumerate(frame_ids):
        for kk in range(max(0, r - window), r + 1):          # s + left neighbours
            s.add_edge_unchecked(f, LCTX_EDGE, frame_ids[kk])
        for kk in range(r, min(n_frames, r + window + 1)):    # s + right neighbours
            s.add_edge_unchecked(f, RCTX_EDGE, frame_ids[kk])

    terms = predict_remove_terms(n_bands, k=k)
    out = np.empty_like(M)
    for r, f in enumerate(frame_ids):
        env = {"s": f}
        for b in range(n_bands):
            out[r, b] = float(s.evaluate(terms[b], env))
    return out.astype(np.float32)


__all__ = ["LCTX_EDGE", "RCTX_EDGE", "predict_remove_band_term",
           "predict_remove_terms", "compose_coarticulation_predict_remove",
           "apply_predict_remove"]
