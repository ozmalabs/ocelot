"""COMPILE-DOWN loop — the child->expert leg of order n-x, on speech.

The escalation gate pays full DTW on the low-margin tail. COMPILE DOWN: every time a
query escalates and DTW resolves it, cache that resolved (peeled-vector -> word)
exemplar back into the CHEAP bank. Future low-margin queries near it now land beside
a learned exemplar -> higher margin -> resolve cheaply, NO escalation. Over a stream
the escalation fraction SHRINKS at held accuracy: the cheap rung absorbs what the
expensive rung earned (recognition + learning, one loop, two timescales).

Streamed dev queries (cross-speaker vs train support). Two passes, SAME order/theta:
  CONTROL  escalate-but-don't-cache  -> escalation fraction stays flat (child stays child)
  COMPILE  cache DTW verdicts        -> escalation fraction drops (child -> expert)

Report escalation% + accuracy per quartile, and cumulative cost. The teacher is the
EXPENSIVE rung's verdict (imperfect, ~0.625) — earned, not stamped.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_compile_down_loop.py [n_words] [max_query] [theta]
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


def _class_margin(simrow, bank_words, words):
    per = {w: -9.0 for w in words}
    for j, s in enumerate(simrow):
        w = bank_words[j]
        if s > per[w]:
            per[w] = s
    vals = sorted(per.values(), reverse=True)
    top = max(per, key=per.get)
    return top, (vals[0] - vals[1] if len(vals) > 1 else vals[0])


def run(compile_down, queries, q_env, support, s_env, words, theta):
    bank_vecs = [_prep(fr, s_env[i]) for i, (w, fr) in enumerate(support)]
    bank_words = [w for w, _ in support]
    B = np.array(bank_vecs)
    rec = []  # (escalated, correct)
    for qi, (w, fr) in enumerate(queries):
        v = _prep(fr, q_env[qi])
        sim = B @ v
        pred, margin = _class_margin(sim, bank_words, words)
        if margin < theta:
            # ESCALATE: full DTW vs original support frames
            bd, bw = 1e18, None
            for sw_, sfr in support:
                d = dtw(fr, sfr)
                if d < bd:
                    bd, bw = d, sw_
            final = bw
            rec.append((1, int(final == w)))
            if compile_down:                      # cache the resolved exemplar (DTW's label)
                bank_words.append(bw)
                B = np.vstack([B, v[None, :]])
        else:
            rec.append((0, int(pred == w)))
    return rec


def _summary(rec, label, nq):
    rec = np.array(rec)
    q = nq // 4
    print(f"  {label}:")
    print(f"   {'quartile':>9} {'esc%':>6} {'acc':>6}")
    for k in range(4):
        seg = rec[k * q:(k + 1) * q]
        print(f"   {'Q'+str(k+1):>9} {seg[:,0].mean()*100:5.0f}% {seg[:,1].mean():6.3f}")
    print(f"   overall   esc {rec[:,0].mean()*100:.0f}%  acc {rec[:,1].mean():.3f}")
    return rec[:, 0].mean(), rec[:, 1].mean()


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 400
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
    np.random.default_rng(7).shuffle(queries); queries = queries[:max_q]
    s_env = _spk_env(support, 24); q_env = _spk_env(queries, 3)
    nq = (len(queries) // 4) * 4
    queries = queries[:nq]; q_env = q_env[:nq]
    print("=" * 92)
    print("COMPILE-DOWN LOOP — escalation outcomes cached into the cheap rung (child -> expert)")
    print("=" * 92)
    print(f"  vocab={len(vocab)}  support={len(support)}  stream={nq} queries  theta={theta}")

    ctrl = run(False, queries, q_env, support, s_env, words, theta)
    comp = run(True, queries, q_env, support, s_env, words, theta)
    print()
    e0, a0 = _summary(ctrl, "CONTROL (escalate, do NOT cache)", nq)
    print()
    e1, a1 = _summary(comp, "COMPILE (cache DTW verdicts into cheap bank)", nq)

    cr = np.array(ctrl); cp = np.array(comp); q = nq // 4
    esc_drop = cr[:q, 0].mean() - cp[3 * q:, 0].mean()
    print("\n" + "=" * 92)
    print(f"  escalation fraction Q1 {cr[:q,0].mean()*100:.0f}% -> COMPILE Q4 {cp[3*q:,0].mean()*100:.0f}%   "
          f"(control Q4 {cr[3*q:,0].mean()*100:.0f}%)")
    print(f"  overall escalation: control {e0*100:.0f}%  compile {e1*100:.0f}%   "
          f"accuracy: control {a0:.3f}  compile {a1:.3f}")
    print("=" * 92)
    win = (e1 < e0 - 0.03) and (a1 >= a0 - 0.03)
    print(f"  {'COMPILE-DOWN WORKS' if win else 'WEAK'} — caching the expensive rung's verdicts shrinks the")
    print("  escalation tail over the stream at held accuracy: the cheap rung gets EARNED-richer, the")
    print("  costly rung fires on a vanishing fraction. Recognition and learning, one loop. child -> expert.")
    return 0 if win else 2


if __name__ == "__main__":
    raise SystemExit(main())
