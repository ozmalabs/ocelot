"""Have the agent PICK the front-end (label-free) and test it on the clustering bound.
The bound is the ENERGY envelope losing formant/spectral detail (the whisper finding: the
message is in the FILTER, not the energy). So offer the agent's label-free selector
(domains/audio_basis_select: shift-coherence = VTL/speaker stability) a family that adds
SPECTRAL-SHAPE front-ends (log-band minus per-frame mean = the formant pattern, energy
removed) to the energy-envelope ones. The AGENT picks by shift-coherence (NO labels); we
then MEASURE the pick on cross-speaker clustering (+ the NC speaker-removal).

Honest outcome either way: the shape front-end breaks the bound, ties, or hurts.

Run: python scripts/fsdd_frontend_pick.py [n_per]
"""
from __future__ import annotations
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import substrate_rs as srs
from substrate_rs import Substrate
from scripts.frontend_improve_xspeaker import band_matrix
from domains import audio_basis_select as SEL
from domains.cross_speaker_clustering import cluster
from scripts.speech_analysis_by_synthesis import load_wav, DATA, FN

NF = 12   # frames; keep flattened dim modest for the native scatter/whiten


def shape(M):
    """per-frame spectral SHAPE = log-bands minus the per-frame mean (remove broadband
    energy/level -> keep the formant pattern = the FILTER, not the source/energy)."""
    L = np.log(M + 1e-6)
    return L - L.mean(axis=1, keepdims=True)


# The candidate family the agent's selector ranges over (frequency/band axis, so
# shift-coherence = VTL stability is meaningful). ENERGY envelope vs SPECTRAL SHAPE.
CANDS = [
    ("energy32", lambda x, fs: band_matrix(x, fs, n_bands=32, n_frames=NF)),
    ("energy48", lambda x, fs: band_matrix(x, fs, n_bands=48, n_frames=NF)),
    ("shape32",  lambda x, fs: shape(band_matrix(x, fs, n_bands=32, n_frames=NF))),
    ("shape48",  lambda x, fs: shape(band_matrix(x, fs, n_bands=48, n_frames=NF))),
]


def purity(a, truth):
    return sum(Counter([truth[i] for i in range(len(a)) if a[i] == c]
                       ).most_common(1)[0][1] for c in set(a)) / len(truth)


def pur3(M, k, truth):
    return float(np.mean([purity(cluster(M, k, seed=sd), truth) for sd in range(3)]))


def _mat(s, A):
    return srs.Vec(items=[srs.Vec(items=[srs.Lit(float(v)) for v in r]) for r in A])._json


def nc(s, F, spk):
    """nuisance-condition: native BetweenScatter(speaker) -> WhitenMany."""
    d = F.shape[1]
    Sb = np.array([[float(v) for v in r] for r in s._inner.evaluate(
        {"type": "BetweenScatter", "a": _mat(s, F),
         "b": srs.Vec(items=[srs.Lit(float(a)) for a in spk])._json}, {})])
    Wr = Sb + 0.2 * (np.trace(Sb) / d) * np.eye(d)
    return np.array([[float(v) for v in r] for r in s._inner.evaluate(
        {"type": "WhitenMany", "a": _mat(s, Wr), "b": _mat(s, F)}, {})])


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    s = Substrate()
    clips, word, spk, sid = [], [], [], {}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            clips.append(load_wav(os.path.join(DATA, fn))[0])
            word.append(int(m.group(1))); spk.append(sid.setdefault(m.group(2), len(sid)))
    k = len(set(word))
    print("=" * 70)
    print(f"AGENT PICKS THE FRONT-END (label-free shift-coherence) — {len(clips)} clips")
    print("=" * 70)

    mats_by_name, per_basis = {}, {}
    for name, fnc in CANDS:
        mats = [fnc(x, 8000) for x in clips]
        mats_by_name[name] = mats
        by_word = defaultdict(list)
        for w, M in zip(word, mats):
            by_word[w].append(M)
        sr = float(SEL.shift_coherence(by_word)[0])
        comp = SEL.compression(mats)
        ed, dl = float(comp[0]), float(comp[1])
        per_basis[name] = {"shift_ratio": sr, "eff_dim": ed, "dl_bits": dl}
        print(f"  {name:9s} shift-coherence={sr:.4f}  eff-dim={ed:.2f}  dl={dl:.1f}")

    pick, _ = SEL.select(per_basis)             # CORRECTED selector = compression (MDL)
    pick_shift = min(per_basis, key=lambda n_: per_basis[n_]["shift_ratio"])  # old criterion
    print(f"\n  AGENT PICKS (corrected selector = compression/MDL): {pick}")
    print(f"  (old shift-coherence criterion would have picked    : {pick_shift})\n")

    # measure EVERY candidate on clustering (+ NC) — the ground truth the selectors proxy.
    print("  cross-speaker clustering purity (label-free; NC = speaker removed):")
    best = (None, -1.0)
    for name, _ in CANDS:
        F = np.array([M.flatten() for M in mats_by_name[name]])
        base = pur3(F, k, word)
        ncp = pur3(nc(s, F, spk), k, word)
        tag = []
        if name == pick: tag.append("agent-pick")
        
        if ncp > best[1]: best = (name, ncp)
        print(f"    {name:9s} raw {base:.3f}   +NC {ncp:.3f}   {','.join(tag)}")
    print(f"\n  BEST clustering = {best[0]} (+NC {best[1]:.3f}); "
          f"agent (corrected selector) picked {pick}.")
    print("=" * 70)


if __name__ == "__main__":
    main()
