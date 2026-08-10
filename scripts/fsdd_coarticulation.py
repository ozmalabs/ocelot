"""Drive the agent's #1 frontier: COARTICULATION predict-remove. Gap: "predict the
coarticulatory shift from the neighbours and remove it to recover the context-free
target" (the removable_context / regress-out shape). The coarticulatory pull is the part
of a frame LINEARLY PREDICTABLE from its neighbours (the smooth articulatory transition);
removing it, f_t - 1/2(f_{t-1}+f_{t+1}), keeps the target that sticks out above the
interpolation = the context-free phoneme.

Test on continuous speech (concatenated FSDD digits): does coart-removal make the frame-
UNITS more digit-discriminative (less context-blended) and sharpen segmentation? A/B on
the shape front-end. LABEL-FREE clustering; digit labels only score.

Run: python scripts/fsdd_coarticulation.py [n_sent] [k]
"""
from __future__ import annotations
import os
import random
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains.cross_speaker_clustering import cluster
from scripts.segmentation_saffran import segment_bidir, tp_table, bwd_table
from scripts.fsdd_segmentation_realspeech import frames, shape, collapse, bf1
from scripts.speech_analysis_by_synthesis import load_wav, DATA, FN

N_BANDS = 24


def coart_remove(M):
    """remove the coarticulatory (linearly-interpolatable-from-neighbours) component;
    keep the target that deviates from the smooth transition. Edges: keep as-is."""
    if len(M) < 3:
        return M.copy()
    out = M.copy()
    out[1:-1] = M[1:-1] - 0.5 * (M[:-2] + M[2:])
    return out


def digit_purity(labels, digit):
    return sum(Counter([digit[i] for i in range(len(labels)) if labels[i] == c]
                       ).most_common(1)[0][1] for c in set(labels)) / len(digit)


def main():
    n_sent = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 28
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    pool = {}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < 12:
            pool.setdefault(int(m.group(1)), []).append(os.path.join(DATA, fn))
    rng = random.Random(0)

    sent_M, sent_digidx = [], []
    for _ in range(n_sent):
        Ms, didx = [], []
        for di in range(6):
            d = rng.randrange(10)
            M = frames(s, bank, load_wav(rng.choice(pool[d]))[0])
            Ms.append(M); didx.extend([d] * len(M))   # tag frames with the DIGIT id
        sent_M.append(np.vstack(Ms)); sent_digidx.append(didx)

    print("=" * 60)
    print(f"COARTICULATION predict-remove — {n_sent} sentences, k={k} units")
    print("=" * 60)
    print(f"  {'front-end':26s} {'frame digit-purity':>18s} {'seg bF1':>9s}")
    print("-" * 60)

    for name, transform in [("shape", lambda M: shape(M)),
                            ("shape + coart-remove", lambda M: coart_remove(shape(M)))]:
        feats = [transform(M) for M in sent_M]
        F = np.vstack(feats)
        labels = cluster(F, k, seed=0)
        digit_flat = [d for didx in sent_digidx for d in didx]
        pur = digit_purity(labels, digit_flat)
        # segmentation: split labels per sentence -> collapse -> bidir segment -> bF1
        seqs, bnds, off = [], [], 0
        for M, didx in zip(feats, sent_digidx):
            u = labels[off:off + len(M)]; off += len(M)
            cs, cb = collapse(list(u), didx); seqs.append(cs); bnds.append(cb)
        fwd = tp_table(seqs); bw = bwd_table(seqs)
        f1s = []
        for cs, tb in zip(seqs, bnds):
            if len(cs) < 2:
                continue
            words = segment_bidir(list(cs), fwd, bw)
            pred, pos = set(), 0
            for w in words[:-1]:
                pos += len(w); pred.add(pos)
            f1s.append(bf1(pred, tb))
        print(f"  {name:26s} {pur:18.3f} {np.mean(f1s):9.3f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
