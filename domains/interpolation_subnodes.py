"""interpolation_subnodes — iter-44: INTERPOLATION sub-nodes that MODEL each word's
token cloud as a CONTINUOUS manifold, so the per-speaker / coarticulation variation
becomes a readable COORDINATE (signal) instead of NOISE.

THE USER'S INSIGHT: "noise is just signal you don't understand; the graph needs
interpolation sub-nodes." The per-word token cloud (the spread of a word's exemplars
across speakers and coarticulation contexts) carries continuous structure — the VTL
continuum, the coarticulation continuum. The two reflexes both FAIL on it:

  · 1-NN over RAW tokens (the CURRENT graph)  IGNORES the cloud's structure — it only
    sees the single nearest exemplar, so a held-out-speaker token between train
    exemplars matches whichever raw token is nearest (often a wrong-word same-speaker
    token).
  · CENTROID-averaging the cloud (iter-41)    DESTROYS the structure — collapsing the
    cloud to one point under-fits the strong channels (the cloud IS signal), so it
    HURT (-0.122 on FSDD).
  · SHARPENING the axis (iter-43, all-pole)    is REDUNDANT — a sharper point-estimate
    of one token doesn't MODEL the spread (drop-it Δ ~+0.00).

THE FIX — MODEL the variation. An interpolation sub-node represents each candidate
word's token cloud as a low-dimensional AFFINE MANIFOLD (the cloud's own principal
directions through its centre — the continuous structure BETWEEN the discrete
exemplars). A heard token is recognised by WHERE IT INTERPOLATES within each word's
manifold: its RECONSTRUCTION distance to the manifold (how well the token is explained
as a convex/affine combination of that word's cloud) is the channel's distance. This
MODELS the spread (helps) where centroid AVERAGES it (hurt) and 1-NN IGNORES it (the
current).

NO-DONKEY / NO-FIT: the manifold is composable GEOMETRY of the agent's OWN exemplars.
The per-word model is centroid + top-r principal directions of the CENTERED cloud
(closed-form thin-SVD of the cloud matrix — the same linear-algebra family as the
agent's owned _autocorr/_levinson and canonical_log_centroid; eigen-decomposition of a
group's own scatter, NOT a trained classifier, NO gradient, NO learned weight, NO net).
The reconstruction distance is an orthogonal-projection residual — pure geometry. The
rank r is bounded by the cloud size (r <= n_tokens-1), a fixed small cap, NOT swept.

DROP-IN: centroid_channel_likelihood / channel_likelihood have the SAME signature shape
— manifold_channel_likelihood returns the SAME {word: likelihood} dict (softmaxed by
its OWN median residual via the identical likelihood_from_distances every channel uses),
so it slots into the variadic Argmax-of-product as one more sub-node, combine-all, the
recognition decision Term UNCHANGED.

Contrast made explicit (the three readings of the SAME token cloud):
    1-NN      : distance to the NEAREST raw exemplar        (ignores spread)
    centroid  : distance to the cloud's MEAN point          (averages spread away)
    manifold  : distance to the cloud's affine SPAN         (MODELS the spread)
"""
from __future__ import annotations

import numpy as np

from domains.many_settings_recognizer import likelihood_from_distances


def _unit(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=np.float64)
    if X.ndim == 1:
        n = np.linalg.norm(X)
        return X / n if n > 1e-9 else X
    return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)


def word_manifold(tokens: np.ndarray, rank: int) -> dict:
    """Model ONE word's token cloud as an AFFINE MANIFOLD: the cloud centroid + the
    top-`rank` principal directions of the CENTERED cloud (the continuous structure
    BETWEEN the exemplars — the VTL / coarticulation continuum). Closed-form thin-SVD
    of the centered cloud matrix; NO fit, NO learned weight. The effective rank is
    capped at n_tokens-1 (an affine span of m points has dimension <= m-1), so a
    single-exemplar cloud degenerates to a point (= the centroid), a 2-exemplar cloud
    to the line between them, etc. — interpolation only where the cloud supports it.

    Returns {centre, basis (r x d, orthonormal), scale (r, the per-direction spread)}.
    Tokens are L2-normalised first so the manifold lives on the same unit-cosine
    geometry every channel's 1-NN / centroid uses."""
    P = _unit(np.asarray(tokens, dtype=np.float64))
    if P.ndim == 1:
        P = P[None, :]
    m, d = P.shape
    centre = P.mean(axis=0)
    r = int(min(rank, m - 1, d))
    if r <= 0:
        # single exemplar (or rank 0): the manifold IS the point — no spread to model.
        return {"centre": centre, "basis": np.zeros((0, d)), "scale": np.zeros(0)}
    C = P - centre                              # centre the cloud
    # thin SVD: C = U S Vt; the rows of Vt are the cloud's principal DIRECTIONS, S the
    # per-direction spread (the continuous extent of the cloud along each axis). Pure
    # closed-form geometry of the group's OWN scatter — no model fit.
    try:
        _U, S, Vt = np.linalg.svd(C, full_matrices=False)
    except np.linalg.LinAlgError:
        return {"centre": centre, "basis": np.zeros((0, d)), "scale": np.zeros(0)}
    basis = Vt[:r]                              # r x d orthonormal principal directions
    scale = S[:r] / np.sqrt(max(m - 1, 1))      # per-direction std (the spread)
    return {"centre": centre, "basis": basis, "scale": scale}


def word_manifolds(train_vecs, train_words, rank: int = 3) -> dict:
    """Build a per-word affine manifold from the TRAIN token cloud of each word.
    {word: manifold}. The agent's owned exemplars, grouped by word; each group's own
    principal directions. NO label beyond the word grouping, NO fit. LOSO is enforced
    by the caller (the held voice's tokens never enter train_vecs)."""
    X = _unit(np.asarray(train_vecs, dtype=np.float64))
    tw = list(train_words)
    by_word = {}
    for i in range(len(tw)):
        by_word.setdefault(tw[i], []).append(X[i])
    return {w: word_manifold(np.asarray(rows), rank) for w, rows in by_word.items()}


def manifold_residual(query_vec: np.ndarray, manifold: dict,
                      ridge: float = 0.0) -> float:
    """The heard token's INTERPOLATED FIT to a word's manifold = its RECONSTRUCTION
    distance: project the centered query onto the manifold's affine span (the
    orthogonal projection onto the principal directions) and measure the residual that
    the span CANNOT explain. SMALL residual = the token interpolates within this word's
    cloud (it lies on the manifold — the variation is explained as a coordinate); LARGE
    residual = the token is off this word's manifold. Pure geometry (an
    orthogonal-projection residual), NO fit.

    The in-plane coefficients basis @ centered are the token's POSITION on the manifold
    (the recovered variation coordinate — the speaker/coarticulation coordinate). They
    are bounded to the cloud's own observed spread (`ridge`>0 tightens to interpolation
    rather than unbounded extrapolation) so the residual measures fit to the cloud's
    SUPPORTED region, not to its infinite linear extension."""
    q = _unit(np.asarray(query_vec, dtype=np.float64))
    centre = manifold["centre"]
    basis = manifold["basis"]                   # r x d orthonormal
    v = q - centre
    if basis.shape[0] == 0:
        # degenerate point-manifold: residual = distance to the centre (= the centroid
        # special case — single-exemplar words can't be interpolated).
        return float(np.linalg.norm(v))
    coeff = basis @ v                           # r: the in-plane coordinates (position)
    if ridge > 0.0:
        # soft-bound the coordinate to the cloud's own spread (interpolation, not wild
        # extrapolation): shrink each coordinate toward the observed per-direction
        # std. A token whose coordinate vastly exceeds the cloud's spread is NOT well
        # interpolated, so it keeps more residual.
        scale = manifold["scale"]
        denom = scale ** 2 + ridge
        coeff = coeff * (scale ** 2) / np.where(denom > 0, denom, 1.0)
    recon = basis.T @ coeff                     # the projection back into the space
    residual = v - recon
    return float(np.linalg.norm(residual))


def manifold_channel_likelihood(query_vec, manifolds: dict, candidate_words,
                                ridge: float = 0.0) -> dict:
    """The channel's per-candidate likelihood from INTERPOLATION-MANIFOLD reconstruction
    distance — the drop-in interpolation replacement for channel_likelihood /
    centroid_channel_likelihood. D_c(s,w) = the reconstruction residual of the query to
    word w's affine manifold; the SAME softmax-by-own-median (likelihood_from_distances)
    every channel uses. Same {word: likelihood} output shape, so it slots into the
    variadic product unchanged. NO fit."""
    dists = {}
    for w in candidate_words:
        man = manifolds.get(w)
        if man is None:
            dists[w] = float("inf")
            continue
        dists[w] = manifold_residual(query_vec, man, ridge=ridge)
    return likelihood_from_distances(dists)


def heldout_1nn_manifold(train_vecs, train_words, test_vecs, test_words,
                         rank: int = 3, ridge: float = 0.0) -> float:
    """Single-channel held-out accuracy using INTERPOLATION MANIFOLD reconstruction
    instead of raw token 1-NN — the per-channel interpolation probe (the manifold
    analogue of heldout_1nn / heldout_1nn_centroid). Predict = argmax-likelihood word."""
    mans = word_manifolds(train_vecs, train_words, rank=rank)
    cands = sorted(set(train_words))
    correct = 0
    for q, truth in zip(test_vecs, test_words):
        p = manifold_channel_likelihood(q, mans, cands, ridge=ridge)
        pred = max(p, key=p.get)
        correct += int(pred == truth)
    return correct / max(len(test_words), 1)


__all__ = ["word_manifold", "word_manifolds", "manifold_residual",
           "manifold_channel_likelihood", "heldout_1nn_manifold"]
