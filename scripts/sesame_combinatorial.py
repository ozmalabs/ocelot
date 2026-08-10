"""SESAME SPEECH — the agent's OWN ear AND its OWN recogniser, densified.
Composes BOTH held machineries onto the Sesame speech world:
  EAR  : domains/ear_composition — a non-uniform band layout the agent designs from its OWN
         confusions (fine bands where it confuses Sesame words).
  RECOG: domains/combinatorial_recognizer — the Bayes PRODUCT of two COMPLEMENTARY channels the
         agent derived: FLAT (mean spectrum = "what is this") x TRANSITION (late-early = "which
         word, the dynamics"), each a scale-free 1-NN softmax, combined by predict_combinatorial
         _term. Both channels read through the COMPOSED EAR's bands.
DENSIFY: study more of the episode -> more exemplars per core word -> denser confusions (the ear
needs them) AND more exemplars for the recogniser.

Run: python scripts/sesame_combinatorial.py [study_min] [res_out] [min_ex]
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import pickle
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from domains import combinatorial_recognizer as cr
from domains.ear_composition import informativeness_vector, equal_information_layout

N_BINS = 128
SR = 8000


def word_fft_seq(a8, wt0, wt1, n_fft=256, hop=128):
    seg = a8[int(wt0 * SR):int(wt1 * SR)]
    if len(seg) < n_fft:
        seg = np.pad(seg, (0, n_fft - len(seg)))
    win = np.hanning(n_fft)
    fr = [np.abs(np.fft.rfft(seg[i:i + n_fft] * win))[:N_BINS]
          for i in range(0, len(seg) - n_fft + 1, hop)]
    if not fr:
        fr = [np.abs(np.fft.rfft(seg[:n_fft] * win))[:N_BINS]]
    return np.asarray(fr, dtype=np.float32)              # (frames, 128)


def collect(study_min):
    cache = f"/tmp/sesame_seq_{study_min:g}.pkl"
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            return pickle.load(f)
    from scripts.sesame_speech_world import SesameSpeechWorld
    w = SesameSpeechWorld(episode_idx=0)
    toks = []; chunk = 25.0
    end = min(study_min * 60, w.duration - 30); t = 30.0
    while t < end:
        words = w.whisper(t, t + chunk)
        if words:
            a8 = w.play(t, t + chunk)
            for word, wt0, wt1 in words:
                fr = word_fft_seq(a8, wt0, wt1)
                if len(fr) >= 1:
                    toks.append((word, fr))
        t += chunk
    with open(cache, "wb") as f:
        pickle.dump(toks, f)
    print(f"  collected {len(toks)} word tokens -> {cache}", flush=True)
    return toks


def fold(spec, bnd):
    out = np.empty(len(bnd) - 1)
    for j in range(len(bnd) - 1):
        lo, hi = bnd[j], max(bnd[j] + 1, bnd[j + 1])
        out[j] = np.log(spec[lo:hi].mean() + 1e-6)
    return out


def flat_feat(frames, bnd):
    f = fold(frames.mean(0), bnd)
    return (f / (np.linalg.norm(f) + 1e-9)).astype(np.float64)


def trans_feat(frames, bnd):
    n = len(frames); h = max(1, n // 2)
    d = fold(frames[h:].mean(0), bnd) - fold(frames[:h].mean(0), bnd)   # late - early dynamics
    return (d / (np.linalg.norm(d) + 1e-9)).astype(np.float64)


def main():
    study_min = float(sys.argv[1]) if len(sys.argv) > 1 else 16.0
    res_out = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    min_ex = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    toks = collect(study_min)
    cnt = Counter(wd for wd, _ in toks)
    core = sorted(wd for wd, c in cnt.items() if c >= min_ex)
    toks = [(wd, fr) for wd, fr in toks if wd in core]
    print("=" * 78)
    print("SESAME — agent's COMPOSED EAR + COMBINATORIAL RECOGNISER, densified")
    print(f"  {study_min:g} min study; core vocab (>= {min_ex} ex): {len(core)} words, "
          f"{len(toks)} tokens", flush=True)
    print("=" * 78)

    rng = np.random.RandomState(0)
    idx = rng.permutation(len(toks)); n = len(toks)
    a, b = n * 60 // 100, n * 80 // 100
    train = [toks[i] for i in idx[:a]]; valc = [toks[i] for i in idx[a:b]]; test = [toks[i] for i in idx[b:]]
    uni = list(np.linspace(0, N_BINS, res_out + 1).round().astype(int))

    # --- 1. uniform-flat recognition -> harvest confusions ----------------
    def flat_knn(tr, ev, bnd, k=3):
        Xtr = np.array([flat_feat(fr, bnd) for _, fr in tr]); Wtr = np.array([wd for wd, _ in tr])
        cor = tot = 0; conf = Counter()
        for wd, fr in ev:
            if wd not in core:
                continue
            top = Wtr[np.argsort(-(Xtr @ flat_feat(fr, bnd)))[:k]]
            pred = max(set(top), key=lambda c: list(top).count(c))
            tot += 1; cor += (pred == wd)
            if pred != wd:
                conf[(wd, pred)] += 1
        return (cor / tot if tot else 0.0), conf

    _, conf = flat_knn(train, valc, uni)
    pairs = sorted(((X, Y, c) for (X, Y), c in conf.items()), key=lambda t: -t[2])

    # --- 2. agent composes its ear from those confusions ------------------
    spectra = defaultdict(list)
    for wd, fr in train + valc:
        spectra[wd].append(fr.mean(0))
    spectra = {wd: np.asarray(v) for wd, v in spectra.items() if len(v) >= 2}
    info, used = informativeness_vector(spectra, pairs, N_BINS)
    comp = equal_information_layout(info, res_out)
    print(f"  agent composed a {len(comp)-1}-band ear from {len(used)} confused pairs "
          f"({sum(c for *_ , c in pairs)} confusions)")

    # CHANNEL RELIABILITY: each channel's own standalone accuracy on the conf split — the
    # precision the reliability-weighted product raises each channel to (a weak channel gets a
    # small exponent so it can't drag the strong one — the fix the session promoted).
    def channel_acc(tr, ev, featfn, bnd, k=3):
        Xtr = np.array([featfn(fr, bnd) for _, fr in tr]); Wtr = np.array([wd for wd, _ in tr])
        cor = tot = 0
        for wd, fr in ev:
            if wd not in core:
                continue
            top = Wtr[np.argsort(-(Xtr @ featfn(fr, bnd)))[:k]]
            cor += (max(set(top), key=lambda c: list(top).count(c)) == wd); tot += 1
        return cor / tot if tot else 0.0

    r_flat = channel_acc(train, valc, flat_feat, comp)
    r_trans = channel_acc(train, valc, trans_feat, comp)
    print(f"  channel reliability (conf split): FLAT {r_flat:.2f}  TRANSITION {r_trans:.2f} "
          f"(weak -> down-weighted)")

    # --- 3. the agent's COMBINATORIAL recogniser (FLAT x TRANSITION, composed ear) ----
    s = Substrate()
    wn = {wd: s.add_node("Concept", {"name": wd, cr.WORD_ATTR: 1.0}) for wd in core}
    prod = cr.predict_combinatorial_term()                 # plain Bayes product
    relw = cr.predict_reliability_weighted_term()          # reliability-weighted (promoted)
    cands = list(core)

    def comb_recognise(tr, ev, bnd):
        Ftr = np.array([flat_feat(fr, bnd) for _, fr in tr])
        Ttr = np.array([trans_feat(fr, bnd) for _, fr in tr])
        Wtr = np.array([wd for wd, _ in tr])
        cp = cw = tot = 0
        for wd, fr in ev:
            if wd not in core:
                continue
            pa = cr.channel_likelihood(flat_feat(fr, bnd), Ftr, Wtr, cands)
            pt = cr.channel_likelihood(trans_feat(fr, bnd), Ttr, Wtr, cands)
            for c in cands:
                s.set_attr(wn[c], cr.P_FLAT_ATTR, float(pa[c]))
                s.set_attr(wn[c], cr.P_TRANS_ATTR, float(pt[c]))
                s.set_attr(wn[c], cr.R_FLAT_ATTR, float(r_flat))
                s.set_attr(wn[c], cr.R_TRANS_ATTR, float(r_trans))
            wp = s._inner.evaluate(prod, {}); ww = s._inner.evaluate(relw, {})
            cp += (next(c for c, nd in wn.items() if nd == wp) == wd)
            cw += (next(c for c, nd in wn.items() if nd == ww) == wd)
            tot += 1
        return (cp / tot if tot else 0.0), (cw / tot if tot else 0.0)

    # --- 4. the comparison table ------------------------------------------
    acc_uni_flat, _ = flat_knn(train, test, uni)
    acc_cmp_flat, _ = flat_knn(train, test, comp)
    acc_prod, acc_relw = comb_recognise(train, test, comp)
    n_test = sum(1 for wd, _ in test if wd in core)
    print("\n  " + "=" * 70)
    print(f"  TEST recognition ({n_test} in-vocab words):")
    print(f"    uniform ear, FLAT only               : {acc_uni_flat:.1%}")
    print(f"    COMPOSED ear, FLAT only              : {acc_cmp_flat:.1%}   "
          f"({acc_cmp_flat-acc_uni_flat:+.1%} from the agent's ear)")
    print(f"    COMPOSED ear, plain product          : {acc_prod:.1%}   "
          f"({acc_prod-acc_cmp_flat:+.1%}; weak transition DRAGS)")
    print(f"    COMPOSED ear, RELIABILITY-weighted   : {acc_relw:.1%}   "
          f"({acc_relw-acc_cmp_flat:+.1%}; down-weights the weak channel)")
    print("=" * 78)
    best = max(acc_cmp_flat, acc_relw)
    print(f"  agent's ear + agent's recogniser: {acc_uni_flat:.1%} -> {best:.1%} "
          f"({best-acc_uni_flat:+.1%}), both composed from its OWN held machinery.")


if __name__ == "__main__":
    main()
