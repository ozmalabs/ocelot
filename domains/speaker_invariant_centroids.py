"""speaker_invariant_centroids — iter-41: CROSS-SPEAKER CLUSTERING of the cue-graph
evidence into SPEAKER-INVARIANT centroids (the agent's own #1-ranked frontier pick:
unsupervised-clustering / cross-speaker-clustering, payoff 82).

THE BOUND (iter-40 + the agent's live order-N derivative + the human reading converge):
feature-space DISCRIMINATION. The cue-graph's per-channel evidence is a 1-NN over the
RAW train EXEMPLARS — and those exemplars are per-SPEAKER tokens. A held-out-speaker
query therefore matches its single nearest TOKEN, which is frequently a same-speaker /
different-word token rather than a different-speaker / same-word token: the raw
feature-space nodes cannot discriminate SPEAKER-INVARIANTLY. This is the gammatone-wall
/ speaker-norm central perception problem, localised in the channel evidence itself.

THE LEVER (the agent's owned machinery, composable, NO-FIT):
  CROSS-SPEAKER CLUSTERING. The agent's frontier ranker picks "an unlabelled
  DISTRIBUTION has recoverable LATENT structure — clustering carves its categories at
  the valleys between modes; across speakers, the same word's tokens are ONE cluster."
  In TRAIN the word label IS known, so the cluster assignment is given and the
  clustering collapses to its no-fit special case: the cluster prototype is the GROUP
  MEAN — the SAME exemplar-average form the agent already owns (axs_channel's
  _axs_word_model = per-word mean trajectory). The only refinement the BOUND dictates:
  cluster ACROSS speakers so the centroid sits at the speaker-INVARIANT centre, not at
  one speaker's token cloud. Two faithful instances:

    · WORD centroid (per-speaker-mean then pool): each TRAIN speaker contributes one
      prototype per word (its per-speaker mean token); the word's speaker-invariant
      centroid = the MEAN of those per-speaker prototypes. Each speaker weighs equally,
      so the centroid is the cross-speaker centre of the word's cluster, not biased to
      the speaker with the most tokens. D_c(s,w) = cosine distance to that centroid.

    · SUB-WORD k-prototypes (k>1 per word): if a word's cross-speaker tokens form
      several modes (e.g. dialect / allophone variants), one centroid under-fits.
      k prototypes per word = k cross-speaker clusters (k-means over the per-speaker
      prototypes, NO label needed beyond the word — still no model fit, just the
      group's own modes). D_c(s,w) = MIN distance to that word's k prototypes. k=1
      recovers the single-centroid case exactly.

NO-FIT / NO-DONKEY: there is no trained classifier, no learned weight, no gradient, no
megaweight fit. The prototypes are GROUP MEANS (and, for k>1, Lloyd iterations over
those means — the textbook unsupervised clusterer, deterministic, seeded, no labels
beyond the word grouping the train set already carries). The recognition DECISION is
UNCHANGED — the same variadic Argmax-of-product over the same per-channel softmax
likelihoods; ONLY the channel's distance source changes from raw-token-1-NN to
cross-speaker-centroid distance. Drop-in: it produces the SAME {word: likelihood} dict
shape channel_likelihood produces, so it slots into heldout_combined unchanged.

This is the agent's own pick (cross-speaker clustering), enacting the convergent bound
(feature-space speaker-invariance), as a composable no-fit transform of the channel
evidence — not a new recogniser, not a net, not a donkey.
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


def word_speaker_prototypes(train_vecs, train_words, train_speakers):
    """Per (word, speaker) prototype = the L2-normalised MEAN of that speaker's tokens
    of that word, in the channel's feature space. The first clustering level: a
    speaker's repeated tokens of a word ARE one within-speaker cluster, prototype =
    its mean. Returns {word: [proto_vec, ...]} (one per speaker that has the word)."""
    Xn = _unit(np.asarray(train_vecs, dtype=np.float64))
    tw = list(train_words)
    ts = list(train_speakers)
    by_ws = {}
    for i in range(len(tw)):
        by_ws.setdefault((tw[i], ts[i]), []).append(Xn[i])
    out = {}
    for (w, _s), rows in by_ws.items():
        proto = _unit(np.mean(np.asarray(rows), axis=0))
        out.setdefault(w, []).append(proto)
    return out


def _kmeans(points: np.ndarray, k: int, seed: int = 0, iters: int = 25):
    """Textbook Lloyd k-means over unit vectors (cosine geometry), deterministic.
    NO label, NO fit beyond the group's own modes. Returns the k centroids (unit).
    k>=len(points) collapses to the points themselves; k==1 = the group mean."""
    P = _unit(np.asarray(points, dtype=np.float64))
    n = P.shape[0]
    if k <= 1 or n <= 1:
        return _unit(np.mean(P, axis=0, keepdims=True))
    if k >= n:
        return P
    rng = np.random.RandomState(seed)
    # k-means++ style spread init (deterministic via seeded rng), cosine distance.
    idx = [int(rng.randint(n))]
    while len(idx) < k:
        C = P[idx]
        d = 1.0 - (P @ C.T).max(axis=1)        # cosine distance to nearest centre
        d = np.clip(d, 0.0, None)
        if d.sum() <= 0:
            idx.append(int(rng.randint(n)))
            continue
        probs = d / d.sum()
        idx.append(int(rng.choice(n, p=probs)))
    C = P[idx].copy()
    for _ in range(iters):
        assign = (P @ C.T).argmax(axis=1)       # nearest centroid (max cosine)
        newC = np.zeros_like(C)
        for j in range(k):
            members = P[assign == j]
            newC[j] = _unit(members.mean(axis=0)) if len(members) else C[j]
        if np.allclose(newC, C):
            C = newC
            break
        C = newC
    return _unit(C)


def speaker_invariant_centroids(train_vecs, train_words, train_speakers,
                                k: int = 1, seed: int = 0):
    """The CROSS-SPEAKER clusters: for each word, cluster its per-speaker prototypes
    (so each train speaker weighs equally) into k centroids. k=1 = the single
    cross-speaker centroid (per-speaker-mean then pool). k>1 = k cross-speaker modes
    via k-means over the per-speaker prototypes. Returns {word: centroids (k x d)}.
    No fit, no label beyond the word grouping; the textbook unsupervised clusterer."""
    protos = word_speaker_prototypes(train_vecs, train_words, train_speakers)
    out = {}
    for w, plist in protos.items():
        out[w] = _kmeans(np.asarray(plist), k, seed=seed)
    return out


def centroid_channel_likelihood(query_vec, centroids: dict, candidate_words,
                                k_unused=None) -> dict:
    """The channel's per-candidate likelihood from CROSS-SPEAKER CENTROID distance —
    the drop-in speaker-invariant replacement for channel_likelihood. D_c(s,w) = the
    MIN cosine distance from the query to word w's cross-speaker centroids; the SAME
    softmax-by-own-median (likelihood_from_distances) every channel uses. Same output
    shape as channel_likelihood, so it slots into the variadic product unchanged."""
    q = _unit(np.asarray(query_vec, dtype=np.float64))
    dists = {}
    for w in candidate_words:
        C = centroids.get(w)
        if C is None or len(C) == 0:
            dists[w] = float("inf")
            continue
        C = np.atleast_2d(np.asarray(C, dtype=np.float64))
        sims = C @ q
        dists[w] = float(1.0 - sims.max())
    return likelihood_from_distances(dists)


def heldout_1nn_centroid(train_vecs, train_words, train_speakers,
                         test_vecs, test_words, k: int = 1, seed: int = 0) -> float:
    """Single-channel held-out accuracy using CROSS-SPEAKER CENTROIDS instead of raw
    token 1-NN — the per-channel speaker-invariance probe (the centroid analogue of
    many_settings_hvpt_accept.heldout_1nn). Predict = argmax-likelihood centroid word."""
    cents = speaker_invariant_centroids(train_vecs, train_words, train_speakers,
                                        k=k, seed=seed)
    cands = sorted(set(train_words))
    correct = 0
    for q, truth in zip(test_vecs, test_words):
        p = centroid_channel_likelihood(q, cents, cands)
        pred = max(p, key=p.get)
        correct += int(pred == truth)
    return correct / max(len(test_words), 1)


__all__ = ["word_speaker_prototypes", "speaker_invariant_centroids",
           "centroid_channel_likelihood", "heldout_1nn_centroid"]
