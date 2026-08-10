"""frame_inference_v2 — recognition as a COLLAPSE over the WEIGHTED ADMISSIBILITY
of MULTIPLE soft-excluder frames (NOT a single frame, NOT a dot product).

THE THEORY (faithful instantiation):
  · v1 showed a single SPEAKER-RELATIVE frame beats removal but UNDER-determines
    (it never reaches absolute recognition). One frame is not enough.
  · The power is the INTERSECTION of MANY frames. But the combine is NOT a dot
    product (a scalar weighted SUM of positive scores = the premature collapse).
    It is WEIGHTED ADMISSIBILITY: each frame is a SOFT EXCLUDER over the candidate
    digits — it ABSTAINS where unsure (leaves everything admissible) and EXCLUDES
    where confident (carves a candidate down). A cue can never HELP a wrong answer
    by adding positive mass; it can only REMOVE admissibility. The frames are
    INTERSECTED (their soft exclusions accumulate) and kept SOFT until the final
    argmax / Viterbi.

REPRESENTATION OF A FRAME (the owned op): a soft excluder is a per-candidate
LOG-ADMISSIBILITY vector e in (-inf, 0]^K:
    e[k] == 0      -> candidate k is FULLY admissible under this frame (no evidence
                      against it; the ABSTAIN limit).
    e[k] <  0      -> candidate k is EXCLUDED to degree -e[k] (this frame carves it).
This is the log of a survival/admissibility mass in (0,1]. Building it from a
positive cue is the owned move: take the cue's per-candidate score s[k] >= 0,
normalise to its own max (admissibility = s[k] / max_j s[j] in (0,1]), take log.
The best-supported candidate sits at e==0 (admissible, abstain); every worse
candidate is carved BELOW it. No candidate is ever pushed ABOVE admissible — a
cue can only exclude, never boost. ABSTAIN (a flat cue, all s equal) -> e all 0.

VECTOR-WEIGHTED INTERSECTION (the collapse, owned ops only):
    E_total[k] = SUM_f  w_f[k] * e_f[k]          (w_f a per-contrast VECTOR weight)
The weight is a VECTOR (per candidate / per contrast), not a scalar — a frame may
be reliable for some contrasts and abstain on others. Summing LOG-admissibilities
is INTERSECTION of admissibility masses (PROD of survival probs); each term is
<= 0, so each frame can only carve, never lift. Kept soft; the final argmax (or
Viterbi over a sequence) reads the surviving weighted-admissible candidate.

THE DOT-PRODUCT CONTROL (the thing we claim to beat): treat each frame as a
positive per-candidate SCORE and combine by a SCALAR weighted SUM:
    score[k] = SUM_f  a_f * s_f[k]               (a_f a SCALAR weight)
    predict  = argmax_k score[k]
This is the premature collapse: positive scores added, a good score on one frame
can RESCUE a wrong candidate another frame excluded (no veto, no intersection).

DONKEY BOUNDARY: frames = owned models (acoustic = v1 relative reading + 1-NN
distances = owned DSP; context/future = owned bigram counts; prior = owned
unigram counts). The soft-exclude / vector-weight / intersect / argmax / Viterbi
combine = owned numpy ops. NO net, NO fit, NO gradient, NO sweep-and-keep-best
(the peakiness/lookahead sweeps REPORT the surface; the combine itself has no
tuned parameter). Recognition is the agent's. Sequence structure is the WORLD's
(an imposed bigram, stated honestly). Held-out speakers never banked.
"""
from __future__ import annotations

import numpy as np


# ===========================================================================
# OWNED OP — build a SOFT EXCLUDER (log-admissibility vector) from a positive
# per-candidate cue. Admissibility = cue / max(cue) in (0,1]; e = log(adm).
# The best candidate sits at e==0 (admissible/abstain target); worse candidates
# carved below. A flat cue (no evidence) -> e all 0 (full abstain). A cue can
# ONLY exclude, never boost above admissible.
# ===========================================================================

_EPS = 1e-9
_FLOOR = -30.0  # log-admissibility floor (an excluded candidate, not -inf, so a
#                 single frame can never make a candidate strictly impossible —
#                 soft, recoverable by other frames).


def soft_exclude_from_score(score, abstain_tol=1e-6):
    """score: (K,) NON-NEGATIVE per-candidate support (higher = more admissible).
    Returns e: (K,) log-admissibility in [_FLOOR, 0]. The max-support candidate ->
    e==0 (admissible); others carved by log(support/max). If the cue is ~flat
    (max-min < abstain_tol*max) the frame ABSTAINS: e all 0 (no evidence to carve
    with). Owned ops: normalise, log, clip."""
    s = np.asarray(score, dtype=np.float64)
    K = s.shape[0]
    s = np.clip(s, 0.0, None)
    mx = float(s.max()) if K else 0.0
    if mx <= _EPS:
        return np.zeros(K, dtype=np.float64)              # no support anywhere -> abstain
    mn = float(s.min())
    if (mx - mn) <= abstain_tol * mx:
        return np.zeros(K, dtype=np.float64)              # flat cue -> abstain
    adm = np.clip(s / mx, np.exp(_FLOOR), 1.0)            # admissibility in (0,1]
    return np.clip(np.log(adm), _FLOOR, 0.0)


def soft_exclude_from_distance(dist, scale=None):
    """dist: (K,) per-candidate DISTANCE (lower = better, the 1-NN acoustic read).
    Convert to a soft excluder directly in log-admissibility space WITHOUT going
    through a positive score: the closest candidate is admissible (e==0), every
    other carved by -(d_k - d_min)/scale (further => more excluded). scale defaults
    to the spread of the finite distances (an owned, data-derived normaliser, NOT a
    tuned knob: it is the MAD-like spread of THIS read). inf distances -> _FLOOR."""
    d = np.asarray(dist, dtype=np.float64)
    K = d.shape[0]
    finite = d[np.isfinite(d)]
    if finite.size == 0:
        return np.zeros(K, dtype=np.float64)              # nothing read -> abstain
    dmin = float(finite.min())
    if scale is None:
        spread = float(np.median(np.abs(finite - np.median(finite)))) * 1.4826
        scale = spread if spread > _EPS else (float(finite.std()) + _EPS)
    if scale <= _EPS:
        scale = 1.0
    e = np.full(K, _FLOOR, dtype=np.float64)
    fin = np.isfinite(d)
    e[fin] = -(d[fin] - dmin) / scale
    return np.clip(e, _FLOOR, 0.0)


def score_from_soft_exclude(e):
    """The DOT-PRODUCT control needs a POSITIVE per-candidate score from the same
    cue. We take the admissibility mass adm = exp(e) in (0,1] — the SAME information
    the soft excluder carries, but as a positive score the scalar weighted sum can
    add (and so let a high score on one frame RESCUE a candidate another excluded).
    This is the honest control: same per-frame information, scalar-positive combine."""
    return np.exp(np.asarray(e, dtype=np.float64))


# ===========================================================================
# THE COLLAPSE — vector-weighted INTERSECTION of soft excluders (sum of weighted
# log-admissibilities). Each term <= 0, so every frame can only carve. Kept soft.
# ===========================================================================

def weighted_admissibility(excluders, weights):
    """excluders: list of (K,) log-admissibility vectors (each <= 0).
    weights: list of either a SCALAR or a (K,) VECTOR weight per frame (>= 0).
    Returns E_total: (K,) = SUM_f w_f (*) e_f — the intersected weighted
    admissibility (still <= 0). The collapse is SOFT (a log-admissibility vector,
    not yet an argmax). Owned ops: broadcast-multiply, sum."""
    if not excluders:
        return None
    K = excluders[0].shape[0]
    tot = np.zeros(K, dtype=np.float64)
    for e, w in zip(excluders, weights):
        wv = np.asarray(w, dtype=np.float64)
        tot = tot + wv * np.asarray(e, dtype=np.float64)
    return tot


def dot_product_combine(scores, weights):
    """The CONTROL. scores: list of (K,) NON-NEGATIVE per-candidate scores.
    weights: list of SCALAR weights (the dot-product is a scalar weighted sum; a
    vector weight here would just be a different positive combine, still not an
    intersection — the control is faithfully the scalar dot product). Returns
    (K,) = SUM_f a_f * s_f. argmax over this is the premature scalar collapse."""
    if not scores:
        return None
    K = scores[0].shape[0]
    tot = np.zeros(K, dtype=np.float64)
    for s, a in zip(scores, weights):
        tot = tot + float(a) * np.asarray(s, dtype=np.float64)
    return tot


# ===========================================================================
# SEQUENCE DECODE — Viterbi over the per-position SOFT admissibilities. The
# acoustic frame is per-position (depends on the clip at that position); the
# context/future frames are TRANSITION admissibilities (depend on neighbours).
# We decode the most-admissible path. For the weighted-admissibility regime the
# emission is the intersected log-admissibility (acoustic (+) prior, vector-
# weighted) and the transition is the (vector-weighted) bigram log-admissibility.
# Owned ops: dynamic programme over log-admissibilities (a max-sum Viterbi).
# ===========================================================================

def viterbi_soft(emission, trans_logadm, w_trans=1.0):
    """emission: (T, K) per-position log-admissibility (<= 0), already the
    intersected acoustic (+) prior (+) any per-position frame.
    trans_logadm: (K, K) bigram log-admissibility, trans[a, b] = how admissible
    b is GIVEN predecessor a (<= 0; 0 = fully admissible transition, negative =
    excluded). w_trans: scalar or (K,K) vector weight on the transition frame.
    Returns the decoded path (list of length T of candidate indices) by max-sum
    Viterbi over log-admissibilities. This realises the CONTEXT frame (predecessor
    constrains) AND, run consistently, the future frame (successor constrains) —
    the forward+backward sheaf is folded into the bidirectional transition term
    below; here Viterbi handles the predecessor direction and the future frame is
    supplied as an extra emission excluder by the caller."""
    T, K = emission.shape
    if T == 0:
        return []
    wt = np.asarray(w_trans, dtype=np.float64)
    Tr = wt * trans_logadm if trans_logadm is not None else np.zeros((K, K))
    dp = np.empty((T, K), dtype=np.float64)
    bp = np.zeros((T, K), dtype=np.int64)
    dp[0] = emission[0]
    for t in range(1, T):
        # for each current b: best over predecessor a of dp[t-1,a] + Tr[a,b]
        cand = dp[t - 1][:, None] + Tr            # (K_prev, K_cur)
        bp[t] = np.argmax(cand, axis=0)
        dp[t] = emission[t] + cand[bp[t], np.arange(K)]
    path = [int(np.argmax(dp[T - 1]))]
    for t in range(T - 1, 0, -1):
        path.append(int(bp[t][path[-1]]))
    path.reverse()
    return path


__all__ = [
    "soft_exclude_from_score", "soft_exclude_from_distance",
    "score_from_soft_exclude", "weighted_admissibility", "dot_product_combine",
    "viterbi_soft", "_FLOOR",
]
