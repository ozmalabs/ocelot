"""REPRESENTATION-GAP BUILD (Step C of the independent speech-arc review).

Step A settled that wav2vec2 DOMINATES the from-scratch (donkey=0) encoders at a fair pool
(recall 0.817 vs APC 0.270; gap +0.55, CIs disjoint). So the gap is REAL. This build asks whether
matched-compute APC variants can close ≥50% of that fair gap (from ~0.27 toward ~0.82), scored on
the SAME locked metric / pool as Step A.

Levers built:
  (ii) OBJECTIVE — MASKED-FRAME CONTRASTIVE PREDICTIVE CODING (Rust `apc_train_masked_cpc`): mask
       frames, encode with bidirectional context, predict each masked frame's TRUE-frame target
       CONTRASTIVELY (InfoNCE over frames) — the specific thing wav2vec2 does that AR-APC does not.
       CONTROL: shuffled positive assignment must collapse the gain.
  (i)  DATA — the same masked-CPC on a 5-10x larger UNLABELED LibriSpeech train pool (masked-CPC is
       label-free, so extra audio is cheap; tests the data-bound hypothesis).
  (iii) DEPTH — a 2-layer recurrence would need the ApcEncode Term extended to multi-layer models;
       NOT built in this bounded first pass (reported honestly; single-layer bidir only).

Baseline = AR-APC (Rust `apc_train`, next-frame L2), the Step-A 0.270-class encoder. All variants
share the identical concat-lift front-end features, encode via the `ApcEncode` graph Term, and are
scored through the identical Rust NN-recall kernel + bootstrap CIs on Step A's 3000-token pool.
donkey=0 at inference (no torch imported here); wav2vec2 features are read from Step A's eval-only
cache (extracted in an isolated subprocess).

Run:
  # (once) extract extra UNLABELED train cochleagrams for the DATA lever (torch-free: av + Rust ear)
  PYTHONPATH=runners/dsl/python:.:scripts VENV_PY scripts/apc_repr_gap_build.py --extract-bigtrain
  # the build
  PYTHONPATH=runners/dsl/python:.:scripts VENV_PY scripts/apc_repr_gap_build.py

Env: TE_CAP(3000) CAPQ(300) NPOS(600) NNEG(1800) BOOT(2000) DH(96) EPOCHS(24) LR(0.05)
     MASK_PROB(0.15) MASK_SPAN(3) DT(64) NCE_TAU(0.1) BATCH(24)
     BIG_SPK(120) BIG_UTTS_PER(12) BIG_CAP(1400) W2V_LAYER(6) W2V_PCA(64)
"""
from __future__ import annotations
import os, sys, glob, pickle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT, os.path.join(ROOT, "scripts")):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
import numpy as np
from collections import defaultdict
import scripts.apc_fair_pool_falsification as FP   # helpers: utt_feats, resample, _traj, ci_from_detail
import scripts.jabberwock_contrastive_speaker_invariant as CI

LIBRI = "/home/matt/data/LibriSpeech"
TRAIN_TREE = os.path.join(LIBRI, "train-clean-100")
SCRATCH = FP.SCRATCH
TRAIN_CACHE = FP.TRAIN_CACHE      # existing labeled train coch (180 utts)
W2V_CACHE = FP.W2V_CACHE          # Step A fair test pool (coch + w2v)
BIG_CACHE = os.path.join(SCRATCH, "apc_bigtrain_coch.pkl")

TE_CAP = FP.TE_CAP
T = FP.T
DH = int(os.environ.get("DH", "96"))
EPOCHS = int(os.environ.get("EPOCHS", "24"))
LR = float(os.environ.get("LR", "0.05"))
MASK_PROB = float(os.environ.get("MASK_PROB", "0.15"))
MASK_SPAN = int(os.environ.get("MASK_SPAN", "3"))
DT = int(os.environ.get("DT", "64"))
NCE_TAU = float(os.environ.get("NCE_TAU", "0.1"))
BATCH = int(os.environ.get("BATCH", "24"))
KAHEAD = int(os.environ.get("KAHEAD", "3"))
LIFT_M = int(os.environ.get("LIFT_MODES", "16"))
CAPQ = FP.CAPQ
NPOS = FP.NPOS
NNEG = FP.NNEG
BOOT = FP.BOOT
BIG_SPK = int(os.environ.get("BIG_SPK", "120"))
BIG_UTTS_PER = int(os.environ.get("BIG_UTTS_PER", "12"))
BIG_CAP = int(os.environ.get("BIG_CAP", "1400"))
W2V_LAYER = int(os.environ.get("W2V_LAYER", "6"))
W2V_PCA = int(os.environ.get("W2V_PCA", "64"))
FPS = 100.0


def _extract_bigtrain():
    """UNLABELED extra train cochleagrams (torch-free: av decode + Rust cochleagram).
    No MMS_FA (masked-CPC is label-free). donkey=0 by construction."""
    import resource, av
    resource.setrlimit(resource.RLIMIT_AS, (14 * 1024**3, 14 * 1024**3))
    from substrate_rs import _native as nat

    def load_flac(path):
        c = av.open(path); s = c.streams.audio[0]
        arr = np.concatenate([f.to_ndarray().flatten().astype(np.float32) for f in c.decode(s)])
        rate = s.rate; c.close()
        peak = max(float(np.abs(arr).max()), 1.0)
        return (arr / peak * 0.7).astype(np.float32), rate

    out = []
    speakers = sorted(os.listdir(TRAIN_TREE))[:BIG_SPK]
    for spk in speakers:
        if len(out) >= BIG_CAP:
            break
        flacs = sorted(glob.glob(os.path.join(TRAIN_TREE, spk, "**", "*.flac"), recursive=True))[:BIG_UTTS_PER]
        for f in flacs:
            if len(out) >= BIG_CAP:
                break
            try:
                x, fs = load_flac(f)
            except Exception:
                continue
            dur = len(x) / fs
            nfr = max(4, int(round(dur * FPS)))
            if nfr < 8:
                continue
            flat = nat.cochleagram(x, int(fs), 50.0, 80.0, nfr)
            coch = np.asarray(flat, np.float32).reshape(nfr, 32).astype(np.float16)
            out.append(coch)
        print(f"  [bigtrain] {spk}: total {len(out)}", flush=True)
    pickle.dump(out, open(BIG_CACHE, "wb"))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
    print(f"  [bigtrain] wrote {len(out)} unlabeled train utts [peak {peak:.2f} GiB]", flush=True)


# ---- feature pipeline (concat-lift + znorm), shared by every variant ----
def concat_lift(nat, coch):
    coch = np.asarray(coch, np.float32); nfr = coch.shape[0]
    feat = FP.utt_feats(coch)
    m = np.asarray(nat.apc_lift(coch.reshape(-1).tolist(), nfr, 32, LIFT_M), np.float32).reshape(nfr, LIFT_M)
    dl = np.diff(m, axis=0); dl = np.vstack([np.zeros((1, m.shape[1]), np.float32), dl])
    return np.concatenate([feat, m, dl], axis=1).astype(np.float32)


def znorm_fit(feats):
    stk = np.concatenate(feats); return stk.mean(0).astype(np.float32), (stk.std(0) + 1e-6).astype(np.float32)
def znorm_apply(feats, mu, sd):
    return [((f - mu) / sd).astype(np.float32) for f in feats]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--extract-bigtrain":
        _extract_bigtrain(); return

    import resource
    resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
    from substrate_rs import _native as nat
    print(f"  [substrate_rs] {nat.__file__}", flush=True)
    assert hasattr(nat, "apc_train_masked_cpc"), "apc_train_masked_cpc missing — rebuild the crate"

    if not os.path.exists(W2V_CACHE):
        print("  ERROR: run Step A extraction first (apc_fair_pool_falsification.py --extract-w2v)")
        return
    train_all = pickle.load(open(TRAIN_CACHE, "rb"))
    tr = [d for d in train_all if d[3] == "train"]
    te = pickle.load(open(W2V_CACHE, "rb"))
    print(f"\n  DATA: labeled TRAIN {len(tr)} utts | HELD-OUT TEST {len(te)} utts; TE_CAP={TE_CAP}", flush=True)

    s = nat.Substrate()
    def apc_encode(model, seqf):
        term = {"type": "ApcEncode", "model": {"type": "Lit", "value": model},
                "seq": {"type": "Lit", "value": FP._traj(seqf)},
                "start": {"type": "Lit", "value": -1}, "end": {"type": "Lit", "value": -1},
                "out_len": {"type": "Lit", "value": seqf.shape[0]}}
        out = s.evaluate(term, {})
        return np.asarray([[float(v) for v in row] for row in out], np.float32)

    # ---- base train features (concat-lift + znorm on labeled train) ----
    tr_cl = [concat_lift(nat, d[0]) for d in tr]
    mu_c, sd_c = znorm_fit(tr_cl); tr_cl = znorm_apply(tr_cl, mu_c, sd_c)
    din = tr_cl[0].shape[1]
    te_cl = znorm_apply([concat_lift(nat, d[0]) for d in te], mu_c, sd_c)

    def flat_lens(feats):
        ff = np.concatenate([f.reshape(-1) for f in feats]).astype(np.float32)
        lens = [int(f.shape[0]) for f in feats]
        return ff.tolist(), lens

    # ---- variant training (cached to disk so long runs resume across bounded calls) ----
    MCACHE = os.path.join(SCRATCH, "apc_gap_models.pkl")
    models = pickle.load(open(MCACHE, "rb")) if os.path.exists(MCACHE) else {}
    sig = f"dh{DH}_ep{EPOCHS}_mp{MASK_PROB}_ms{MASK_SPAN}_dt{DT}_tau{NCE_TAU}_b{BATCH}_din{din}"
    def cached(key, fn):
        k = f"{key}|{sig}"
        if k in models:
            print(f"  [cache] {key} loaded", flush=True); return models[k]
        v = fn(); models[k] = v; pickle.dump(models, open(MCACHE, "wb")); return v

    print(f"\n--- TRAIN variants (din={din} dh={DH} epochs={EPOCHS}) ---", flush=True)
    ff, lens = flat_lens(tr_cl)
    ml_ar = cached("AR-APC", lambda: [float(v) for v in
        (print("  [baseline] AR-APC next-frame (apc_train, bidir)", flush=True) or
         nat.apc_train(ff, lens, din, DH, KAHEAD, EPOCHS, LR, True, 0, False))])
    ml_mc = cached("masked-CPC", lambda: [float(v) for v in
        (print(f"  [objective] masked-CPC (mask_prob={MASK_PROB} span={MASK_SPAN} dt={DT} tau={NCE_TAU})", flush=True) or
         nat.apc_train_masked_cpc(ff, lens, din, DH, EPOCHS, LR, True, 0, MASK_PROB, MASK_SPAN, DT, NCE_TAU, BATCH, False))])
    ml_sh = cached("masked-CPC-shuf", lambda: [float(v) for v in
        (print("  [control] masked-CPC SHUFFLED positives (must collapse)", flush=True) or
         nat.apc_train_masked_cpc(ff, lens, din, DH, EPOCHS, LR, True, 0, MASK_PROB, MASK_SPAN, DT, NCE_TAU, BATCH, True))])

    variants = {"AR-APC (baseline)": ml_ar, "masked-CPC (objective)": ml_mc,
                "masked-CPC SHUFFLED (ctrl)": ml_sh}

    # ---- DATA lever: masked-CPC on the larger unlabeled train pool ----
    if os.path.exists(BIG_CACHE):
        big = pickle.load(open(BIG_CACHE, "rb"))
        big_cl = [concat_lift(nat, c) for c in big]
        mu_b, sd_b = znorm_fit(big_cl); big_cl = znorm_apply(big_cl, mu_b, sd_b)
        te_cl_big = znorm_apply([concat_lift(nat, d[0]) for d in te], mu_b, sd_b)
        ffb, lensb = flat_lens(big_cl)
        BIG_EP = int(os.environ.get("BIG_EPOCHS", str(max(12, EPOCHS // 2))))
        print(f"\n  [data] masked-CPC on {len(big)} UNLABELED train utts (~{len(big)/max(1,len(tr)):.1f}x), "
              f"epochs={BIG_EP}", flush=True)
        ml_big = cached(f"masked-CPC-DATA-n{len(big)}-ep{BIG_EP}", lambda: [float(v) for v in
            nat.apc_train_masked_cpc(ffb, lensb, din, DH, BIG_EP, LR, True, 0,
                                     MASK_PROB, MASK_SPAN, DT, NCE_TAU, BATCH, False)])
    else:
        print("\n  [data] BIG_CACHE missing — DATA lever SKIPPED (run --extract-bigtrain)", flush=True)
        ml_big, te_cl_big = None, None

    # ---- encode the fair pool (identical order/words/spk) per variant ----
    words, spk = [], []
    reps = {name: [] for name in variants}
    if ml_big is not None:
        reps["masked-CPC +DATA"] = []
    reps["wav2vec2 L%d (eval-only)" % W2V_LAYER] = []

    # wav2vec2 PCA (per-utt CMN + unsupervised PCA) on the layer, same as Step A
    frames = []
    for d in te:
        f = np.asarray(d[3][W2V_LAYER], np.float32); f = f - f.mean(0, keepdims=True); frames.append(f)
    X = np.concatenate(frames, axis=0)
    if len(X) > 20000:
        X = X[np.random.default_rng(0).choice(len(X), 20000, replace=False)]
    w2v_mu = X.mean(0); U, S, Vt = np.linalg.svd(X - w2v_mu, full_matrices=False)
    w2v_V = Vt[:W2V_PCA]; print(f"  [w2v L{W2V_LAYER}] PCA var retained {(S[:W2V_PCA]**2).sum()/(S**2).sum():.3f}", flush=True)

    h_cache = {}
    for ui, d in enumerate(te):
        for name, model in variants.items():
            h_cache[(name, ui)] = apc_encode(model, te_cl[ui])
        if ml_big is not None:
            h_cache[("masked-CPC +DATA", ui)] = apc_encode(ml_big, te_cl_big[ui])

    ntok = 0
    for ui, d in enumerate(te):
        coch, wspans, sp, wd = d
        Tu = np.asarray(coch).shape[0]
        w2v_f = np.asarray(wd[W2V_LAYER], np.float32); w2v_f = w2v_f - w2v_f.mean(0, keepdims=True)
        w2v_red = (w2v_f - w2v_mu) @ w2v_V.T
        for (w, f0, f1) in wspans:
            if ntok >= TE_CAP:
                break
            words.append(w); spk.append(sp)
            for name in variants:
                reps[name].append(FP.resample(h_cache[(name, ui)][f0:f1], T))
            if ml_big is not None:
                reps["masked-CPC +DATA"].append(FP.resample(h_cache[("masked-CPC +DATA", ui)][f0:f1], T))
            Tw = w2v_red.shape[0]
            g0 = int(round(f0 * Tw / max(1, Tu))); g1 = max(g0 + 1, int(round(f1 * Tw / max(1, Tu)))); g1 = min(g1, Tw)
            reps["wav2vec2 L%d (eval-only)" % W2V_LAYER].append(FP.resample(w2v_red[g0:g1], T))
            ntok += 1
        if ntok >= TE_CAP:
            break
    print(f"\n  POOL: {ntok} tokens, {len(set(spk))} spk, {len(set(words))} words (identical for all reps)", flush=True)

    # ---- score all through the identical kernel + bootstrap CIs ----
    _wi, _si = {}, {}
    wi = np.array([_wi.setdefault(x, len(_wi)) for x in words], np.int64)
    si = np.array([_si.setdefault(x, len(_si)) for x in spk], np.int64)
    def score(name, arr):
        arr = np.asarray(arr, np.float32); n = arr.shape[0]; dim = arr.shape[2]
        det = nat.apc_recall_detail(arr.reshape(-1).tolist(), n, T, dim, wi.tolist(), si.tolist(),
                                    CAPQ, NPOS, NNEG, 0)
        r = FP.ci_from_detail(det, BOOT)
        print(f"  {name:>28}  dim={dim:4d}  recall {r['recall']:.3f} "
              f"[{r['recall_ci'][0]:.3f},{r['recall_ci'][1]:.3f}]  AUC {r['auc']:.3f} "
              f"[{r['auc_ci'][0]:.3f},{r['auc_ci'][1]:.3f}]", flush=True)
        return r

    print(f"\n--- ★ SCORING on the fair pool (cap_q={CAPQ}, boot={BOOT}) ---")
    res = {}
    order = ["AR-APC (baseline)", "masked-CPC (objective)", "masked-CPC SHUFFLED (ctrl)"]
    if ml_big is not None:
        order.append("masked-CPC +DATA")
    order.append("wav2vec2 L%d (eval-only)" % W2V_LAYER)
    for name in order:
        res[name] = score(name, reps[name])

    donkey = [mn for mn in ("torch", "torchaudio", "allosaurus", "faster_whisper") if mn in sys.modules]
    print(f"\n--- donkey=0 AT INFERENCE: torch/... in sys.modules: {donkey or 'NONE'} ---")

    # ---- verdict: % of the fair gap closed ----
    base = res["AR-APC (baseline)"]["recall"]
    w2v = res["wav2vec2 L%d (eval-only)" % W2V_LAYER]["recall"]
    gap = w2v - base
    print("\n" + "=" * 96)
    print(f"  fair gap: AR-APC {base:.3f} -> wav2vec2 {w2v:.3f}  (gap {gap:+.3f})")
    best_name, best_close = None, -1e9
    for name in order:
        if name in ("AR-APC (baseline)", "wav2vec2 L%d (eval-only)" % W2V_LAYER):
            continue
        r = res[name]["recall"]
        closed = (r - base) / gap * 100 if gap > 1e-6 else float("nan")
        tag = "  <- CONTROL (should NOT close)" if "SHUFFLED" in name else ""
        print(f"    {name:>28}: recall {r:.3f}  Δ{r-base:+.3f}  gap closed {closed:5.1f}%{tag}")
        if "SHUFFLED" not in name and closed > best_close:
            best_close = closed; best_name = name
    obj = res["masked-CPC (objective)"]["recall"]; ctrl = res["masked-CPC SHUFFLED (ctrl)"]["recall"]
    print(f"  control check: objective {obj:.3f} vs shuffled {ctrl:.3f}  "
          f"({'PASS — shuffle collapses' if obj > ctrl + 0.01 else 'WEAK/FAIL — shuffle did not collapse'})")
    gate = best_close is not None and best_close >= 50.0
    print(f"  ★★★ GATE (any variant closes >=50% of the fair gap)?  "
          f"{'YES via ' + str(best_name) if gate else 'NO'}  (best {best_name} {best_close:.1f}%)")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
    print(f"  [memory] peak RSS: {peak:.2f} GiB")
    print("=" * 96)


if __name__ == "__main__":
    main()
