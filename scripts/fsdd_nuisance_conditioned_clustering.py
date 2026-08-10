"""Wire + measure the agent's DERIVED nuisance-conditioned transform (commit 85375da1):
remove the variation explained by the OBSERVED speaker attribute, WITHOUT word labels,
then cluster words. The agent's derivation: "compute the BETWEEN-observed-group scatter
and whiten by it." Between-speaker scatter Sb = St - Sw_speaker, both from the native
WithinScatter primitive (St = all-one-label total scatter; Sw = speaker-labelled within
scatter). Whiten by Sb (+ ridge) shrinks the speaker directions; the word structure
surfaces in the residual; then cluster.

LABEL-FREE for the TARGET: word labels are read ONLY to score purity. The SPEAKER
attribute is observed (the whole point of nuisance-conditioning). Uses the agent's
composed clusterer + its two native matrix primitives (WithinScatter, Whiten).

Run: python scripts/fsdd_nuisance_conditioned_clustering.py [n_per]
"""
from __future__ import annotations
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import substrate_rs as srs
from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains.cross_speaker_clustering import cluster
from scripts.speech_analysis_by_synthesis import load_wav, feat, DATA, FN, N_BANDS


def _vec(xs):
    return srs.Vec(items=[srs.Lit(float(v)) for v in xs])


def purity(assign, truth):
    return sum(Counter([truth[i] for i in range(len(assign)) if assign[i] == c]
                       ).most_common(1)[0][1]
               for c in set(assign)) / len(truth)


def native_between_scatter(s, M, labels):
    """Sb in ONE native op (BetweenScatter) instead of numpy St - Sw."""
    data = srs.Vec(items=[_vec(r) for r in M])._json
    labs = _vec([float(a) for a in labels])._json
    Sbv = s._inner.evaluate({"type": "BetweenScatter", "a": data, "b": labs}, {})
    return np.array([[float(v) for v in row] for row in Sbv])


def native_whiten_all(s, W, M):
    """Batch whiten via the native WhitenMany (factors the Cholesky ONCE)."""
    Wmat = srs.Vec(items=[_vec([float(v) for v in row]) for row in W])._json
    Xmat = srs.Vec(items=[_vec(x) for x in M])._json
    out = s._inner.evaluate({"type": "WhitenMany", "a": Wmat, "b": Xmat}, {})
    return np.array([[float(v) for v in row] for row in out])


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)

    M, word, spk = [], [], []
    spk_id = {}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            M.append(feat(s, bank, load_wav(os.path.join(DATA, fn))[0], 8000)
                     .flatten().astype(np.float64))
            word.append(int(m.group(1)))
            spk.append(spk_id.setdefault(m.group(2), len(spk_id)))
    M = np.asarray(M); k = len(set(word)); d = M.shape[1]
    print("=" * 74)
    print("NUISANCE-CONDITIONED clustering (agent-derived; observed speaker, no word labels)")
    print(f"  {len(M)} tokens, {len(spk_id)} speakers, k={k} words, d={d}")
    print("=" * 74)

    floor = purity([np.random.RandomState(i).randint(0, k) for i in range(len(M))], word)
    base = np.mean([purity(cluster(M, k, seed=sd), word) for sd in range(3)])
    print(f"  random floor                 : {floor:.3f}")
    print(f"  raw clustering (baseline)    : {base:.3f}")

    # BETWEEN-SPEAKER scatter — ONE native op (the agent's BetweenScatter primitive),
    # not numpy St - Sw. Fully native: BetweenScatter then Whiten, both in-substrate.
    Sb = native_between_scatter(s, M, spk)           # between-speaker (the nuisance)
    print(f"  native BetweenScatter: tr(Sb) = {np.trace(Sb):.3f} "
          f"(the variance the speaker explains)")

    for rel in (0.05, 0.2, 0.5):
        Wreg = Sb + rel * (np.trace(Sb) / d) * np.eye(d)   # ridge for conditioning
        Mw = native_whiten_all(s, Wreg, M)                 # native Whiten by Sb -> shrink speaker dirs
        pur = np.mean([purity(cluster(Mw, k, seed=sd), word) for sd in range(3)])
        print(f"  nuisance-conditioned (ridge={rel}): {pur:.3f}   (delta {pur-base:+.3f})")
    print("=" * 74)


if __name__ == "__main__":
    main()
