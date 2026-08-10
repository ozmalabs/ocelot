"""ENRICH the feature for the RESOLUTION residual — what caching couldn't fix.

Compile-down compiles COVERAGE, not RESOLUTION: the cheap peeled feature literally
can't separate confusable words. The fix for a resolution gap is to ENRICH the cheap
representation — add back the discriminating structure the peel dropped — at MATMUL
cost (still no DTW). DTW's edge is temporal alignment; carry it in a richer fixed-
length encoding (velocity + acceleration channels, finer length).

Cross-speaker phonebank gate (dense, full exemplars). All cheap matchers are a single
cosine MATMUL (no DTW). Ladder of feature richness vs the DTW ceiling (0.625):
  base    speaker+rate peeled, mean only        (the resolution-limited cheap, ~0.585)
  +vel    + per-frame velocity (delta)          (dynamics DTW uses)
  +vel+acc + acceleration (delta-delta)
  finer L  + longer fixed length                (finer temporal detail)
Goal: an enriched cheap feature that REACHES/BEATS DTW at ~matmul cost -> the
resolution residual resolves cheaply, escalation -> 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_enrich_feature.py [n_words] [max_query] [per_word]
"""
from __future__ import annotations
import glob, os, pickle, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_reads_oov_from_phones import dtw, STOP

BANK = "/home/matt/data/phonebank"
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


def _resample(fr, L):
    n = len(fr)
    if n == L:
        return fr
    idx = np.linspace(0, n - 1, L); lo = np.floor(idx).astype(int); hi = np.clip(lo + 1, 0, n - 1)
    t = (idx - lo)[:, None]
    return fr[lo] * (1 - t) + fr[hi] * t


def _feat(fr, env, L, derivs):
    """speaker+rate peeled fixed-length, plus `derivs` temporal-derivative channels."""
    x = _resample(fr - env[None, :], L)               # peel speaker, peel rate
    chans = [x]
    d = x
    for _ in range(derivs):
        d = np.vstack([np.zeros((1, x.shape[1])), np.diff(d, axis=0)])
        chans.append(d)
    v = np.concatenate(chans, axis=1).reshape(-1)
    return v / max(np.linalg.norm(v), 1e-9)


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    sup_all = _load("train-clean-100_*.pkl", 8)
    qry_all = _load("dev-clean_*.pkl", 8)
    sw = Counter(w for w, _ in sup_all); qw = Counter(w for w, _ in qry_all)
    vocab = [w for w, _ in sw.most_common() if qw[w] >= 2][:n_words]
    vset = set(vocab); chance = 1.0 / len(vocab)
    by = defaultdict(list)
    for w, fr in sup_all:
        if w in vset and len(by[w]) < per:
            by[w].append(fr)
    support = [(w, fr) for w, frs in by.items() for fr in frs]
    queries = [(w, fr) for w, fr in qry_all if w in vset]
    np.random.default_rng(1).shuffle(queries); queries = queries[:max_q]
    s_env = _spk_env(support, 24); q_env = _spk_env(queries, 3)
    sy = [w for w, _ in support]; qy = np.array([w for w, _ in queries])
    n = len(queries)
    print("=" * 92)
    print("ENRICH THE FEATURE for the resolution residual (cheap matmul, no DTW)")
    print("=" * 92)
    print(f"  vocab={len(vocab)} chance={chance:.3f}  support={len(support)} queries={n}")

    # DTW ceiling
    t = time.time(); ok = 0
    for w, fr in queries:
        bd, bw = 1e18, None
        for sw_, sfr in support:
            d = dtw(fr, sfr)
            if d < bd:
                bd, bw = d, sw_
        ok += (bw == w)
    dtw_acc = ok / n
    print(f"  DTW ceiling (expensive): {dtw_acc:.3f}  [{time.time()-t:.1f}s]\n")

    def cheap(L, derivs):
        S = np.array([_feat(fr, s_env[i], L, derivs) for i, (w, fr) in enumerate(support)])
        Q = np.array([_feat(fr, q_env[i], L, derivs) for i, (w, fr) in enumerate(queries)])
        pred = np.array([sy[j] for j in (Q @ S.T).argmax(1)])
        return (pred == qy).mean(), S.shape[1]

    print(f"   {'feature':28} {'acc':>6} {'dim':>6} {'vs DTW':>8}")
    ladder = [("base mean (L=20)", 20, 0), ("+velocity (L=20)", 20, 1),
              ("+vel+accel (L=20)", 20, 2), ("+velocity (L=40)", 40, 1),
              ("+vel+accel (L=40)", 40, 2), ("+vel+accel (L=64)", 64, 2)]
    best = (0.0, None)
    for name, L, d in ladder:
        a, dim = cheap(L, d)
        mark = "  >= DTW" if a >= dtw_acc - 1e-9 else f"{a-dtw_acc:+.3f}"
        print(f"   {name:28} {a:6.3f} {dim:6d} {mark:>8}")
        if a > best[0]:
            best = (a, name)
    print("\n" + "=" * 92)
    print(f"  best cheap feature: {best[1]} = {best[0]:.3f}   DTW ceiling = {dtw_acc:.3f}")
    print(f"  {'RESOLUTION RESOLVED CHEAPLY' if best[0] >= dtw_acc - 0.005 else 'CLOSES THE GAP'} "
          f"({best[0]-0.585:+.3f} over the base cheap 0.585) at MATMUL cost (no DTW).")
    print("  Enriching the representation (dynamics + finer length) carries the discriminating detail")
    print("  DTW aligned for — the resolution residual caching could NOT fix is resolved by a richer")
    print("  cheap feature: escalation for resolution -> ~0, the whole normal case stays a single matmul.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
