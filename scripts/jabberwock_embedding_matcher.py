"""The jabberwock builds the CONTINUOUS EMBEDDING MATCHER.

The syllable UNIT integrates well (per-syllable 0.18 > phone 0.10) but discrete sparse-
token matching squanders it (content recall 0.03: 4131 syllable types, OOV, brittle exact
match). Fix the BACK-END: match syllables in CONTINUOUS EMBEDDING space. A word = a
SEQUENCE of syllable EMBEDDINGS (no discrete token, no OOV); recognise by embedding-DTW of
that sequence against the decoded syllable-embedding stream. Combines the syllable's
integration (discrimination) with the phone string's non-brittle (approximate) matching.

  WORD TEMPLATE : syllabify the word; each syllable -> its integrated embedding (syllable
                  encoder), averaged over train exemplars -> a short embedding SEQUENCE.
  DECODE        : continuous utterance -> energy-prominence syllable spans (stress
                  localizes) -> syllable embeddings -> the decoded embedding stream.
  MATCH         : sliding embedding-DTW (cosine local cost) of each content word's
                  embedding sequence over the stream; low normalised cost = transmitted.

Content recall vs discrete-syllable (0.03) and phone sub-word (0.35).
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_embedding_matcher.py [n_test] [K]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_syllable_recognizer import (syllabify, syl_feat, key,
                                                    syl_spans_proportional, syl_spans_energy)


def dtw_cos(A, B):
    """length-normalised DTW between two syllable-embedding sequences (cosine local cost)."""
    A = np.asarray(A); B = np.asarray(B)
    if len(A) == 0 or len(B) == 0:
        return 1.0
    D = 1.0 - A @ B.T
    n, m = D.shape
    dp = np.full((n + 1, m + 1), 1e18); dp[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i, j] = D[i - 1, j - 1] + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])
    return dp[n, m] / (n + m)


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    per = 20
    train = _load_ph("train-clean-100_*.pkl", 12)
    print("=" * 84)
    print("CONTINUOUS EMBEDDING MATCHER — word = syllable-embedding sequence, embedding-DTW")
    print("=" * 84)

    # ---- earn the syllable encoder (PCA->LDA on syllable classes) ----
    sc = Counter(key(s) for w, fr, ph in train for s in syllabify(ph))
    inv = set(s for s, _ in sc.most_common(800))
    X, Y = [], []
    for w, fr, ph in train:
        syl = syllabify(ph)
        for (a, b), sy in zip(syl_spans_proportional(len(fr), len(syl)), syl):
            if key(sy) in inv:
                X.append(syl_feat(fr[a:b])); Y.append(key(sy))
        if len(X) >= 60000:
            break
    X = np.array(X); nS = len(set(Y)); P = min(200, X.shape[0] - nS - 1)
    mu, Wp = _fit_pca(X, P); Wl = _fit_lda((X - mu) @ Wp, Y, k=min(P, nS - 1))
    def enc1(v):
        r = ((np.asarray(v) - mu) @ Wp) @ Wl
        return r / max(np.linalg.norm(r), 1e-9)
    print(f"  syllable encoder {Wl.shape[1]}d  train spans={len(X)}", flush=True)

    # ---- content vocab + word templates = syllable-embedding SEQUENCES (train) ----
    sw = Counter(w for w, _, _ in train)
    func = set(w for w, _ in sw.most_common(50))
    def is_content(w): return w not in func and len(w) >= 4
    devw = Counter(w for w, _, _ in _load_ph("dev-clean_*.pkl", 12))
    cvocab = [w for w, _ in sw.most_common() if is_content(w) and devw[w] >= 1][:K]
    cset = set(cvocab)
    seqs = defaultdict(list)            # word -> list of (per-exemplar syllable-embedding seq)
    cnt = defaultdict(int)
    for w, fr, ph in train:
        if w in cset and cnt[w] < per:
            syl = syllabify(ph)
            emb = [enc1(syl_feat(fr[a:b]))
                   for (a, b) in syl_spans_proportional(len(fr), len(syl))]
            if emb:
                seqs[w].append(emb); cnt[w] += 1
    tmpl = {}
    for w, lst in seqs.items():
        modal = Counter(len(e) for e in lst).most_common(1)[0][0]   # modal syllable count
        good = [e for e in lst if len(e) == modal]
        if good:
            tmpl[w] = [np.mean([g[i] for g in good], 0) for i in range(modal)]
            tmpl[w] = [v / max(np.linalg.norm(v), 1e-9) for v in tmpl[w]]
    print(f"  content word templates={len(tmpl)} (embedding sequences)", flush=True)

    # ---- decode continuous + content recall via sliding embedding-DTW ----
    def best_match(W, stream):
        S = len(W); best = 1.0
        for i in range(0, max(1, len(stream) - S + 1)):
            for span in (S, S + 1, max(1, S - 1)):
                best = min(best, dtw_cos(W, stream[i:i + span]))
        return best

    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); tsp = set(spk[-6:])
    test = [p for p in pairs if p[1] in tsp][:n_test]
    rng = np.random.default_rng(0)
    pos, neg = [], []; t0 = time.time()
    tmpl_words = list(tmpl)
    for (path, sp, ch, ut, tr) in test:
        try:
            M, e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        stream = [enc1(syl_feat(M[a:b])) for (a, b) in syl_spans_energy(e)]
        if not stream:
            continue
        present = set(w.lower() for w in L.normalise(tr))
        in_utt = [w for w in present if w in tmpl]
        for w in in_utt:                              # POSITIVES: words that ARE there
            pos.append(best_match(tmpl[w], stream))
        # NEGATIVES: same count of words NOT in this utterance (the discriminative control)
        cand = [w for w in tmpl_words if w not in present]
        for w in rng.choice(cand, min(len(in_utt), len(cand)), replace=False):
            neg.append(best_match(tmpl[w], stream))
    pos = np.array(pos); neg = np.array(neg)
    # AUC = P(a present word matches better (lower cost) than an absent one)
    auc = float(np.mean(pos[:, None] < neg[None, :])) if len(pos) and len(neg) else 0.0
    thr = float(np.percentile(neg, 10)) if len(neg) else 0.0      # FPR = 10%
    recall = float(np.mean(pos <= thr)) if len(pos) else 0.0
    print("=" * 84)
    print(f"  DISCRIMINATIVE control: present-word DTW {pos.mean():.3f} vs absent-word {neg.mean():.3f}")
    print(f"  AUC (present matches better than absent): {auc:.3f}   (0.5 = chance/over-generation)")
    print(f"  content recall @ 10% false-positive rate: {recall:.3f}   ({len(pos)} present, {len(neg)} absent)")
    print(f"  [{time.time()-t0:.0f}s]  (the raw min-over-windows recall was a false-positive artifact)")
    print("=" * 84)
    print(f"  {'EMBEDDING MATCHER DISCRIMINATES content (real)' if auc > 0.6 else 'over-generates (AUC~0.5): no real discrimination'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
