"""DECOMPOSE the per-frame phone gap (~0.13 -> real 0.5-0.7) into DATA-SCALE vs MODEL-DEPTH.

The shallow energy/PCA->LDA+GMM phone model caps ~0.13/frame; real phone models hit 0.5-0.7.
The arc's discipline (ozma_earn_not_borrow_is_data): when earned < target, RUN THE DATA-SCALING
CURVE FIRST. If the earned curve still climbs with more held data the gap is DATA, not method;
if it plateaus it is a DEPTH/method gap. So this script does BOTH, honestly, at matched data:

  LABELS   : Viterbi forced-alignment (the EM E-step) under a small bootstrap shallow model mints
             CLEAN (frame-context, phone) labels from the KNOWN per-word phone sequence. The SAME
             aligned labels feed shallow AND deep, so the only variable is the model class.
  SHALLOW  : the current default emission — PCA->LDA encoder (the agent's WithinScatter) + GMM
             phone centroids, per-frame nearest-centroid argmax (graph-native Dot/topk decision).
  DEEP     : a from-scratch RANDOM-INIT MLP trained by the agent's own SGD (numpy, no torch, no
             pretrained weights — earned, not borrowed; the weights are graph data like LDA is) on
             the SAME (frame-context, phone) pairs, with the SAME +-W temporal context.

  CURVES   : per-frame phone acc + boundary-free content recall vs held-data size, for BOTH models.
             climbing-or-plateaued verdict + slope. PER-FRAME COST (us/frame) for the cheap-method-
             leverage call: does depth belong on the cheap base layer or as an ESCALATION tier?

  CONTROLS : real-trained vs scrambled-label (training does the work); chance baseline; grep-clean
             (no from_pretrained/download/torch.hub/borrowed weights). donkey=0.

OOM-HARDENING (the prior run died here): the killer was fit_model's PCA via
``np.linalg.svd(X-mu, full_matrices=False)`` which materialises a full (n_frames x D)
float64 U matrix (multiple GB) plus duplicated float64 feats / double concatenations.
This script (a) computes PCA from the bounded D x D covariance (eigh) — mathematically the
same top-P directions, no giant U; (b) keeps every design matrix float32; (c) builds X ONCE
per scale (no feats-list + concatenate duplication); (d) normalises the MLP per mini-batch
(no full normalised copy); (e) wraps each scale in try/except MemoryError to DEGRADE and
report the bound rather than die. Set ``ulimit -v`` before running for fail-fast.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_decompose_phone_gap.py [max_words] [n_test]
"""
import os, sys, time, gc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_subword_recognizer import _load_ph, best_window_match
from scripts.jabberwock_earns_phone_model import (
    ctxd, phone_emission, viterbi_align,
)

W = 4  # context half-window (matches ctxd default)


# ----------------------------------------------------- memory-bounded fit ----
def _fit_pca_cov(X, P):
    """PCA top-P directions from the bounded D x D covariance (float32 eigh).

    Mathematically identical to ``Vt[:P].T`` from ``svd(X-mu)`` (the top-P right singular
    vectors == top-P eigenvectors of (X-mu)^T(X-mu)) but NEVER forms the (n_frames x D) U
    matrix that OOM'd the prior run. Sign of an eigenvector is arbitrary and irrelevant to
    the downstream LDA projection / cosine emission."""
    mu = X.mean(0).astype(np.float32)
    Xc = X - mu                                  # one float32 copy (bounded ~1.5GB @ 32k)
    C = (Xc.T @ Xc).astype(np.float64)           # D x D (D ~ 576) — trivial
    del Xc
    evals, evecs = np.linalg.eigh(C)             # ascending
    Wp = evecs[:, -P:][:, ::-1].astype(np.float32)   # top-P descending (D x P)
    return mu, Wp


def _fit_lda_fast(Z, y, k, eps=1e-2):
    """Fisher LDA, vectorised grouping (boolean masks, not per-class Python list comps).
    Same Sw/Sb construction as the shared _fit_lda, just memory/speed-bounded."""
    y = np.asarray(y)
    classes = np.unique(y)
    d = Z.shape[1]; mu = Z.mean(0)
    Sw = np.zeros((d, d), np.float64); Sb = np.zeros((d, d), np.float64)
    for c in classes:
        Zc = Z[y == c]
        if len(Zc) == 0:
            continue
        mc = Zc.mean(0); D = (Zc - mc).astype(np.float64)
        Sw += D.T @ D
        diff = (mc - mu).astype(np.float64)[:, None]
        Sb += len(Zc) * (diff @ diff.T)
    Sw += eps * np.trace(Sw) / d * np.eye(d)
    evals, evecs = np.linalg.eig(np.linalg.solve(Sw, Sb))
    order = np.argsort(-evals.real)
    return evecs[:, order[:k]].real.astype(np.float32)


def fit_model_mem(X, Yidx, phones_set, pi, K=4):
    """Memory-bounded mirror of jabberwock_earns_phone_model.fit_model: PCA(cov)->LDA encoder
    + per-phone GMM(k-means) centroids. Same math, float32, no giant SVD-U. Yidx = phone-index
    per frame (int)."""
    y = np.asarray(Yidx)
    nP = len(phones_set)
    P = min(120, X.shape[0] - nP - 1)
    mu, Wp = _fit_pca_cov(X, P)
    Z = (X - mu) @ Wp                            # (n x P) float32, bounded
    Wl = _fit_lda_fast(Z, y, k=min(P, nP - 1))

    def enc(A):
        R = ((np.asarray(A, np.float32) - mu) @ Wp) @ Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)

    E = enc(X)
    cent, cphone = [], []
    rng = np.random.default_rng(0)
    for p in phones_set:
        Zp = E[y == pi[p]]
        if len(Zp) == 0:
            continue
        Cc = Zp[rng.choice(len(Zp), min(K, len(Zp)), replace=False)].copy()
        for _ in range(6):
            lab = (((Zp[:, None, :] - Cc[None]) ** 2).sum(2)).argmin(1)
            for kk in range(len(Cc)):
                m = Zp[lab == kk]
                if len(m):
                    Cc[kk] = m.mean(0)
        for c in Cc:
            cent.append(c); cphone.append(pi[p])
    cent = np.asarray(cent, np.float32)
    cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
    return enc, cent, np.asarray(cphone)


# ------------------------------------------------------------------ data ----
def load_words(cap_pkls):
    """load banked (word, frames, phones[, energy]) tuples up to cap_pkls shards."""
    return _load_ph("train-clean-100_*.pkl", cap_pkls, with_energy=True)


def _feat(fr, en, has_energy):
    """float32 per-word context feature (the OOM fix is keeping everything float32)."""
    return ctxd(fr, e=en if has_energy else None).astype(np.float32)


def bootstrap_align(words, phones_set, pi, has_energy):
    """mint CLEAN per-frame phone labels by Viterbi forced-alignment under a quick
    bootstrap shallow model (flat-start -> fit -> 1 EM realign).

    OOM-hardened: returns the CONCATENATED design matrix X (float32) and the flat per-frame
    label list directly, so main never re-concatenates a second full copy. The per-word feats
    list is built once, used for the bootstrap fit + the Viterbi realign, then freed."""
    nP = len(phones_set)
    feats = [_feat(fr, en, has_energy) for _w, fr, _ph, en in words]
    pjs = [[pi[p] for p in ph] for _w, _f, ph, _e in words]
    # flat-start proportional labels (per-word phone-index lists)
    labels = []
    for cx, (_w, _f, ph, _e) in zip(feats, words):
        n = len(cx); Pn = len(ph)
        labels.append([pi[ph[int(i * Pn / n)]] for i in range(n)])

    # bootstrap fit on flat-start labels (one concatenation; freed after)
    Xb = np.concatenate(feats)
    Yb = [i for s in labels for i in s]
    enc, cent, cph = fit_model_mem(Xb, Yb, phones_set, pi)
    del Xb, Yb; gc.collect()

    # one EM realign -> clean labels (uses per-word feats)
    new = []
    for cx, pj in zip(feats, pjs):
        emis = phone_emission(cx, enc, cent, cph, nP)
        new.append(viterbi_align(emis, pj))

    # final design matrix + flat labels (single concatenation, then free feats)
    X = np.concatenate(feats)
    Yidx = [i for s in new for i in s]
    del feats, new, labels; gc.collect()
    return X, Yidx


# --------------------------------------------------------------- shallow ----
def shallow_acc(enc, cent, cph, Xde, Yde_idx):
    pred = cph[(enc(Xde) @ cent.T).argmax(1)]
    return float(np.mean(pred == np.asarray(Yde_idx)))


# ----------------------------------------------------------------- deep ----
def train_mlp(X, Yidx, nP, Xde, Yde_idx, hidden=(512, 256), epochs=25, bs=256, lr=0.2, seed=0):
    """from-scratch random-init MLP, the agent's own SGD (numpy). EARNED not borrowed.

    OOM-hardened: standardisation is applied PER MINI-BATCH (and once for the dev block) so
    no full normalised copy of the design matrix is ever held — only X (float32) + a 256-row
    batch live at once."""
    y = np.asarray(Yidx)
    mu = X.mean(0); sd = X.std(0) + 1e-6
    rng = np.random.default_rng(seed)
    dims = [X.shape[1]] + list(hidden) + [nP]
    Ws = [rng.standard_normal((dims[i], dims[i + 1])).astype(np.float32) * np.float32(np.sqrt(2.0 / dims[i]))
          for i in range(len(dims) - 1)]
    Bs = [np.zeros(dims[i + 1], np.float32) for i in range(len(dims) - 1)]
    vW = [np.zeros_like(w) for w in Ws]; vB = [np.zeros_like(b) for b in Bs]
    n = len(X)

    def fwd(A):
        acts = [A]
        for li in range(len(Ws)):
            Z = acts[-1] @ Ws[li] + Bs[li]
            acts.append(np.maximum(Z, 0) if li < len(Ws) - 1 else Z)
        return acts

    for ep in range(epochs):
        idx = rng.permutation(n)
        for s in range(0, n, bs):
            b = idx[s:s + bs]
            Ab = ((X[b] - mu) / sd).astype(np.float32)   # per-batch standardise (bounded)
            acts = fwd(Ab); Z = acts[-1]
            Z = Z - Z.max(1, keepdims=True); P = np.exp(Z); P /= P.sum(1, keepdims=True)
            G = P; G[np.arange(len(b)), y[b]] -= 1; G /= len(b)
            for li in range(len(Ws) - 1, -1, -1):
                gW = acts[li].T @ G; gb = G.sum(0)
                vW[li] = 0.9 * vW[li] - lr * gW; vB[li] = 0.9 * vB[li] - lr * gb
                G = G @ Ws[li].T
                if li > 0:
                    G = G * (acts[li] > 0)
                Ws[li] += vW[li]; Bs[li] += vB[li]

    Xdn = ((Xde - mu) / sd).astype(np.float32)
    pred = fwd(Xdn)[-1].argmax(1)
    acc = float((pred == np.asarray(Yde_idx)).mean())

    def predict(Zin):
        return fwd(((np.asarray(Zin, np.float32) - mu) / sd).astype(np.float32))[-1].argmax(1)
    return acc, predict


# ----------------------------------------------------- content recall ----
def content_recall(decode_fn, n_test):
    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    def is_content(w): return len(w) >= 4
    rx50 = tot = 0
    for (path, sp, ch, ut, tr) in test:
        try:
            M, e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        pseq = decode_fn(M, e)
        for w in set(w.lower() for w in L.normalise(tr)):
            if not is_content(w):
                continue
            tgt = cmu_phones(w)
            if not tgt:
                continue
            tot += 1
            if best_window_match(pseq, [str(x) for x in tgt]) <= 0.50:
                rx50 += 1
    return rx50 / max(tot, 1), tot


def collapse(idx, phones_set):
    seq, prev = [], -1
    for k in idx:
        if k != prev:
            seq.append(phones_set[k]); prev = k
    return seq


# ------------------------------------------------------------------ main ----
def main():
    max_words = int(sys.argv[1]) if len(sys.argv) > 1 else 16000
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    SCALES = [s for s in (500, 1000, 2000, 4000, 8000, 16000, 32000) if s <= max_words]

    # load enough shards: ~4000 words/shard
    cap_pkls = min(113, max_words // 3500 + 3)
    print("=" * 92)
    print("DECOMPOSE the per-frame phone gap: DATA-SCALE vs MODEL-DEPTH (deep MLP, earned from scratch)")
    print("=" * 92, flush=True)
    t0 = time.time()
    all_words = load_words(cap_pkls)
    has_energy = bool(all_words) and all_words[0][3] is not None
    print(f"  banked words available (shards={cap_pkls}): {len(all_words)}"
          f"   energy-channel-in-bank: {has_energy}  [{time.time()-t0:.0f}s]", flush=True)
    max_words = min(max_words, len(all_words))
    SCALES = [s for s in SCALES if s <= max_words]
    if not SCALES or SCALES[-1] != max_words:
        SCALES.append(max_words)

    phones_set = sorted({p for _w, _f, ph, _e in all_words for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}; nP = len(phones_set)
    print(f"  phones={nP}  feat dim={_feat(all_words[0][1], all_words[0][3], has_energy).shape[1]}"
          f"  (float32)", flush=True)

    # held-out dev (fixed; proportional labels for a comparable per-frame acc proxy) -------------
    dev = _load_ph("dev-clean_*.pkl", 6, with_energy=True)
    Xde_l, Yde_l = [], []
    for (_w, fr, ph, en) in dev[:1500]:
        cx = _feat(fr, en, has_energy)
        n = len(cx); Pn = len(ph)
        for i in range(n):
            p = ph[int(i * Pn / n)]
            if p in pi:
                Xde_l.append(cx[i]); Yde_l.append(pi[p])
    Xde = np.asarray(Xde_l, np.float32); Yde_idx = Yde_l
    del Xde_l, dev; gc.collect()
    chance = max(Counter(Yde_idx).values()) / len(Yde_idx)
    print(f"  dev frames={len(Yde_idx)}  chance(majority)={chance:.3f}", flush=True)

    rows = []
    for scale in SCALES:
        ts = time.time()
        try:
            words = all_words[:scale]
            X, Yidx = bootstrap_align(words, phones_set, pi, has_energy)

            # SHALLOW (current default emission) ---------------------------------------------
            enc, cent, cph = fit_model_mem(X, Yidx, phones_set, pi)
            sh_acc = shallow_acc(enc, cent, cph, Xde, Yde_idx)
            blk = Xde[:200]
            tcost = time.time()
            for _ in range(20):
                _ = cph[(enc(blk) @ cent.T).argmax(1)]
            sh_us = (time.time() - tcost) / (20 * len(blk)) * 1e6

            def sh_decode(M, e, enc=enc, cent=cent, cph=cph):
                idx = cph[(enc(_feat(M, e, has_energy)) @ cent.T).argmax(1)]
                return collapse(idx, phones_set)
            sh_cr, sh_tot = content_recall(sh_decode, n_test)

            # DEEP (from-scratch MLP) -------------------------------------------------------
            dp_acc, predict = train_mlp(X, Yidx, nP, Xde, Yde_idx)
            tcost = time.time()
            for _ in range(20):
                _ = predict(blk)
            dp_us = (time.time() - tcost) / (20 * len(blk)) * 1e6

            def dp_decode(M, e, predict=predict):
                idx = predict(_feat(M, e, has_energy))
                return collapse(idx, phones_set)
            dp_cr, _ = content_recall(dp_decode, n_test)

            rows.append((scale, len(Yidx), sh_acc, sh_cr, dp_acc, dp_cr, sh_us, dp_us))
            print(f"  [{scale:>6} words / {len(Yidx):>7} frames]  "
                  f"SHALLOW acc {sh_acc:.3f} cr {sh_cr:.3f}  |  DEEP acc {dp_acc:.3f} cr {dp_cr:.3f}  "
                  f"|  us/frame sh {sh_us:.1f} deep {dp_us:.1f}  [{time.time()-ts:.0f}s]", flush=True)
            del X, Yidx, enc, cent, cph, predict; gc.collect()
        except MemoryError:
            print(f"  [{scale:>6} words] MemoryError -> DEGRADE: scale exceeds the RAM budget; "
                  f"curve BOUNDED at {rows[-1][0] if rows else 'n/a'} words. (honest bound)", flush=True)
            gc.collect()
            break

    if not rows:
        print("  no scale fit the budget; reduce max_words.")
        return 1

    # ---- DISCRIMINATIVE control: scrambled labels (training must do the work) ---------------
    scN = rows[-1][0]
    words = all_words[:scN]
    X, Yidx = bootstrap_align(words, phones_set, pi, has_energy)
    rng = np.random.default_rng(1)
    Yscr = rng.permutation(np.asarray(Yidx)).tolist()
    scr_acc, _ = train_mlp(X, Yscr, nP, Xde, Yde_idx)
    del X, Yidx; gc.collect()
    print("=" * 92)
    print(f"  CONTROL (scrambled-label deep): acc {scr_acc:.3f}  (chance {chance:.3f}) "
          f"-- real deep at max {rows[-1][4]:.3f}  => training does the work: {rows[-1][4] > scr_acc + 0.03}")

    # ---- DECOMPOSITION ---------------------------------------------------------------------
    print("=" * 92)
    print("  CURVE (per-frame phone acc | content recall@0.50):")
    for (sc, fr, sa, scr_, da, dcr, su, du) in rows:
        print(f"    {sc:>6}w / {fr:>7}f   shallow acc {sa:.3f} cr {scr_:.3f}   deep acc {da:.3f} cr {dcr:.3f}")
    sh0, shN = rows[0][2], rows[-1][2]; dp0, dpN = rows[0][4], rows[-1][4]
    sh_climb = shN - rows[-2][2] if len(rows) > 1 else 0.0
    dp_climb = dpN - rows[-2][4] if len(rows) > 1 else 0.0
    # log-linear slope per decade for the deep model
    if len(rows) > 1:
        xs = np.log10([r[1] for r in rows]); ys = np.array([r[4] for r in rows])
        A = np.vstack([xs, np.ones_like(xs)]).T
        slope_dec = float(np.linalg.lstsq(A, ys, rcond=None)[0][0])
        xs_s = np.log10([r[1] for r in rows]); ys_s = np.array([r[2] for r in rows])
        slope_sh = float(np.linalg.lstsq(np.vstack([xs_s, np.ones_like(xs_s)]).T, ys_s, rcond=None)[0][0])
    else:
        slope_dec = slope_sh = 0.0
    print("=" * 92)
    print(f"  SHALLOW: {sh0:.3f} -> {shN:.3f}  (last-step d={sh_climb:+.3f}, ~{slope_sh:+.3f}/decade) "
          f"=> {'CLIMBING' if sh_climb > 0.005 else 'PLATEAUED'}")
    print(f"  DEEP   : {dp0:.3f} -> {dpN:.3f}  (last-step d={dp_climb:+.3f}, ~{slope_dec:+.3f}/decade) "
          f"=> {'CLIMBING' if dp_climb > 0.005 else 'PLATEAUED'}")
    depth_lift = dpN - shN
    print(f"  DEPTH at matched MAX data: deep {dpN:.3f} - shallow {shN:.3f} = {depth_lift:+.3f}")
    cost_ratio = rows[-1][7] / max(rows[-1][6], 1e-9)
    print(f"  PER-FRAME COST: shallow {rows[-1][6]:.1f} us  deep {rows[-1][7]:.1f} us  "
          f"(deep is {cost_ratio:.0f}x the base) "
          f"=> {'ESCALATION tier' if rows[-1][7] > 4*rows[-1][6] else 'cheap enough for base'}")
    # extrapolate deep toward 0.5 if climbing
    if slope_dec > 0.005 and dpN < 0.5:
        decades = (0.5 - dpN) / slope_dec
        need = rows[-1][1] * (10 ** decades)
        print(f"  EXTRAPOLATION (deep, log-linear): to reach 0.50/frame needs ~{decades:.1f} more decades "
              f"(~{need:.0e} frames). Bank has ~{len(all_words)} words (~{len(all_words)*20:.0e} frames).")
    print(f"  GAP DECOMP to 0.5-0.7: depth buys {depth_lift:+.3f} (deep-vs-shallow at matched data); "
          f"data buys the curve slopes above; remaining to 0.50 = {0.5 - max(dpN, shN):.3f}.")
    print(f"  donkey=0: per-frame decision is argmax (graph-native Dot/topk for shallow); "
          f"deep weights earned from scratch by the agent's SGD; no LLM, no borrowed weights.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
