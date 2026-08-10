"""FAIR-POOL FALSIFICATION (Step A of the independent speech-arc review).

The review found the historical cross-speaker numbers are POOL-SIZE-DEPENDENT and that
wav2vec2's 0.668 was quoted at a DIFFERENT pool than the donkey=0 encoders. This settles it:
score THREE representations through the *identical* guaranteed-support NN-recall kernel on the
*identical* large fixed pool of HELD-OUT dev-clean word tokens (TE_CAP=3000):

  (1) APC front-end            — the earned self-supervised context-predictive encoder (donkey=0)
  (2) REF MetricEncoder        — the numpy from-scratch triplet encoder (donkey=0, ~0.245-class)
  (3) wav2vec2 features        — pretrained, ISOLATED torch subprocess, EVAL-ONLY (NOT donkey=0)

All three: same words, same speakers, same pool order, same Rust DtwTo kernel
(`apc_recall_detail`), same cap_q / n_pos / n_neg. Report cross-speaker NN-recall + ROC-AUC + d'
WITH bootstrap CIs. THE DECISION: does wav2vec2 DOMINATE at this fair pool (gap real) or not
(gap collapses)?

★ ARCHITECTURE / donkey=0: the recall kernel is Rust; APC train = Rust `apc_train`; encode =
  `ApcEncode` graph Term. torch appears ONLY in the isolated `--extract-w2v` subprocess (eval-only,
  frozen wav2vec2 + MMS_FA word spans, same bootstrap discipline as the existing harness). The
  analysis process imports NO torch.

Run:
  # 1) isolated torch extraction of the test pool (coch + w2v layers + MMS_FA spans)
  PYTHONPATH=runners/dsl/python:.:scripts VENV_PY scripts/apc_fair_pool_falsification.py --extract-w2v
  # 2) torch-free fair scoring
  PYTHONPATH=runners/dsl/python:.:scripts VENV_PY scripts/apc_fair_pool_falsification.py

Env: TE_CAP(3000) KTEST(20) UTTS(12) CAPQ(300) NPOS(600) NNEG(1800) BOOT(2000)
     DH(96) KAHEAD(3) EPOCHS(18) LR(0.05) DZ(24) ME_EPOCHS(220) ME_CAP(6000) TRAIN_CAP(6000)
     W2V_LAYERS(6,9,12) W2V_PCA(64)
"""
from __future__ import annotations
import os, sys, glob, pickle, subprocess, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT, os.path.join(ROOT, "scripts")):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
import numpy as np
from collections import defaultdict

VENV_PY = "/home/matt/ozma/internal/research/.venv/bin/python"
LIBRI = "/home/matt/data/LibriSpeech"
TRAIN_TREE = os.path.join(LIBRI, "train-clean-100")
TEST_TREE = os.path.join(LIBRI, "dev-clean")
SCRATCH = os.environ.get(
    "SCRATCH",
    "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
    "3ed12bb3-7b58-44c0-b051-98640926c040/scratchpad")
os.makedirs(SCRATCH, exist_ok=True)
TRAIN_CACHE = os.path.join(SCRATCH, "apc_libri_uttframes.pkl")   # existing (train coch reused)
W2V_CACHE = os.path.join(SCRATCH, "apc_fair_test_w2v.pkl")       # fresh test pool (coch + w2v)

KTEST = int(os.environ.get("KTEST", "20"))
UTTS = int(os.environ.get("UTTS", "12"))
TE_CAP = int(os.environ.get("TE_CAP", "3000"))
T = 20
DH = int(os.environ.get("DH", "96"))
KAHEAD = int(os.environ.get("KAHEAD", "3"))
EPOCHS = int(os.environ.get("EPOCHS", "18"))
LR = float(os.environ.get("LR", "0.05"))
DZ = int(os.environ.get("DZ", "24"))
ME_EPOCHS = int(os.environ.get("ME_EPOCHS", "220"))
ME_CAP = int(os.environ.get("ME_CAP", "6000"))
TRAIN_CAP = int(os.environ.get("TRAIN_CAP", "6000"))
CAPQ = int(os.environ.get("CAPQ", "300"))
NPOS = int(os.environ.get("NPOS", "600"))
NNEG = int(os.environ.get("NNEG", "1800"))
BOOT = int(os.environ.get("BOOT", "2000"))
W2V_LAYERS = [int(x) for x in os.environ.get("W2V_LAYERS", "6,9,12").split(",") if x]
W2V_PCA = int(os.environ.get("W2V_PCA", "64"))
FPS = 100.0


# ============================================================================ #
#  ISOLATED torch extraction — TEST tree only: Rust cochleagram (donkey=0 ear) +
#  MMS_FA word spans (bootstrap-only) + FROZEN wav2vec2 layer features (eval-only).
#  Per utt: (coch[Tu,32]f16, wspans[(w,f0,f1) coch-frames], "test:spk",
#            {layer: w2v[Tw,768]f16}).
# ============================================================================ #
def _extract_w2v():
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
    import torch
    torch.set_num_threads(os.cpu_count() or 4)
    from torchaudio.pipelines import MMS_FA as FA, WAV2VEC2_BASE as W2V
    from scripts.librispeech_wer import load_flac
    from substrate_rs import _native as nat
    fam, tok, aln = FA.get_model(), FA.get_tokenizer(), FA.get_aligner()
    w2v = W2V.get_model()
    print(f"  [extract] wav2vec2 layers {W2V_LAYERS} (1-indexed); MMS_FA spans", flush=True)

    def transcripts(d):
        tr = {}
        for tf in glob.glob(os.path.join(d, "**", "*.trans.txt"), recursive=True):
            for line in open(tf):
                line = line.strip()
                if " " in line:
                    k, v = line.split(" ", 1); tr[k] = v
        return tr

    def align_utt(audio, fs, transcript):
        words = [re.sub(r"[^a-z]", "", w.lower()) for w in transcript.split()]
        keep = [(i, w) for i, w in enumerate(words) if w]
        if not keep:
            return []
        wav = torch.tensor(np.asarray(audio), dtype=torch.float32).unsqueeze(0)
        try:
            with torch.inference_mode():
                emission, _ = fam(wav)
                spans = aln(emission[0], tok([w for _i, w in keep]))
        except Exception:
            return []
        ratio = wav.size(1) / emission.size(1)
        return [(w, sp[0].start * ratio / fs, sp[-1].end * ratio / fs) for (_i, w), sp in zip(keep, spans)]

    out = []
    speakers = sorted(os.listdir(TEST_TREE))[:KTEST]
    for spk in speakers:
        tr = transcripts(os.path.join(TEST_TREE, spk))
        flacs = sorted(glob.glob(os.path.join(TEST_TREE, spk, "**", "*.flac"), recursive=True))[:UTTS]
        nutt = 0
        for f in flacs:
            base = os.path.basename(f)[:-5]
            if base not in tr:
                continue
            x, fs = load_flac(f); x = np.asarray(x, np.float32)
            dur = len(x) / fs
            nfr = max(4, int(round(dur * FPS)))
            spans = align_utt(x, fs, tr[base])
            if not spans:
                continue
            flat = nat.cochleagram(x, int(fs), 50.0, 80.0, nfr)
            coch = np.asarray(flat, np.float32).reshape(nfr, 32).astype(np.float16)
            wspans = []
            for (w, t0, t1) in spans:
                if not (w.isalpha() and len(w) >= 2 and (t1 - t0) >= 0.06):
                    continue
                f0 = max(0, int(t0 * FPS)); f1 = min(nfr, int(t1 * FPS))
                if f1 - f0 >= 3:
                    wspans.append((w, f0, f1))
            if not wspans:
                continue
            # frozen wav2vec2 layer features (whole utterance, 16 kHz)
            wav = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
            with torch.inference_mode():
                feats, _ = w2v.extract_features(wav)   # list of [1,Tw,768]
            wd = {L: feats[L - 1][0].numpy().astype(np.float16) for L in W2V_LAYERS}
            out.append((coch, wspans, f"test:{spk}", wd)); nutt += 1
        print(f"  [extract] {spk}: {nutt} utts (total {len(out)})", flush=True)
    pickle.dump(out, open(W2V_CACHE, "wb"))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
    ntok = sum(len(o[1]) for o in out)
    print(f"  [extract] wrote {len(out)} test utts / {ntok} word spans [peak {peak:.2f} GiB]", flush=True)


# ---------- features (numpy) ----------
def utt_feats(coch):
    coch = np.asarray(coch, np.float32)
    val = coch - coch.mean(0, keepdims=True)
    dlt = np.diff(coch, axis=0)
    dlt = np.vstack([np.zeros((1, coch.shape[1]), np.float32), dlt])
    return np.concatenate([val, dlt], axis=1).astype(np.float32)


def resample(fr, t):
    fr = np.asarray(fr, np.float32); n = len(fr)
    if n == t:
        return fr
    if n < 1:
        return np.zeros((t, fr.shape[1]), np.float32)
    idx = np.linspace(0, n - 1, t)
    lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, n - 1); f = (idx - lo)[:, None]
    return (fr[lo] * (1 - f) + fr[hi] * f).astype(np.float32)


def _traj(fr):
    return tuple(tuple(float(v) for v in row) for row in fr)


# ---------- bootstrap CI helpers over the detail arrays ----------
def _parse_detail(arr):
    arr = np.asarray(arr, np.float32); i = 0
    nh = int(arr[i]); i += 1; hits = arr[i:i + nh].copy(); i += nh
    npv = int(arr[i]); i += 1; pos = arr[i:i + npv].astype(np.float64); i += npv
    nnv = int(arr[i]); i += 1; neg = arr[i:i + nnv].astype(np.float64); i += nnv
    return hits, pos, neg


def _auc(pos, neg):
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    negs = np.sort(neg)
    # P(neg > pos): for each pos, count negs strictly greater + 0.5*ties
    gt = len(neg) - np.searchsorted(negs, pos, side="right")
    eq = np.searchsorted(negs, pos, side="right") - np.searchsorted(negs, pos, side="left")
    return float((gt.sum() + 0.5 * eq.sum()) / (len(pos) * len(neg)))


def _dprime(pos, neg):
    if len(pos) < 2 or len(neg) < 2:
        return float("nan")
    v = 0.5 * (pos.var() + neg.var())
    return float((neg.mean() - pos.mean()) / (np.sqrt(v) + 1e-9))


def ci_from_detail(arr, boot, seed=0):
    hits, pos, neg = _parse_detail(arr)
    rng = np.random.default_rng(seed)
    recall = float(hits.mean()) if len(hits) else float("nan")
    auc = _auc(pos, neg); dpr = _dprime(pos, neg)
    rboot, aboot, dboot = [], [], []
    nh, npv, nnv = len(hits), len(pos), len(neg)
    for _ in range(boot):
        if nh:
            rboot.append(hits[rng.integers(0, nh, nh)].mean())
        pb = pos[rng.integers(0, npv, npv)] if npv else pos
        nb = neg[rng.integers(0, nnv, nnv)] if nnv else neg
        aboot.append(_auc(pb, nb)); dboot.append(_dprime(pb, nb))
    def ci(v):
        v = np.asarray([x for x in v if not np.isnan(x)])
        if len(v) == 0:
            return (float("nan"), float("nan"))
        return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))
    return dict(recall=recall, recall_ci=ci(rboot), auc=auc, auc_ci=ci(aboot),
                dprime=dpr, dprime_ci=ci(dboot), n_query=nh, n_pos=npv, n_neg=nnv)


# ============================================================================ #
#  MAIN (torch-free)
# ============================================================================ #
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--extract-w2v":
        _extract_w2v(); return

    import resource
    resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
    from substrate_rs import _native as nat
    print(f"  [substrate_rs] {nat.__file__}", flush=True)
    assert hasattr(nat, "apc_recall_detail"), "apc_recall_detail missing — rebuild the crate"
    import scripts.jabberwock_contrastive_speaker_invariant as CI

    if not os.path.exists(W2V_CACHE):
        print("== isolated torch extraction of test pool (coch + w2v + spans) ==", flush=True)
        env = dict(os.environ, PYTHONPATH=f"runners/dsl/python:.:scripts:{os.environ.get('PYTHONPATH','')}")
        subprocess.run([VENV_PY, os.path.abspath(__file__), "--extract-w2v"], cwd=ROOT, env=env, check=True)

    # ---- TRAIN coch reused from the existing cache; TEST pool from the fresh w2v cache ----
    train_all = pickle.load(open(TRAIN_CACHE, "rb"))
    tr = [d for d in train_all if d[3] == "train"]
    te = pickle.load(open(W2V_CACHE, "rb"))   # list of (coch, wspans, "test:spk", w2v_dict)
    n_tr_spk = len(set(d[2] for d in tr)); n_te_spk = len(set(d[2] for d in te))
    print(f"\n  DATA: TRAIN {len(tr)} utts / {n_tr_spk} spk (train-clean-100) | "
          f"HELD-OUT TEST {len(te)} utts / {n_te_spk} spk (dev-clean); TE_CAP={TE_CAP}", flush=True)

    s = nat.Substrate()

    def apc_encode(model_list, seqf, out_len):
        term = {"type": "ApcEncode",
                "model": {"type": "Lit", "value": model_list},
                "seq": {"type": "Lit", "value": _traj(seqf)},
                "start": {"type": "Lit", "value": -1}, "end": {"type": "Lit", "value": -1},
                "out_len": {"type": "Lit", "value": out_len}}
        out = s.evaluate(term, {})
        return np.asarray([[float(v) for v in row] for row in out], np.float32)

    def znorm_fit(feats):
        stk = np.concatenate(feats); return stk.mean(0).astype(np.float32), (stk.std(0) + 1e-6).astype(np.float32)
    def znorm_apply(feats, mu, sd):
        return [((f - mu) / sd).astype(np.float32) for f in feats]

    # ---------------- (1) APC front-end (concat-lift BIDIR = the arc's best APC) ----------------
    LIFT_M = int(os.environ.get("LIFT_MODES", "16"))
    def lift_mag(coch):
        coch = np.asarray(coch, np.float32); nfr = coch.shape[0]
        m = np.asarray(nat.apc_lift(coch.reshape(-1).tolist(), nfr, 32, LIFT_M), np.float32)
        return m.reshape(nfr, LIFT_M)
    def concat_lift(feat, coch):
        m = lift_mag(coch)
        dl = np.diff(m, axis=0); dl = np.vstack([np.zeros((1, m.shape[1]), np.float32), dl])
        return np.concatenate([feat, m, dl], axis=1).astype(np.float32)

    tr_cl = [concat_lift(utt_feats(d[0]), d[0]) for d in tr]
    te_cl = [concat_lift(utt_feats(d[0]), d[0]) for d in te]
    mu_c, sd_c = znorm_fit(tr_cl)
    tr_cl = znorm_apply(tr_cl, mu_c, sd_c); te_cl = znorm_apply(te_cl, mu_c, sd_c)

    def train_apc(feats, bidir):
        ff = np.concatenate([f.reshape(-1) for f in feats]).astype(np.float32)
        lens = [int(f.shape[0]) for f in feats]; din = feats[0].shape[1]
        return [float(v) for v in nat.apc_train(ff.tolist(), lens, din, DH, KAHEAD, EPOCHS, LR, True, 0, False)]
    print(f"\n--- training APC (Rust apc_train, concat-lift BIDIR din={tr_cl[0].shape[1]} dh={DH}) ---", flush=True)
    ml = train_apc(tr_cl, bidir=True)

    # ---------------- (2) REF MetricEncoder (numpy triplet) ----------------
    def word_feat(coch, f0, f1):
        return CI.frame_features(np.asarray(coch, np.float32)[f0:f1])
    tr_wf, tr_ww, tr_ws = [], [], []
    for d in tr:
        for (w, f0, f1) in d[1]:
            tr_wf.append(word_feat(d[0], f0, f1)); tr_ww.append(w); tr_ws.append(d[2])
    if len(tr_wf) > ME_CAP:
        ridx = np.random.default_rng(0).choice(len(tr_wf), ME_CAP, replace=False)
        tr_wf = [tr_wf[i] for i in ridx]; tr_ww = [tr_ww[i] for i in ridx]; tr_ws = [tr_ws[i] for i in ridx]
    mu_w, sd_w = znorm_fit(tr_wf); tr_wf = znorm_apply(tr_wf, mu_w, sd_w)
    din_w = tr_wf[0].shape[1]
    print(f"--- training REF MetricEncoder (numpy, din={din_w} dz={DZ}) on {len(tr_wf)} train words ---", flush=True)
    ref_enc = CI.MetricEncoder(din_w, DZ, seed=0).fit(tr_wf, tr_ww, tr_ws, ME_EPOCHS, verbose=False)

    # ---------------- (3) wav2vec2 PCA fit (per layer) on test frames, dim reduce ----------------
    def fit_pca(layerkey, cap=20000):
        frames = []
        for d in te:
            f = np.asarray(d[3][layerkey], np.float32)
            f = f - f.mean(0, keepdims=True)          # per-utt CMN (fair, standard)
            frames.append(f)
        X = np.concatenate(frames, axis=0)
        if len(X) > cap:
            X = X[np.random.default_rng(0).choice(len(X), cap, replace=False)]
        mu = X.mean(0); Xc = X - mu
        # SVD for top-k principal directions
        U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
        k = min(W2V_PCA, Vt.shape[0])
        var_ret = float((S[:k] ** 2).sum() / (S ** 2).sum())
        return mu.astype(np.float32), Vt[:k].astype(np.float32), var_ret
    pca = {}
    for L in W2V_LAYERS:
        mu, V, vr = fit_pca(L)
        pca[L] = (mu, V, vr)
        print(f"  [w2v PCA] layer {L}: 768->{V.shape[0]} dims, var retained {vr:.3f}", flush=True)

    # ---------------- build the ONE shared held-out pool (identical order) ----------------
    words, spk = [], []
    R = {"APC (donkey=0)": [], "REF MetricEncoder (donkey=0)": []}
    for L in W2V_LAYERS:
        R[f"wav2vec2 L{L}"] = []
    ntok = 0
    for ui, d in enumerate(te):
        coch, wspans, sp, wd = d
        coch = np.asarray(coch, np.float32)
        Tu = coch.shape[0]
        h = apc_encode(ml, te_cl[ui], te_cl[ui].shape[0])
        # per-layer w2v arrays (per-utt CMN)
        w2v_arr = {}
        for L in W2V_LAYERS:
            f = np.asarray(wd[L], np.float32); f = f - f.mean(0, keepdims=True)
            mu, V, _ = pca[L]
            w2v_arr[L] = ((f - mu) @ V.T).astype(np.float32)   # [Tw, k]
        for (w, f0, f1) in wspans:
            if ntok >= TE_CAP:
                break
            words.append(w); spk.append(sp)
            R["APC (donkey=0)"].append(resample(h[f0:f1], T))
            R["REF MetricEncoder (donkey=0)"].append(
                ref_enc.encode(znorm_apply([word_feat(coch, f0, f1)], mu_w, sd_w)[0]))
            for L in W2V_LAYERS:
                Tw = w2v_arr[L].shape[0]
                g0 = int(round(f0 * Tw / max(1, Tu))); g1 = max(g0 + 1, int(round(f1 * Tw / max(1, Tu))))
                g1 = min(g1, Tw)
                R[f"wav2vec2 L{L}"].append(resample(w2v_arr[L][g0:g1], T))
            ntok += 1
        if ntok >= TE_CAP:
            break
    print(f"\n  POOL: {ntok} held-out word tokens, {len(set(spk))} speakers, "
          f"{len(set(words))} distinct words (IDENTICAL for all reps)", flush=True)

    # ---------------- score all reps through the identical Rust kernel + bootstrap CIs ----------------
    _wi, _si = {}, {}
    wi = np.array([_wi.setdefault(x, len(_wi)) for x in words], np.int64)
    si = np.array([_si.setdefault(x, len(_si)) for x in spk], np.int64)

    def score(name, arr):
        arr = np.asarray(arr, np.float32); n = arr.shape[0]; dim = arr.shape[2]
        det = nat.apc_recall_detail(arr.reshape(-1).tolist(), n, T, dim, wi.tolist(), si.tolist(),
                                    CAPQ, NPOS, NNEG, 0)
        r = ci_from_detail(det, BOOT)
        print(f"  {name:>30}  dim={dim:4d}  recall {r['recall']:.3f} "
              f"[{r['recall_ci'][0]:.3f},{r['recall_ci'][1]:.3f}]  "
              f"AUC {r['auc']:.3f} [{r['auc_ci'][0]:.3f},{r['auc_ci'][1]:.3f}]  "
              f"d' {r['dprime']:.2f} [{r['dprime_ci'][0]:.2f},{r['dprime_ci'][1]:.2f}]  "
              f"(nq={r['n_query']})", flush=True)
        return r

    print(f"\n--- ★ FAIR-POOL cross-speaker NN-recall + ROC-AUC + d' (cap_q={CAPQ}, "
          f"n_pos={NPOS}, n_neg={NNEG}, boot={BOOT}) ---")
    print(f"  {'representation':>30}  {'':>4}  NN-recall [95% CI]         ROC-AUC [95% CI]        d' [95% CI]")
    res = {}
    res["apc"] = score("APC (donkey=0)", R["APC (donkey=0)"])
    res["ref"] = score("REF MetricEncoder (donkey=0)", R["REF MetricEncoder (donkey=0)"])
    w2v_best_L, w2v_best = None, None
    for L in W2V_LAYERS:
        r = score(f"wav2vec2 L{L} (torch, eval-only)", R[f"wav2vec2 L{L}"])
        res[f"w2v_L{L}"] = r
        if w2v_best is None or r["recall"] > w2v_best["recall"]:
            w2v_best, w2v_best_L = r, L

    # ---------------- donkey=0 ----------------
    donkey = [mn for mn in ("torch", "torchaudio", "allosaurus", "faster_whisper") if mn in sys.modules]
    print(f"\n--- donkey=0 AT INFERENCE: torch/... in analyze sys.modules: {donkey or 'NONE'} ---")

    # ---------------- VERDICT ----------------
    best_d0 = max(res["apc"]["recall"], res["ref"]["recall"])
    best_d0_name = "APC" if res["apc"]["recall"] >= res["ref"]["recall"] else "REF"
    w2v_lo, w2v_hi = w2v_best["recall_ci"]
    d0_best_r = res["apc"] if best_d0_name == "APC" else res["ref"]
    d0_lo, d0_hi = d0_best_r["recall_ci"]
    dominates = w2v_lo > d0_hi          # w2v recall CI strictly above best donkey=0 recall CI
    print("\n" + "=" * 96)
    print(f"  ★★★ FAIR POOL ({ntok} tokens, {len(set(spk))} held-out spk): best wav2vec2 = L{w2v_best_L} "
          f"recall {w2v_best['recall']:.3f} [{w2v_lo:.3f},{w2v_hi:.3f}]")
    print(f"      best donkey=0 = {best_d0_name} recall {best_d0:.3f} [{d0_lo:.3f},{d0_hi:.3f}]")
    print(f"      gap (w2v - best donkey=0) = {w2v_best['recall'] - best_d0:+.3f}")
    print(f"  ★★★ DOES wav2vec2 DOMINATE (CIs non-overlapping)?  {'YES — gap is REAL' if dominates else 'NO — gap collapses / CIs overlap'}")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
    print(f"  [memory] peak RSS this process: {peak:.2f} GiB")
    print("=" * 96)


if __name__ == "__main__":
    main()
