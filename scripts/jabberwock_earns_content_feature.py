"""The jabberwock EARNS an acoustic feature for CONTENT words — the real floor.

Signal transmission is carried by CONTENT words (high-information, high-effort/clear);
function words are reduced and reconstructed from the prior (commit 4caa583d). But the
encoder is fit on ALL words, and function words DOMINATE by frequency, so the earned
LDA subspace is spent separating them — diluting content-word discrimination (shape_std
0.075, content recall ~0.05).

The agent EARNS (not borrows) a CONTENT-discriminative encoder: PCA -> LDA (its
WithinScatter/BetweenScatter primitive, closed-form, no gradient/torch) fit on CONTENT
CLASSES ONLY, so the subspace captures content distinctions. Cross-speaker (train fit,
dev test, disjoint speakers). Measures content-word top-1/5 + the content shape spread.

Levers:
  baseline encoder  : fit on a broad class set (incl. the dominant function words)
  content encoder   : fit on CONTENT classes only (the earned content subspace)
  + capacity        : content encoder, more LDA dims + longer temporal feature (content
                      words are ~50% longer -> more temporal structure to earn from)

NOTE: the thermodynamic ENERGY/effort channel (content = high effort = energy carries
info) is NOT available — the phonebank L2-normalised it away at banking and the aligner
(torchaudio) is gone; re-banking with energy is the named extension. This earns from the
spectral SHAPE only.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_earns_content_feature.py [K] [maxq] [per] [nbg]
"""
import glob, os, pickle, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda

BANK = "/home/matt/data/phonebank"


def _load(g, cap):
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, g)))[:cap]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 2 and isinstance(e[0], str):
                w = e[0].lower(); fr = np.asarray(e[1], float)
                if w.isalpha() and fr.shape[0] >= 3:
                    out.append((w, fr))
    return out


def _feat(fr, env, Ln):
    n = len(fr)
    idx = np.linspace(0, n - 1, Ln); lo = np.floor(idx).astype(int)
    hi = np.clip(lo + 1, 0, n - 1); t = (idx - lo)[:, None]
    x = (fr - env[None, :]); x = x[lo] * (1 - t) + x[hi] * t
    d = np.vstack([np.zeros((1, x.shape[1])), np.diff(x, axis=0)])
    v = np.concatenate([x, d], axis=1).reshape(-1)
    return v / max(np.linalg.norm(v), 1e-9)


def _env(fr):
    return np.asarray(fr, float).mean(0)


def main():
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    maxq = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    nbg = int(sys.argv[4]) if len(sys.argv) > 4 else 1200

    train = _load("train-clean-100_*.pkl", 12)
    dev = _load("dev-clean_*.pkl", 12)
    sw = Counter(w for w, _ in train); qw = Counter(w for w, _ in dev)
    func = set(w for w, _ in sw.most_common(50))
    def content(w): return w not in func and len(w) >= 4

    # content eval vocab: top-K content words present in both splits
    cvocab = [w for w, _ in sw.most_common() if content(w) and qw[w] >= 1][:K]
    cset = set(cvocab); chance = 1.0 / len(cvocab)
    print("=" * 86)
    print(f"EARN A CONTENT-WORD FEATURE — content vocab K={len(cvocab)}, chance {chance:.4f}")
    print("=" * 86)

    def gather(vocab_set, cap):
        by = defaultdict(list)
        for w, fr in train:
            if w in vocab_set and len(by[w]) < cap:
                by[w].append(fr)
        return by

    cby = gather(cset, per)
    cqry = [(w, fr) for w, fr in dev if w in cset]
    np.random.default_rng(1).shuffle(cqry); cqry = cqry[:maxq]
    qy = [w for w, _ in cqry]
    print(f"  content support words={len(cby)}  queries={len(cqry)}", flush=True)

    def evaluate(fit_classes, Ln, pca_dim, lda_dim, tag):
        # FIT the encoder on `fit_classes` (the earned subspace)
        fby = gather(set(fit_classes), per)
        Fx, fy = [], []
        for w, frs in fby.items():
            for fr in frs:
                Fx.append(_feat(fr, _env(fr), Ln)); fy.append(w)
        Fx = np.array(Fx); nC = len(set(fy))
        P = min(pca_dim, Fx.shape[0] - nC - 1)
        mu, Wp = _fit_pca(Fx, P)
        Wl = _fit_lda((Fx - mu) @ Wp, fy, k=min(P, lda_dim, nC - 1))
        def enc(X):
            Y = ((X - mu) @ Wp) @ Wl
            return Y / np.clip(np.linalg.norm(Y, axis=1, keepdims=True), 1e-9, None)
        # content centroids (train) + query encode (dev)
        cent, words = [], []
        for w in cvocab:
            if not cby[w]:
                continue
            E = enc(np.array([_feat(fr, _env(fr), Ln) for fr in cby[w]]))
            c = E.mean(0); cent.append(c / max(np.linalg.norm(c), 1e-9)); words.append(w)
        cent = np.array(cent)
        Qe = enc(np.array([_feat(fr, _env(fr), Ln) for w, fr in cqry]))
        sims = Qe @ cent.T
        order = np.argsort(-sims, axis=1)[:, :5]
        t1 = np.mean([words[order[i, 0]] == qy[i] for i in range(len(qy))])
        t5 = np.mean([qy[i] in [words[j] for j in order[i]] for i in range(len(qy))])
        sstd = float(np.std(sims))
        print(f"  {tag:42} top1 {t1:.3f}  top5 {t5:.3f}  ({t1/chance:.0f}x)  sim-std {sstd:.3f}",
              flush=True)
        return t1

    broad = [w for w, _ in sw.most_common() if len(w) >= 2][:nbg]
    content_bg = [w for w, _ in sw.most_common() if content(w)][:nbg]

    b = evaluate(broad, 20, 200, 200, "BASELINE (broad fit incl function, L20)")
    c = evaluate(content_bg, 20, 200, 300, "EARNED content fit (L20)")
    c2 = evaluate(content_bg, 32, 300, 400, "EARNED content fit + capacity (L32, more dims)")

    print("=" * 86)
    best = max(b, c, c2)
    print(f"  content top1: broad {b:.3f} -> content-earned {c:.3f} -> +capacity {c2:.3f}")
    print(f"  {'EARNED CONTENT FEATURE LIFTS content discrimination' if best > b + 0.02 else 'no clear lift'} "
          f"(the words that carry the signal).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
