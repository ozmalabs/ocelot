"""How far can we push 'X as a shape'? Peel speech into a STACK of separable shapes,
each cheap to estimate-and-subtract (AntiUnify along its axis, Substitute inverse),
and watch the cost collapse — the creator's "extremely cheap normal case".

Components peeled, cheapest-first:
  RATE     a shape: resample each word to a FIXED length -> matching becomes one
           COSINE / matmul, no DTW. (DTW is expensive ONLY because of the rate axis.)
  SPEAKER  a shape: subtract the speaker band-envelope (discovered unsupervised).
  CONTEXT  a shape: subtract the local temporal moving-average per band
           (coarticulation removal -> the allophonic spread that needed many exemplars).
The RESIDUAL = the canonical word identity — small, irreducible ("not all the way").

Cross-speaker phonebank gate (dev vs train-clean-100). COST = scalar mul-adds/query
(DTW ~ N*Lbar^2 with Python overhead; cosine ~ N*D as one matmul; prototype ~ W*D).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_components_as_shapes.py [n_words] [max_query] [per_word]
"""
from __future__ import annotations
import glob, os, pickle, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_reads_oov_from_phones import dtw, STOP

BANK = "/home/matt/data/phonebank"
L = 20            # fixed length after rate-peel
NB = 32


def _l2rows(fr):
    fr = np.asarray(fr, dtype=np.float64)
    if fr.ndim == 1:
        fr = fr.reshape(1, -1)
    return fr / np.clip(np.linalg.norm(fr, axis=1, keepdims=True), 1e-9, None)


def _load(g, cap):
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, g)))[:cap]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 2 and isinstance(e[0], str):
                w = e[0].lower(); fr = _l2rows(e[1])
                if w not in STOP and len(w) >= 3 and fr.shape[0] >= 3:
                    out.append((w, fr))
    return out


def _kmeans(X, K, it=10):
    rng = np.random.default_rng(0)
    C = X[rng.choice(len(X), min(K, len(X)), replace=False)].copy()
    for _ in range(it):
        lab = (((X[:, None, :] - C[None, :, :]) ** 2).sum(2)).argmin(1)
        for k in range(len(C)):
            m = X[lab == k]
            if len(m):
                C[k] = m.mean(0)
    return lab


def _spk_env(words, K):
    feat = np.array([np.concatenate([fr.mean(0), fr.std(0)]) for _w, fr in words])
    feat = feat / np.clip(np.linalg.norm(feat, axis=1, keepdims=True), 1e-9, None)
    lab = _kmeans(feat, K)
    envs = {k: np.concatenate([words[i][1] for i in range(len(words)) if lab[i] == k], 0).mean(0)
            for k in set(lab)}
    return [envs[lab[i]] for i in range(len(words))]


def _context_norm(fr, win=2):
    """subtract local temporal moving-average per band (coarticulation shape)."""
    n = len(fr); out = np.empty_like(fr)
    for i in range(n):
        lo, hi = max(0, i - win), min(n, i + win + 1)
        out[i] = fr[i] - fr[lo:hi].mean(0)
    return out


def _resample(fr, length=L):
    """rate-peel: linear-interp the frame trajectory to a FIXED length."""
    n = len(fr)
    if n == length:
        r = fr
    else:
        idx = np.linspace(0, n - 1, length)
        lo = np.floor(idx).astype(int); hi = np.clip(lo + 1, 0, n - 1); t = (idx - lo)[:, None]
        r = fr[lo] * (1 - t) + fr[hi] * t
    return r


def _prep(fr, env, peel_speaker, peel_context):
    x = fr
    if peel_context:
        x = _context_norm(x)
    if peel_speaker:
        x = x - env[None, :]
    x = _resample(x)
    v = x.reshape(-1)
    return v / max(np.linalg.norm(v), 1e-9)


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    sup_all = _load("train-clean-100_*.pkl", 8)
    qry_all = _load("dev-clean_*.pkl", 8)
    sw = Counter(w for w, _ in sup_all); qw = Counter(w for w, _ in qry_all)
    vocab = [w for w, _ in sw.most_common() if qw[w] >= 2][:n_words]
    vset = set(vocab); chance = 1.0 / len(vocab); W = len(vocab)
    by = defaultdict(list)
    for w, fr in sup_all:
        if w in vset and len(by[w]) < per:
            by[w].append(fr)
    support = [(w, fr) for w, frs in by.items() for fr in frs]
    queries = [(w, fr) for w, fr in qry_all if w in vset]
    np.random.default_rng(1).shuffle(queries); queries = queries[:max_q]
    N = len(support); n = len(queries); D = L * NB
    print("=" * 96)
    print("COMPONENTS AS SHAPES — peel the stack, watch the cost collapse")
    print("=" * 96)
    print(f"  vocab={W} chance={chance:.3f}  support(N)={N}  queries={n}  fixed-len D={D}")

    q_env = _spk_env(queries, 3); s_env = _spk_env(support, 24)
    sy = [w for w, _ in support]
    qy = [w for w, _ in queries]
    Lbar = np.mean([len(fr) for _w, fr in support])

    def acc_dtw():
        t = time.time(); ok = 0
        for w, fr in queries:
            bd, bw = 1e18, None
            for sw_, sfr in support:
                d = dtw(fr, sfr)
                if d < bd:
                    bd, bw = d, sw_
            ok += (bw == w)
        return ok / n, N * Lbar * Lbar * NB, time.time() - t

    def matrices(peel_speaker, peel_context):
        S = np.array([_prep(fr, s_env[i], peel_speaker, peel_context) for i, (w, fr) in enumerate(support)])
        Q = np.array([_prep(fr, q_env[i], peel_speaker, peel_context) for i, (w, fr) in enumerate(queries)])
        return S, Q

    def acc_cos(S, Q, proto=False):
        t = time.time()
        if proto:
            # one prototype/word = mean of the word's (peeled, fixed-len) support vectors
            P = []; PW = []
            for w in vocab:
                idx = [i for i in range(N) if sy[i] == w]
                v = S[idx].mean(0); P.append(v / max(np.linalg.norm(v), 1e-9)); PW.append(w)
            P = np.array(P)
            sim = Q @ P.T
            pred = [PW[j] for j in sim.argmax(1)]
            cost = W * D
        else:
            sim = Q @ S.T
            pred = [sy[j] for j in sim.argmax(1)]
            cost = N * D
        ok = sum(pred[i] == qy[i] for i in range(n))
        return ok / n, cost, time.time() - t

    print("\n  peeling (accuracy / cost = mul-adds per query / wall):")
    a0, c0, w0 = acc_dtw()
    print(f"   0. DTW full exemplars (no peel)          acc={a0:.3f}  cost~{c0/1e6:.1f}M  [{w0:.1f}s]")
    S1, Q1 = matrices(False, False)
    a1, c1, w1 = acc_cos(S1, Q1)
    print(f"   1. +RATE (fixed-len cosine, full)        acc={a1:.3f}  cost~{c1/1e6:.2f}M  [{w1:.2f}s]  ({c0/c1:.0f}x cheaper)")
    S2, Q2 = matrices(True, False)
    a2, c2, w2 = acc_cos(S2, Q2)
    print(f"   2. +RATE+SPEAKER                         acc={a2:.3f}  cost~{c2/1e6:.2f}M")
    S3, Q3 = matrices(True, True)
    a3, c3, w3 = acc_cos(S3, Q3)
    print(f"   3. +RATE+SPEAKER+CONTEXT                 acc={a3:.3f}  cost~{c3/1e6:.2f}M")
    a4, c4, w4 = acc_cos(S3, Q3, proto=True)
    print(f"   4. +ALL peels, 1 PROTOTYPE/word          acc={a4:.3f}  cost~{c4/1e6:.3f}M  [{w4:.3f}s]  ({c0/c4:.0f}x cheaper than DTW)")

    print("\n" + "=" * 96)
    print(f"  DTW full        : acc {a0:.3f}  cost {c0/1e6:.1f}M mul-adds/query")
    print(f"  cheapest (peel+proto): acc {a4:.3f}  cost {c4/1e6:.3f}M  ->  {c0/c4:.0f}x cheaper, accuracy {a4/a0:.0%} of full")
    print("=" * 96)
    print("  Each component (rate, speaker, context) is a SHAPE: one cheap estimate, Substituted out.")
    print("  Peeling rate alone turns expensive DTW into a single matmul; speaker+context let one")
    print("  prototype/word stand in for many exemplars. The residual is the irreducible word identity")
    print("  ('not all the way'). Extremely cheap NORMAL case; escalate to full DTW only on the tail.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
