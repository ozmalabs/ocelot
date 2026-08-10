"""The ESCALATION gate: cheap peeled-matmul on the NORMAL case, escalate only the
low-margin TAIL to full DTW (order n-x). Does margin-gating recover full accuracy at
near-cheap average cost?

Tier 1 (cheap): peel rate+speaker+context -> fixed-length cosine matmul vs exemplars.
  Per query: predicted word + a CONFIDENCE MARGIN (best-class sim - 2nd-class sim).
Tier 2 (expensive): full DTW vs all exemplars — run ONLY when margin < theta.

Sweep theta. Report accuracy, escalated fraction, and AVERAGE cost (mul-adds/query)
vs the all-DTW and all-cheap endpoints. The premise works iff the cheap matcher's
ERRORS sit at LOW margin (escalate the tail -> recover them). ORACLE = escalate
exactly the cheap-wrong queries (upper bound).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_escalation_gate.py [n_words] [max_query] [per_word]
"""
from __future__ import annotations
import glob, os, pickle, sys, time
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
    # peel context (temporal moving-avg) + speaker (band-envelope) + rate (fixed length)
    x = _ctx(fr) - env[None, :]
    v = _resample(x).reshape(-1)
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
    N, n, D = len(support), len(queries), L * NB
    sy = [w for w, _ in support]; qy = [w for w, _ in queries]
    s_env = _spk_env(support, 24); q_env = _spk_env(queries, 3)
    Lbar = float(np.mean([len(fr) for _w, fr in support]))
    CHEAP, DTWC = N * D, N * Lbar * Lbar * NB
    print("=" * 96)
    print("ESCALATION GATE — cheap peeled-matmul normal case + escalate the low-margin tail to DTW")
    print("=" * 96)
    print(f"  vocab={len(vocab)} chance={chance:.3f}  N={N} queries={n}  cheap={CHEAP/1e6:.2f}M  dtw={DTWC/1e6:.1f}M /query")

    # tier 1: cheap cosine + class-margin
    S = np.array([_prep(fr, s_env[i]) for i, (w, fr) in enumerate(support)])
    Q = np.array([_prep(fr, q_env[i]) for i, (w, fr) in enumerate(queries)])
    sims = Q @ S.T
    words = sorted(vset)
    widx = {w: k for k, w in enumerate(words)}
    by_word_cols = {w: [j for j in range(N) if sy[j] == w] for w in words}
    cheap_pred, margin = [], []
    for i in range(n):
        per_word = np.array([sims[i, by_word_cols[w]].max() for w in words])
        order = np.argsort(-per_word)
        cheap_pred.append(words[order[0]])
        margin.append(float(per_word[order[0]] - per_word[order[1]]))
    cheap_pred = np.array(cheap_pred); margin = np.array(margin)
    cheap_ok = cheap_pred == np.array(qy)
    print(f"  tier-1 cheap acc = {cheap_ok.mean():.3f}")

    # tier 2: DTW answers (cache once)
    t = time.time(); dtw_pred = []
    for w, fr in queries:
        bd, bw = 1e18, None
        for sw_, sfr in support:
            d = dtw(fr, sfr)
            if d < bd:
                bd, bw = d, sw_
        dtw_pred.append(bw)
    dtw_pred = np.array(dtw_pred); dtw_ok = dtw_pred == np.array(qy)
    print(f"  tier-2 DTW acc   = {dtw_ok.mean():.3f}  [{time.time()-t:.1f}s for all]")

    # sweep escalation fraction by margin threshold
    print("\n  escalate lowest-margin fraction -> accuracy + avg cost:")
    print(f"   {'esc%':>5} {'acc':>6} {'avgcost(M)':>11} {'xCheaperThanDTW':>16}")
    order = np.argsort(margin)                      # lowest margin first
    for frac in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.0):
        k = int(round(frac * n))
        esc = set(order[:k].tolist())
        pred = np.array([dtw_pred[i] if i in esc else cheap_pred[i] for i in range(n)])
        acc = (pred == np.array(qy)).mean()
        avg = (CHEAP + (k / n) * DTWC)
        print(f"   {frac*100:4.0f}% {acc:6.3f} {avg/1e6:11.3f} {DTWC/avg:16.0f}")

    # oracle: escalate exactly the cheap-wrong ones
    k = int((~cheap_ok).sum())
    pred = np.array([dtw_pred[i] if not cheap_ok[i] else cheap_pred[i] for i in range(n)])
    print(f"\n  ORACLE (escalate the {k/n*100:.0f}% cheap-wrong): acc={ (pred==np.array(qy)).mean():.3f}  "
          f"avgcost={(CHEAP+(k/n)*DTWC)/1e6:.3f}M")
    # how concentrated are cheap errors at low margin?
    med_ok = float(np.median(margin[cheap_ok])); med_err = float(np.median(margin[~cheap_ok]))
    print(f"  margin median: correct={med_ok:.4f}  wrong={med_err:.4f}  "
          f"(errors at lower margin: {med_err < med_ok})")
    print("=" * 96)
    print("  Cheap matmul handles the confident normal case; escalate only the low-margin tail to DTW.")
    print("  If errors concentrate at low margin, a small escalation fraction recovers ~full accuracy at")
    print("  a fraction of the average cost — order n-x: cheap default, pay the expensive rung on the tail.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
