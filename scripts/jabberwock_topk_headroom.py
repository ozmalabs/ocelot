"""Diagnose the 0.75 -> human gap: where does the error live, and how much does each
lever buy? Measures top-k accuracy (the CONTEXT headroom: a language model picks among
the acoustic top-k) + the top confusions (are they confusable function words?).

If top-1=0.75 but top-3 is high, the acoustic features already CONTAIN the answer and
the missing piece is a sequence/language prior (context) — the biggest single lever,
exactly how humans recognise reduced function words.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_topk_headroom.py [n_words] [max_query] [per_word]
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_learned_encoder import _load, _spk_env, _feat, _fit_pca, _fit_lda


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    sup_all = _load("train-clean-100_*.pkl", 8)
    qry_all = _load("dev-clean_*.pkl", 10)
    sw = Counter(w for w, _ in sup_all); qw = Counter(w for w, _ in qry_all)
    vocab = [w for w, _ in sw.most_common() if qw[w] >= 2][:n_words]
    vset = set(vocab); C = len(vocab)
    by = defaultdict(list)
    for w, fr in sup_all:
        if w in vset and len(by[w]) < per:
            by[w].append(fr)
    support = [(w, fr) for w, frs in by.items() for fr in frs]
    queries = [(w, fr) for w, fr in qry_all if w in vset]
    np.random.default_rng(1).shuffle(queries); queries = queries[:max_q]
    s_env = _spk_env(support, 24); q_env = _spk_env(queries, 3)
    sy = [w for w, _ in support]; qy = [w for w, _ in queries]

    Sx = np.array([_feat(fr, s_env[i]) for i, (w, fr) in enumerate(support)])
    Qx = np.array([_feat(fr, q_env[i]) for i, (w, fr) in enumerate(queries)])
    mu, Wp = _fit_pca(Sx, min(120, len(Sx) - C - 1))
    Wl = _fit_lda((Sx - mu) @ Wp, sy, C - 1)
    enc = lambda X: ((X - mu) @ Wp @ Wl) / np.clip(np.linalg.norm((X - mu) @ Wp @ Wl, axis=1, keepdims=True), 1e-9, None)
    Se, Qe = enc(Sx), enc(Qx)
    cent = np.array([Se[[i for i in range(len(sy)) if sy[i] == w]].mean(0) for w in vocab])
    cent = cent / np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)

    sims = Qe @ cent.T                                   # (Nq x C)
    ranks = np.argsort(-sims, axis=1)
    print("=" * 88)
    print("0.75 -> HUMAN: where the error lives (top-k headroom = the context lever)")
    print("=" * 88)
    print(f"  vocab={C}  queries={len(queries)}  (function-word vocab: {vocab})")
    for k in (1, 2, 3, 5):
        acc = np.mean([qy[i] in [vocab[j] for j in ranks[i, :k]] for i in range(len(qy))])
        print(f"  top-{k} acc = {acc:.3f}")

    # top confusions (true -> predicted), top-1
    conf = Counter()
    for i in range(len(qy)):
        pred = vocab[ranks[i, 0]]
        if pred != qy[i]:
            conf[(qy[i], pred)] += 1
    print("\n  top confusions (true -> pred):")
    for (t, p), n in conf.most_common(8):
        print(f"     {t:>8} -> {p:<8}  x{n}")
    print("=" * 88)
    print("  Reading: if top-3 >> top-1, the acoustics already CONTAIN the answer; the missing")
    print("  piece is a CONTEXT / language prior choosing among candidates — humans' main tool for")
    print("  reduced function words. That is the biggest single lever to human level.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
