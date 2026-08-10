"""The jabberwock EARNS a better phone model — EM forced alignment + delta features.

The sub-word recognizer works (content 0.01->0.36 boundary-free) but the per-frame phone
model is crude (~0.09) because it was trained on FLAT-START proportional alignment (frames
near phone boundaries are mislabelled). The agent EARNS a better one the classic way:

  E-step: for each word, VITERBI-align its frames to its KNOWN phone sequence under the
          current model (monotonic forced alignment) -> clean (frame, phone) labels.
  M-step: re-fit the phone encoder (PCA->LDA WithinScatter) + GMM centroids on the
          re-aligned pairs.
  iterate (EM) — the alignment and the model bootstrap each other.
plus DELTA features (the spectral velocity channel) in the per-frame context.

Measures per-frame phone accuracy per EM iteration + final boundary-free content recall,
vs the flat-start baseline.
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_earns_phone_model.py [n_test] [iters]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.jabberwock_subword_recognizer import _load_ph, best_window_match


def ctxd(M, W=4, e=None):
    """per-frame context (t-W..t+W) + DELTA (velocity) channel, L2.

    BACKWARD COMPATIBLE: called as ``ctxd(M)`` (no energy) it is BIT-IDENTICAL to
    the prior shape-only feature — the spectral SHAPE channels never change, so
    every existing consumer that reads the L2-normalised shape is unaffected.

    DEFAULT-PATH ENERGY (additive): when the per-frame energy ``e`` is supplied
    (the magnitude frames() divides out by per-frame L2-norm), a log-energy +
    delta-log-energy channel is APPENDED to the shape feature. The shape block is
    bit-identical; energy is purely an extra suffix block. This is the FREE win
    (commit 74aaa27e): retaining the discarded per-frame energy cues stops' bursts
    and fricatives' frication at ~zero added per-frame cost."""
    M = np.asarray(M, float); n, nb = M.shape
    d = np.vstack([np.zeros((1, nb)), np.diff(M, axis=0)])
    Pm = np.pad(M, ((W, W), (0, 0)), mode="edge")
    Pd = np.pad(d, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, (2 * W + 1) * nb * 2))
    for t in range(n):
        v = np.concatenate([Pm[t:t + 2 * W + 1].reshape(-1), Pd[t:t + 2 * W + 1].reshape(-1)])
        out[t] = v / max(np.linalg.norm(v), 1e-9)
    if e is None:
        return out
    return np.concatenate([out, energy_channel(e, W)], axis=1)


def energy_channel(e, W=4):
    """per-frame ENERGY context: log-energy + delta-log-energy over the t-W..t+W
    window, z-scored WITHIN the utterance (speaker/gain invariant). This is the
    channel that per-frame L2-normalisation discards. Identical to the gate's
    feat_energy (scripts.jabberwock_phone_capacity), promoted to the default path."""
    e = np.asarray(e, float); n = len(e)
    le = np.log(e + 1e-6)
    le = (le - le.mean()) / (le.std() + 1e-9)
    dle = np.concatenate([[0.0], np.diff(le)])
    Pl = np.pad(le, (W, W), mode="edge")
    Pd = np.pad(dle, (W, W), mode="edge")
    out = np.empty((n, (2 * W + 1) * 2))
    for t in range(n):
        out[t] = np.concatenate([Pl[t:t + 2 * W + 1], Pd[t:t + 2 * W + 1]])
    return out


def fit_model(X, Y, phones_set, pi, K=4):
    nP = len(phones_set)
    P = min(120, X.shape[0] - nP - 1)
    mu, Wp = _fit_pca(X, P)
    Wl = _fit_lda((X - mu) @ Wp, Y, k=min(P, nP - 1))
    def enc(Z):
        R = ((np.asarray(Z) - mu) @ Wp) @ Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)
    E = enc(X)
    cent, cphone = [], []
    rng = np.random.default_rng(0)
    for p in phones_set:
        Zp = E[[i for i in range(len(Y)) if Y[i] == p]]
        if len(Zp) == 0:
            continue
        Cc = Zp[rng.choice(len(Zp), min(K, len(Zp)), replace=False)].copy()
        for _ in range(6):
            lab = (((Zp[:, None, :] - Cc[None]) ** 2).sum(2)).argmin(1)
            for k in range(len(Cc)):
                m = Zp[lab == k]
                if len(m):
                    Cc[k] = m.mean(0)
        for c in Cc:
            cent.append(c); cphone.append(pi[p])
    cent = np.array(cent); cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
    return enc, cent, np.array(cphone)


def phone_emission(feats, enc, cent, cphone, nP):
    """(n_frames x nP) max-over-centroids cosine emission per phone."""
    sims = enc(feats) @ cent.T               # (n, ncent)
    emis = np.full((sims.shape[0], nP), -1e9)
    for c in range(cent.shape[0]):
        np.maximum(emis[:, cphone[c]], sims[:, c], out=emis[:, cphone[c]])
    return emis


def viterbi_align(emis, pj):
    """monotonic forced alignment: assign each frame a position in the phone seq pj
    (non-decreasing, contiguous), maximising summed emission. Returns per-frame phone idx."""
    n = emis.shape[0]; P = len(pj)
    if P == 1:
        return [pj[0]] * n
    NEG = -1e18
    dp = np.full((n, P), NEG); bp = np.zeros((n, P), int)
    dp[0, 0] = emis[0, pj[0]]
    for i in range(1, n):
        for j in range(min(i + 1, P)):
            stay = dp[i - 1, j]
            adv = dp[i - 1, j - 1] if j > 0 else NEG
            if stay >= adv:
                dp[i, j] = stay + emis[i, pj[j]]; bp[i, j] = j
            else:
                dp[i, j] = adv + emis[i, pj[j]]; bp[i, j] = j - 1
    j = P - 1; out = [0] * n
    for i in range(n - 1, -1, -1):
        out[i] = pj[j]; j = bp[i, j]
    return out


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    # DEFAULT phone model now loads with the energy channel (with_energy=True);
    # banks predating the energy channel return e=None -> ctxd degrades to shape-only.
    train = _load_ph("train-clean-100_*.pkl", 12, with_energy=True)[:8000]
    dev = _load_ph("dev-clean_*.pkl", 12, with_energy=True)
    has_energy = bool(train) and train[0][3] is not None
    print("=" * 84)
    print("EARN A BETTER PHONE MODEL — EM forced alignment + delta features"
          + ("  [+ENERGY default channel]" if has_energy else "  [shape-only bank]"))
    print("=" * 84)

    # precompute per-word context+delta(+energy) features + phone-index sequences.
    # ctxd(fr, e=en) APPENDS the energy channel when present (additive); ctxd(fr) is
    # bit-identical shape-only otherwise. The DEFAULT path opts in.
    phones_set = sorted({p for _w, _f, ph, _e in train for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}; nP = len(phones_set)
    feats = [ctxd(fr, e=en) for _w, fr, _ph, en in train]
    pjs = [[pi[p] for p in ph] for _w, _f, ph, _e in train]
    # flat-start (proportional) labels
    labels = []
    for cx, ph in zip(feats, [t[2] for t in train]):
        n = len(cx); P = len(ph)
        labels.append([pi[ph[int(i * P / n)]] for i in range(n)])
    iv = {i: p for p, i in pi.items()}
    print(f"  phones={nP}  train words={len(train)}  feat dim={feats[0].shape[1]}", flush=True)

    # dev eval data (proportional dev labels, for a comparable per-frame acc proxy)
    dfeat = [ctxd(fr, e=en) for _w, fr, _ph, en in dev[:1500]]
    dlab = []
    for cx, (_w, _f, ph, _e) in zip(dfeat, dev[:1500]):
        n = len(cx); P = len(ph); dlab.append([ph[int(i * P / n)] for i in range(n)])
    Xde = np.concatenate(dfeat); Yde = [p for s in dlab for p in s]

    enc = cent = cphone = None
    for it in range(iters + 1):
        X = np.concatenate(feats); Y = [iv[i] for s in labels for i in s]
        enc, cent, cphone = fit_model(X, Y, phones_set, pi)
        pred = cphone[(enc(Xde) @ cent.T).argmax(1)]
        acc = np.mean([phones_set[pred[k]] == Yde[k] for k in range(len(Yde))])
        tag = "flat-start" if it == 0 else f"EM iter {it}"
        print(f"  [{tag:11}] per-frame phone acc (dev): {acc:.3f}", flush=True)
        if it == iters:
            break
        # E-step: Viterbi forced-align every train word under the current model
        new = []
        for cx, pj in zip(feats, pjs):
            emis = phone_emission(cx, enc, cent, cphone, nP)
            new.append(viterbi_align(emis, pj))
        labels = new

    # ---- final: boundary-free content recall on continuous utterances ----
    func = set(w for w, _, _, _ in train[:0]) or set(w for w, _ in Counter(w for w, _, _, _ in train).most_common(50))
    def is_content(w): return w not in func and len(w) >= 4

    def decode(M, e=None):
        idx = cphone[(enc(ctxd(M, e=e)) @ cent.T).argmax(1)]
        seq, prev = [], -1
        for k in idx:
            if k != prev:
                seq.append(phones_set[k]); prev = k
        return seq

    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    rx35 = rx50 = tot = 0; t0 = time.time()
    for (path, sp, ch, ut, tr) in test:
        try:
            M, e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        pseq = decode(M, e if has_energy else None)
        for w in set(w.lower() for w in L.normalise(tr)):
            if not is_content(w):
                continue
            tgt = cmu_phones(w)
            if not tgt:
                continue
            tot += 1; d = best_window_match(pseq, [str(x) for x in tgt])
            rx35 += (d <= 0.35); rx50 += (d <= 0.50)
    print("=" * 84)
    print(f"  boundary-free content recall: @0.35 {rx35/max(tot,1):.3f}  @0.50 {rx50/max(tot,1):.3f}  "
          f"({tot} content words) [{time.time()-t0:.0f}s]")
    print(f"  (flat-start phone model: per-frame ~0.09, content @0.50 ~0.36; EM should lift both)")
    print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
