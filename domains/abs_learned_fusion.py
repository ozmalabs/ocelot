"""abs_learned_fusion — close the data-bound residual the EARNED way: FUSE the holistic
analysis-by-synthesis GEOMETRY channel (the earned ceiling, 66.7%) WITH a LEARNED-from-
background DATA channel, as a graph-native late-fusion DECISION. donkey=0, earn-not-borrow.

THE ARC (do not re-derive): the EARNED Omniglot 20-way-1-shot ladder is geometric ~34% ->
fixed scattering 55.4% -> from-scratch learned head 63% -> holistic AbS 66.7% (the earned
CEILING via STRUCTURE — every finer DECOMPOSITION nulls because discretising into stroke
identities loses the INTER-STROKE JOINT SHAPE holistic AbS scores directly). BORROWED Gemma
= 91%, BPL = 96.7%. The residual to 91% is genuinely DATA-SCALE (the learned head's curve
climbed monotonically: 2 alph 39% -> 30 alph 63%, STILL CLIMBING).

THE TEST (the user's directive "close the gap via earn and learn"): attack the DATA-SCALE
residual with a LEARNED-but-EARNED channel, scaled on MORE held background, COMBINED WITH
(not replacing) holistic AbS. Two channels:
  GEOMETRY  = holistic AbS render-and-compare (held ShapeContextDist+TpsDeformDist over the
              rendered program point-set) — the STRUCTURE channel. KEPT, never decomposed.
  DATA      = a from-scratch learned head (random init, held BACKGROUND alphabets only, NO
              borrowed weights), cosine 1-NN over its earned embedding — the DATA channel
              that should CLIMB with more background.

THE FUSION DECISION IS A HELD RUST TERM (reused verbatim from domains/native_fusion's proven
Argmax-of-Plus-of-top-centred-channels pattern): per candidate support class w,

    score(w) = top_centred(geom_sim, w)  +  w_learn * top_centred(learn_sim, w)
    predict  = Argmax_w score(w)

with the two channels TOP-CENTRED (Minus of Attr and MaxOver over the candidate set) so they
are scale-comparable, w_learn a per-fold Lit (NOT tuned against test — a fixed/measured
weight), and the whole decision — centring, weighting, summing, argmax — evaluated NATIVELY by
substrate.evaluate (Rust). Python is world-adapter glue only: it computes the two channel
similarities (held AbS Terms + the learned head's earned embedding cosine), writes them as
graph attrs, evaluates the Term, reads back the winning candidate.

donkey=0: NO LLM anywhere; the learned head is random-init + background-only (no borrowed
weights); the fusion decision is a graph Term, not a Python argmax.

numpy/torch usage (flagged): torch trains the from-scratch head (no pretrained / .from_pretrained
/ download); numpy is the point-set / raster / cosine adapter. The fusion DECISION is the Rust
Term, not Python.
"""
from __future__ import annotations
import numpy as _np                  # ADAPTER: point-sets, cosine, channel arrays
import substrate_rs as _srs
import domains.native_fusion as _nf   # the proven Argmax-of-Plus fusion Term machinery (reused)

# Per-candidate graph attrs the wrapper populates (RAW similarities; the Term top-centres them).
GEOM_ATTR = "geom_sim"     # holistic-AbS similarity (= -render_compare_score; HIGHER = better)
LEARN_ATTR = "learn_sim"   # learned-head cosine similarity (HIGHER = better)
CAND_ATTR = "is_cand"      # candidate-support-class marker (== 1.0)

_S = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}


# --------------------------------------------------------------------------- #
#  THE HELD FUSION TERM  (Argmax over Plus of two top-centred channels)
#  Reuses native_fusion's _top_centred / _Plus / _Times / _Argmax verbatim — same shape the
#  speech hearing path's multi-prong fusion uses, here over the two handwriting channels.
# --------------------------------------------------------------------------- #

def _cand_set():
    """The candidate node set: every Concept with is_cand == 1 (one per support class)."""
    return _nf._NodesWhere("Concept", CAND_ATTR, _L(1.0))


def _top_centred(var_name: str, attr_key: str) -> dict:
    """Attr(var, attr) - MaxOver_w'(Attr(w', attr)) over the candidate set — top-centring so the
    best candidate = 0, others < 0. Native (fresh inner var, evaluated by the Rust evaluator)."""
    inner = "_c_top_" + attr_key
    return _nf._Minus(
        _nf._Attr(_nf._V(var_name), attr_key),
        _nf._MaxOver(_cand_set(), inner, _nf._Attr(_nf._V(inner), attr_key)),
    )


def fusion_score_term(w_learn: float) -> dict:
    """score(w) = geom_c[w] + w_learn * learn_c[w], each channel top-centred IN the graph. The
    GEOMETRY channel (holistic AbS) is the unweighted ANCHOR (the earned ceiling); the LEARNED
    DATA channel is added at weight w_learn (a per-fold Lit). A graph Plus of two soft scorers."""
    return _nf._Plus([
        _top_centred("w", GEOM_ATTR),                                       # holistic-AbS ANCHOR
        _nf._Times([_L(float(w_learn)), _top_centred("w", LEARN_ATTR)]),    # learned DATA channel
    ])


def predict_fusion_term(w_learn: float) -> dict:
    """predict = Argmax over candidate support classes of fusion_score_term — the WHOLE late-
    fusion decision as graph data (same Argmax-of-score shape native_fusion proved native)."""
    return _nf._Argmax(_cand_set(), "w", fusion_score_term(w_learn))


def single_channel_term(attr_key: str) -> dict:
    """Argmax over candidates of a SINGLE channel's raw similarity — the per-channel baselines,
    decided by the SAME native Argmax (so the fusion is compared like-for-like to its channels)."""
    return _nf._Argmax(_cand_set(), "w", _nf._Attr(_nf._V("w"), attr_key))


# --------------------------------------------------------------------------- #
#  WORLD-ADAPTER GLUE: build the candidate substrate, feed the two channels as attrs,
#  evaluate the native Term, read back the argmax candidate INDEX. NO decision here.
# --------------------------------------------------------------------------- #

def _build_substrate(Substrate, n_cand):
    s = Substrate()
    nodes = []
    for i in range(n_cand):
        nid = s.add_node("Concept", {"idx": float(i)})
        s.set_attr(nid, CAND_ATTR, 1.0)
        nodes.append(nid)
    return s, nodes


def fuse_predict(Substrate, Pred, geom_sims, learn_sims, w_learn: float) -> int:
    """Feed the two RAW per-candidate channel similarity arrays as graph attrs, evaluate the
    native fusion Term, return the winning candidate INDEX. geom_sims / learn_sims are length-K
    arrays (K support classes); the Term top-centres + weights + sums + argmaxes natively."""
    s, nodes = _build_substrate(Substrate, len(geom_sims))
    for i, nid in enumerate(nodes):
        s.set_attr(nid, GEOM_ATTR, float(geom_sims[i]))
        s.set_attr(nid, LEARN_ATTR, float(learn_sims[i]))
    pick = s.evaluate(Pred(predict_fusion_term(w_learn)), {})
    return int(round(s.node(pick)["attrs"]["idx"]))


def channel_predict(Substrate, Pred, sims, attr_key: str) -> int:
    """Single-channel argmax via the SAME native Argmax Term (geometry-alone / learned-alone)."""
    s, nodes = _build_substrate(Substrate, len(sims))
    for i, nid in enumerate(nodes):
        s.set_attr(nid, attr_key, float(sims[i]))
    pick = s.evaluate(Pred(single_channel_term(attr_key)), {})
    return int(round(s.node(pick)["attrs"]["idx"]))


# --------------------------------------------------------------------------- #
#  CHANNEL SIMILARITIES (adapter math; the held AbS Terms ARE the geometry channel)
# --------------------------------------------------------------------------- #

def geom_sims(query_ps, support_ps_list):
    """Holistic-AbS similarity per support class = -(render_compare_score) so HIGHER = better.
    render_compare_score is the held ShapeContextDist+TpsDeformDist over the rendered program
    point-sets (domains/analysis_by_synthesis) — the STRUCTURE channel, never decomposed."""
    import domains.analysis_by_synthesis as _abs
    return _np.array([-_abs.render_compare_score(query_ps, s) for s in support_ps_list], float)


def cos_sims(query_vec, support_vecs):
    """Learned-head cosine similarity per support class (HIGHER = better) — the DATA channel."""
    out = []
    qn = _np.linalg.norm(query_vec)
    for s in support_vecs:
        sn = _np.linalg.norm(s)
        out.append(float(query_vec @ s / (qn * sn)) if qn > 0 and sn > 0 else 0.0)
    return _np.array(out, float)


__all__ = [
    "GEOM_ATTR", "LEARN_ATTR", "CAND_ATTR",
    "fusion_score_term", "predict_fusion_term", "single_channel_term",
    "fuse_predict", "channel_predict", "geom_sims", "cos_sims",
]
