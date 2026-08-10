"""The jabberwock builds the SYLLABLE recognizer — where all the threads converge.

The phone is too small (frame-level feature ~0.10, energy-less). The WORD integrated over
its whole span gives 0.78 but needs oracle boundaries. The SYLLABLE is the unit that
(a) INTEGRATES enough to discriminate (like the word, unlike the phone), (b) is LOCALIZABLE
by stress/energy peaks (prominence peaks ~ syllables, r=0.93), (c) is SUB-WORD (boundary-
free sequence-decodable). It unifies the stress thread + the sub-word-sequence thread.

  SYLLABIFY : phones -> syllables (one vowel-nucleus each).
  FEATURE   : per-syllable INTEGRATED feature (peel + resample L + velocity) -> earn a
              syllable encoder (PCA->LDA WithinScatter) + centroids. The integration is
              the point: a syllable span, not a frame.
  DECODE    : continuous utterance -> energy prominence -> syllable spans (between energy
              valleys, each around a peak) -> syllable feature -> nearest centroid ->
              syllable sequence. Boundary-free; stress localizes.
  CONTENT   : a content word transmits if its syllable-sequence matches the decoded
              syllable sequence (token edit distance).

Tests per-SYLLABLE accuracy (vs phone 0.10) + boundary-free content recall.
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_syllable_recognizer.py [n_test] [K_inv]
"""
import os, re, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_stress_feature import sonority

VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY",
          "OW", "OY", "UH", "UW"}


def is_vowel(p):
    return re.sub(r"\d", "", str(p)).upper() in VOWELS


def syllabify(phs):
    """phones -> syllables, one vowel nucleus each (onset+nucleus; trailing coda joins last)."""
    syl, cur = [], []
    for p in phs:
        cur.append(str(p))
        if is_vowel(p):
            syl.append(tuple(cur)); cur = []
    if cur:
        if syl:
            syl[-1] = syl[-1] + tuple(cur)
        else:
            syl = [tuple(cur)]
    return syl


def _resample(fr, Ln):
    n = len(fr)
    if n == Ln:
        return fr
    idx = np.linspace(0, n - 1, Ln); lo = np.floor(idx).astype(int)
    hi = np.clip(lo + 1, 0, n - 1); t = (idx - lo)[:, None]
    return fr[lo] * (1 - t) + fr[hi] * t


def syl_feat(span, Ln=12):
    """INTEGRATED syllable feature: peel span mean, resample to Ln, + velocity, flat, L2."""
    span = np.asarray(span, float)
    if len(span) < 2:
        span = np.vstack([span, span])
    x = _resample(span - span.mean(0), Ln)
    d = np.vstack([np.zeros((1, x.shape[1])), np.diff(x, axis=0)])
    v = np.concatenate([x, d], axis=1).reshape(-1)
    return v / max(np.linalg.norm(v), 1e-9)


def syl_spans_proportional(nframes, nsyl):
    cuts = np.linspace(0, nframes, nsyl + 1).astype(int)
    return [(cuts[i], cuts[i + 1]) for i in range(nsyl) if cuts[i + 1] > cuts[i]]


def syl_spans_energy(e):
    """continuous syllable spans: cut the sonority contour at its local minima (between
    adjacent prominence peaks = syllable nuclei). Stress localizes the syllables."""
    s = sonority(e); cuts = [0]
    for i in range(1, len(s) - 1):
        if s[i] <= s[i - 1] and s[i] < s[i + 1]:
            cuts.append(i)
    cuts.append(len(s))
    return [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1) if cuts[i + 1] - cuts[i] >= 3]


def key(syl):
    return "+".join(syl)


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    K_inv = int(sys.argv[2]) if len(sys.argv) > 2 else 800
    train = _load_ph("train-clean-100_*.pkl", 12)
    dev = _load_ph("dev-clean_*.pkl", 12)
    print("=" * 84)
    print("SYLLABLE RECOGNIZER — integrated unit, stress-localized, boundary-free")
    print("=" * 84)

    # syllable inventory (top-K by frequency)
    sc = Counter()
    for w, fr, ph in train:
        for sy in syllabify(ph):
            sc[key(sy)] += 1
    inv = [s for s, _ in sc.most_common(K_inv)]
    iset = set(inv); si = {s: i for i, s in enumerate(inv)}
    print(f"  distinct syllables={len(sc)}  inventory K={len(inv)}  "
          f"(covers {100*sum(sc[s] for s in inv)/sum(sc.values()):.0f}% of tokens)", flush=True)

    # training pairs: per word, syllabify + proportional frame split -> (syl_feat, syl)
    X, Y = [], []
    for w, fr, ph in train:
        syl = syllabify(ph)
        for (a, b), sy in zip(syl_spans_proportional(len(fr), len(syl)), syl):
            k = key(sy)
            if k in iset:
                X.append(syl_feat(fr[a:b])); Y.append(k)
        if len(X) >= 60000:
            break
    X = np.array(X); nS = len(set(Y))
    P = min(200, X.shape[0] - nS - 1)
    mu, Wp = _fit_pca(X, P); Wl = _fit_lda((X - mu) @ Wp, Y, k=min(P, nS - 1))
    def enc(Z):
        R = ((np.asarray(Z) - mu) @ Wp) @ Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)
    E = enc(X)
    cent = np.array([E[[i for i in range(len(Y)) if Y[i] == s]].mean(0) for s in inv if s in set(Y)])
    cwords = [s for s in inv if s in set(Y)]
    cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
    print(f"  syllable classes={len(cwords)}  train spans={len(X)}  encoder {Wl.shape[1]}d", flush=True)

    # per-SYLLABLE accuracy (dev, cross-speaker; proportional spans)
    Xd, Yd = [], []
    for w, fr, ph in dev[:1500]:
        syl = syllabify(ph)
        for (a, b), sy in zip(syl_spans_proportional(len(fr), len(syl)), syl):
            if key(sy) in iset:
                Xd.append(syl_feat(fr[a:b])); Yd.append(key(sy))
    pred = (enc(np.array(Xd)) @ cent.T).argmax(1)
    acc = np.mean([cwords[pred[i]] == Yd[i] for i in range(len(Yd))])
    print(f"  per-SYLLABLE accuracy (dev): {acc:.3f}  (chance {1/len(cwords):.4f})  "
          f"[vs per-frame phone 0.10]", flush=True)

    # boundary-free decode + content recall
    func = set(w for w, _ in Counter(w for w, _, _ in train).most_common(50))
    def is_content(w): return w not in func and len(w) >= 4

    def syl_edit(a, b):
        la, lb = len(a), len(b)
        if not la or not lb:
            return 1.0
        d = list(range(lb + 1))
        for i in range(1, la + 1):
            prev = d[0]; d[0] = i
            for j in range(1, lb + 1):
                cur = d[j]; d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1])); prev = cur
        return d[lb] / max(la, lb)

    def decode_syls(M, e):
        out = []
        for a, b in syl_spans_energy(e):
            out.append(cwords[int((cent @ enc([syl_feat(M[a:b])])[0]).argmax())])
        return out

    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); tsp = set(spk[-6:])
    test = [p for p in pairs if p[1] in tsp][:n_test]
    rx40 = rx60 = tot = 0; t0 = time.time()
    for (path, sp, ch, ut, tr) in test:
        try:
            M, e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        dsy = decode_syls(M, e)
        for w in set(w.lower() for w in L.normalise(tr)):
            if not is_content(w):
                continue
            tgt = cmu_phones(w)
            if not tgt:
                continue
            wsy = [key(s) for s in syllabify([str(x) for x in tgt])]
            tot += 1
            best = min((syl_edit(dsy[i:i + len(wsy) + 1], wsy)
                        for i in range(max(1, len(dsy) - len(wsy) + 1))), default=1.0)
            rx40 += (best <= 0.40); rx60 += (best <= 0.60)
    print("=" * 84)
    print(f"  boundary-free content recall (syllable-seq match): @0.40 {rx40/max(tot,1):.3f}  "
          f"@0.60 {rx60/max(tot,1):.3f}  ({tot} words) [{time.time()-t0:.0f}s]")
    print(f"  (phone sub-word: per-frame 0.10, content @0.50 0.35)")
    print("=" * 84)
    ok = acc > 0.20
    print(f"  {'SYLLABLE UNITS INTEGRATE -> far more discriminable than phones' if ok else 'limited'} "
          f"(per-syllable {acc:.2f} vs per-frame phone 0.10).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
