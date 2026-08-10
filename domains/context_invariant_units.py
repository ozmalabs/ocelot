"""context_invariant_units — the agent COMPOSES context (coarticulation)
invariance as a graph Term-tree, forward, from its OWN coarticulation science +
the Kaldi/Sphinx context-dependent-unit mine. Link-2 of the invariance chain
(speaker-invariant -> CONTEXT-invariant -> word chunks).

WHY this is the agent's to compose (not hand-engineered numpy), and WHY this
mechanism. The agent holds the science (seeds/.../speech_production_decomposition:
`coarticulation`): "articulators move continuously toward upcoming + away from
preceding targets, so any segment's acoustics depend on its NEIGHBOURS" — the
production-side CAUSE of the lack-of-invariance the perception side must overcome.
CMVN (link-1) removed the per-utterance speaker/channel CONSTANT; what is left
that still smears a phone's acoustics is the slow, neighbour-driven drift across
the segment — carryover from the preceding phone + anticipation of the following
one. That drift is a LOCAL (in time) baseline, NOT a global one.

THE MINE (mechanism, not code). Kaldi/Sphinx handle coarticulation with
CONTEXT-DEPENDENT units: triphones (a phone modelled jointly with its left+right
neighbour) + a phonetic decision TREE that CLUSTERS similar contexts so parameters
are shared (avoids fragmentation/sparsity). Two ideas: (1) a unit is defined by
its context; (2) cluster/share across SIMILAR contexts so you don't shatter into
too many rare units.

THE AGENT'S CHOICE OF MECHANISM (reasoned from the science + THIS pipeline's
constraint). The forward TP-trough chunker (domains/forward_segmentation) needs
STABLE, RECURRING units — its bigram transitional probabilities are only
meaningful if the same phone in different contexts maps to the SAME symbol. Naive
triphones do the OPPOSITE: they tag every phone by its neighbours, multiplying the
alphabet (|phones|^3) and making nearly every unit rare -> TP -> 1.0 everywhere ->
no trough structure (the chunker's documented degenerate-TP failure). So the agent
does NOT shatter into triphones. It takes the OTHER face of the mine — the
clustering/sharing idea pushed to its limit: collapse ALL contexts of a phone onto
ONE canonical realisation by REMOVING the neighbour effect. That is exactly the
CMVN move (subtract a constant baseline) applied over the CONTEXT axis instead of
the whole-utterance axis: subtract the LOCAL running context mean (a per-band mean
over each frame's temporal neighbour window). The neighbour-driven drift is the
local baseline; subtract it and a phone clusters the same regardless of what sits
beside it, while the unit alphabet stays SMALL (good for the chunker's TP).

THE COMPOSITION (a graph Term-tree, evaluated natively — no Python arithmetic).
The I/O boundary lays each frame s out with a `ctx_frame` edge to every frame in
its local temporal window (s itself + the +-w neighbours). The agent's Term then,
per band b, subtracts the window mean from s's value — the identical shape as
cmvn_band_term, but aggregating over `ctx_frame` (a LOCAL neighbour set) rather
than `has_stat_frame` (the WHOLE utterance):

    ctxmu_b(s) = ( Sum_{g in ctx(s)} band_b(g) ) / Count(ctx(s))
    ctxnorm_b(s) = band_b(s) - ctxmu_b(s)

Primitives used (ALL already owned): Sum, Count, Div, Minus, Attr, Var,
Neighbours. Same compose move as cmvn_band_term / order_n / the cue tilts — only
the aggregation edge (the context window) and its scope differ. Composed as
feature_kind=context_invariant Concepts carrying the Term-tree, the same authoring
act as compose_cmvn / compose_order_n_features. The Terms ride the L2/L5 JIT for
free (Term-trees), so no opt-in.

The window radius w is the one parameter. Mechanism first: a small fixed radius
(w=2 frames at ~50 fps ~= 80 ms, the coarticulatory span). If a genuine setpoint
is needed it becomes an L3 drive (setpoint = cross-context unit invariance);
the accept harness reports whether a constant suffices.

HONEST. Coarticulation is hard and context-norm is a blunt instrument: removing a
local mean also erases some genuine slow spectral identity, so it can HELP (units
stabilise across contexts) or HURT (the canonicalisation throws away the signal
the chunker needs). The accept harness (scripts/context_invariant_librispeech_
accept) measures raw vs CMVN vs CMVN+context on the forward chunker with numbers
and states which, with no tuning to force it. See [[ozma_speaker_normalization]] /
[[ozma_order_n_concepts]] / [[ozma_agent_writes_its_own_code]] / cmvn.py.
"""
from __future__ import annotations

from substrate_rs import Attr, Var, Sum, Count, Div, Minus, Neighbours


# The I/O boundary lays this edge: target frame s -> every frame in its local
# temporal context window (s + the +-w neighbours). The agent's Term aggregates
# the neighbour-driven (coarticulatory) baseline over it.
CTX_EDGE = "ctx_frame"


def _band_attr(node: "Var", b: int) -> Attr:
    return Attr(node, f"band{b}")


def context_norm_band_term(b: int):
    """The agent's composed CONTEXT-NORMALIZATION Term-tree for ONE band b.
    Evaluated with env {"s": target_frame_node}; returns band b's value at s with
    the local context (coarticulatory) baseline removed. Pure graph composition.

        ctxmu_b(s)   = (Sum_{g in ctx(s)} band_b(g)) / Count(ctx(s))
        ctxnorm_b(s) = band_b(s) - ctxmu_b(s)

    Same shape as cmvn_band_term but the aggregation runs over the LOCAL
    `ctx_frame` window (the neighbour effect), not the whole utterance."""
    ctx = Neighbours(Var("s"), CTX_EDGE)                 # s's local temporal window
    n = Count(ctx)
    mu = Div(a=Sum(source=ctx, var_name="g", value=_band_attr(Var("g"), b)),
             b=n)                                        # running local context mean
    return Minus(a=_band_attr(Var("s"), b), b=mu)        # remove the neighbour drift


def context_norm_terms(n_bands: int) -> list:
    """The full context-normalization transform: one composed Term per band."""
    return [context_norm_band_term(b) for b in range(n_bands)]


def compose_context_invariant(substrate, n_bands: int, window: int = 2) -> list:
    """The agent composes context-normalization and records each per-band Term as a
    Concept (feature_kind=context_invariant) carrying its Term-tree — the same
    authoring move as compose_cmvn / compose_order_n_features. `window` is the
    context radius (frames each side) the I/O boundary uses to lay ctx_frame edges.
    Returns [(concept_id, name)]. Idempotent."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind")
                == "context_invariant"}
    created = []
    for b, term in enumerate(context_norm_terms(n_bands)):
        name = f"ctxnorm_band{b}"
        if name in existing:
            continue
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "context_invariant", "band": b,
            "window": int(window), "predicate": term.to_dict(),
            "origin": "phonology", "composed_by": "agent",
            "mechanism": "context_normalisation",
            "science": "coarticulation = a phone's acoustics depend on its "
                       "neighbours (carryover+anticipation) -> a LOCAL drifting "
                       "baseline; subtract the running local context mean -> the "
                       "phone clusters the same regardless of context, alphabet "
                       "stays small (vs triphones, which fragment the alphabet "
                       "and break the chunker's TP)"})
        created.append((c, name))
    return created


# ---------------------------------------------------------------------------
# I/O boundary: apply the agent's composed context-norm Term to a frames x bands
# matrix. ONLY Python here, a mechanical translator (matrix -> frame graph with a
# local context window per frame -> evaluate the agent's Term -> matrix). No
# decisions over graph state — it runs the agent's program on the native evaluator.
# Mirrors cmvn.apply_cmvn.
# ---------------------------------------------------------------------------

def apply_context_norm(M, window: int = 2, substrate=None):
    """Apply the agent's composed context-normalization Term-tree to one
    utterance's frames x bands matrix; return the normalized matrix (same shape).

    Mechanical I/O translation: lay each row out as a Frame node, then for every
    frame s add a `ctx_frame` edge to each frame within +-window (s included).
    Evaluate the agent's per-band context-norm Term natively for every (frame,
    band). The numbers come out of the substrate evaluator, not numpy."""
    import numpy as np
    from substrate_rs import Substrate

    M = np.asarray(M, dtype=np.float64)
    n_frames, n_bands = M.shape
    s = substrate if substrate is not None else Substrate()

    frame_ids = []
    for r in range(n_frames):
        attrs = {f"band{b}": float(M[r, b]) for b in range(n_bands)}
        frame_ids.append(s.add_node("Frame", attrs))
    # Lay the local temporal context window per frame (mechanical, signal-derived).
    for r, f in enumerate(frame_ids):
        lo = max(0, r - window)
        hi = min(n_frames - 1, r + window)
        for k in range(lo, hi + 1):
            s.add_edge_unchecked(f, CTX_EDGE, frame_ids[k])

    terms = context_norm_terms(n_bands)
    out = np.empty_like(M)
    for r, f in enumerate(frame_ids):
        env = {"s": f}
        for b in range(n_bands):
            out[r, b] = float(s.evaluate(terms[b], env))
    return out.astype(np.float32)


__all__ = ["CTX_EDGE", "context_norm_band_term", "context_norm_terms",
           "compose_context_invariant", "apply_context_norm"]
