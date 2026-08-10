"""The jabberwock builds the SUB-WORD SEQUENCE recognizer — the boundary-free paradigm.

Whole-word template matching caps at oracle boundaries (commit 8daf66db). The fix is the
frame-level / sub-word frame: model PHONES per frame, decode a continuous utterance to a
phone STRING (no word boundaries), recover words by their phone-sequences in that string.
The phonebank stores phones per word; phones() is the lexicon (word -> phone-seq).

  PHONE MODEL : proportional-align each word's frames to its phones -> (frame-context,
                phone) pairs; earn a phone encoder (PCA->LDA, the agent's WithinScatter,
                ~40 classes) + phone centroids. Per-frame phone = argmax centroid.
  DECODE      : continuous utterance -> per-frame phone -> collapse repeats (CTC-style)
                -> phone string. Boundary-free.
  TRANSMISSION: a CONTENT word transmits if its phone-seq matches (approx, normalised
                edit distance) a window of the decoded phone string. No word boundaries.

Measures per-frame phone accuracy (cross-speaker) + content recall vs whole-word ~0.
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_subword_recognizer.py [n_test]
"""
import glob, os, pickle, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda

BANK = "/home/matt/data/phonebank"


def _load_ph(g, cap, with_energy=False):
    """Load banked (word, frames, phones) tuples.

    BACKWARD COMPATIBLE: returns the historical 3-tuple ``(w, fr, ph)`` by default
    so every existing consumer is unaffected. Banks written with the energy channel
    carry a 4th element (per-frame pre-norm energy); with ``with_energy=True`` this
    is surfaced as ``(w, fr, ph, e)`` for the DEFAULT energy-augmented phone model.
    Older energy-less banks return ``e=None`` so callers degrade to shape-only."""
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, g)))[:cap]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 3 and isinstance(e[0], str):
                w = e[0].lower(); fr = np.asarray(e[1], float); ph = e[2]
                if w.isalpha() and fr.shape[0] >= 3 and isinstance(ph, (list, tuple)) and ph:
                    if with_energy:
                        en = np.asarray(e[3], float) if len(e) >= 4 and e[3] is not None else None
                        out.append((w, fr, [str(x) for x in ph], en))
                    else:
                        out.append((w, fr, [str(x) for x in ph]))
    return out


def ctx(M, W=5):
    """per-frame context feature: stack frames t-W..t+W (edge-padded), L2."""
    M = np.asarray(M, float); n, nb = M.shape
    P = np.pad(M, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, (2 * W + 1) * nb))
    for t in range(n):
        v = P[t:t + 2 * W + 1].reshape(-1)
        out[t] = v / max(np.linalg.norm(v), 1e-9)
    return out


def align_pairs(data, cap=40000):
    """proportional (frame-context, phone) pairs (HMM flat-start)."""
    X, Y = [], []
    for w, fr, ph in data:
        cx = ctx(fr); n = len(cx); P = len(ph)
        for i in range(n):
            X.append(cx[i]); Y.append(ph[int(i * P / n)])
        if len(X) >= cap:
            break
    return np.array(X), Y


def norm_edit(a, b):
    """normalised edit distance between two phone sequences."""
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 1.0
    d = list(range(lb + 1))
    for i in range(1, la + 1):
        prev = d[0]; d[0] = i
        for j in range(1, lb + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return d[lb] / max(la, lb)


def best_window_match(pseq, target):
    """min normalised edit distance of `target` against any ~|target|-window of pseq."""
    lt = len(target)
    if lt == 0 or len(pseq) < 1:
        return 1.0
    best = 1.0
    for s in range(0, max(1, len(pseq) - lt + 1)):
        for L2 in (lt, max(1, lt - 1), lt + 1):
            best = min(best, norm_edit(pseq[s:s + L2], target))
        if best == 0:
            break
    return best


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    train = _load_ph("train-clean-100_*.pkl", 12)
    dev = _load_ph("dev-clean_*.pkl", 12)
    print("=" * 84)
    print("SUB-WORD SEQUENCE RECOGNIZER — phone model + boundary-free decode")
    print("=" * 84)

    # ---- PHONE MODEL: earn a phone encoder + centroids (cross-speaker) ----
    Xtr, Ytr = align_pairs(train)
    phones_set = sorted(set(Ytr)); pi = {p: i for i, p in enumerate(phones_set)}
    nP = len(phones_set)
    Pdim = min(120, Xtr.shape[0] - nP - 1)
    mu, Wp = _fit_pca(Xtr, Pdim)
    Wl = _fit_lda((Xtr - mu) @ Wp, Ytr, k=min(Pdim, nP - 1))
    def enc(X):
        Y = ((np.asarray(X) - mu) @ Wp) @ Wl
        return Y / np.clip(np.linalg.norm(Y, axis=1, keepdims=True), 1e-9, None)
    Etr = enc(Xtr)
    # GMM-like: K centroids per phone (k-means) so multimodal phones aren't one blob.
    def kmeans(Z, K, it=8):
        if len(Z) <= K:
            return Z.copy()
        rng = np.random.default_rng(0); Cc = Z[rng.choice(len(Z), K, replace=False)].copy()
        for _ in range(it):
            lab = (((Z[:, None, :] - Cc[None]) ** 2).sum(2)).argmin(1)
            for k in range(K):
                m = Z[lab == k]
                if len(m):
                    Cc[k] = m.mean(0)
        return Cc
    cent, cphone = [], []
    for p in phones_set:
        Zp = Etr[[i for i in range(len(Ytr)) if Ytr[i] == p]]
        for c in kmeans(Zp, 4):
            cent.append(c); cphone.append(pi[p])
    cent = np.array(cent); cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
    cphone = np.array(cphone)
    print(f"  phones={nP}  train frames={len(Ytr)}  encoder {Wl.shape[1]}d  centroids={len(cent)}", flush=True)

    # per-frame phone accuracy (cross-speaker dev) — nearest centroid -> its phone
    Xde, Yde = align_pairs(dev, cap=12000)
    pred = cphone[(enc(Xde) @ cent.T).argmax(1)]
    acc = np.mean([phones_set[pred[i]] == Yde[i] for i in range(len(Yde))])
    print(f"  per-frame phone accuracy (dev, cross-speaker): {acc:.3f}  (chance {1/nP:.3f})", flush=True)

    def decode_phones(M):
        """continuous utterance -> per-frame phone -> collapse repeats -> phone string."""
        idx = cphone[(enc(ctx(M)) @ cent.T).argmax(1)]
        seq, prev = [], -1
        for k in idx:
            if k != prev:
                seq.append(phones_set[k]); prev = k
        return seq

    # ---- BOUNDARY-FREE content transmission on continuous utterances ----
    func = set(w for w, _ in Counter(w for w, _, _ in train).most_common(50))
    def is_content(w): return w not in func and len(w) >= 4
    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    test = [p for p in pairs if p[1] in test_spk][:n_test]

    # vocab of content words with a CMU phone-seq (for the negative control)
    vocab = sorted({w.lower() for _w, _f, _p in []} |
                   {w for w, _ in Counter(w for w, _, _ in train).most_common()
                    if is_content(w) and cmu_phones(w)})
    rng = np.random.default_rng(0)
    pos, neg = [], []; t0 = time.time()
    for (path, sp, ch, ut, tr) in test:
        try:
            M, _e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        pseq = decode_phones(M)
        present = set(w.lower() for w in L.normalise(tr))
        inw = [w for w in present if is_content(w) and cmu_phones(w)]
        for w in inw:                                    # POSITIVE: word IS in the utterance
            pos.append(best_window_match(pseq, [str(x) for x in cmu_phones(w)]))
        cand = [w for w in vocab if w not in present]    # NEGATIVE: word is NOT
        for w in rng.choice(cand, min(len(inw), len(cand)), replace=False):
            neg.append(best_window_match(pseq, [str(x) for x in cmu_phones(w)]))
    pos = np.array(pos); neg = np.array(neg)
    auc = float(np.mean(pos[:, None] < neg[None, :])) if len(pos) and len(neg) else 0.0
    thr = float(np.percentile(neg, 10)) if len(neg) else 0.0
    recall = float(np.mean(pos <= thr)) if len(pos) else 0.0
    print("\n" + "=" * 84)
    print(f"  DISCRIMINATIVE control (present vs absent content words, the honest metric):")
    print(f"     present-word edit {pos.mean():.3f} vs absent-word {neg.mean():.3f}")
    print(f"     AUC (present matches better than absent): {auc:.3f}  (0.5 = over-generation)")
    print(f"     content recall @ 10% false-positive rate: {recall:.3f}  ({len(pos)} present, {len(neg)} absent)")
    print(f"  per-frame phone acc {acc:.3f}  [{time.time()-t0:.0f}s]")
    print("=" * 84)
    print(f"  {'SUB-WORD SEQUENCE TRANSMITS CONTENT (AUC>0.6, real)' if auc > 0.6 else 'OVER-GENERATION (AUC~0.5): the raw 0.35 was a false-positive artifact too'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
