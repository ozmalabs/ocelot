"""Test the COVERAGE prediction: compile-down SHRINKS a coverage-gap tail (even though
it could not shrink the resolution-gap tail).

Diagnosis from the null: compile-down works for COVERAGE gaps (rare-but-representable
items the cheap rung hasn't SEEN) but not RESOLUTION gaps (distinctions the cheap
representation can't make). Test it by controlling the gap KIND via the cheap bank's
SEED DENSITY:

  DENSE seed (full support, ~30/word): coverage is already there -> the tail is
        RESOLUTION-limited -> compile-down should NOT drop escalation (the prior null).
  SPARSE seed (1/word): the tail is COVERAGE-limited (queries far from any cheap
        exemplar) -> caching the DTW-resolved exemplars FILLS coverage -> escalation
        should DROP over the stream while accuracy RISES (child -> expert).

Expensive rung (DTW) always uses FULL support. Streamed cross-speaker dev queries;
compile vs control (cache vs don't), per quartile.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_compile_coverage.py [n_words] [max_query] [theta]
"""
from __future__ import annotations
import glob, os, pickle, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_reads_oov_from_phones import dtw, STOP

BANK = "/home/matt/data/phonebank"
L, NB = 20, 32


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


def _ctx(fr, win=2):
    n = len(fr); out = np.empty_like(fr)
    for i in range(n):
        lo, hi = max(0, i - win), min(n, i + win + 1)
        out[i] = fr[i] - fr[lo:hi].mean(0)
    return out


def _resample(fr):
    n = len(fr)
    if n == L:
        return fr
    idx = np.linspace(0, n - 1, L); lo = np.floor(idx).astype(int); hi = np.clip(lo + 1, 0, n - 1)
    t = (idx - lo)[:, None]
    return fr[lo] * (1 - t) + fr[hi] * t


def _prep(fr, env):
    v = _resample(_ctx(fr) - env[None, :]).reshape(-1)
    return v / max(np.linalg.norm(v), 1e-9)


def _cm(simrow, bank_words, words):
    per = {w: -9.0 for w in words}
    for j, s in enumerate(simrow):
        if s > per[bank_words[j]]:
            per[bank_words[j]] = s
    vals = sorted(per.values(), reverse=True)
    return max(per, key=per.get), (vals[0] - vals[1] if len(vals) > 1 else vals[0])


def run(compile_down, seed_k, queries, q_env, support, s_env, sup_pre, words, theta, rng):
    """COVERAGE trigger: escalate when the query is FAR from the cheap bank (top
    similarity < theta) — a novelty/coverage signal, not the margin (which detects
    resolution). Caching fills coverage -> future top-sim rises -> fewer escalate."""
    by = defaultdict(list)
    for i, (w, _fr) in enumerate(support):
        by[w].append(i)
    seed_idx = []
    for w in words:
        idx = by[w][:]; rng.shuffle(idx)
        seed_idx += idx[:seed_k]
    bank = [sup_pre[i] for i in seed_idx]
    bank_words = [support[i][0] for i in seed_idx]
    B = np.array(bank)
    rec = []
    for qi, (w, fr) in enumerate(queries):
        v = _prep(fr, q_env[qi])
        sim = B @ v
        top_sim = float(sim.max())
        pred = bank_words[int(sim.argmax())]
        if top_sim < theta:                          # COVERAGE gap: far from the bank
            bd, bw = 1e18, None
            for sw_, sfr in support:                 # expensive rung: FULL support
                d = dtw(fr, sfr)
                if d < bd:
                    bd, bw = d, sw_
            rec.append((1, int(bw == w)))
            if compile_down:
                bank_words.append(bw); B = np.vstack([B, v[None, :]])
        else:
            rec.append((0, int(pred == w)))
    return np.array(rec)


def _q(rec):
    n = len(rec); k = n // 4
    return [(rec[i*k:(i+1)*k, 0].mean(), rec[i*k:(i+1)*k, 1].mean()) for i in range(4)]


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 320
    theta = float(sys.argv[3]) if len(sys.argv) > 3 else 0.04
    per = 30

    sup_all = _load("train-clean-100_*.pkl", 8)
    qry_all = _load("dev-clean_*.pkl", 12)
    sw = Counter(w for w, _ in sup_all); qw = Counter(w for w, _ in qry_all)
    vocab = [w for w, _ in sw.most_common() if qw[w] >= 2][:n_words]
    vset = set(vocab); words = sorted(vset)
    by = defaultdict(list)
    for w, fr in sup_all:
        if w in vset and len(by[w]) < per:
            by[w].append(fr)
    support = [(w, fr) for w, frs in by.items() for fr in frs]
    queries = [(w, fr) for w, fr in qry_all if w in vset]
    np.random.default_rng(7).shuffle(queries)
    nq = (min(max_q, len(queries)) // 4) * 4
    queries = queries[:nq]
    s_env = _spk_env(support, 24); q_env = _spk_env(queries, 3)[:nq]
    sup_pre = [_prep(fr, s_env[i]) for i, (w, fr) in enumerate(support)]
    # calibrate the COVERAGE threshold: median top-sim of queries vs the DENSE bank
    Bd = np.array(sup_pre)
    qvecs = np.array([_prep(fr, q_env[i]) for i, (w, fr) in enumerate(queries)])
    theta = float(np.median((qvecs @ Bd.T).max(1)))
    print("=" * 94)
    print("COVERAGE TEST — compile-down shrinks a COVERAGE gap (top-sim trigger, not margin)")
    print("=" * 94)
    print(f"  vocab={len(vocab)}  support={len(support)}  stream={nq}  theta(top-sim)={theta:.3f}")

    for seed_k, name in [(per, "DENSE seed (full coverage -> RESOLUTION-limited)"),
                         (1, "SPARSE seed 1/word (COVERAGE-limited)")]:
        ctrl = run(False, seed_k, queries, q_env, support, s_env, sup_pre, words, theta,
                   np.random.default_rng(1))
        comp = run(True, seed_k, queries, q_env, support, s_env, sup_pre, words, theta,
                   np.random.default_rng(1))
        cq, pq = _q(ctrl), _q(comp)
        print(f"\n  {name}:")
        print(f"    {'':10}{'Q1':>12}{'Q2':>12}{'Q3':>12}{'Q4':>12}   overall")
        print(f"    control esc " + "".join(f"{cq[i][0]*100:11.0f}%" for i in range(4)) +
              f"   {ctrl[:,0].mean()*100:.0f}%")
        print(f"    compile esc " + "".join(f"{pq[i][0]*100:11.0f}%" for i in range(4)) +
              f"   {comp[:,0].mean()*100:.0f}%")
        print(f"    compile acc " + "".join(f"{pq[i][1]:12.3f}" for i in range(4)) +
              f"   {comp[:,1].mean():.3f}")
        drop = pq[0][0] - pq[3][0]
        print(f"    -> compile escalation Q1 {pq[0][0]*100:.0f}% -> Q4 {pq[3][0]*100:.0f}%  "
              f"(drop {drop*100:+.0f} pts; control Q1->Q4 {(cq[0][0]-cq[3][0])*100:+.0f})")

    print("\n" + "=" * 94)
    print("  PREDICTION: DENSE -> little/no drop (resolution floor, the prior null); SPARSE -> clear")
    print("  drop as caching FILLS coverage (child -> expert). Compile-down compiles COVERAGE, not resolution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
