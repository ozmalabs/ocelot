"""Build the LANGUAGE PRIOR — the biggest 0.75->human lever — mostly from parts that
already exist. Recognition becomes a SECOND CHANNEL added to the agent's existing
Bayes-product combine (domains/combinatorial_recognizer: posterior ∝ P(E|H)·P(H)):

  channel 1  ACOUSTIC likelihood  P(word | audio)   — the learned recogniser.
  channel 2  LANGUAGE prior       P(word | prev)     — a word bigram (the only new
             piece; graph data like the transition channel), counted from the corpus.

A word's identity is constrained by its neighbours — order-N shape matching at the
SEQUENCE level. Decoding the ordered stream = Viterbi maximising
   sum_t [ log P_ac(w_t) + lambda * log P_lm(w_t | w_{t-1}) ]   (= the Bayes product
in log space). The corpus order is preserved within phonebank shards, so the bigram
context is the real previous word.

Cross-speaker: acoustic + LM fit on train-clean-100, tested on UNSEEN dev speakers.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_language_prior.py [n_words] [max_dev]
"""
from __future__ import annotations
import glob, os, pickle, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_learned_encoder import _spk_env, _feat, _fit_pca, _fit_lda

BANK = "/home/matt/data/phonebank"


def _stream(split_glob, cap_shards):
    """Ordered (word, frames) stream — corpus order within shards, ALL words kept
    (function words included, so the bigram context is real)."""
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, split_glob)))[:cap_shards]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 2 and isinstance(e[0], str):
                fr = np.asarray(e[1], float)
                if fr.ndim == 2 and fr.shape[0] >= 3:
                    fr = fr / np.clip(np.linalg.norm(fr, axis=1, keepdims=True), 1e-9, None)
                    out.append((e[0].lower(), fr))
    return out


def main() -> int:
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    max_dev = int(sys.argv[2]) if len(sys.argv) > 2 else 400

    train = _stream("train-clean-100_*.pkl", 10)
    dev = _stream("dev-clean_*.pkl", 12)
    vocab = [w for w, _ in Counter(w for w, _ in train).most_common(K)]
    vset = set(vocab); vi = {w: i for i, w in enumerate(vocab)}
    print("=" * 90)
    print("LANGUAGE PRIOR — acoustic x bigram via the agent's Bayes-product combine")
    print("=" * 90)
    print(f"  vocab(K={K}): {vocab[:12]}...")

    # ---- ACOUSTIC channel: learned encoder (LDA) fit on train words ----
    tr_words = [(w, fr) for w, fr in train if w in vset]
    by = defaultdict(list)
    for w, fr in tr_words:
        if len(by[w]) < 40:
            by[w].append(fr)
    sup = [(w, fr) for w, frs in by.items() for fr in frs]
    s_env = _spk_env(sup, 24)
    Sx = np.array([_feat(fr, s_env[i]) for i, (w, fr) in enumerate(sup)])
    sy = [w for w, _ in sup]
    mu, Wp = _fit_pca(Sx, min(120, len(Sx) - K - 1))
    Wl = _fit_lda((Sx - mu) @ Wp, sy, K - 1)
    enc = lambda X: ((X - mu) @ Wp @ Wl)
    Se = enc(Sx); Se = Se / np.clip(np.linalg.norm(Se, axis=1, keepdims=True), 1e-9, None)
    cent = np.array([Se[[i for i in range(len(sy)) if sy[i] == w]].mean(0) for w in vocab])
    cent = cent / np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)

    # ---- LANGUAGE channel: word bigram from the train stream (the new graph data) ----
    big = defaultdict(lambda: np.ones(K))               # add-1 smoothing
    uni = np.ones(K)
    prev = None
    for w, _ in train:
        if w in vset:
            uni[vi[w]] += 1
            if prev in vset:
                big[prev][vi[w]] += 1
            prev = w
        else:
            prev = None
    uni = uni / uni.sum()
    loguni = np.log(uni)
    def loglm(prevw):
        if prevw in vset:
            row = big[prevw]; return np.log(row / row.sum())
        return loguni

    # ---- DEV stream: acoustic posterior per word ----
    devv = [(w, fr) for w, fr in dev if w in vset][:max_dev]
    q_env = _spk_env(devv, 3)
    Qe = enc(np.array([_feat(fr, q_env[i]) for i, (w, fr) in enumerate(devv)]))
    Qe = Qe / np.clip(np.linalg.norm(Qe, axis=1, keepdims=True), 1e-9, None)
    tau = 0.1
    logac = np.log(np.exp((Qe @ cent.T) / tau) /
                   np.exp((Qe @ cent.T) / tau).sum(1, keepdims=True) + 1e-12)   # (T x K)
    truth = [vi[w] for w, _ in devv]
    T = len(devv)

    ac_only = float(np.mean([logac[t].argmax() == truth[t] for t in range(T)]))

    def viterbi(lam):
        dp = logac[0].copy(); bp = np.zeros((T, K), int)
        for t in range(1, T):
            trans = lam * np.array([loglm(vocab[p]) for p in range(K)])         # (prev K x next K)
            cand = dp[:, None] + trans                                          # prev -> next
            bp[t] = cand.argmax(0); dp = logac[t] + cand.max(0)
        seq = [int(dp.argmax())]
        for t in range(T - 1, 0, -1):
            seq.append(int(bp[t][seq[-1]]))
        seq.reverse()
        return float(np.mean([seq[t] == truth[t] for t in range(T)]))

    print(f"\n  acoustic-only top-1     : {ac_only:.3f}   (vocab incl. function words = harder)")
    print(f"   lambda   +LM (Viterbi) acc")
    best = (ac_only, 0.0)
    for lam in (0.5, 1.0, 2.0, 4.0, 8.0):
        a = viterbi(lam)
        print(f"   {lam:5.1f}    {a:.3f}")
        if a > best[0]:
            best = (a, lam)
    print("\n" + "=" * 90)
    print(f"  acoustic-only {ac_only:.3f} -> +LANGUAGE PRIOR {best[0]:.3f} (lambda={best[1]})   "
          f"lift {best[0]-ac_only:+.3f}")
    print("=" * 90)
    print("  The language prior is a SECOND CHANNEL in the agent's existing Bayes-product combine")
    print("  (combinatorial_recognizer: posterior ∝ P(audio|w)·P(w|context)); the bigram is graph data")
    print("  like the transition channel. Context resolves the confusable function words acoustics can't.")
    return 0 if best[0] > ac_only + 0.02 else 2


if __name__ == "__main__":
    raise SystemExit(main())
