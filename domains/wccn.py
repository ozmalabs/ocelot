"""wccn — PER-CUE within-word/across-speaker covariance whitening (the agent's recogniser upgrade, decision b,
ask_jabberwock_recognizer). CMVN rotated from the TIME axis to the SPEAKER axis: estimate the speaker (nuisance)
covariance from a multi-speaker bank, whiten it out per cue, then run the SAME combine-all product over the
whitened cues -- keeping the product's robust conjunction AND removing the speaker key.

Closed-form linear algebra (eigendecompose, no gradient, no loss) -- an admissible graph-resident linear
operator, the same family as domains/cmvn.apply_cmvn. Guards: shrinkage toward isotropic + an eigenvalue floor
(an ill-estimated / rank-deficient cue Sigma cannot blow up -> worst case is the raw cue, never worse).
"""
from __future__ import annotations

import numpy as np
import domains.many_settings_recognizer as MS


def fit_per_cue(banked, lam=0.1):
    """banked: list of (word, [vec_c per cue]). Returns W_c = Sigma_c^-1/2 per cue (the speaker-key remover).
    Sigma_c = covariance of the WITHIN-word residuals (= speaker + noise variation), shrunk + eigen-floored."""
    if not banked:
        return None
    ncue = len(banked[0][1])
    y = np.array([w for (w, _v) in banked])
    Ws = []
    for c in range(ncue):
        X = np.stack([np.asarray(v[c], dtype=np.float64) for (_w, v) in banked])
        d, n = X.shape[1], len(X)
        R = X.copy()
        for w in set(y):
            m = (y == w)
            R[m] = X[m] - X[m].mean(0)                 # within-word residual = the speaker nuisance
        Sig = (R.T @ R) / max(n, 1)
        Sig = Sig + lam * (np.trace(Sig) / max(d, 1)) * np.eye(d)   # shrinkage -> invertible
        ev, U = np.linalg.eigh(Sig)
        ev = np.clip(ev, 1e-6, None)                   # eigen-floor -> degenerate dirs can't blow up
        Ws.append(U @ np.diag(ev ** -0.5) @ U.T)
    return Ws


def whiten(channels, Ws):
    """Apply the per-cue whitening to a clip's cue readouts (mechanical I/O, like apply_cmvn)."""
    if Ws is None:
        return [np.asarray(c, dtype=np.float64) for c in channels]
    return [np.asarray(channels[c], dtype=np.float64) @ Ws[c] for c in range(min(len(channels), len(Ws)))]


def recognise(channels, banked, Ws, candidates):
    """The combine-all PRODUCT over the WHITENED cues: each cue's 1-NN exemplar likelihood (whitened), summed
    in log, argmax. Same product as the raw recogniser -- only the cue vectors are speaker-key-removed first."""
    bw = [(w, whiten(v, Ws)) for (w, v) in banked]
    q = whiten(channels, Ws)
    nch = min(len(q), min(len(v) for (_w, v) in bw)) if bw else 0
    logp = {c: 0.0 for c in candidates}
    train_words = [w for (w, _v) in bw]
    for ci in range(nch):
        Xc = np.stack([v[ci] for (_w, v) in bw])
        p = MS.channel_likelihood(np.asarray(q[ci]), Xc, train_words, candidates)
        for c in candidates:
            logp[c] += np.log(p[c] + 1e-12)
    return max(candidates, key=lambda c: logp[c]) if candidates else None
