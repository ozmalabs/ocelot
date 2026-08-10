"""Per-chunk OPEN-VOCAB recognition accuracy — which lever lifts it (isolated from
segmentation: CLEAN forced-aligned phonebank words as the chunks).

The continuous pass recognises each chunk by raw peel+velocity cosine to labelled
train exemplars (top-1 ~0.305, 300-way). Substitution error is the residual WER>1x.
Candidate levers, measured cross-speaker (train support vs dev queries, disjoint spk):

  raw _feat, nearest exemplar      : the current recogniser (baseline)
  raw _feat, class centroid        : average a word's exemplars (denoise; C compares)
  LEARNED encoder (PCA->LDA), fit on BACKGROUND classes, applied to open vocab
                                     : the earned discriminative subspace that
                                       collapses speaker/rate/alignment, TRANSFERRED
  + class centroid in encoder space
  DTW ceiling (subset)             : the expensive alignment headroom

The encoder is fit on background train words DISJOINT from nothing special — it
learns directions that separate words generally; the test is whether that subspace
transfers to recognising the open-vocab set. Reports top-1 / top-5 for each.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_lifts_speech_phonebank import _load
from scripts.jabberwock_learned_encoder import _feat, _fit_pca, _fit_lda
from scripts.jabberwock_reads_oov_from_phones import dtw


def _env(fr):
    return np.asarray(fr, float).mean(0)


def topk_acc(Q, qy, S, sy, k=5):
    sims = Q @ S.T
    order = np.argsort(-sims, axis=1)[:, :k]
    t1 = t5 = 0
    preds = []
    for i in range(len(qy)):
        cand = [sy[j] for j in order[i]]
        # dedup preserving order for top-k membership
        t1 += (cand[0] == qy[i]); t5 += (qy[i] in cand); preds.append(cand[0])
    return t1 / len(qy), t5 / len(qy), len(set(preds))


def main():
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    n_bg = int(sys.argv[4]) if len(sys.argv) > 4 else 500

    train = _load("train-clean-100_*.pkl", 12)
    dev = _load("dev-clean_*.pkl", 12)
    sw = Counter(w for w, _ in train); qw = Counter(w for w, _ in dev)
    vocab = [w for w, _ in sw.most_common() if qw[w] >= 1 and len(w) >= 2][:K]
    vset = set(vocab); chance = 1.0 / len(vocab)
    print("=" * 90)
    print(f"OPEN-VOCAB per-chunk recognition levers (K={len(vocab)}, chance {chance:.4f})")
    print("=" * 90)

    by = defaultdict(list)
    for w, fr in train:
        if w in vset and len(by[w]) < per:
            by[w].append(fr)
    sup = [(w, fr) for w, frs in by.items() for fr in frs]
    qry = [(w, fr) for w, fr in dev if w in vset]
    np.random.default_rng(1).shuffle(qry); qry = qry[:max_q]
    sy = [w for w, _ in sup]; qy = [w for w, _ in qry]
    Sx = np.array([_feat(fr, _env(fr)) for w, fr in sup])
    Qx = np.array([_feat(fr, _env(fr)) for w, fr in qry])
    print(f"  support={len(sup)} queries={len(qry)} featdim={Sx.shape[1]}", flush=True)

    # 1) raw _feat nearest exemplar
    r1, r5, rd = topk_acc(Qx, qy, Sx, sy)
    print(f"  raw _feat, nearest exemplar : top1 {r1:.3f}  top5 {r5:.3f}  "
          f"({r1/chance:.0f}x)  distinct {rd}", flush=True)

    # 2) raw _feat class centroid
    cents = np.array([Sx[[i for i in range(len(sy)) if sy[i] == w]].mean(0) for w in vocab])
    cents /= np.clip(np.linalg.norm(cents, axis=1, keepdims=True), 1e-9, None)
    c1, c5, cd = topk_acc(Qx, qy, cents, vocab)
    print(f"  raw _feat, class centroid   : top1 {c1:.3f}  top5 {c5:.3f}", flush=True)

    # 3) LEARNED encoder fit on BACKGROUND classes (top n_bg train words), applied here
    bg_vocab = [w for w, _ in sw.most_common() if len(w) >= 2][:n_bg]
    bgset = set(bg_vocab)
    bgby = defaultdict(list)
    for w, fr in train:
        if w in bgset and len(bgby[w]) < per:
            bgby[w].append(fr)
    bg = [(w, fr) for w, frs in bgby.items() for fr in frs]
    Bx = np.array([_feat(fr, _env(fr)) for w, fr in bg]); bgy = [w for w, _ in bg]
    nC = len(set(bgy))
    P = min(200, Bx.shape[0] - nC - 1)
    mu, Wp = _fit_pca(Bx, P)
    Wl = _fit_lda((Bx - mu) @ Wp, bgy, k=min(P, nC - 1))
    def enc(X):
        Y = ((X - mu) @ Wp) @ Wl
        return Y / np.clip(np.linalg.norm(Y, axis=1, keepdims=True), 1e-9, None)
    print(f"  [encoder fit on {nC} bg classes -> {Wl.shape[1]}d subspace]", flush=True)
    Se, Qe = enc(Sx), enc(Qx)
    e1, e5, ed = topk_acc(Qe, qy, Se, sy)
    print(f"  LEARNED enc, nearest exemplar: top1 {e1:.3f}  top5 {e5:.3f}  "
          f"({e1/chance:.0f}x)  distinct {ed}", flush=True)
    ecent = np.array([Se[[i for i in range(len(sy)) if sy[i] == w]].mean(0) for w in vocab])
    ecent /= np.clip(np.linalg.norm(ecent, axis=1, keepdims=True), 1e-9, None)
    ec1, ec5, _ = topk_acc(Qe, qy, ecent, vocab)
    print(f"  LEARNED enc, class centroid  : top1 {ec1:.3f}  top5 {ec5:.3f}", flush=True)

    # 4) DTW ceiling on a small subset (expensive)
    sub = qry[:80]
    t = time.time(); ok = ok5 = 0
    for w, fr in sub:
        ds = sorted(((dtw(fr, sfr), sw_) for sw_, sfr in sup), key=lambda x: x[0])[:5]
        cand = [c for _d, c in ds]
        ok += (cand[0] == w); ok5 += (w in cand)
    print(f"  DTW ceiling (n=80 subset)    : top1 {ok/len(sub):.3f}  top5 {ok5/len(sub):.3f}  "
          f"[{time.time()-t:.0f}s]", flush=True)

    print("=" * 90)
    best = max(r1, c1, e1, ec1)
    print(f"  best top1 = {best:.3f} (raw {r1:.3f} / raw-cent {c1:.3f} / enc {e1:.3f} / enc-cent {ec1:.3f})")
    print(f"  lever verdict: {'LEARNED ENCODER LIFTS' if max(e1,ec1) > r1 + 0.02 else 'no clear encoder gain'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
