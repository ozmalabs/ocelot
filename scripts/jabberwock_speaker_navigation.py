"""NAVIGATE SPEAKER SPACE — for a speaker you have no key for, AbS passes step you closer (if reachable).

The keyspace was learned (within-word scatter = the speaker subspace V, 91% of the variance). The
insight now: you do NOT need a key for a new speaker. As long as their distance in SPEAKER SPACE is not
too far, analysis-by-synthesis passes NAVIGATE you there — guess the word, read off the speaker offset
that hypothesis implies (its coordinate in the learned keyspace V), STEP the key toward it, re-guess.
The key moves through the learned speaker subspace toward the unseen voice; the message and the key
co-settle. This constrains the search to REAL speaker directions (fixing the channel/reverb over-fit)
and gives "distance in speaker space" a meaning. Compared: no key, static projection (one-shot remove
the whole subspace), and the NAVIGATION; and accuracy bucketed by how FAR the test voice starts
(reachable vs too far).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_speaker_navigation [topK]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scipy.linalg import eigh
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_shape_pc_paired import content_words
from scripts.jabberwock_enacts_xvector import frame_feats

N_PCA = 60
KEYDIM = 30          # the learned speaker subspace (top within-word-variance directions)


def pool(seg):
    F = frame_feats(seg)
    return np.concatenate([F.mean(0), F.std(0)])


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print("=" * 96)
    print("NAVIGATE SPEAKER SPACE — AbS passes step the key through the learned subspace toward a new voice.")
    print("=" * 96)
    train, test = multi_extract()
    words = content_words(train, topK, min_ex=12)
    wi = set(words)
    allex = {}
    for (w, g) in train + test:
        if w in wi:
            allex.setdefault(w, []).append(g)
    by, te = {}, []
    for w in words:
        ex = allex[w]; nho = max(2, len(ex) // 5)
        by[w] = ex[:-nho]; te += [(w, g) for g in ex[-nho:]]
    print(f"  top-{len(words)} CONTENT words (chance {100/max(len(words),1):.0f}%, "
          f"{sum(len(v) for v in by.values())} train / {len(te)} held-out)\n")
    if len(words) < 6 or len(te) < 25:
        print("  too few."); return

    tr = [(w, g) for w in words for g in by[w]]
    EXw = [w for (w, _g) in tr]
    Xtr = np.stack([pool(g) for (_w, g) in tr])
    Xte = np.stack([pool(g) for (_w, g) in te]); yte = [w for (w, _g) in te]
    m0, s0 = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xtr = (Xtr - m0) / s0; Xte = (Xte - m0) / s0
    mu = Xtr.mean(0)
    U, S, Vt = np.linalg.svd(Xtr - mu, full_matrices=False)
    k = min(N_PCA, (S > 1e-9).sum()); P = Vt[:k].T
    E = (Xtr - mu) @ P                                   # exemplars in PCA space
    Z = (Xte - mu) @ P
    EXa = np.asarray(EXw)

    # LEARN the speaker subspace V = top within-word-scatter directions (the keyspace).
    Sw = np.zeros((k, k));
    for w in words:
        d = E[EXa == w] - E[EXa == w].mean(0); Sw += d.T @ d
    vals, vecs = eigh(Sw)
    V = vecs[:, ::-1][:, :KEYDIM]                        # top-KEYDIM speaker directions

    def nn(zn):
        j = int(np.argmin(((E - zn) ** 2).sum(1))); return EXa[j], E[j]

    def navigate(z, iters=8):
        key = np.zeros(k)
        traj = []
        for _ in range(iters):
            zn = z - key                                # remove current speaker key
            m, T = nn(zn)                               # AbS: guess word from key-normalised obs
            knew = V @ (V.T @ (z - T))                  # speaker offset this hypothesis implies (in V)
            traj.append(m)
            if np.linalg.norm(knew - key) < 1e-4:
                break
            key = knew                                  # step the key through speaker space
        return traj[-1], traj

    # baselines
    raw = np.mean([nn(z)[0] == w for z, w in zip(Z, yte)])
    Vp = np.eye(k) - V @ V.T                            # static projection: remove the whole subspace
    Enap = E @ Vp.T; Znap = Z @ Vp.T
    nap = np.mean([EXa[int(np.argmin(((Enap - zn) ** 2).sum(1)))] == w for zn, w in zip(Znap, yte)])

    # navigation + reachability bucketing (distance to nearest training exemplar = how far the voice starts)
    d0 = np.array([np.sqrt(((E - z) ** 2).sum(1).min()) for z in Z])
    med = np.median(d0)
    nav_first = nav_last = 0
    near = [0, 0]; far = [0, 0]
    for z, w in zip(Z, yte):
        m, traj = navigate(z)
        nav_first += int(traj[0] == w)                 # one pass (no navigation)
        nav_last += int(m == w)                        # converged
        b = near if np.sqrt(((E - z) ** 2).sum(1).min()) <= med else far
        b[1] += 1; b[0] += int(m == w)

    n = len(te)
    print(f"  {'no key (nearest exemplar)':<44} {raw*100:>5.0f}%")
    print(f"  {'static: remove whole speaker subspace':<44} {nap*100:>5.0f}%")
    print(f"  {'NAVIGATE (1 pass, no stepping)':<44} {nav_first/n*100:>5.0f}%")
    print(f"  {'NAVIGATE (AbS passes, converged)':<44} {nav_last/n*100:>5.0f}%")
    print(f"\n  reachability: NEAR voices {near[0]}/{near[1]}={near[0]/max(near[1],1)*100:.0f}%   "
          f"FAR voices {far[0]}/{far[1]}={far[0]/max(far[1],1)*100:.0f}%")

    print("\n" + "=" * 96)
    if nav_last / n > max(raw, nap, nav_first / n) + 0.02 and near[0] / max(near[1], 1) > far[0] / max(far[1], 1):
        print(f"  IT NAVIGATES: AbS passes step the key closer and recognition rises {nav_first/n*100:.0f}% (1 pass)")
        print(f"  -> {nav_last/n*100:.0f}% (converged), and NEAR voices land better than FAR ones — speaker space is")
        print("  a navigable metric, and 'not too far' is exactly reachability, as reasoned.")
    elif near[0] / max(near[1], 1) > far[0] / max(far[1], 1) + 0.03:
        print(f"  REACHABILITY HOLDS (near {near[0]/max(near[1],1)*100:.0f}% > far {far[0]/max(far[1],1)*100:.0f}%): "
              f"distance in speaker space governs success, as reasoned, even though the net lift over static is")
        print("  small (linear subspace + the 91% non-linear key cap what stepping can recover).")
    else:
        print(f"  navigation {nav_last/n*100:.0f}% vs static {nap*100:.0f}%: on this linear keyspace the stepping adds")
        print("  little beyond removing the subspace once — the non-linear 91% key is the ceiling here.")
    print("=" * 96)


if __name__ == "__main__":
    main()
