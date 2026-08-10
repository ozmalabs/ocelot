"""PUSH the DEEP per-frame phone encoder on MUCH MORE DATA — extend the data-scale curve far
past the prior 16k-word ceiling toward the full banked corpus (~4.5e5 words / ~1e7 frames).

Context (the controls' verdict, commits ba3377d4 / 1afd6698): the per-frame phone model's floor
is DEPTH + DATA, not a richer feature. DEPTH is the dominant lever (deep > shallow at matched
data, still climbing at 16k). The decompose script only trained the deep MLP to ~16k words. The
full shape-only /home/matt/data/phonebank has all 113 train-clean-100 shards banked. So MORE DATA
is already on disk — the task is to TRAIN THE DEEP ENCODER ON FAR MORE OF IT and trace how far the
per-frame curve climbs toward real-phone 0.5-0.7, and locate the bound (data-bound vs capacity-bound).

EARN / donkey=0: the deep encoder is the agent's OWN from-scratch random-init MLP trained by its
own numpy SGD (weights are graph data, like LDA; NO torch, NO pretrained/from_pretrained/torch.hub/
download). Per-frame decision = graph-native argmax over emissions. No LLM in the decision path.

THE MEMORY DISCIPLINE (the headline risk — more data = more frames = OOM; prior phone runs OOM'd):
the full +-W context-expanded design matrix is ~23GB at the full bank and CANNOT live in RAM. So we
do NOT materialise it. Instead:
  (1) load the RAW banked frames (float32, ~1.3GB for the full bank) + mint clean per-frame phone
      labels by Viterbi forced-alignment under a FIXED bootstrap shallow aligner (fit once on a
      subset; the aligner is label-minting infrastructure, identical across the curve, so the only
      variable is the deep model's TRAINING-SET SIZE);
  (2) write the context-expanded features ONCE to a disk-backed float32 MEMMAP in .bigtmp/
      (regenerable; never committed), sized to the max scale;
  (3) train the from-scratch deep MLP per scale by CHUNK-SHUFFLED streaming mini-batch SGD reading
      contiguous blocks from the memmap (block order shuffled each epoch + within-block full shuffle).
      RAM stays bounded to one block (~150MB) + the tiny weights + the in-RAM dev block, REGARDLESS
      of scale. mu/sd computed in one streaming pass. The full context matrix is NEVER in RAM.

GATE (all donkey=0, honest): the deep per-frame data-scale curve 16k->max (climbing or plateaued +
slope/decade + honest extrapolation to 0.5-0.7); DISCRIMINATIVE (real-trained beats scrambled-label
at the max scale -> training does the work); CAPACITY (wider/deeper MLP at max -> lift + per-frame
cost for the cheap-method-leverage call); MEMORY (bounded, no OOM — peak is one block, not the matrix).

Run (SMOKE first, small): PYTHONPATH=runners/dsl/python:.:scripts python3 \
        scripts/jabberwock_deep_phone_datascale.py [max_words] [epochs]
  max_words default = all banked; smoke e.g. 8000.
"""
import os, sys, time, gc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_earns_phone_model import ctxd, phone_emission, viterbi_align
from scripts.jabberwock_decompose_phone_gap import fit_model_mem

HERE = os.path.dirname(os.path.abspath(__file__))
BIGTMP = os.path.join(HERE, os.pardir, ".bigtmp")
MMPATH = os.path.join(BIGTMP, "deep_phone_datascale_ctx.f32")


# ---------------------------------------------------------------- features ----
def build_ctx_inram(words, featdim):
    """single-allocation context matrix for a SUBSET (no feats-list+concatenate duplication).
    Used only for the bootstrap aligner (kept small). e=None bank -> ctxd shape-only."""
    counts = [len(w[1]) for w in words]
    X = np.empty((sum(counts), featdim), np.float32)
    off = 0
    for (_w, fr, _ph, _e) in words:
        c = ctxd(fr).astype(np.float32)
        X[off:off + len(c)] = c
        off += len(c)
    return X


def flat_labels(words, pi):
    """flat-start (proportional) per-frame phone-index labels (HMM flat-start)."""
    Y = []
    for (_w, fr, ph, _e) in words:
        n = len(fr); P = len(ph)
        Y.extend(pi[ph[int(i * P / n)]] for i in range(n))
    return Y


def fit_bootstrap_aligner(words, phones_set, pi, featdim):
    """FIXED bootstrap shallow aligner (PCA->LDA enc + per-phone GMM centroids), flat-start fit then
    ONE EM realign refit. Used to mint clean labels for EVERY scale (identical across the curve)."""
    nP = len(phones_set)
    X = build_ctx_inram(words, featdim)
    counts = [len(w[1]) for w in words]
    offs = np.cumsum([0] + counts)
    enc, cent, cph = fit_model_mem(X, flat_labels(words, pi), phones_set, pi)
    # one EM realign on the subset -> refit (a better, stable aligner)
    newY = []
    for k, (_w, _fr, ph, _e) in enumerate(words):
        cx = X[offs[k]:offs[k + 1]]
        emis = phone_emission(cx, enc, cent, cph, nP)
        newY.extend(viterbi_align(emis, [pi[p] for p in ph]))
    enc, cent, cph = fit_model_mem(X, newY, phones_set, pi)
    del X; gc.collect()
    return enc, cent, cph


def build_memmap(words, enc, cent, cph, pi, nP, featdim):
    """align ALL words (Viterbi forced-alignment under the fixed aligner) and write the context-
    expanded features ONCE to a disk-backed float32 memmap; labels kept in a small int16 array.
    Returns (ctx_memmap, labels, cum_frames_per_word)."""
    counts = [len(w[1]) for w in words]
    cum = np.cumsum([0] + counts)
    total = int(cum[-1])
    os.makedirs(BIGTMP, exist_ok=True)
    mm = np.memmap(MMPATH, dtype=np.float32, mode="w+", shape=(total, featdim))
    labels = np.empty(total, np.int16)
    off = 0
    for (_w, fr, ph, _e) in words:
        cx = ctxd(fr).astype(np.float32)
        emis = phone_emission(cx, enc, cent, cph, nP)
        lab = viterbi_align(emis, [pi[p] for p in ph])
        n = len(cx)
        mm[off:off + n] = cx
        labels[off:off + n] = np.asarray(lab, np.int16)
        off += n
    mm.flush()
    return mm, labels, cum


# ----------------------------------------------------------- streaming MLP ----
def stream_meanstd(mm, n, featdim, ch=65536):
    s = np.zeros(featdim, np.float64); ss = np.zeros(featdim, np.float64)
    for st in range(0, n, ch):
        b = np.asarray(mm[st:min(st + ch, n)], np.float64)
        s += b.sum(0); ss += (b * b).sum(0)
    mu = s / n
    sd = np.sqrt(np.maximum(ss / n - mu * mu, 0.0)) + 1e-6
    return mu.astype(np.float32), sd.astype(np.float32)


def train_stream(mm, labels, n, nP, Xde, Yde, featdim,
                 hidden=(512, 256), epochs=12, bs=256, lr=0.2, seed=0, ch=65536):
    """from-scratch random-init MLP, the agent's own numpy SGD (EARNED not borrowed), trained by
    CHUNK-SHUFFLED streaming mini-batch SGD over the disk memmap. RAM bounded to one block + weights.

    `labels` is the per-frame phone-index array (len n) paired ROW-FOR-ROW with mm[:n] — pass a
    permuted copy for the scrambled-label discriminative control."""
    mu, sd = stream_meanstd(mm, n, featdim, ch)
    rng = np.random.default_rng(seed)
    dims = [featdim] + list(hidden) + [nP]
    Ws = [rng.standard_normal((dims[i], dims[i + 1])).astype(np.float32)
          * np.float32(np.sqrt(2.0 / dims[i])) for i in range(len(dims) - 1)]
    Bs = [np.zeros(dims[i + 1], np.float32) for i in range(len(dims) - 1)]
    vW = [np.zeros_like(w) for w in Ws]; vB = [np.zeros_like(b) for b in Bs]

    def fwd(A):
        acts = [A]
        for li in range(len(Ws)):
            Z = acts[-1] @ Ws[li] + Bs[li]
            acts.append(np.maximum(Z, 0) if li < len(Ws) - 1 else Z)
        return acts

    starts = list(range(0, n, ch))
    for ep in range(epochs):
        rng.shuffle(starts)
        for c0 in starts:
            c1 = min(c0 + ch, n)
            block = ((np.asarray(mm[c0:c1], np.float32) - mu) / sd).astype(np.float32)
            yb_all = np.asarray(labels[c0:c1], np.int64)
            perm = rng.permutation(len(block))
            block = block[perm]; yb_all = yb_all[perm]
            for s in range(0, len(block), bs):
                Ab = block[s:s + bs]; yb = yb_all[s:s + bs]
                acts = fwd(Ab); Z = acts[-1]
                Z = Z - Z.max(1, keepdims=True); P = np.exp(Z); P /= P.sum(1, keepdims=True)
                G = P; G[np.arange(len(yb)), yb] -= 1; G /= len(yb)
                for li in range(len(Ws) - 1, -1, -1):
                    gW = acts[li].T @ G; gb = G.sum(0)
                    vW[li] = 0.9 * vW[li] - lr * gW; vB[li] = 0.9 * vB[li] - lr * gb
                    G = G @ Ws[li].T
                    if li > 0:
                        G = G * (acts[li] > 0)
                    Ws[li] += vW[li]; Bs[li] += vB[li]
            del block, yb_all

    Xdn = ((Xde - mu) / sd).astype(np.float32)
    acc = float((fwd(Xdn)[-1].argmax(1) == np.asarray(Yde)).mean())

    def predict(Zin):
        return fwd(((np.asarray(Zin, np.float32) - mu) / sd).astype(np.float32))[-1].argmax(1)
    # per-frame cost (us/frame) on an in-RAM block
    blk = Xde[:200]; t = time.time()
    for _ in range(20):
        _ = predict(blk)
    us = (time.time() - t) / (20 * len(blk)) * 1e6
    return acc, us, predict


# ------------------------------------------------------------------ main ----
def main():
    max_words = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 12

    print("=" * 96)
    print("PUSH THE DEEP PER-FRAME PHONE ENCODER ON MORE DATA — extend the data-scale curve past 16k")
    print("=" * 96, flush=True)
    t0 = time.time()
    # load ALL banked shards (raw frames, float32) -> cast to float32 to halve RAM
    all_words = _load_ph("train-clean-100_*.pkl", 113, with_energy=True)
    all_words = [(w, np.asarray(fr, np.float32), ph, en) for (w, fr, ph, en) in all_words]
    has_energy = bool(all_words) and all_words[0][3] is not None
    n_avail = len(all_words)
    max_words = min(max_words, n_avail)
    all_words = all_words[:max_words]
    featdim = ctxd(all_words[0][1]).shape[1]
    total_frames = sum(len(w[1]) for w in all_words)
    print(f"  banked words available: {n_avail}   using: {max_words}   total frames: {total_frames}"
          f"   energy-in-bank: {has_energy}   feat dim: {featdim}   [{time.time()-t0:.0f}s]", flush=True)
    print(f"  (full context matrix would be {total_frames*featdim*4/1e9:.1f} GB -> NOT in RAM; "
          f"using disk memmap + chunk-shuffled streaming SGD)", flush=True)

    phones_set = sorted({p for _w, _f, ph, _e in all_words for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}; nP = len(phones_set)

    # held-out dev (fixed; proportional labels for a comparable per-frame acc proxy) ------------
    dev = _load_ph("dev-clean_*.pkl", 6, with_energy=True)
    Xde_l, Yde = [], []
    for (_w, fr, ph, _e) in dev[:1500]:
        cx = ctxd(fr).astype(np.float32)
        n = len(cx); Pn = len(ph)
        for i in range(n):
            p = ph[int(i * Pn / n)]
            if p in pi:
                Xde_l.append(cx[i]); Yde.append(pi[p])
    Xde = np.asarray(Xde_l, np.float32)
    del Xde_l, dev; gc.collect()
    chance = max(Counter(Yde).values()) / len(Yde)
    print(f"  phones={nP}  dev frames={len(Yde)}  chance(majority)={chance:.3f}  [{time.time()-t0:.0f}s]",
          flush=True)

    # FIXED bootstrap aligner (fit once on a subset; identical across the whole curve) ----------
    align_fit = min(24000, max_words)
    enc, cent, cph = fit_bootstrap_aligner(all_words[:align_fit], phones_set, pi, featdim)
    print(f"  bootstrap aligner fit on {align_fit} words (fixed across the curve)  [{time.time()-t0:.0f}s]",
          flush=True)

    # align ALL words + write the context memmap ONCE -------------------------------------------
    mm = None
    try:
        mm, labels, cum = build_memmap(all_words, enc, cent, cph, pi, nP, featdim)
        n_total = int(cum[-1])
        print(f"  context memmap built: {n_total} frames x {featdim}  "
              f"({os.path.getsize(MMPATH)/1e9:.1f} GB on disk)  [{time.time()-t0:.0f}s]", flush=True)
        del all_words; gc.collect()   # raw frames no longer needed; RAM now bounded for training

        # scales (in WORDS), mapped to frame counts via the per-word cumulative ------------------
        sc_words = [s for s in (16000, 32000, 64000, 128000, 256000) if s < max_words]
        sc_words.append(max_words)
        rows = []
        for sw in sc_words:
            ts = time.time()
            nfr = int(cum[sw])
            try:
                acc, us, _ = train_stream(mm, labels[:nfr], nfr, nP, Xde, Yde, featdim, epochs=epochs)
            except MemoryError:
                print(f"  [{sw:>7} words] MemoryError -> DEGRADE; curve bounded at "
                      f"{rows[-1][0] if rows else 'n/a'} words.", flush=True)
                gc.collect(); break
            rows.append((sw, nfr, acc, us))
            print(f"  [{sw:>7} words / {nfr:>8} frames]  DEEP per-frame acc {acc:.3f}  "
                  f"({us:.1f} us/frame)  [{time.time()-ts:.0f}s, tot {time.time()-t0:.0f}s]", flush=True)

        if not rows:
            print("  no scale completed."); return 1

        # DISCRIMINATIVE control: scrambled labels at the max completed scale -------------------
        scN, nfrN = rows[-1][0], rows[-1][1]
        rng = np.random.default_rng(1)
        lab_scr = rng.permutation(np.asarray(labels[:nfrN]))
        scr_acc, _, _ = train_stream(mm, lab_scr, nfrN, nP, Xde, Yde, featdim, epochs=epochs)
        del lab_scr; gc.collect()

        # CAPACITY bump at the max scale (wider+deeper; earned from scratch) --------------------
        cap_acc, cap_us, _ = train_stream(mm, labels[:nfrN], nfrN, nP, Xde, Yde, featdim,
                                          hidden=(1024, 512, 256), epochs=epochs)
    finally:
        if mm is not None:
            del mm; gc.collect()
        if os.path.exists(MMPATH):
            os.remove(MMPATH)   # regenerable; never committed

    # ---- REPORT ------------------------------------------------------------------------------
    print("=" * 96)
    print("  DEEP per-frame data-scale curve (canonical metric; from-scratch numpy SGD, donkey=0):")
    for (sw, nfr, acc, us) in rows:
        print(f"    {sw:>7}w / {nfr:>8}f   acc {acc:.3f}   {us:.1f} us/frame")
    dp0, dpN = rows[0][2], rows[-1][2]
    last_step = dpN - rows[-2][2] if len(rows) > 1 else 0.0
    if len(rows) > 1:
        xs = np.log10([r[1] for r in rows]); ys = np.array([r[2] for r in rows])
        slope = float(np.linalg.lstsq(np.vstack([xs, np.ones_like(xs)]).T, ys, rcond=None)[0][0])
    else:
        slope = 0.0
    print("=" * 96)
    verdict = "CLIMBING" if last_step > 0.003 else "PLATEAUED"
    print(f"  DEEP: {dp0:.3f} @ {rows[0][0]}w -> {dpN:.3f} @ {rows[-1][0]}w   "
          f"(last-step d={last_step:+.3f}, ~{slope:+.3f}/decade)  => {verdict}")
    print(f"  DISCRIMINATIVE: real {dpN:.3f} vs scrambled-label {scr_acc:.3f} (chance {chance:.3f}) "
          f"=> training does the work: {dpN > scr_acc + 0.03}")
    print(f"  CAPACITY (1024,512,256) vs base (512,256) at max: {cap_acc:.3f} vs {dpN:.3f} "
          f"= {cap_acc-dpN:+.3f}   cost {cap_us:.1f} vs {rows[-1][3]:.1f} us/frame")
    if slope > 0.005 and dpN < 0.5:
        decades = (0.5 - dpN) / slope
        print(f"  EXTRAPOLATION (log-linear): to reach 0.50/frame needs ~{decades:.1f} more decades of "
              f"data (~{rows[-1][1]*10**decades:.1e} frames). On disk: ~{rows[-1][1]:.1e} frames "
              f"(=> {decades:.1f} decades = {10**decades:.0f}x MORE than the full bank).")
    print(f"  BOUND: reached {rows[-1][0]} words / {rows[-1][1]} frames "
          f"(of {max_words} available). Memory: bounded to one ~"
          f"{65536*featdim*4/1e6:.0f}MB block (the full {rows[-1][1]*featdim*4/1e9:.1f}GB matrix never in RAM).")
    print(f"  donkey=0: deep encoder = from-scratch random-init MLP, agent's own numpy SGD (no torch, "
          f"no borrowed weights); per-frame decision = graph-native argmax.")
    print("=" * 96, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
