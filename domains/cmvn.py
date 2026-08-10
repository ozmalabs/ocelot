"""cmvn — the agent COMPOSES Cepstral Mean-Variance Normalization as a graph
Term-tree, from its OWN speaker_norm science + the DSL primitives it already owns.

WHY this is the agent's to compose (not hand-engineered numpy). The agent's
speaker_norm science says a speaker is a CONSTANT term on the feature axis: vocal-
tract length is a log-frequency shift, channel / loudness is a per-band offset, and
the long-term spectrum carries speaker + recording identity, NOT phonetic content.
SUBTRACT that constant term and the speaker is gone — exactly the move vtl_terms
makes for formants (F_i - mean(F1,F2,F3)). CMVN is that same subtraction applied
PER BAND OVER TIME: remove each band's per-utterance mean (the speaker/channel
offset), then divide by its per-utterance std (the speaker's dynamic-range term).
What's left is the speaker-invariant phonetic trajectory.

THE COMPOSITION (a graph Term-tree, evaluated natively — no Python arithmetic):
for an utterance node u with frame nodes f (edge `has_frame`), band attr `band{b}`,
and a target frame s:

    mu_b   = Sum_{f in frames} Attr(f, band_b)  /  Count(frames)
    var_b  = Sum_{f in frames} (Attr(f, band_b) - mu_b)^2  /  Count(frames)
    cmvn_b(s) = (Attr(s, band_b) - mu_b) / Sqrt(var_b + eps)

Primitives used (ALL already in the agent's DSL — NO new primitive needed): Sum,
Count, Div, Minus, Times (square = Times(d,d)), Sqrt, Plus, Lit, Attr, Var,
Neighbours. The agent checked: it has Sqrt, so it composes FULL CMVN (mean AND
variance), not mean-only. This is the same compose move as order_n_concepts
(recursive Minus over a dimension), the cue tilts (Plus/Minus over band attrs),
and speaker_norm's vtl_terms — one layer up, aggregating over the time dimension.

The aggregation runs over a frame SUBSET edge (`has_stat_frame`) so the stats can be
taken over voiced frames only (silence padding must not bias the mean) — exactly
what the numpy side-experiment did. Which frames are voiced is a MECHANICAL signal
gate set at the I/O boundary (energy threshold), not agent reasoning; the agent's
Term just sums over whatever frame set the boundary tagged.

Validated (scripts/cmvn_default_accept): FSDD leave-one-speaker-out DTW and the
LibriSpeech forward-chunker F1 match/exceed the invariant_units.py numpy side-
experiment, now driven by THIS composed Term in the default path. See
[[ozma_speaker_normalization]] / [[ozma_order_n_concepts]] / [[ozma_agent_writes_its_own_code]].
"""
from __future__ import annotations

from substrate_rs import (Attr, Var, Sum, Count, Div, Minus, Times, Sqrt,
                          Plus, Lit, Neighbours)


# Edge names the I/O boundary uses to lay an utterance out as a frame graph.
FRAME_EDGE = "has_frame"          # u -> every frame, in time order
STAT_EDGE = "has_stat_frame"      # u -> the frames the per-band stats average over
                                  #      (voiced frames; = has_frame if none gated)


def _band_attr(node: "Var", b: int) -> Attr:
    return Attr(node, f"band{b}")


def cmvn_band_term(b: int, eps: float = 1e-6, do_variance: bool = True):
    """The agent's composed CMVN Term-tree for ONE band b. Evaluated with env
    {"u": utterance_node, "s": target_frame_node}; returns the band's normalized
    value at frame s. Pure graph composition over the agent's own primitives.

    do_variance=False yields mean-only CMVN (the fallback the agent would emit if it
    lacked Sqrt — it does NOT, so the default is full mean+variance)."""
    stats = Neighbours(Var("u"), STAT_EDGE)               # the frames to average
    n = Count(stats)
    # mu_b = (Σ_f band_b(f)) / N
    mu = Div(a=Sum(source=stats, var_name="f", value=_band_attr(Var("f"), b)),
             b=n)
    centred = Minus(a=_band_attr(Var("s"), b), b=mu)       # x - mu_b  (mean removal)
    if not do_variance:
        return centred
    # var_b = (Σ_f (band_b(f) - mu_b)^2) / N   — square via Times(dev, dev)
    dev = Minus(a=_band_attr(Var("f"), b), b=mu)
    var = Div(a=Sum(source=stats, var_name="f", value=Times(items=(dev, dev))),
              b=n)
    # std_b + eps: eps OUTSIDE the sqrt (Kaldi/CMVN convention) so a flat band
    # (var->0) doesn't blow up the quotient — matches the numpy side-experiment.
    std = Plus(items=(Sqrt(arg=var), Lit(float(eps))))
    return Div(a=centred, b=std)                           # (x - mu_b) / (std_b+eps)


def cmvn_terms(n_bands: int, eps: float = 1e-6, do_variance: bool = True) -> list:
    """The full CMVN transform: one composed Term per band. Returns a list of
    n_bands Term objects, band 0..n_bands-1."""
    return [cmvn_band_term(b, eps=eps, do_variance=do_variance)
            for b in range(n_bands)]


def compose_cmvn(substrate, n_bands: int, eps: float = 1e-6,
                 do_variance: bool = True) -> list:
    """The agent composes CMVN and records each per-band Term as a Concept
    (feature_kind=cmvn) carrying its Term-tree — the same authoring move as
    compose_speaker_normalization / compose_order_n_features. Returns
    [(concept_id, name)]. Idempotent."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind") == "cmvn"}
    created = []
    for b, term in enumerate(cmvn_terms(n_bands, eps=eps, do_variance=do_variance)):
        name = f"cmvn_band{b}"
        if name in existing:
            continue
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "cmvn", "band": b, "eps": float(eps),
            "do_variance": bool(do_variance), "predicate": term.to_dict(),
            "origin": "phonology", "composed_by": "agent",
            "science": "speaker = constant per-band offset+scale over time; "
                       "subtract mean, divide by std -> speaker-invariant"})
        created.append((c, name))
    return created


# ---------------------------------------------------------------------------
# I/O boundary: apply the agent's composed CMVN Term to a frames x bands matrix.
# This is the ONLY Python here, and it is a mechanical translator (matrix ->
# frame graph -> evaluate the agent's Term -> matrix). No reasoning, no decisions
# over graph state — it just runs the agent's program on the native evaluator.
# ---------------------------------------------------------------------------

def apply_cmvn(M, substrate=None, eps: float = 1e-6, do_variance: bool = True,
               voiced_floor: float = 0.25):
    """Apply the agent's CMVN to one utterance's frames x bands matrix and return
    the normalized matrix.

    The agent's CMVN is brought in as a NATIVE PRIMITIVE — the same pattern as
    `cochleagram`: the transform runs batched in Rust (substrate_rs._native.cmvn,
    the faithful port of the composed cmvn_band_term), and the Python here is the
    affordance handoff. Mechanical I/O only: compute the voicing gate (a signal
    threshold, not agent reasoning), hand the matrix + mask to the native primitive,
    reshape back. Falls back to evaluating the agent's composed CMVN Term-tree on
    the native graph evaluator if the primitive is unavailable — same numbers, but
    O(frames^2 * bands) (it walls on long utterances; the primitive is ~1000x)."""
    import numpy as np

    M = np.asarray(M, dtype=np.float64)
    n_frames, n_bands = M.shape

    # Mechanical voicing gate (signal threshold, not agent reasoning): the stat set
    # = frames whose total energy clears the floor, mirroring the side-experiment.
    energy = M.sum(axis=1)
    emax = float(energy.max()) if energy.size else 0.0
    if emax > 1e-12:
        voiced = energy >= voiced_floor * emax
        if int(voiced.sum()) < 2:
            voiced = np.ones(n_frames, dtype=bool)
    else:
        voiced = np.ones(n_frames, dtype=bool)

    # Fast path: the agent's CMVN as a native Rust primitive (batched, the
    # cochleagram handoff pattern). One line into Rust; the numbers come back out.
    try:
        from substrate_rs import _native
        flat = _native.cmvn(np.asarray(M, np.float32).reshape(-1).tolist(),
                            int(n_frames), int(n_bands), float(eps), bool(do_variance),
                            voiced.astype(np.uint8).tolist())
        return np.asarray(flat, np.float32).reshape(n_frames, n_bands)
    except Exception:
        pass

    # Fallback: evaluate the agent's composed per-band CMVN Term-tree natively, one
    # cell at a time, over a frame graph. Faithful (numbers from the evaluator) but
    # O(frames^2 * bands) — only used when the native primitive is absent.
    from substrate_rs import Substrate
    s = substrate if substrate is not None else Substrate()
    u = s.add_node("Utterance", {})
    frame_ids = []
    for r in range(n_frames):
        attrs = {f"band{b}": float(M[r, b]) for b in range(n_bands)}
        f = s.add_node("Frame", attrs)
        s.add_edge_unchecked(u, FRAME_EDGE, f)
        if voiced[r]:
            s.add_edge_unchecked(u, STAT_EDGE, f)
        frame_ids.append(f)
    terms = cmvn_terms(n_bands, eps=eps, do_variance=do_variance)
    out = np.empty_like(M)
    for r, f in enumerate(frame_ids):
        env = {"u": u, "s": f}
        for b in range(n_bands):
            out[r, b] = float(s.evaluate(terms[b], env))
    return out.astype(np.float32)


__all__ = ["FRAME_EDGE", "STAT_EDGE", "cmvn_band_term", "cmvn_terms",
           "compose_cmvn", "apply_cmvn"]
