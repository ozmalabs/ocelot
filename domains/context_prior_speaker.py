"""context_prior_speaker — SHARED CONTEXT AS A MESSAGE PRIOR. The diagnosis-driven follow-up to
the pragmatic-speaker null (commit 212f4316). donkey=0, earn-not-borrow, graph-native.

THE NULL THIS ACTS ON. The pragmatic speaker (J = ListenerRecovery - lambda*ProductionCost, a held
Argmax-of-Plus Term over a cheap->explicit spectrum) selects a genuine interior midpoint and beats a
listener-blind speaker — BUT the sharp wife-vs-wide prediction ("terser with a richer shared model")
was a CLEAN NULL when "shared-model quality" = the listener's background-training size: more
background makes the listener UNIFORMLY better, not more TERSE-TOLERANT.

THE DIAGNOSIS (the creator's). The real wife mechanism is "good models of each other AND CONTEXT" =
a PEAKED PRIOR OVER MESSAGES from shared context: she can PREDICT what you'll say, so the residual a
signal must carry is tiny. A generic recognizer has a FLAT message prior and gains nothing from
brevity. So "shared model" = a PRIOR OVER MESSAGES, and the prediction to test is: chosen terseness
RISES with prior-PEAKEDNESS (measured in bits of MI between context and message).

THE BAYESIAN LISTENER (this module). Recognition becomes a POSTERIOR, not a bare likelihood:

    log posterior(c | signal, context) = log Likelihood(signal | c)  +  log Prior(c | context)
    recovery(signal)                   = softmax_c[ log posterior ]  at the TRUE class

The listener LIKELIHOOD is the held recognizer EXACTLY as in pragmatic_speaker.py (held AbS
render-compare geometry + the from-scratch learned head, NO borrowed weights). The PRIOR encodes
shared context (what the audience expects). The pragmatic speaker then optimizes terseness against
the POSTERIOR: J(rung) = posterior_recovery(rung) - lambda*ProductionCost(rung), the SAME held
Argmax-of-Plus machinery (pragmatic_speaker.choose_term).

THE BAYES COMBINE IS A HELD GRAPH TERM. Per candidate Concept c the posterior log-score is
Plus([ Log(likelihood_c) , Log(prior_c) ]) — log-domain so the Bayes product is an ADDITIVE Term
(reusing native_fusion._Plus / _Attr verbatim, plus the native Log term). The posterior PROBABILITY
of the true class is then exp(logpost_true) / Sum_c exp(logpost_c) — Exp / Sum / Div, all native. The
WHOLE recovery (likelihood x prior -> normalise -> read the true class) is one substrate.evaluate. The
speaker's terseness argmax over rungs is the held choose_term from pragmatic_speaker. Python is glue:
it computes the per-candidate held likelihoods + writes the context prior as attrs, evaluates the
Terms, reads back recovery and the chosen rung. 0 LLM, 0 borrowed weights at the decision.

MESSAGE PRIORS + PEAKEDNESS AS A MEASURED AXIS.
  * PARAMETRIC sweep: a concentration/temperature knob takes the prior FLAT (uniform, max entropy)
    -> PEAKED (mass on the true class + near neighbours, low entropy). Peakedness is REPORTED in bits
    as MI(context;message) = H(message) - H(message|context) (see context_prior_gate).
  * REAL held-context prior: a NEIGHBOUR-SIMILARITY prior derived from the held AbS geometry between
    the *support exemplars* (context = "the audience has seen these shapes and knows which cluster the
    message lives in") — an ACTUAL cue that narrows candidates, peakedness varying naturally per
    episode. Built here (neighbour_prior); the gate measures its MI and runs the discriminative
    control on it too.

numpy USAGE (flagged): adapter math only — softmax/entropy/cosine/array assembly. The Bayes posterior
combine + the terseness argmax are Rust Terms via substrate.evaluate.
"""
from __future__ import annotations
import numpy as _np
import substrate_rs as _srs
import domains.native_fusion as _nf
import domains.pragmatic_speaker as _PS
import domains.analysis_by_synthesis as _abs

_L = lambda v: {"type": "Lit", "value": v}

# Per-candidate graph attrs the wrapper populates for the Bayes posterior Term.
LIK_ATTR = "likelihood"     # held-listener likelihood of the signal under candidate c (>0)
PRIOR_ATTR = "msg_prior"    # message prior P(c | context)  (>0, sums to 1 over candidates)
CAND_ATTR = "is_cand"       # candidate-class marker (== 1.0)
TRUE_ATTR = "is_true"       # the true class marker (== 1.0 on exactly one candidate)
_EPS = 1e-12


# --------------------------------------------------------------------------- #
#  THE HELD BAYES-POSTERIOR RECOVERY TERM
#  recovery = P(true | signal, context)
#           = exp(logpost_true) / Sum_c exp(logpost_c),
#    logpost(c) = Log(likelihood_c) + Log(prior_c)         (log-domain = additive Bayes combine)
#  All native: Log / Exp / Plus / Sum / Div / Attr / Argmax / NodesWhere. 0 new primitives.
# --------------------------------------------------------------------------- #

def _cand_set():
    """The candidate-class node set: every Concept with is_cand == 1 (one per support class)."""
    return _nf._NodesWhere("Concept", CAND_ATTR, _L(1.0))


def _Log(a):  return {"type": "Log", "arg": a}
def _Exp(a):  return {"type": "Exp", "arg": a}


def _logpost(var_name: str) -> dict:
    """logpost(c) = Log(likelihood_c) + Log(prior_c) — the log-domain Bayes combine (additive),
    a graph Plus of the two log-channels. This is the held posterior combine the task requires."""
    return _nf._Plus([
        _Log(_nf._Attr(_nf._V(var_name), LIK_ATTR)),    # log-likelihood (signal | c)
        _Log(_nf._Attr(_nf._V(var_name), PRIOR_ATTR)),  # log-prior (c | context) = shared context
    ])


def _true_node() -> dict:
    """The unique TRUE candidate node (is_true == 1) — picked natively via Argmax over the marker
    so the recovery Term reads the true class without Python choosing it."""
    return _nf._Argmax(_cand_set(), "_t", _nf._Attr(_nf._V("_t"), TRUE_ATTR))


def posterior_recovery_term() -> dict:
    """recovery = P(true | signal, context) = exp(logpost_true) / Sum_c exp(logpost_c). The WHOLE
    Bayesian posterior — likelihood x prior in log-domain, normalised, read at the true class — as
    ONE held graph Term (Div of Exp(logpost at the true node) by Sum_c Exp(logpost(c)))."""
    # numerator: exp(logpost) at the true node. Reuse _logpost with the true node bound to its var.
    num = _Exp(_nf._Plus([
        _Log(_nf._Attr(_true_node(), LIK_ATTR)),
        _Log(_nf._Attr(_true_node(), PRIOR_ATTR)),
    ]))
    # denominator: Sum_c exp(logpost(c)) over the candidate set (fresh summation var).
    den = _nf._Sum(_cand_set(), "c", _Exp(_logpost("c")))
    return _nf._Div(num, den)


def posterior_argmax_term() -> dict:
    """The Bayes DECISION: Argmax_c of logpost(c) — the class the posterior names (used by the
    discriminative control's hard-accuracy check; same Argmax-of-score shape as the recovery)."""
    return _nf._Argmax(_cand_set(), "w", _logpost("w"))


# --------------------------------------------------------------------------- #
#  WORLD-ADAPTER GLUE — feed likelihoods + prior as attrs, evaluate the held Term.
# --------------------------------------------------------------------------- #

def _build(Substrate, n_cand, true_idx, likelihoods, prior):
    s = Substrate()
    nodes = []
    for i in range(n_cand):
        nid = s.add_node("Concept", {"idx": float(i)})
        s.set_attr(nid, CAND_ATTR, 1.0)
        s.set_attr(nid, TRUE_ATTR, 1.0 if i == true_idx else 0.0)
        s.set_attr(nid, LIK_ATTR, float(max(likelihoods[i], _EPS)))
        s.set_attr(nid, PRIOR_ATTR, float(max(prior[i], _EPS)))
        nodes.append(nid)
    return s, nodes


def posterior_recovery(Substrate, Pred, likelihoods, prior, true_idx) -> float:
    """Evaluate the held Bayes-posterior recovery Term: feed the per-candidate held likelihoods and
    the context message prior as graph attrs, return P(true | signal, context). The combine
    (log-lik + log-prior -> normalise -> true class) is the native Term; Python only marshals."""
    s, _ = _build(Substrate, len(likelihoods), true_idx, likelihoods, prior)
    return float(s.evaluate(Pred(posterior_recovery_term()), {}))


def posterior_predict(Substrate, Pred, likelihoods, prior, true_idx) -> int:
    """The Bayes hard decision (argmax of the posterior) via the held Term — returns the chosen
    candidate index (for the discriminative control's accuracy check)."""
    s, _ = _build(Substrate, len(likelihoods), true_idx, likelihoods, prior)
    pick = s.evaluate(Pred(posterior_argmax_term()), {})
    return int(round(s.node(pick)["attrs"]["idx"]))


# --------------------------------------------------------------------------- #
#  LISTENER LIKELIHOOD — the held recognizer, EXACTLY as pragmatic_speaker (no borrowed weights).
#  Returns an UN-normalised per-candidate likelihood vector (the prior does the normalising in the
#  Bayes Term). geometry = held AbS render-compare; learned = from-scratch head cosine.
# --------------------------------------------------------------------------- #

def fused_likelihoods(signal_strokes, support_point_sets, embed_fn, support_embeds, temp=0.05):
    """Per-candidate FUSED likelihood L(signal | c) for every support class, from the held listener
    channels (held AbS geometry + from-scratch learned head), as a softmax-shaped likelihood (the
    same temp/shape pragmatic_speaker uses, but kept as the FULL vector so the held Bayes Term can
    multiply by the prior). NOT normalised to the true class here — the Term normalises."""
    qps = _PS._strokes_point_set(signal_strokes)
    if qps is None:
        return None
    gsims = _np.array([-_abs.render_compare_score(qps, s) for s in support_point_sets], float)
    g = _PS._softmax(gsims, temp)
    if embed_fn is None or support_embeds is None or any(e is None for e in support_embeds):
        return g
    import domains.abs_learned_fusion as _F
    qv = embed_fn(signal_strokes)
    if qv is None:
        return g
    l = _PS._softmax(_F.cos_sims(qv, support_embeds), temp)
    return (g + l) / 2.0


def learned_likelihoods(signal_strokes, embed_fn, support_embeds, temp=0.05):
    """Per-candidate LEARNED-ONLY likelihood vector (the purest shared-model channel)."""
    import domains.abs_learned_fusion as _F
    if embed_fn is None or support_embeds is None or any(e is None for e in support_embeds):
        return None
    qv = embed_fn(signal_strokes)
    if qv is None:
        return None
    return _PS._softmax(_F.cos_sims(qv, support_embeds), temp)


# --------------------------------------------------------------------------- #
#  MESSAGE PRIORS — shared context as a distribution over the candidate set.
# --------------------------------------------------------------------------- #

def parametric_prior(n_cand: int, true_idx: int, peak: float, neighbour_idx=None,
                     n_neighbours: int = 3):
    """A concentration-controlled prior over the candidate set, FLAT->PEAKED-ON-TRUTH.
    `peak` in [0,1]: 0 = uniform (max entropy, no shared context), 1 = mass concentrated on the
    true class + its `n_neighbours` nearest candidates (a tight, correct shared expectation).
    The 'near neighbours' make it a realistic shared context (the audience expects the true message
    OR a near-confusable), not a point mass. neighbour_idx (a similarity ranking of candidates to
    the true class) supplies the neighbours; falls back to index-adjacency if absent."""
    p = _np.ones(n_cand, float) / n_cand
    if peak <= 0:
        return p
    mass = _np.ones(n_cand, float) * (1.0 - peak)            # residual uniform floor
    if neighbour_idx is None:
        nbrs = [(true_idx + k) % n_cand for k in range(1, n_neighbours + 1)]
    else:
        nbrs = [i for i in neighbour_idx if i != true_idx][:n_neighbours]
    mass[true_idx] += peak * 0.6 * n_cand
    for j in nbrs:
        mass[j] += peak * (0.4 / max(len(nbrs), 1)) * n_cand
    return mass / mass.sum()


def shuffled_prior(prior, true_idx: int, wrong_idx: int):
    """The DISCRIMINATIVE control prior: the SAME peakedness as `prior` but concentrated on the
    WRONG class. Swaps the true-class mass with a wrong candidate's mass (and rotates the peak's
    neighbourhood with it) so entropy/MI is identical but the shared context points at the wrong
    message. If the speaker still abbreviates here, recovery must collapse (genuine shared context
    vs mere prior sharpness)."""
    p = _np.asarray(prior, float).copy()
    p[true_idx], p[wrong_idx] = p[wrong_idx], p[true_idx]
    return p


def neighbour_prior(true_idx: int, support_point_sets, peak: float = 1.0):
    """A REAL held-context prior: the audience's expectation derived from the held AbS GEOMETRY
    between the SUPPORT exemplars themselves (context = 'the audience knows which shape-cluster the
    message lives in'). Prior(c) (softmax over candidates) of the held render-compare similarity of
    candidate c's exemplar to the TRUE class's exemplar — candidates geometrically near the true
    message get more prior mass, so peakedness varies NATURALLY with how isolated the true shape is
    in this episode. `peak` is an inverse-temperature on the similarity (sharper context = higher).
    This is an ACTUAL cue (held AbS, no borrowed data); the gate measures its MI per episode."""
    n = len(support_point_sets)
    ref = support_point_sets[true_idx]
    sims = _np.array([-_abs.render_compare_score(ref, s) for s in support_point_sets], float)
    sims[true_idx] = sims.max() + 1e-6     # the true message is the most-expected (self-similar)
    return _PS._softmax(sims, max(1.0 / max(peak, 1e-6), 1e-6))


def support_self_sims(support_point_sets):
    """The held-AbS self-similarity MATRIX between the support exemplars (sims[i][j] = -render_compare
    of exemplar i vs j) — computed ONCE per episode so neighbour_prior/neighbour_ranking can be
    derived per target without recomputing the expensive render-compare."""
    n = len(support_point_sets)
    sims = _np.zeros((n, n), float)
    for i in range(n):
        for j in range(n):
            sims[i, j] = -_abs.render_compare_score(support_point_sets[i], support_point_sets[j])
    return sims


def neighbour_prior_from_sims(self_sims, true_idx: int, peak: float = 1.0):
    """neighbour_prior but from a precomputed self-similarity matrix (see support_self_sims)."""
    sims = _np.asarray(self_sims, float)[true_idx].copy()
    sims[true_idx] = sims.max() + 1e-6
    return _PS._softmax(sims, max(1.0 / max(peak, 1e-6), 1e-6))


def neighbour_ranking_from_sims(self_sims, true_idx: int):
    sims = _np.asarray(self_sims, float)[true_idx]
    order = _np.argsort(-sims)
    return [int(i) for i in order if i != true_idx]


def neighbour_ranking(true_idx: int, support_point_sets):
    """Indices of candidates ranked by held-AbS similarity to the true class (nearest first,
    excluding the true class) — supplies parametric_prior's 'near neighbours' from REAL geometry."""
    ref = support_point_sets[true_idx]
    sims = _np.array([-_abs.render_compare_score(ref, s) for s in support_point_sets], float)
    order = _np.argsort(-sims)
    return [int(i) for i in order if i != true_idx]


# --------------------------------------------------------------------------- #
#  PEAKEDNESS IN BITS — entropy / mutual information of the prior (the measured axis).
# --------------------------------------------------------------------------- #

def entropy_bits(p):
    """H(p) in bits."""
    p = _np.asarray(p, float)
    p = p[p > 0]
    return float(-(p * _np.log2(p)).sum())


def context_mi_bits(priors):
    """MI(context; message) in bits over a set of per-context priors (each a distribution over the
    SAME candidate set, one per context/episode, equally likely contexts):
        MI = H(message) - H(message | context)
    H(message|context) = mean over contexts of H(prior_context); H(message) = H of the average prior
    (the marginal). A FLAT prior in every context -> MI 0 (context tells you nothing); a sharply
    peaked, context-VARYING prior -> high MI (context narrows the message)."""
    P = _np.asarray(priors, float)
    marginal = P.mean(0)
    H_msg = entropy_bits(marginal)
    H_msg_given_ctx = float(_np.mean([entropy_bits(p) for p in P]))
    return H_msg - H_msg_given_ctx, H_msg, H_msg_given_ctx


__all__ = [
    "LIK_ATTR", "PRIOR_ATTR", "CAND_ATTR", "TRUE_ATTR",
    "posterior_recovery_term", "posterior_argmax_term",
    "posterior_recovery", "posterior_predict",
    "fused_likelihoods", "learned_likelihoods",
    "parametric_prior", "shuffled_prior", "neighbour_prior", "neighbour_ranking",
    "entropy_bits", "context_mi_bits",
]
