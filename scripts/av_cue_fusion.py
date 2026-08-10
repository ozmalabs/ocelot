"""DRIVE AUDIOVISUAL CUE FUSION — the agent's next frontier (RELIABILITY-WEIGHTED multi-cue
integration), wired through the HELD combinatorial recognizer (Bayes PRODUCT of per-channel
1-NN exemplar likelihoods, domains/combinatorial_recognizer) across MODALITIES.

Two REAL digit modalities, shared 10-digit label space:
  AUDIO  cue = FSDD spoken digits -> held cochlea -> time-resampled flat feature
  VISUAL cue = sklearn handwritten digits (8x8) -> flattened vector
Each channel -> cr.channel_likelihood (scale-free softmax); fused = the agent's NATIVE
predict_combinatorial_term (Argmax of the product), evaluated on the substrate.

The held product is reliability-AGNOSTIC: a confidently-WRONG weak channel still produces a
peaked likelihood and DRAGS the strong one. The axis is RELIABILITY-weighted fusion, so we add
the precision weight the held product lacks: raise each channel's likelihood to its MEASURED
reliability r_c (calibration accuracy) BEFORE the held product -> log-linear cue integration
(Argmax Pi_c P_c^{r_c} = Ernst-Banks precision weighting). r_c is RE-ESTIMATED as a cue
degrades, so fusion adapts. The fusion DECISION stays the held product Term; the exponent is
per-channel evidence shaping (like the channel's own temperature).

Three isolations (the way Saffran isolated segmentation):
  (1) FUSION vs single cues — unweighted (drags) vs reliability-weighted (recovers).
  (2) GRACEFUL DEGRADATION — noise a cue; its r drops; fused leans on the reliable cue.
  (3) McGURK CONFLICT — audio=A, vision=B; the percept follows the MORE RELIABLE cue.

Run: python scripts/av_cue_fusion.py
"""
from __future__ import annotations
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains import combinatorial_recognizer as cr
from scripts.fsdd_segmentation_realspeech import frames
from scripts.speech_analysis_by_synthesis import load_wav, DATA, FN

N_BANDS = 24
CANDS = list(range(10))


def audio_feat(M, T0=12):
    """time-resample the held cochlear frames to a fixed length and flatten (richer than the
    mean -> a usable audio cue, ~0.5 held-out)."""
    idx = np.linspace(0, len(M) - 1, T0)
    return np.asarray([M[int(round(i))] for i in idx]).flatten().astype(np.float64)


def build_audio(s, bank, test_spk, n_per=25):
    Xtr, Wtr, test = [], [], {d: [] for d in range(10)}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if not (m and int(m.group(3)) < n_per):
            continue
        d, spk = int(m.group(1)), m.group(2)
        v = audio_feat(frames(s, bank, load_wav(os.path.join(DATA, fn))[0]))
        if spk in test_spk:
            test[d].append(v)
        else:
            Xtr.append(v); Wtr.append(d)
    return np.asarray(Xtr), np.asarray(Wtr), test


def build_visual(seed=0):
    from sklearn.datasets import load_digits
    dg = load_digits(); X = dg.data.astype(np.float64); y = dg.target
    rng = np.random.RandomState(seed); idx = rng.permutation(len(X)); h = len(X) // 2
    test = {d: [X[i] for i in idx[h:] if y[i] == d] for d in range(10)}
    return X[idx[:h]], y[idx[:h]], test


def calib(Xtr, Wtr, pool):
    """channel reliability r_c = 1-NN accuracy on a held-out slice of its own train data.
    SHUFFLE first — FSDD train is ordered by digit, so a contiguous split leaves the
    validation labels disjoint from the exemplar labels (spurious 0 accuracy)."""
    idx = np.random.RandomState(0).permutation(len(Xtr))
    Xs, Ws = Xtr[idx], Wtr[idx]
    n = max(1, len(Xs) // 5)
    Xv, Wv, Xt, Wt = Xs[:n], Ws[:n], Xs[n:], Ws[n:]
    ok = sum(max((p := cr.channel_likelihood(q, Xt, Wt, CANDS)), key=p.get) == w
             for q, w in zip(Xv, Wv))
    return ok / len(Wv)


def main():
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    test_spk = {"george", "jackson"}
    Xa, Wa, A = build_audio(s, bank, test_spk)
    Xv, Wv, V = build_visual()

    word_node = {d: s.add_node("Concept", {"name": f"d{d}", cr.WORD_ATTR: 1.0}) for d in range(10)}
    # the HELD reliability-weighted Term — the exponent is the native Pow inside the score
    # Term now, NOT folded into the likelihood by this adapter.
    term = cr.predict_reliability_weighted_term()
    rng = np.random.RandomState(1)
    La = lambda q: cr.channel_likelihood(q, Xa, Wa, CANDS)
    Lv = lambda q: cr.channel_likelihood(q, Xv, Wv, CANDS)
    am = lambda p: max(p, key=p.get)

    def fuse(pa, pv, ra=1.0, rv=1.0):
        for d in CANDS:
            s.set_attr(word_node[d], cr.P_FLAT_ATTR, float(pa[d]))
            s.set_attr(word_node[d], cr.P_TRANS_ATTR, float(pv[d]))
            s.set_attr(word_node[d], cr.R_FLAT_ATTR, float(ra))
            s.set_attr(word_node[d], cr.R_TRANS_ATTR, float(rv))
        win = s._inner.evaluate(term, {})
        return next(d for d, n in word_node.items() if n == win)

    ra = calib(Xa, Wa, A); rv = calib(Xv, Wv, V)
    print("=" * 70)
    print("AUDIOVISUAL CUE FUSION — held Bayes-product recognizer, reliability-weighted")
    print(f"  audio=FSDD cochlear (held-out {sorted(test_spk)}), visual=sklearn digits 8x8")
    print(f"  calibrated reliability:  r_audio={ra:.2f}  r_visual={rv:.2f}")
    print("=" * 70)

    # (1) fusion vs single cues — unweighted vs reliability-weighted
    na = nv = nu = nw = tot = 0
    for d in range(10):
        for _ in range(40):
            qa = A[d][rng.randint(len(A[d]))]; qv = V[d][rng.randint(len(V[d]))]
            pa, pv = La(qa), Lv(qv)
            na += am(pa) == d; nv += am(pv) == d
            nu += fuse(pa, pv) == d                       # unweighted product
            nw += fuse(pa, pv, ra, rv) == d               # reliability-weighted
            tot += 1
    print("\n(1) FUSION vs single cues (matched pairs):")
    print(f"    audio {na/tot:.3f}   visual {nv/tot:.3f}   "
          f"FUSED-unweighted {nu/tot:.3f}   FUSED-reliability {nw/tot:.3f}")

    # (2) graceful degradation — noise visual, RE-CALIBRATE r_v, fused leans on audio
    print("\n(2) GRACEFUL DEGRADATION (noise the visual cue; r_v re-estimated each level):")
    print(f"    {'sigma_v':>8} {'r_v':>5} {'audio':>7} {'visual':>7} {'FUSED-rel':>10}")
    for sg in (0.0, 1.0, 2.0, 4.0):
        def nz(v):
            return v if sg == 0 else v + rng.normal(0, sg * (v.std() + 1e-9), size=v.shape)
        Xvn = np.asarray([nz(x) for x in Xv])
        rvn = calib(Xvn, Wv, None)
        Lvn = lambda q: cr.channel_likelihood(q, Xvn, Wv, CANDS)
        na2 = nv2 = nf2 = t2 = 0
        for d in range(10):
            for _ in range(30):
                qa = A[d][rng.randint(len(A[d]))]; qv = nz(V[d][rng.randint(len(V[d]))])
                pa, pv = La(qa), Lvn(qv)
                na2 += am(pa) == d; nv2 += am(pv) == d; nf2 += fuse(pa, pv, ra, rvn) == d; t2 += 1
        print(f"    {sg:8.1f} {rvn:5.2f} {na2/t2:7.3f} {nv2/t2:7.3f} {nf2/t2:10.3f}")

    # (3) McGurk conflict — audio=A, visual=B; reliability-weighted fused follows reliable cue
    print("\n(3) McGURK CONFLICT (audio=A, visual=B; reliability-weighted fusion):")
    print(f"    {'regime':>20} {'r_a':>5} {'r_v':>5} {'->AUDIO':>9} {'->VISUAL':>9}")
    for label, sa, sv in (("clean", 0.0, 0.0), ("audio noised", 3.0, 0.0), ("visual noised", 0.0, 3.0)):
        def nza(v): return v if sa == 0 else v + rng.normal(0, sa*(v.std()+1e-9), size=v.shape)
        def nzv(v): return v if sv == 0 else v + rng.normal(0, sv*(v.std()+1e-9), size=v.shape)
        rA = calib(np.asarray([nza(x) for x in Xa]), Wa, None)
        rV = calib(np.asarray([nzv(x) for x in Xv]), Wv, None)
        fa = fvis = t3 = 0
        for da in range(10):
            for db in range(10):
                if da == db:
                    continue
                qa = nza(A[da][rng.randint(len(A[da]))]); qv = nzv(V[db][rng.randint(len(V[db]))])
                pred = fuse(La(qa), Lv(qv), rA, rV)
                fa += pred == da; fvis += pred == db; t3 += 1
        print(f"    {label:>20} {rA:5.2f} {rV:5.2f} {fa/t3:9.3f} {fvis/t3:9.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
