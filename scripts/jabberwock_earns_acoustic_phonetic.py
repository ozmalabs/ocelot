"""The jabberwock EARNS the acoustic-phonetic decoder (N2) — recover the ENERGY channel.

Per-frame phone accuracy is capped ~0.13 and survives classifier (linear==kernel),
alignment (EM), context, deltas. The one demonstrably-DISCARDED information is ENERGY:
the phonebank L2-normalised it away per frame, but obstruents (stops/fricatives/affricates)
are strongly energy- and dynamics-cued. Continuous frames() RETAINS energy, so build the
phone training set straight from audio (train + test both via frames(), energy consistent)
and test whether re-introducing the energy channel lifts per-frame phone accuracy.

  feature: per-frame [normalised bands] (+ optional [log-energy]) -> context +-W + delta.
  align  : whole-utterance phones proportionally to frames (no aligner; noisier than the
           phonebank's per-word, but identical for both variants so the COMPARISON is fair).
  variants: spectral-only  vs  spectral+energy  vs  cepstral(DCT)  -> per-frame phone acc.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_earns_acoustic_phonetic.py [n_train] [n_dev]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda

LIB = "/home/matt/data/LibriSpeech"


def gather(split, n_utt):
    base = os.path.join(LIB, split); out = []
    for root, _, names in os.walk(base):
        trans = {}
        for fn in names:
            if fn.endswith(".trans.txt"):
                for line in open(os.path.join(root, fn)):
                    pr = line.strip().split(" ", 1)
                    if len(pr) == 2:
                        trans[pr[0]] = pr[1]
        for fn in names:
            if fn.endswith(".flac") and fn[:-5] in trans:
                out.append((os.path.join(root, fn), trans[fn[:-5]]))
        if len(out) >= n_utt:
            break
    return out[:n_utt]


def utt_phones(tr):
    seq = []
    for w in tr.lower().split():
        w = "".join(c for c in w if c.isalpha())
        if not w:
            continue
        ph = cmu_phones(w)
        if ph:
            seq += [str(x) for x in ph]
    return seq


import scripts.librispeech_wer as L


def context(B, W=4):
    """context +-W + delta over a per-frame base matrix B (n, d)."""
    n, d = B.shape
    dd = np.vstack([np.zeros((1, d)), np.diff(B, axis=0)])
    Pb = np.pad(B, ((W, W), (0, 0)), mode="edge"); Pd = np.pad(dd, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, (2 * W + 1) * d * 2))
    for t in range(n):
        v = np.concatenate([Pb[t:t + 2 * W + 1].reshape(-1), Pd[t:t + 2 * W + 1].reshape(-1)])
        out[t] = v / max(np.linalg.norm(v), 1e-9)
    return out


def _dct(nb, nk):
    k = np.arange(nk)[:, None]; n = np.arange(nb)[None, :]
    return np.cos(np.pi * (n + 0.5) * k / nb)            # DCT-II basis (nk x nb)


def build(utts, mode, cap=45000):
    """per-frame (feature, phone) pairs. mode: spectral | energy | cepstral."""
    DM = _dct(32, 20)
    X, Y = [], []
    for path, tr in utts:
        try:
            M, e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        seq = utt_phones(tr)
        if len(seq) < 2 or len(M) < 4:
            continue
        if mode == "cepstral":
            B = (M @ DM.T)                                # decorrelated spectral shape
        else:
            B = M
        if mode == "energy":
            le = np.log(np.asarray(e, float) + 1e-6)
            le = (le - le.mean()) / (le.std() + 1e-6)     # z-scored log-energy
            B = np.concatenate([M, le[:, None]], axis=1)
        F = context(B)
        P = len(seq)
        for i in range(len(F)):
            X.append(F[i]); Y.append(seq[int(i * P / len(F))])
        if len(X) >= cap:
            break
    return np.array(X), Y


def per_frame_acc(Xtr, Ytr, Xde, Yde):
    phset = sorted(set(Ytr)); pi = {p: i for i, p in enumerate(phset)}; nP = len(phset)
    Pd = min(120, Xtr.shape[0] - nP - 1)
    mu, Wp = _fit_pca(Xtr, Pd); Wl = _fit_lda((Xtr - mu) @ Wp, Ytr, k=min(Pd, nP - 1))
    def enc(Z):
        R = ((np.asarray(Z) - mu) @ Wp) @ Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)
    E = enc(Xtr); rng = np.random.default_rng(0)
    cent, cph = [], []
    for p in phset:
        Zp = E[[i for i in range(len(Ytr)) if Ytr[i] == p]]
        if not len(Zp):
            continue
        C = Zp[rng.choice(len(Zp), min(4, len(Zp)), replace=False)].copy()
        for _ in range(5):
            lab = (((Zp[:, None] - C[None]) ** 2).sum(2)).argmin(1)
            for k in range(len(C)):
                m = Zp[lab == k]
                if len(m):
                    C[k] = m.mean(0)
        for c in C:
            cent.append(c); cph.append(pi[p])
    cent = np.array(cent); cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
    cph = np.array(cph)
    keep = [k for k in range(len(Yde)) if Yde[k] in pi]
    pred = cph[(enc(Xde[keep]) @ cent.T).argmax(1)]
    return float(np.mean([phset[pred[i]] == Yde[keep[i]] for i in range(len(keep))])), 1.0 / nP


def main():
    n_tr = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    n_de = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    tr = gather("train-clean-100", n_tr); de = gather("dev-clean", n_de)
    print("=" * 80)
    print("EARN THE ACOUSTIC-PHONETIC DECODER — does the ENERGY channel lift per-frame phone acc?")
    print("=" * 80)
    print(f"  train utts={len(tr)}  dev utts={len(de)} (cross-split speakers)", flush=True)
    t0 = time.time()
    for mode in ("spectral", "cepstral", "energy"):
        Xtr, Ytr = build(tr, mode); Xde, Yde = build(de, mode, cap=15000)
        acc, ch = per_frame_acc(Xtr, Ytr, Xde, Yde)
        print(f"  [{mode:9}] per-frame phone acc: {acc:.3f}  (chance {ch:.3f})  dim={Xtr.shape[1]}", flush=True)
    print("=" * 80)
    print(f"  [{time.time()-t0:.0f}s]  energy>spectral => the discarded energy channel was the missing")
    print("  information (obstruents are energy-cued); the acoustic-phonetic decoder's floor is the FEATURE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
