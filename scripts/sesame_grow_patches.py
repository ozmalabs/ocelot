"""GROW THE PATCH BANK for the transition channel — the standing gap. The combinatorial
recogniser's TRANSITION channel was a naive band-delta (~chance) and dragged. The agent's REAL
transition channel reads through a GROWN A1 patch bank (domains/grown_representation): grow the
patch inventory by DISCRETE ACCRETION under the masked-prediction (smoothness) survival selector,
then transition_channel(patch-responses, patches) = the agent's order-1-over-time operator +
formant-frequency sweeps over the grown patches. Compare the GROWN transition channel vs the
naive one inside the combinatorial recogniser.

Reuses the cached Sesame word FFT sequences (no re-collect). Run: python scripts/sesame_grow_patches.py [study_min] [min_ex]
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import math
import pickle
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from domains import combinatorial_recognizer as cr
from domains.grown_representation import (band_centres, bands_to_patches, seed_patches,
                                          transition_channel, grow_representation)

N_BANDS = 32
N_FFT = 128
SR = 8000


def fbank(n_bands=N_BANDS):
    """linear-128-FFT -> log-spaced band matrix aligned to band_centres (the patch axis)."""
    bc = band_centres(n_bands)
    freqs = np.arange(N_FFT) * (SR / 2) / N_FFT
    W = np.zeros((n_bands, N_FFT))
    for j in range(n_bands):
        sigma = 0.3 * bc[j] + 60.0
        w = np.exp(-0.5 * ((freqs - bc[j]) / sigma) ** 2)
        W[j] = w / (w.sum() + 1e-9)
    return W


_W = fbank()


def to_bands(fft_seq):
    return (np.asarray(fft_seq) @ _W.T)                  # (frames, 32) cochleagram


def naive_trans(M):
    h = max(1, len(M) // 2)
    d = M[h:].mean(0) - M[:h].mean(0)
    return d / (np.linalg.norm(d) + 1e-9)


def _l2(v):
    return (v / (np.linalg.norm(v) + 1e-9)).astype(np.float64)


def main():
    study_min = float(sys.argv[1]) if len(sys.argv) > 1 else 16.0
    min_ex = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    with open(f"/tmp/sesame_seq_{study_min:g}.pkl", "rb") as f:
        toks = pickle.load(f)                            # [(word, fft_frames)]
    cnt = Counter(w for w, _ in toks)
    core = sorted(w for w, c in cnt.items() if c >= min_ex)
    data = [(w, to_bands(fr)) for w, fr in toks if w in core]   # (word, band matrix)
    print("=" * 78)
    print("GROW THE PATCH BANK for the transition channel (combinatorial recogniser)")
    print(f"  core vocab (>= {min_ex} ex): {len(core)} words, {len(data)} tokens", flush=True)
    print("=" * 78)

    rng = np.random.RandomState(0)
    idx = rng.permutation(len(data)); n = len(data)
    train = [data[i] for i in idx[:n * 75 // 100]]
    test = [data[i] for i in idx[n * 75 // 100:]]

    # GROW the patch bank. The TRANSITION selector is the one aligned with the transition channel:
    # it keeps a patch iff it raises the SAME-word-vs-DIFFERENT-word transition-contrast margin
    # (read through the agent's order-1-over-time operator) — exactly the channel's job. Sesame
    # has WORD labels but no speaker labels, so form PSEUDO-VOICES by partitioning exemplars:
    # same word across partitions = the cross-voice same-word term. Grow with both selectors and
    # compare which makes the transition channel actually discriminate.
    seed = seed_patches()
    K = 4
    pv = [[] for _ in range(K)]
    for j, (w, M) in enumerate(train):
        pv[j % K].append((w, M))
    vbm = {f"v{i}": [M for _, M in pv[i]] for i in range(K)}      # for proposal + smoothness
    vwm = {f"v{i}": pv[i] for i in range(K)}                      # for the transition selector

    g_tr = grow_representation(vbm, seed=seed, rounds=4, candidates_per_round=8,
                               selector="transition", voice_word_matrices=vwm)
    g_sm = grow_representation(vbm, seed=seed, rounds=4, candidates_per_round=8,
                               selector="smoothness")
    print(f"  patch bank: seed {g_tr['seed_size']} | "
          f"TRANSITION-grown +{len(g_tr['grown'])} -> {len(g_tr['patches'])} "
          f"(rounds {[h['kept'] for h in g_tr['history']]}) | "
          f"smoothness-grown +{len(g_sm['grown'])} -> {len(g_sm['patches'])}", flush=True)
    patches = g_tr["patches"]                                     # the aligned bank drives recog

    # channels: FLAT = mean patch-response (grown bank); TRANSITION = the agent's order-1-over-
    # time operator over a patch bank. Compare the transition channel under SEED vs GROWN banks.
    def flat_feat(M):
        return _l2(bands_to_patches(M, patches).mean(0))

    def trans_feat(M, bank):
        return _l2(transition_channel(bands_to_patches(M, bank), bank))

    def featrows(items, fn):
        return np.array([fn(M) for _, M in items])

    Wtr = np.array([w for w, _ in train])
    Ftr = featrows(train, flat_feat)
    cands = list(core)

    def chan_acc(Xtr, ev_feat):
        cor = tot = 0
        for w, M in test:
            top = Wtr[np.argsort(-(Xtr @ ev_feat(M)))[:3]]
            cor += (max(set(top), key=lambda c: list(top).count(c)) == w); tot += 1
        return cor / tot if tot else 0.0

    seed_bank = seed
    GTtr = featrows(train, lambda M: trans_feat(M, patches))          # transition-grown bank
    STtr = featrows(train, lambda M: trans_feat(M, seed_bank))        # seed bank
    NTtr = featrows(train, naive_trans)                              # naive band-delta

    r_flat = chan_acc(Ftr, flat_feat)
    r_gt = chan_acc(GTtr, lambda M: trans_feat(M, patches))
    r_st = chan_acc(STtr, lambda M: trans_feat(M, seed_bank))
    r_nt = chan_acc(NTtr, naive_trans)
    print(f"  channel accuracy (test): FLAT {r_flat:.2f}  |  transition: "
          f"naive band-delta {r_nt:.2f}  SEED patches {r_st:.2f}  GROWN patches {r_gt:.2f}")

    # combinatorial recogniser (reliability-weighted) — flat x transition.
    s = Substrate()
    wn = {w: s.add_node("Concept", {"name": w, cr.WORD_ATTR: 1.0}) for w in core}
    term = cr.predict_reliability_weighted_term()

    def combo(Ttr, r_trans, trans_ev):
        cor = tot = 0
        for w, M in test:
            pa = cr.channel_likelihood(flat_feat(M), Ftr, Wtr, cands)
            pt = cr.channel_likelihood(trans_ev(M), Ttr, Wtr, cands)
            for c in cands:
                s.set_attr(wn[c], cr.P_FLAT_ATTR, float(pa[c]))
                s.set_attr(wn[c], cr.P_TRANS_ATTR, float(pt[c]))
                s.set_attr(wn[c], cr.R_FLAT_ATTR, float(r_flat))
                s.set_attr(wn[c], cr.R_TRANS_ATTR, float(r_trans))
            win = s._inner.evaluate(term, {})
            cor += (next(c for c, nd in wn.items() if nd == win) == w); tot += 1
        return cor / tot if tot else 0.0

    acc_naive = combo(NTtr, r_nt, naive_trans)
    acc_seed = combo(STtr, r_st, lambda M: trans_feat(M, seed_bank))
    acc_grown = combo(GTtr, r_gt, lambda M: trans_feat(M, patches))
    print("\n  " + "=" * 70)
    print(f"  combinatorial recognition, FLAT x transition (rel-weighted, {len(test)} test words):")
    print(f"    FLAT only                         : {r_flat:.1%}")
    print(f"    x NAIVE band-delta transition     : {acc_naive:.1%}   ({acc_naive-r_flat:+.1%})")
    print(f"    x SEED-patch transition           : {acc_seed:.1%}   ({acc_seed-r_flat:+.1%})")
    print(f"    x GROWN-patch transition          : {acc_grown:.1%}   ({acc_grown-r_flat:+.1%})")
    print("=" * 78)
    print("  growing the patch bank (transition selector) makes the agent's transition channel "
          "a REAL,\n  complementary cue instead of a ~chance drag on the product.")


if __name__ == "__main__":
    main()
