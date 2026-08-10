"""native_cognition — Ranks 2 & the rel-formant invariant of the hearing pipeline as
graph-resident native Rust Terms (the agent's design, see docs/native_migration_design.md).

This module is a SEPARATE consumer (world-adapter glue only). It does NOT modify the
scoring files scripts/articulatory_gamma.py or scripts/perception_composition.py (owned by
the concurrent perception_rescoring run); it imports their forward-model + helpers READ-ONLY
and re-composes the cognition natively.

Two migrations, both ZERO-new-primitive at the composition level (the only new primitives are
the scalar Log/Exp added to the grammar, used by rel_formants_term):

  (A) d_A(w) — the per-digit ARTICULATORY admissibility distance, as a graph Argmin Term:

        d_A(w) = Plus([ Times([Lit(W_FORMANT_SHADOW), DtwTo(Attr(q, obs_rel), Attr(w, syn_rel))]),
                        Times([Lit(W_GAMMA),           Attr(w, gamma)]) ])
        pred_art = Argmin over { Concept : is_word==1 } of d_A(w)

      The Python `articulatory_distance` resamples each digit's synthesised speaker-relative
      formant track to the observed length, takes the mean per-frame L2 vs obs_rel, and adds
      W_GAMMA * gamma. The agent re-composes this with DtwTo — the banded Sakoe-Chiba
      alignment is a SUPERSET of the monotone resample-then-L2 (it absorbs the gesture-timing
      warp), so NO Resample primitive is needed. The synthesised track `syn_rel` and the
      Γ-cost `gamma` are FORWARD-MODEL CONSTANTS (the model consumes no observed data), stored
      as graph attrs on each digit Concept — seed-like data, not a Term. OWNERSHIP not
      fidelity: DtwTo alignment != the Python fixed resample, so divergence on close calls is
      EXPECTED (memory: ozma_native_migration_is_ownership_not_fidelity).

  (B) rel_formants(F) — the speaker-invariant transform log(F) - mean(log(F)) as a native
      Term over a fixed-length formant frame, exercising the new Log primitive + composed
      Mean (Sum/Count/Div). The load-bearing VTL-cancelling invariant the recognition rests
      on. (relative_formants_frame in formant_trajectory_dynamics.py.)
"""
from __future__ import annotations

import numpy as np


# ---- Term constructors (raw-dict, mirroring native_fusion / formant_trajectory_dynamics) ----

def _V(n):
    return {"type": "Var", "name": n}


def _Lit(v):
    return {"type": "Lit", "value": v}


def _Attr(node, k):
    return {"type": "Attr", "node": node, "key": k}


def _Plus(items):
    return {"type": "Plus", "items": items}


def _Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def _Times(items):
    return {"type": "Times", "items": items}


def _Div(a, b):
    return {"type": "Div", "a": a, "b": b}


def _Nth(items, index):
    return {"type": "Nth", "items": items, "index": int(index)}


def _Log(arg):
    return {"type": "Log", "arg": arg}


def _DtwTo(a, b):
    return {"type": "DtwTo", "a": a, "b": b}


def _Argmin(src, var, val):
    return {"type": "Argmin", "source": src, "var_name": var,
            "value": val, "default": None}


def _NodesWhere(t, k, v):
    return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


# Graph attrs the wrapper populates.
WORD_ATTR = "is_word"
OBS_REL_ATTR = "obs_rel"     # observed speaker-relative formant track (tuple-of-3-vecs), on the Query
SYN_REL_ATTR = "syn_rel"     # synthesised speaker-relative formant track (forward-model const), per digit
GAMMA_ATTR = "art_gamma"     # the digit's Γ-cost (forward-model const)
OBS_VOI_ATTR = "obs_voi"     # observed voicing/gap envelope (tuple-of-1-vecs), on the Query
SYN_VOI_ATTR = "syn_voi"     # synthesised voicing envelope (forward-model const), per digit


def _word_set():
    return _NodesWhere("Concept", WORD_ATTR, _Lit(1.0))


# ---- (A) d_A native Term ----

def articulatory_score_term(w_formant_shadow: float, w_gamma: float,
                            w_voicing_shadow: float = 0.0) -> dict:
    """d_A(w) = W_FORMANT_SHADOW * DtwTo(obs_rel, syn_rel(w)) + W_GAMMA * gamma(w)
              [+ W_VOICING_SHADOW * DtwTo(obs_voi, syn_voi(w))   iff w_voicing_shadow > 0].
    A graph Plus of the formant-shadow alignment distance, the Γ-cost, and (when the
    re-composed perception observes the gap channel) the voicing-envelope alignment distance —
    the same Argmin-of-distance shape as formant_trajectory_dynamics.dtw_predict_term. The
    voicing term is the native realisation of perception_composition's W_VOICING_SHADOW prong;
    DtwTo (banded alignment) is the ownership superset of the Python fixed-resample L1."""
    terms = [
        _Times([_Lit(float(w_formant_shadow)),
                _DtwTo(_Attr(_V("q"), OBS_REL_ATTR), _Attr(_V("w"), SYN_REL_ATTR))]),
        _Times([_Lit(float(w_gamma)), _Attr(_V("w"), GAMMA_ATTR)]),
    ]
    if w_voicing_shadow and w_voicing_shadow > 0.0:
        terms.append(_Times([_Lit(float(w_voicing_shadow)),
                             _DtwTo(_Attr(_V("q"), OBS_VOI_ATTR), _Attr(_V("w"), SYN_VOI_ATTR))]))
    return _Plus(terms)


def predict_articulatory_term(w_formant_shadow: float, w_gamma: float,
                              w_voicing_shadow: float = 0.0) -> dict:
    """predict = Argmin over candidate words of d_A(w). The whole articulatory-prong
    DECISION as graph data (native eval)."""
    return _Argmin(_word_set(), "w",
                   articulatory_score_term(w_formant_shadow, w_gamma, w_voicing_shadow))


def _traj_tuple(track):
    """A (frames x 3) track -> tuple-of-tuples graph attr (the DtwTo frame sequence)."""
    if track is None or len(track) == 0:
        return ((0.0, 0.0, 0.0),)
    return tuple(tuple(float(v) for v in frame) for frame in track)


def _voi_tuple(env):
    """A (frames,) voicing envelope -> tuple-of-1-vecs graph attr (the DtwTo frame sequence)."""
    if env is None or len(env) == 0:
        return ((0.0,),)
    return tuple((float(v),) for v in np.asarray(env).reshape(-1))


def build_articulatory_substrate(Substrate, models, w_formant_shadow, w_gamma,
                                 with_voicing: bool = False):
    """A Substrate carrying the forward model AS GRAPH DATA: one Concept per digit with its
    synthesised speaker-relative track + Γ-cost (+ synthesised voicing envelope when the
    re-composed perception observes the gap) as attrs, plus a reusable Query node. The forward
    model consumes no observed data, so this is one-time seed-like construction.
    Returns (substrate, query_node, {digit: node_id})."""
    s = Substrate()
    word_nodes = {}
    for w, m in models.items():
        nid = s.add_node("Concept", {"name": w})
        s.set_attr(nid, WORD_ATTR, 1.0)
        s.set_attr(nid, SYN_REL_ATTR, _traj_tuple(m["rel"]))
        s.set_attr(nid, GAMMA_ATTR, float(m["gamma"]))
        if with_voicing:
            s.set_attr(nid, SYN_VOI_ATTR, _voi_tuple(m["voi"]))
        word_nodes[w] = nid
    q_attrs = {OBS_REL_ATTR: ((0.0, 0.0, 0.0),)}
    if with_voicing:
        q_attrs[OBS_VOI_ATTR] = ((0.0,),)
    q = s.add_node("Query", q_attrs)
    return s, q, word_nodes


def native_articulatory_predict(s, q, obs_rel, w_formant_shadow, w_gamma, Pred,
                                obs_voi=None, w_voicing_shadow: float = 0.0):
    """Feed the observed speaker-relative track (+ optional voicing envelope) onto the Query and
    return the native-Term Argmin digit. `Pred` is the evaluable-Term wrapper
    (many_settings_recognizer._Pred / formant_trajectory_dynamics._P)."""
    s.set_attr(q, OBS_REL_ATTR, _traj_tuple(obs_rel))
    if obs_voi is not None and w_voicing_shadow > 0.0:
        s.set_attr(q, OBS_VOI_ATTR, _voi_tuple(obs_voi))
    term = Pred(predict_articulatory_term(w_formant_shadow, w_gamma, w_voicing_shadow))
    pick = s.evaluate(term, {"q": q})
    return s.node(pick)["attrs"]["name"]


def native_articulatory_scores(s, q, word_nodes, obs_rel, w_formant_shadow, w_gamma, Pred,
                               obs_voi=None, w_voicing_shadow: float = 0.0):
    """The per-digit native d_A(w) = W_FORMANT_SHADOW*DtwTo(obs_rel, syn_rel(w)) + W_GAMMA*γ(w)
    [+ W_VOICING_SHADOW*DtwTo(obs_voi, syn_voi(w))], evaluated natively per digit Concept (the
    SAME score Term the Argmin ranks, read out per word so the fusion prong can consume it).
    Returns {word: d_A}. The DtwTo warp is the OWNERSHIP divergence from the Python fixed-
    resample L2/L1 (memory: ozma_native_migration_is_ownership_not_fidelity)."""
    s.set_attr(q, OBS_REL_ATTR, _traj_tuple(obs_rel))
    if obs_voi is not None and w_voicing_shadow > 0.0:
        s.set_attr(q, OBS_VOI_ATTR, _voi_tuple(obs_voi))
    score = Pred(articulatory_score_term(w_formant_shadow, w_gamma, w_voicing_shadow))
    out = {}
    for w, wn in word_nodes.items():
        v = s.evaluate(score, {"q": q, "w": wn})
        out[w] = float(v) if v is not None else float("inf")
    return out


# ---- (B) rel-formants native transform (Log + composed Mean) ----

def rel_formants_term(n_formants: int = 3) -> dict:
    """log(F_i) - mean_j(log(F_j)) for a fixed-length formant frame fed as Var("f") (a 3-vec).
    Mean = Div(Plus([Log(Nth(f,0)),..]), Lit(n)) — COMPOSED from Sum/Count/Div, no Mean
    primitive. Returns the per-channel speaker-relative value for channel `_chan` (Var-bound),
    matching relative_formants_frame. The whole frame is built by evaluating once per channel.
    Here we return a SCALAR Term for channel index given by Lit substitution at call time."""
    logs = [_Log(_Nth(_V("f"), i)) for i in range(n_formants)]
    mean_log = _Div(_Plus(logs), _Lit(float(n_formants)))
    # per-channel: Log(Nth(f, chan)) - mean_log  ; chan supplied by the caller as a concrete Nth
    return mean_log  # mean component reused by rel_formants_channel_term


def rel_formants_channel_term(chan: int, n_formants: int = 3) -> dict:
    """The speaker-relative value of formant channel `chan`: Log(Nth(f,chan)) - mean(Log(f))."""
    logs = [_Log(_Nth(_V("f"), i)) for i in range(n_formants)]
    mean_log = _Div(_Plus(logs), _Lit(float(n_formants)))
    return _Minus(_Log(_Nth(_V("f"), chan)), mean_log)


def native_rel_formants(s, formants, Pred, n_formants: int = 3):
    """Evaluate the native rel-formants Term over a single formant frame (a 3-vec). Returns
    the (n_formants,) speaker-relative vector. Var("f") bound to the formant tuple."""
    ftuple = tuple(float(v) for v in formants)
    out = []
    for c in range(n_formants):
        term = Pred(rel_formants_channel_term(c, n_formants))
        out.append(float(s.evaluate(term, {"f": ftuple})))
    return out


__all__ = [
    "WORD_ATTR", "OBS_REL_ATTR", "SYN_REL_ATTR", "GAMMA_ATTR",
    "articulatory_score_term", "predict_articulatory_term",
    "build_articulatory_substrate", "native_articulatory_predict",
    "rel_formants_channel_term", "native_rel_formants",
]
