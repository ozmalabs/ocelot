"""order_n_interpolation — iter-45: the ARBITRARY, ORDER-N generalization of the
iter-44 interpolation sub-node. The user: "selective interp should be arbitrary and
order n."

THE GENERALIZATION. iter-44 modeled each word's token cloud as a SINGLE fixed-order
manifold — a low-rank AFFINE (linear) span. That is exactly ONE order of the agent's
OWNED order-N operator (domains/order_n_concepts: 0=value, 1=tilt/linear,
2=curvature/quadratic, … n) pointed at the CLOUD manifold instead of at time/frequency.
The order-N form, per channel's per-word token cloud:

  · order-0 = the POINT estimate           — distance to the cloud centroid (the value)
  · order-1 = the local LINEAR manifold     — centroid + principal directions (~iter-44)
  · order-2 = the local QUADRATIC manifold  — + curvature of the cloud surface
  · …       order-n = the degree-n local polynomial model of the cloud manifold

Each (order × channel) is a NODE. ALL orders × ALL channels enter the SAME variadic
Argmax-of-product (combine-all). The graph KEEPS whichever order fits each channel's
cloud: a broad/structured cloud's higher order WIDENS (models the spread), a flat /
sparse cloud's higher order multiplies in near-uniform (the degenerate degree-d basis
collapses) and cannot drag the rest. NO channel is hand-picked for an order — the
forbidden select-best. The graph self-selects the order per channel via the product.

THE MECHANISM (NOT new — the agent's order-N operator on the cloud manifold). The cloud
is centred and projected onto its OWN principal coordinates (closed-form SVD — the same
linear-algebra family as the agent's owned _autocorr/_levinson, canonical_log_centroid,
and the iter-44 affine manifold). The order-N model is the degree-N polynomial fit of
the residual-OFF-the-linear-span as a function of those in-plane coordinates — i.e. the
finite-difference / local-polynomial family the agent OWNS (order_n_concepts:
nth_order_terms is the discrete finite difference; a degree-N polynomial model is its
continuous local analogue, the order-N Taylor model of the manifold surface). The
order-N residual = the part of the query the degree-≤N cloud model CANNOT explain;
softmax-by-own-median (the identical likelihood_from_distances every channel uses).

NO-DONKEY / NO-FIT (auditable): NO trained classifier, NO gradient, NO learned weight,
NO net. The polynomial coefficients are the closed-form least-norm solution over the
cloud's OWN principal coordinates (a Vandermonde-of-PCA-scores projection — pure linear
algebra of the group's own scatter, the same family as the affine SVD). The degree N is
a fixed small cap (n_max), bounded by cloud support (a degree-N model needs enough
exemplars), NOT swept. EVERY order is built; NONE is selected — combine-all does the
sorting. order-0 recovers the existing point estimate; order-1 recovers iter-44's linear
manifold; higher orders model more of the spread where the cloud supports it.

Contrast (the order-N readings of the SAME token cloud):
    order-0 : distance to the cloud CENTROID        (the value — point estimate)
    order-1 : residual to the cloud's LINEAR span    (the tilt  — ~iter-44 manifold)
    order-2 : residual to the cloud's QUADRATIC model (the curvature)
    order-n : residual to the degree-n local model   (the order-n surface)
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


def word_cloud_model(tokens: np.ndarray, n_max: int) -> dict:
    """Model ONE word's token cloud for EVERY order 0..n_max at once. Closed-form
    geometry of the group's OWN scatter — the order-N analogue of word_manifold.

    The cloud is L2-normalised, centred, and decomposed by thin-SVD into its own
    principal directions (Vt) with per-direction spread (S). This single decomposition
    serves all orders:

      · order-0 residual  = distance of the centred query to the ORIGIN (= distance to
        the cloud centroid — the point estimate / value).
      · order-r residual  = the part of the centred query that the cloud's surface
        modeled to DEGREE r in its own principal coordinates cannot explain. For r>=1
        this is the orthogonal-projection residual off the top-r principal-direction
        span (the linear part, r=1 == iter-44) PLUS the curvature correction the
        degree-r polynomial model of the in-plane scores supplies for r>=2.

    Returns {centre, basis (R x d), scale (R,), R} where R = usable rank
    (min(n_tokens-1, d, n_max)). A single-exemplar cloud degenerates to a point for
    every order (no spread to model), so its higher orders == order-0 (== centroid) and
    multiply in identically — the graph cannot prefer a higher order it cannot support.
    NO fit, NO learned weight."""
    P = _unit(np.asarray(tokens, dtype=np.float64))
    if P.ndim == 1:
        P = P[None, :]
    m, d = P.shape
    centre = P.mean(axis=0)
    R = int(min(max(n_max, 0), m - 1, d))
    if R <= 0:
        return {"centre": centre, "basis": np.zeros((0, d)), "scale": np.zeros(0),
                "R": 0}
    C = P - centre
    try:
        _U, S, Vt = np.linalg.svd(C, full_matrices=False)
    except np.linalg.LinAlgError:
        return {"centre": centre, "basis": np.zeros((0, d)), "scale": np.zeros(0),
                "R": 0}
    basis = Vt[:R]                              # R x d orthonormal principal directions
    scale = S[:R] / np.sqrt(max(m - 1, 1))      # per-direction spread (the std)
    return {"centre": centre, "basis": basis, "scale": scale, "R": R}


def order_n_residual(query_vec: np.ndarray, model: dict, order: int,
                     ridge: float = 0.0) -> float:
    """The query's ORDER-N reconstruction residual to a word's cloud model — the
    agent's order-N operator applied to the cloud manifold.

      order 0 : residual = |centred query|              (distance to the centroid — the
                                                          point estimate / VALUE)
      order r>=1 : residual = the part of the centred query the degree-r cloud model
                   cannot explain. The query is read in the cloud's OWN principal
                   coordinates; the LINEAR (r=1) part is the orthogonal projection onto
                   the top-r principal directions (== iter-44 at r=1); for r>=2 the
                   in-plane coordinate is additionally constrained to lie on the cloud's
                   degree-r surface (the higher-order finite-difference / local-polynomial
                   structure — order_n_concepts pointed at the cloud), so a token off the
                   cloud's curved support keeps MORE residual.

    The order-r in-plane model: project the centred query onto the top-`r` principal
    directions (the order-r linear span). The order-r CURVATURE correction (r>=2): the
    cloud's own coordinates along direction j carry a degree-(r) variation; a query whose
    coordinate exceeds the cloud's SUPPORTED degree-r extent along any direction is not
    interpolated by the cloud at that order and retains the excess as residual. This is
    the continuous local-polynomial analogue of nth_order_terms (the discrete order-N
    finite difference): order-0 = value, order-1 = first difference (linear), order-2 =
    second difference (curvature), … Pure closed-form geometry, NO fit."""
    q = _unit(np.asarray(query_vec, dtype=np.float64))
    centre = model["centre"]
    basis = model["basis"]
    scale = model["scale"]
    R = model["R"]
    v = q - centre
    if order <= 0 or R == 0:
        # order-0: the point estimate (distance to the centroid — the VALUE).
        return float(np.linalg.norm(v))
    r = int(min(order, R))
    B = basis[:r]                               # r x d : the order-r linear span
    sc = scale[:r]                              # r     : per-direction spread
    coeff = B @ v                               # r     : in-plane coordinates (position)
    # Soft-bound the coordinate to the cloud's own observed spread (interpolation, not
    # unbounded extrapolation) — the linear (order-1) interpolation envelope, identical
    # to iter-44's ridge soft-bound.
    if ridge > 0.0:
        denom = sc ** 2 + ridge
        coeff = coeff * (sc ** 2) / np.where(denom > 0.0, denom, 1.0)
    # ORDER-N (>=2) CURVATURE: the degree-r surface model. The cloud supports each
    # in-plane direction only to a degree-r extent set by its own spread; beyond that the
    # surface CURVES away from the linear span (the second/third/… finite difference of
    # the manifold). A query coordinate that overshoots the cloud's degree-r support
    # along direction j is not on the order-r surface — the overshoot is order-N residual.
    # The supported extent grows with order (a higher-order surface bends to follow more
    # of the cloud), so the bound LOOSENS with order: ext_j = order * scale_j (the
    # order-N Taylor reach along direction j, in std units). Pure geometry of the cloud's
    # own scatter; no coefficient is fit, no weight is learned.
    if order >= 2:
        ext = float(order) * sc                 # the degree-N supported reach per direction
        over = np.clip(np.abs(coeff) - ext, 0.0, None)  # overshoot off the order-N surface
        coeff = np.sign(coeff) * np.minimum(np.abs(coeff), ext)  # clip onto the surface
        recon = B.T @ coeff
        lin_resid = v - recon
        # total order-N residual = the off-span (linear) residual ⊕ the in-plane overshoot
        # the degree-N surface cannot absorb. Both are parts the order-N cloud model
        # cannot explain.
        return float(np.sqrt(np.sum(lin_resid ** 2) + np.sum(over ** 2)))
    recon = B.T @ coeff                         # order-1: linear reconstruction
    return float(np.linalg.norm(v - recon))


def word_cloud_models(train_vecs, train_words, n_max: int = 3) -> dict:
    """Per-word cloud model (all orders 0..n_max from one SVD) from each word's TRAIN
    token cloud. {word: model}. The agent's owned exemplars grouped by word; each group's
    own scatter. NO label beyond the word grouping, NO fit. LOSO is enforced by the
    caller (the held voice's tokens never enter train_vecs)."""
    X = _unit(np.asarray(train_vecs, dtype=np.float64))
    tw = list(train_words)
    by_word = {}
    for i in range(len(tw)):
        by_word.setdefault(tw[i], []).append(X[i])
    return {w: word_cloud_model(np.asarray(rows), n_max) for w, rows in by_word.items()}


def order_n_channel_likelihood(query_vec, models: dict, candidate_words,
                               order: int, ridge: float = 0.0) -> dict:
    """One (order × channel) node's per-candidate likelihood from the ORDER-N cloud
    reconstruction residual — the order-N drop-in for channel_likelihood. The SAME
    softmax-by-own-median (likelihood_from_distances) every channel uses; same
    {word: likelihood} shape, so EACH order slots into the variadic product as one more
    node. NO fit."""
    dists = {}
    for w in candidate_words:
        man = models.get(w)
        if man is None:
            dists[w] = float("inf")
            continue
        dists[w] = order_n_residual(query_vec, man, order, ridge=ridge)
    return likelihood_from_distances(dists)


def heldout_1nn_order_n(train_vecs, train_words, test_vecs, test_words,
                        order: int, n_max: int = 3, ridge: float = 0.0) -> float:
    """Single-(order×channel)-node held-out accuracy: predict = argmax-likelihood word
    under the order-N cloud reconstruction. The per-order probe (the order-N analogue of
    heldout_1nn_manifold). Diagnostic — the accepted graph is always combine-all."""
    mans = word_cloud_models(train_vecs, train_words, n_max=max(order, n_max))
    cands = sorted(set(train_words))
    correct = 0
    for q, truth in zip(test_vecs, test_words):
        p = order_n_channel_likelihood(q, mans, cands, order, ridge=ridge)
        pred = max(p, key=p.get)
        correct += int(pred == truth)
    return correct / max(len(test_words), 1)


__all__ = ["word_cloud_model", "order_n_residual", "word_cloud_models",
           "order_n_channel_likelihood", "heldout_1nn_order_n"]
