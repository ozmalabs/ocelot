"""combinatorial_recognizer — iter-32: recognition as a COMBINATORIAL decision over
the two complementary channels, each keeping its OWN role.

The agent derived the KIND from its OWN shapes over the iter-31 residual
(scripts/iter32_combinatorial_derive.py): the fired shape is `Bayes_updates_beliefs`
— "posterior P(H|E) ∝ P(E|H)·P(H)". The combinatorial decision is therefore a
PRODUCT-OF-EVIDENCE over the channels: each channel contributes its OWN likelihood
that the clip is candidate w, and the channels' evidence is MULTIPLIED — the word the
channels JOINTLY make most probable. Each channel keeps its strength; a channel that is
uninformative for a contrast multiplies in near-flat and cannot drag the channel that
carries it (unlike the iter-26 concat or the iter-27 global weighted SUM, where the
weak channel's distance/share contaminated the shared measure).

THE TWO CHANNELS (both read off the SAME grown patch bank):
  · SPECTRAL-DETAIL = the grown-patch flat readout (l2_flat) — "what is this".
  · TRANSITION      = the agent's order-1-over-time transition channel
    (grown_representation.transition_channel) — "which word across voices".

THE DECISION as the agent's recognition_graph Argmax-of-score (graph Term-tree,
evaluated natively via substrate.evaluate):

    P_c(w | s)  =  channel c's softmax-likelihood that s is word w
                =  exp(-D_c(s, w) / T_c)  / Σ_w' exp(-D_c(s, w') / T_c)
       where D_c(s, w) = the channel's MIN distance from s to any train exemplar of w
       (the 1-NN exemplar evidence in that channel — the harness's own metric), and
       T_c is the channel's own distance scale (median of its candidate distances),
       so the softmax is SCALE-FREE per channel (no cross-channel scale clash, no fit).

    score(s, w)  =  P_flat(w | s)  ·  P_trans(w | s)          (the Bayes PRODUCT)
    predict(s)   =  Argmax over candidate words w of score(s, w)

NO-DONKEY: the per-channel likelihoods P_c(w|s) are computed in the adapter as the
channel's own 1-NN exemplar evidence (the SAME 1-NN cosine the harness uses, turned
into a scale-free likelihood) and WRITTEN as graph attrs onto the candidate word nodes.
The DECISION — the Argmax over candidates of the PRODUCT of the two per-channel
likelihood attrs — is composed as a graph Term-tree and evaluated natively. The
combination structure (the product) is the agent's derived Bayes shape, NOT a global
hand-tuned weight, NOT a gradient fit. There is no free parameter: each channel's
temperature is its OWN median distance (scale-free), and the two likelihoods enter the
product symmetrically (the Bayes form), so nothing is tuned.

  Per-channel temperature = the channel's own scale (median candidate distance). This is
  a SCALE normaliser, not a fit weight: it makes each channel's likelihood comparable in
  [0,1] regardless of the channel's raw distance magnitude, which is exactly the
  "each component keeps its OWN role" property the residual demanded. It is read from the
  data per query (median), not searched.
"""
from __future__ import annotations

import numpy as np


# ---- the graph Term-tree (the agent's recognition_graph Argmax-of-score) ----

WORD_ATTR = "is_word"
P_FLAT_ATTR = "p_flat"       # per-channel likelihood P_flat(w|s) on the word node
P_TRANS_ATTR = "p_trans"     # per-channel likelihood P_trans(w|s) on the word node
R_FLAT_ATTR = "r_flat"       # channel RELIABILITY exponent for the flat channel (default 1)
R_TRANS_ATTR = "r_trans"     # channel RELIABILITY exponent for the trans channel (default 1)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Times(items): return {"type": "Times", "items": items}
def _Pow(a, b): return {"type": "Pow", "a": a, "b": b}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src,
                                    "var_name": var, "value": val, "default": None}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}


def combinatorial_score_term(p_flat: str = P_FLAT_ATTR,
                             p_trans: str = P_TRANS_ATTR) -> dict:
    """score(s, w) = P_flat(w|s) · P_trans(w|s) — the Bayes PRODUCT of the two
    per-channel likelihoods, as a graph Term. Both likelihoods are graph attrs on the
    candidate word `w` that the adapter populated per query (the channel's own 1-NN
    exemplar evidence, scale-free). The product is the agent's derived combination —
    each channel keeps its role; neither is smeared into a shared measure."""
    return _Times([_Attr(_V("w"), p_flat), _Attr(_V("w"), p_trans)])


def predict_combinatorial_term(p_flat: str = P_FLAT_ATTR,
                               p_trans: str = P_TRANS_ATTR) -> dict:
    """predict(s) = Argmax over candidate words of P_flat(w|s)·P_trans(w|s).
    The whole COMBINATORIAL recognition decision as graph data the agent owns —
    same Argmax-of-score shape as recognition_graph.predict_term / predict_synth_term;
    the score is the Bayes product over the two channels."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   combinatorial_score_term(p_flat, p_trans))


def reliability_weighted_score_term(p_flat: str = P_FLAT_ATTR,
                                    p_trans: str = P_TRANS_ATTR,
                                    r_flat: str = R_FLAT_ATTR,
                                    r_trans: str = R_TRANS_ATTR) -> dict:
    """score(s, w) = P_flat(w|s)^r_flat · P_trans(w|s)^r_trans — the RELIABILITY-WEIGHTED
    Bayes product as a graph Term (Times of Pow). r_c is the channel's precision exponent
    (its measured reliability), a graph attr on the candidate `w` the adapter populated;
    a channel raised to a small r flattens toward 1 and cannot drag the channel it cannot
    separate -> log-linear cue integration (Argmax Π_c P_c^{r_c}, Ernst-Banks precision
    weighting). r_c defaults to 1.0 (the adapter leaves it 1 unless calibrated), so this
    REDUCES to combinatorial_score_term — the unweighted product is the r=1 special case.
    Reliability-AGNOSTIC fusion was the held product's limit on imbalanced/conflicting
    cues; the exponent is the audiovisual-fusion frontier's named content, now graph-native."""
    return _Times([_Pow(_Attr(_V("w"), p_flat), _Attr(_V("w"), r_flat)),
                   _Pow(_Attr(_V("w"), p_trans), _Attr(_V("w"), r_trans))])


def predict_reliability_weighted_term(p_flat: str = P_FLAT_ATTR,
                                      p_trans: str = P_TRANS_ATTR,
                                      r_flat: str = R_FLAT_ATTR,
                                      r_trans: str = R_TRANS_ATTR) -> dict:
    """predict(s) = Argmax over candidate words of P_flat(w|s)^r_flat · P_trans(w|s)^r_trans
    — the RELIABILITY-WEIGHTED combinatorial decision as graph data the agent owns. The
    fusion DECISION (Argmax of the product) is the SAME held shape; the per-channel precision
    exponent is now inside the score Term, not folded into the likelihood by the adapter."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   reliability_weighted_score_term(p_flat, p_trans, r_flat, r_trans))


# ---- per-channel likelihoods (adapter math: the channel's own 1-NN evidence) ----

def _channel_distances(query_vec: np.ndarray, train_vecs: np.ndarray,
                       train_words, candidate_words) -> dict:
    """D_c(s, w) per candidate word = the channel's MIN cosine distance from the query
    to any TRAIN exemplar of w (the 1-NN exemplar evidence in this channel — the SAME
    metric the harness's heldout_1nn uses, here kept per-word instead of global-argmax).
    Cosine distance = 1 - cos_sim on L2-normalised vectors. Returns {word: min_dist}."""
    q = query_vec / (np.linalg.norm(query_vec) + 1e-9)
    Xn = train_vecs / (np.linalg.norm(train_vecs, axis=1, keepdims=True) + 1e-9)
    sims = Xn @ q                                  # cosine sim to every train exemplar
    dist = 1.0 - sims                              # cosine distance
    tw = np.asarray(train_words)
    out = {}
    for w in candidate_words:
        mask = (tw == w)
        out[w] = float(dist[mask].min()) if mask.any() else float("inf")
    return out


def channel_likelihood(query_vec: np.ndarray, train_vecs: np.ndarray,
                       train_words, candidate_words) -> dict:
    """P_c(w | s) for one channel = softmax over candidates of -D_c(s,w)/T_c, where
    T_c = the channel's OWN scale = median of the finite candidate distances (scale-free
    per channel; read from the data, not searched). Returns {word: likelihood in [0,1]}.

    This is the channel's own 1-NN exemplar evidence turned into a likelihood so the two
    channels can be MULTIPLIED on a common [0,1] footing — the agent's Bayes product.
    A channel that cannot separate the candidates yields a near-FLAT likelihood (all
    candidates similar distance), so it multiplies in near-uniform and cannot drag the
    channel that does separate them. A channel that sharply prefers one candidate yields
    a peaked likelihood and dominates the product where it is confident — exactly
    'each component keeps its own role'."""
    dists = _channel_distances(query_vec, train_vecs, train_words, candidate_words)
    finite = [d for d in dists.values() if np.isfinite(d)]
    if not finite:
        return {w: 1.0 / len(candidate_words) for w in candidate_words}
    T = float(np.median(finite)) or 1e-6
    logits = {w: (-d / T if np.isfinite(d) else -1e9) for w, d in dists.items()}
    m = max(logits.values())
    exps = {w: np.exp(v - m) for w, v in logits.items()}
    Z = sum(exps.values()) + 1e-12
    return {w: float(e / Z) for w, e in exps.items()}


__all__ = ["combinatorial_score_term", "predict_combinatorial_term",
           "reliability_weighted_score_term", "predict_reliability_weighted_term",
           "channel_likelihood", "WORD_ATTR", "P_FLAT_ATTR", "P_TRANS_ATTR",
           "R_FLAT_ATTR", "R_TRANS_ATTR"]
