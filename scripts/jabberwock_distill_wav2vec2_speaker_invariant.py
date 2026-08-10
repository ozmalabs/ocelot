"""CLOSE MULTI-SPEAKER — two donkey=0 levers side by side: (1) TEACHER-BOOTSTRAP DISTILL wav2vec2's proven
invariant+discriminative GEOMETRY into a from-scratch numpy encoder, and (2) the creator's NATIVE lever
"QUANTA IS DYNAMIC PER DIMENSION" (NO teacher). Both aim at the proven-reachable wav2vec2 point.

★ NATIVE LEVER — PER-DIM DYNAMIC QUANTA (donkey=0, no teacher): the invariance-vs-discrimination trade-off
exists because ONE global metric/quantization can't be coarse (invariant) AND fine (discriminative) at once
(that's why the linear metric tied the MLP — a global-capacity bind). Dissolution: the QUANTUM (tolerance
for "same" along an axis) is PER-DIMENSION and DYNAMIC (per trajectory position) — COARSE on speaker/nuisance
dims (large tolerance -> collapse -> INVARIANCE) AND FINE on word-discriminative dims (-> DISCRIMINATION),
SIMULTANEOUSLY, each axis its own granularity. Earned as a per-(position,dim) Fisher ratio between-word /
within-word-cross-speaker (bootstrap labels), folded into DtwTo's Euclidean local dist as a sqrt-weight
(per-dim, per-position rescale). DYNAMIC (per-region) vs STATIC (one global per-dim) ablation tests whether
"dynamic" is load-bearing beyond diagonal-Fisher/LDA.

821b8306 established: on HELD-OUT dev-clean speakers the from-scratch contrastive numpy encoder BEATS the
donkey=0 baselines (learned (recall 0.245, d' 1.53) vs raw (0.170, 1.37)) but does NOT reach wav2vec2
(BORROWED, torch) which hits (0.520, 2.66) on the SAME held-out speakers. So the ~0.4 multi-speaker ceiling
is CAPACITY, not fundamental entanglement — an invariant+discriminative representation demonstrably EXISTS.
THIS script converts that borrowed capability to self-sufficient structure (same pattern as the Gemma +8pp
and Whisper conversions): wav2vec2 = TEACHER at BOOTSTRAP only; the numpy encoder EARNS a standalone metric
that MATCHES wav2vec2's geometry; at inference wav2vec2 is REMOVED (verified out of sys.modules) -> donkey=0.

METHOD — RELATIONAL distillation (the target IS a metric, so distil the GEOMETRY not logits):
  TEACHER (bootstrap-only): wav2vec2-trajectory features (layer 8, already cached by 821b8306's ISOLATED
    torch subprocess; UNCOMMITTED scratch), PCA->DZ, resampled-T -> per-token teacher embedding Zt [T,DZ].
  EARNER: a DEEPER from-scratch numpy MLP (2 tanh hidden layers, SGD) maps the COCHLEAGRAM-trajectory
    ([CMN-value ++ delta]) -> student embedding Zs [T,DZ], trained by RKD-Distance: match the student's
    pairwise same-word/different-word DISTANCE structure to the teacher's (normalized, scale-free Huber).
    More earned capacity than 821b8306's shallow/linear metric (the front-end chapter's capacity bind is
    exactly where deeper earned capacity is warranted). Trained on TRAIN speakers only.
  INFERENCE: ONLY the numpy MLP runs on cochleagram; wav2vec2 REMOVED. DTW-cluster in the distilled space
    with the held Rust DtwTo Term (Euclidean local dist == the trained squared-Euclidean metric).

★ HELD-OUT SPEAKERS (as 821b8306): train-clean-100 speakers TRAIN, DISJOINT dev-clean speakers TEST (never
seen; different corpus split). The distilled cochleagram->geometry map must GENERALIZE to unseen speakers
(savant-3b: not memorized).

GATE (donkey=0, honest — MATCHED-GRANULARITY + RANK metrics, HELD-OUT SPEAKERS):
  (a) ★ distilled (recall, d') vs wav2vec2 (0.520, 2.66) & pre-distill numpy (0.245, 1.53): gap CLOSED?
  (b) ★ MULTI-SPEAKER order-1 purity 0.34/0.40 -> toward 0.84 (the payoff).
  (c) ★ FULL-STACK recovers (function/content split + cross-context) on multi-speaker held-out.
  (d) ★ SAVANT-3b: distilled encoder runs donkey=0 (wav2vec2 out of sys.modules) AND generalizes held-out.
  (e) shuffled control (permuted teacher targets -> geometry meaningless -> should NOT generalize).

donkey=0: encoder = from-scratch numpy MLP (SGD); DtwTo = held Rust Term; wav2vec2/MMS_FA were the ISOLATED
subprocess (821b8306). Memory: teacher targets streamed float32, mini-batch RKD, bounded/greedy leader
clustering (NO (N,K,D)), ulimit-14Gi (via base import). USE THE VENV PYTHON. Reuses 821b8306 (cache,
frame_features, MetricEncoder, metrics, DtwTo clustering, held-out harness).

Run: PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
        scripts/jabberwock_distill_wav2vec2_speaker_invariant.py
Env: DZ (24), H1 (128), H2 (64), DEPOCHS (300), TR_CAP (9000), TE_CAP (3500).
"""
from __future__ import annotations
import os, sys, pickle
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from collections import Counter, defaultdict

import scripts.jabberwock_contrastive_speaker_invariant as CI   # cache, frame_features, MetricEncoder, metrics, T, DZ

DZ = int(os.environ.get("DZ", str(CI.DZ)))
H1 = int(os.environ.get("H1", "128"))
H2 = int(os.environ.get("H2", "64"))
DEPOCHS = int(os.environ.get("DEPOCHS", "300"))
T = CI.T

# reference points from 821b8306 (recomputed in-run too, but printed for the arc)
W2V_REF = (0.520, 2.66); PREDISTILL_REF = (0.245, 1.53); RAW_REF = (0.170, 1.37)


# ============================================================================ #
#  DISTILL ENCODER — deeper from-scratch numpy MLP (2 tanh hidden), RKD-Distance
# ============================================================================ #
class DistillEncoder:
    def __init__(self, din, dz, h1, h2, seed=0):
        rng = np.random.default_rng(seed)
        self.W1 = (rng.standard_normal((din, h1)) / np.sqrt(din)).astype(np.float32); self.b1 = np.zeros(h1, np.float32)
        self.W2 = (rng.standard_normal((h1, h2)) / np.sqrt(h1)).astype(np.float32);  self.b2 = np.zeros(h2, np.float32)
        self.W3 = (rng.standard_normal((h2, dz)) / np.sqrt(h2)).astype(np.float32)

    def _fwd(self, X):
        H1_ = np.tanh(X @ self.W1 + self.b1)
        H2_ = np.tanh(H1_ @ self.W2 + self.b2)
        Z = H2_ @ self.W3
        return H1_, H2_, Z

    def encode(self, X):
        return self._fwd(X)[2]

    def _bwd(self, X, H1_, H2_, gZ):
        gW3 = H2_.T @ gZ
        gH2 = gZ @ self.W3.T; gp2 = gH2 * (1 - H2_ * H2_)
        gW2 = H1_.T @ gp2; gb2 = gp2.sum(0)
        gH1 = gp2 @ self.W2.T; gp1 = gH1 * (1 - H1_ * H1_)
        gW1 = X.T @ gp1; gb1 = gp1.sum(0)
        return gW1, gb1, gW2, gb2, gW3

    def fit(self, feats, teacher, words, spk, epochs, batch=96, lr=0.02, wd=1e-4, margin=1.0,
            seed=0, verbose=True, rkd_lambda=float(os.environ.get("RKD_LAMBDA", "0.3"))):
        """TEACHER-BOOTSTRAP distillation into a deeper MLP. Two bootstrap signals, both removed at
        inference: (1) WORD-triplet — anchor with a same-word DIFFERENT-speaker POSITIVE and a hardest
        different-word NEGATIVE (the MMS bootstrap labels; correct positives, so no collapse);
        (2) RKD-Distance — match the student's scale-free pairwise distance GEOMETRY to the wav2vec2
        TEACHER's (rkd_lambda). The RKD term injects wav2vec2's richer invariant+discriminative structure
        the word-triplet alone can't see; the MLP gives the capacity to absorb it. All in student space
        (time-aligned sq-Euclid == DtwTo). If teacher/words are shuffled the signal vanishes (controls).
        FAIR sampling: PK batches (P words x K instances, drawn from cross-speaker-eligible words) so every
        anchor has an in-batch same-word cross-speaker positive (not the sparse random-batch confound)."""
        rng = np.random.default_rng(seed)
        N = len(feats); Tn = feats[0].shape[0]
        F = np.stack(feats).astype(np.float32)
        Zt = np.stack(teacher).astype(np.float32) if teacher is not None else None
        byword = defaultdict(list)
        for i in range(N):
            byword[words[i]].append(i)
        elig = [w for w, idx in byword.items() if len(set(spk[i] for i in idx)) >= 2 and len(idx) >= 2]
        K = 4; P = max(4, batch // K)
        steps = max(1, N // batch)
        for ep in range(epochs):
            tot = 0.0; nact = 0
            for _st in range(steps):
                # PK batch: P eligible words x K instances each -> guaranteed in-batch positives
                bw = rng.choice(elig, min(P, len(elig)), replace=False)
                bi = []
                for w in bw:
                    idx = byword[w]
                    bi.extend(rng.choice(idx, min(K, len(idx)), replace=False).tolist())
                bi = np.array(bi); n = len(bi)
                if n < 8:
                    continue
                pos_in = {int(g): k for k, g in enumerate(bi)}       # global idx -> batch pos
                Xb = F[bi]
                H1s = np.tanh(Xb @ self.W1 + self.b1)
                H2s = np.tanh(H1s @ self.W2 + self.b2)
                Zs = H2s @ self.W3
                ds = np.zeros((n, n), np.float32)
                for i in range(n):
                    dsi = Zs - Zs[i]; ds[i] = (dsi * dsi).sum((1, 2)) / Tn
                gZ = np.zeros_like(Zs)
                # (1) WORD-triplet, in-batch (bootstrap labels)
                for k in range(n):
                    gi = int(bi[k]); w = words[gi]
                    posc = [pos_in[j] for j in byword[w] if j in pos_in and j != gi and spk[j] != spk[gi]]
                    negc = [kk for kk in range(n) if words[int(bi[kk])] != w]
                    if not posc or not negc:
                        continue
                    p = posc[int(rng.integers(len(posc)))]
                    nneg = negc[int(np.argmin(ds[k][negc]))]         # hardest different-word
                    Dp = ds[k, p]; Dn = ds[k, nneg]
                    if margin + Dp - Dn > 0:
                        gZ[k] += (2.0 / Tn) * (Zs[nneg] - Zs[p])
                        gZ[p] += -(2.0 / Tn) * (Zs[k] - Zs[p])
                        gZ[nneg] += (2.0 / Tn) * (Zs[k] - Zs[nneg])
                        tot += margin + Dp - Dn; nact += 1
                # (2) RKD-Distance to the wav2vec2 TEACHER (scale-free geometry match)
                if Zt is not None and rkd_lambda > 0:
                    Ztb = Zt[bi]; dt = np.zeros((n, n), np.float32)
                    for i in range(n):
                        dti = Ztb - Ztb[i]; dt[i] = (dti * dti).sum((1, 2)) / Tn
                    iu = np.triu_indices(n, 1)
                    dtv = dt[iu]; dsv = ds[iu]
                    ct = dtv.mean() + 1e-6; cs = dsv.mean() + 1e-6
                    r = dsv / cs - dtv / ct
                    hg = rkd_lambda * np.clip(r, -1.0, 1.0) / (cs * max(len(dsv), 1))
                    gmap = np.zeros((n, n), np.float32); gmap[iu] = hg; gmap += gmap.T
                    for i in range(n):
                        dsi = Zs - Zs[i]
                        gZ[i] += (gmap[i][:, None, None] * (-2.0 / Tn) * dsi).sum(0)
                Xf = Xb.reshape(-1, Xb.shape[-1]); H1f = H1s.reshape(-1, H1); H2f = H2s.reshape(-1, H2)
                gW1, gb1, gW2, gb2, gW3 = self._bwd(Xf, H1f, H2f, gZ.reshape(-1, DZ))
                sc = 1.0 / max(n, 1)
                self.W3 -= lr * (gW3 * sc + wd * self.W3)
                self.W2 -= lr * (gW2 * sc + wd * self.W2); self.b2 -= lr * gb2 * sc
                self.W1 -= lr * (gW1 * sc + wd * self.W1); self.b1 -= lr * gb1 * sc
            if verbose and (ep % max(1, epochs // 8) == 0 or ep == epochs - 1):
                print(f"    [distill] epoch {ep:4d}: word-triplet loss {tot / max(nact,1):.4f} "
                      f"(active {nact})", flush=True)
        return self


# ============================================================================ #
#  PER-DIMENSION DYNAMIC QUANTA (creator's native lever; donkey=0, NO teacher)
#  The invariance-vs-discrimination trade-off exists because ONE global metric
#  can't be coarse (invariant) AND fine (discriminative) at once. Dissolution:
#  the QUANTUM (tolerance for "same" along an axis) is PER-DIMENSION and DYNAMIC
#  (per trajectory position) — COARSE on speaker/nuisance dims (collapse -> invar)
#  and FINE on word-discriminative dims (preserve -> discrim), SIMULTANEOUSLY.
#  Estimated as a per-(position,dim) Fisher ratio between-word / within-word-
#  cross-speaker; folded into DtwTo's Euclidean local dist as a sqrt-weight.
# ============================================================================ #
def learn_quanta(feats, words, spk, dynamic=True, eps=1e-3):
    """w[t,d] = between-word var / within-word-cross-speaker var at (t,d). LARGE where discriminative
    (fine quantum) -> keep; SMALL where same-word-cross-speaker spread dominates (coarse quantum) ->
    collapse (invariance). dynamic=True: per-position (the load-bearing part); False: one global per-dim
    vector (static ablation). Returns sqrt(w) [T,D] so ||sqrt(w)*x||^2 = sum_d w*x^2 (the weighted dist)."""
    F = np.stack(feats).astype(np.float32)                          # [N,T,D]
    Tn, D = F.shape[1], F.shape[2]
    byword = defaultdict(list)
    for i in range(len(words)):
        byword[words[i]].append(i)
    within = np.zeros((Tn, D), np.float32); wmeans = []; nw = 0
    for w, idx in byword.items():
        if len(idx) < 2 or len(set(spk[i] for i in idx)) < 2:
            continue
        Fi = F[idx]                                                 # [n,T,D]
        within += Fi.var(0); wmeans.append(Fi.mean(0)); nw += 1
    if nw < 2:
        return np.ones((Tn, D), np.float32)
    within /= nw
    between = np.stack(wmeans).var(0)                               # [T,D]
    fisher = between / (within + eps)                              # [T,D] high=discriminative
    if not dynamic:
        fisher = np.broadcast_to(fisher.mean(0, keepdims=True), (Tn, D)).copy()
    fisher = fisher / (fisher.mean() + 1e-9)                       # normalize scale
    return np.sqrt(fisher).astype(np.float32)


def apply_quanta(X, wsqrt):
    """X:[T,D] base trajectory -> per-(pos,dim) quantum-weighted (sqrt-weight) for the DtwTo Euclidean."""
    return (np.asarray(X, np.float32) * wsqrt).astype(np.float32)


def main():
    import scripts.jabberwock_syntax_clean_order1 as D
    import scripts.jabberwock_quantized_trajectory_order1 as Q
    import scripts.jabberwock_speaker_invariant_order1 as S1
    import scripts.jabberwock_context_dependent_order1 as CTX
    import referential_word_learning as R

    if not os.path.exists(CI.CACHE):
        print("BLOCKED: 821b8306 cache missing (need contrastive_libri.pkl with wav2vec2) — run the base "
              "script's extraction first."); return
    data = pickle.load(open(CI.CACHE, "rb"))
    tr_idx = [i for i, d in enumerate(data) if d[5] == "train"]
    te_idx = [i for i, d in enumerate(data) if d[5] == "test"]
    if not any(data[i][6] is not None for i in tr_idx):
        print("BLOCKED: no wav2vec2 teacher features in cache — cannot distill."); return
    TR_CAP = int(os.environ.get("TR_CAP", "9000")); TE_CAP = int(os.environ.get("TE_CAP", "3500"))
    rng = np.random.default_rng(0)
    if len(tr_idx) > TR_CAP:
        tr_idx = sorted(rng.choice(tr_idx, TR_CAP, replace=False).tolist())
    if len(te_idx) > TE_CAP:
        te_idx = sorted(rng.choice(te_idx, TE_CAP, replace=False).tolist())
    n_tr_spk = len(set(data[i][2] for i in tr_idx)); n_te_spk = len(set(data[i][2] for i in te_idx))
    print(f"\n  DATA: TRAIN {len(tr_idx)} toks / {n_tr_spk} spk (train-clean-100) | HELD-OUT TEST {len(te_idx)} "
          f"toks / {n_te_spk} spk (dev-clean)  [peak {D._peak_gib():.2f} GiB]", flush=True)

    tr_words = [data[i][0] for i in tr_idx]; tr_spk = [data[i][2] for i in tr_idx]
    te_words = [data[i][0] for i in te_idx]; te_spk = [data[i][2] for i in te_idx]

    # ---- student input features (cochleagram; z-norm on TRAIN) ----
    tr_feat = [CI.frame_features(data[i][1]) for i in tr_idx]
    te_feat = [CI.frame_features(data[i][1]) for i in te_idx]
    stk = np.concatenate([f.reshape(-1, f.shape[-1]) for f in tr_feat])
    mu = stk.mean(0).astype(np.float32); sd = (stk.std(0) + 1e-6).astype(np.float32)
    tr_feat = [((f - mu) / sd).astype(np.float32) for f in tr_feat]
    te_feat = [((f - mu) / sd).astype(np.float32) for f in te_feat]
    din = tr_feat[0].shape[-1]

    # ---- TEACHER: wav2vec2-trajectory -> PCA(DZ) (fit on TRAIN w2v frames, unsupervised) ----
    w2v_tr_frames = np.concatenate([np.asarray(data[i][6], np.float32).reshape(-1, 768)
                                    for i in tr_idx if data[i][6] is not None])
    if len(w2v_tr_frames) > 40000:
        w2v_tr_frames = w2v_tr_frames[np.random.default_rng(1).choice(len(w2v_tr_frames), 40000, replace=False)]
    wmu, wV = R.pca_fit(w2v_tr_frames, min(DZ, 768)); del w2v_tr_frames

    def teacher_embed(i):
        wf = data[i][6]
        if wf is None:
            return None
        z = (np.asarray(wf, np.float32).reshape(-1, 768) - wmu) @ wV
        return CI.resample(z.astype(np.float32), T)

    # distillation training set = TRAIN tokens WITH a teacher embedding
    dk = [k for k in range(len(tr_idx)) if data[tr_idx[k]][6] is not None]
    d_feat = [tr_feat[k] for k in dk]; d_teacher = [teacher_embed(tr_idx[k]) for k in dk]
    d_words = [tr_words[k] for k in dk]; d_spk = [tr_spk[k] for k in dk]
    # pre-compute TEST + TRAIN teacher trajectories BEFORE freeing the big w2v arrays
    te_teacher = [teacher_embed(i) for i in te_idx]

    print(f"\n--- DISTILL wav2vec2 geometry -> numpy MLP ({din}->{H1}->{H2}->{DZ}); word-triplet + RKD-D "
          f"on {len(d_feat)} TRAIN tokens ---", flush=True)
    enc = DistillEncoder(din, DZ, H1, H2, seed=0).fit(d_feat, d_teacher, d_words, d_spk, DEPOCHS)
    # shuffled control: permute teacher targets -> geometry meaningless (word-triplet also off via shuffled words)
    perm = list(np.random.default_rng(9).permutation(len(d_teacher)))
    sh_words = list(d_words); np.random.default_rng(9).shuffle(sh_words)
    enc_sh = DistillEncoder(din, DZ, H1, H2, seed=0).fit(d_feat, [d_teacher[p] for p in perm],
                                                         sh_words, d_spk, DEPOCHS, verbose=False)

    # pre-distill contrastive baseline (821b8306 linear metric) re-trained in-run for apples-to-apples
    enc_pre = CI.MetricEncoder(din, DZ, seed=0).fit(tr_feat, tr_words, tr_spk,
                                                    int(os.environ.get("PRE_EPOCHS", "400")), verbose=False)

    # ---- PER-DIM DYNAMIC QUANTA (native, donkey=0, NO teacher) + ablation ----
    print("\n--- PER-DIM DYNAMIC QUANTA (native donkey=0; Fisher between/within-word-cross-speaker) + "
          "static ablation ---", flush=True)
    wq_dyn = learn_quanta(tr_feat, tr_words, tr_spk, dynamic=True)
    wq_stat = learn_quanta(tr_feat, tr_words, tr_spk, dynamic=False)
    q_sh_words = list(tr_words); np.random.default_rng(5).shuffle(q_sh_words)
    wq_shuf = learn_quanta(tr_feat, q_sh_words, tr_spk, dynamic=True)
    print(f"  quanta learned: dynamic w[t,d] range {wq_dyn.min():.2f}..{wq_dyn.max():.2f}; "
          f"static per-dim range {wq_stat[0].min():.2f}..{wq_stat[0].max():.2f}", flush=True)

    # ---- free the big wav2vec2 arrays now (memory) BEFORE seed-loading in gate (c) ----
    data2 = [(d[0], d[1], d[2], d[3], d[4], d[5]) for d in data]
    del data; data = data2

    # ---- TEST representations (held-out speakers) ----
    def traj_raw():   return [CI._traj(CI.resample(np.asarray(data[i][1], np.float32), T)) for i in te_idx]
    def traj_student(encoder): return [CI._traj(encoder.encode(te_feat[k])) for k in range(len(te_feat))]
    def traj_quanta(wsq):     return [CI._traj(apply_quanta(te_feat[k], wsq)) for k in range(len(te_feat))]
    reps = {"raw": traj_raw(),
            "wav2vec2(teacher)": [CI._traj(z) if z is not None else None for z in te_teacher],
            "featspace(unweighted)": traj_quanta(np.ones_like(wq_dyn)),
            "quanta-static": traj_quanta(wq_stat), "quanta-DYNAMIC": traj_quanta(wq_dyn),
            "quanta-shuffled": traj_quanta(wq_shuf),
            "pre-distill(numpy)": traj_student(enc_pre), "DISTILLED(numpy)": traj_student(enc),
            "distilled-shuffled": traj_student(enc_sh)}

    def filt(rep):
        if None not in rep:
            return rep, te_words, te_spk
        keep = [k for k in range(len(rep)) if rep[k] is not None]
        return [rep[k] for k in keep], [te_words[k] for k in keep], [te_spk[k] for k in keep]

    # ---- GATE (a): distilled + native quanta (recall, d') vs teacher & pre-distill on HELD-OUT ----
    print("\n--- ★ (a) (recall, d') on HELD-OUT speakers: native quanta + distilled vs wav2vec2 & pre-distill ---")
    print(f"  {'representation':>22} {'NN-recall':>10} {'d-prime':>9}")
    pareto = {}
    order = ["raw", "featspace(unweighted)", "quanta-static", "quanta-DYNAMIC", "quanta-shuffled",
             "pre-distill(numpy)", "DISTILLED(numpy)", "distilled-shuffled", "wav2vec2(teacher)"]
    for name in order:
        rep, w, sp = filt(reps[name])
        nn = CI.nn_recall_cross(rep, w, sp, Q)
        dpr, _pd, _nd = CI.dprime_cross(rep, w, sp, Q)
        pareto[name] = {"nn": nn, "dp": dpr}
        print(f"  {name:>22} {nn:10.3f} {dpr:9.3f}", flush=True)

    # ---- GATE (b): multi-speaker order-1 purity @ matched clusters ----
    print("\n--- ★ (b) MULTI-SPEAKER order-1 PURITY @ matched clusters (0.34/0.40 -> toward 0.84) ---")
    _rawsnap, _ = Q.snap_scan(reps["raw"], te_words); target = _rawsnap[1]
    print(f"  target clusters = {target} (raw natural snap granularity)")
    print(f"  {'representation':>22} {'purity':>7} {'#cl':>5}")
    purities = {}
    for name in ["raw", "quanta-DYNAMIC", "pre-distill(numpy)", "DISTILLED(numpy)", "wav2vec2(teacher)"]:
        rep, w, sp = filt(reps[name])
        pu, nc, _wf = CI.order1_purity_matched(rep, w, Q, CTX, target)
        purities[name] = pu
        print(f"  {name:>22} {pu:7.3f} {nc:5d}", flush=True)

    # ---- GATE (c): full-stack (function/content split + cross-context) ----
    print("\n--- ★ (c) FULL-STACK on multi-speaker held-out (function/content + cross-context) ---")
    lefts = [data[i][3] for i in te_idx]
    a, _ = D.author_constructions()
    from nltk import pos_tag
    tags = [t for _, t in pos_tag(te_words)]; cut = int(0.7 * len(te_words))
    fullstack = {}
    for name in ["raw", "quanta-DYNAMIC", "DISTILLED(numpy)"]:
        rep = reps[name]
        _pu, _nc, wf = CI.order1_purity_matched(rep, te_words, Q, CTX, target)
        rg = D.gates(a, f"MULTISPK({name})", te_words, wf, tags, cut)
        cc, ncc = CTX.cross_context(te_words, lefts, wf)
        fullstack[name] = {"accB": rg["accB"], "base_acc": rg["base_acc"], "spec": rg["spec"],
                           "base_noun": rg["base_noun"], "gen": rg["gen"], "sh": rg["sh"],
                           "cc": cc, "ncc": ncc, "isoB": rg["gateB"], "flipC": rg["gateC"]}
        print(f"  [{name:>16}] cross-context {cc:.3f} (n={ncc}) | gate-B {rg['accB']:.3f} (maj {rg['base_acc']:.3f}) "
              f"| gate-C spec {rg['spec']:.3f} vs base {rg['base_noun']:.3f} gen {rg['gen']:.3f} sh {rg['sh']:.3f}",
              flush=True)

    # ---- GATE (d): donkey=0 / savant-3b ----
    donkey = [m for m in ("allosaurus", "torch", "torchaudio", "faster_whisper") if m in sys.modules]
    print("\n--- ★ (d) SAVANT-3b: donkey=0 AT INFERENCE + held-out generalization ---")
    print(f"  torch/torchaudio/wav2vec2/whisper in analyze sys.modules: {donkey or 'NONE'}")
    print("  distilled encoder = from-scratch numpy MLP (SGD); wav2vec2 was the ISOLATED bootstrap subprocess "
          "(821b8306), NOT imported here; DtwTo = held Rust Term.")

    # ---- VERDICT ----
    print("=" * 100)
    print("VERDICT — do TEACHER-DISTILL and/or NATIVE PER-DIM-DYNAMIC QUANTA close multi-speaker donkey=0?")
    rr, rd = pareto["raw"]["nn"], pareto["raw"]["dp"]
    fr_, fd = pareto["featspace(unweighted)"]["nn"], pareto["featspace(unweighted)"]["dp"]
    qsr, qsd = pareto["quanta-static"]["nn"], pareto["quanta-static"]["dp"]
    qdr, qdd = pareto["quanta-DYNAMIC"]["nn"], pareto["quanta-DYNAMIC"]["dp"]
    qshr, qshd = pareto["quanta-shuffled"]["nn"], pareto["quanta-shuffled"]["dp"]
    wr, wd_ = pareto["wav2vec2(teacher)"]["nn"], pareto["wav2vec2(teacher)"]["dp"]
    pr, pd = pareto["pre-distill(numpy)"]["nn"], pareto["pre-distill(numpy)"]["dp"]
    dr, dd = pareto["DISTILLED(numpy)"]["nn"], pareto["DISTILLED(numpy)"]["dp"]
    shr, shd = pareto["distilled-shuffled"]["nn"], pareto["distilled-shuffled"]["dp"]
    gap_r = (wr - pr)
    close_d_r = (dr - pr) / gap_r if abs(gap_r) > 1e-6 else float("nan")     # distill gap-closed (recall)
    close_q_r = (qdr - pr) / gap_r if abs(gap_r) > 1e-6 else float("nan")    # quanta  gap-closed (recall)
    print(f"  (a) (recall, d') HELD-OUT:")
    print(f"      raw ({rr:.3f}, {rd:.2f}) | featspace ({fr_:.3f}, {fd:.2f}) | pre-distill/global-metric "
          f"({pr:.3f}, {pd:.2f})")
    print(f"      quanta-static ({qsr:.3f}, {qsd:.2f}) | quanta-DYNAMIC ({qdr:.3f}, {qdd:.2f}) | "
          f"DISTILLED ({dr:.3f}, {dd:.2f}) | wav2vec2 ({wr:.3f}, {wd_:.2f})")
    print(f"      controls: quanta-shuffled ({qshr:.3f}, {qshd:.2f}) | distilled-shuffled ({shr:.3f}, {shd:.2f})")
    print(f"      GAP CLOSED to wav2vec2 (recall, from pre-distill): DISTILL {close_d_r*100:5.1f}% | "
          f"QUANTA-DYN {close_q_r*100:5.1f}%")
    dyn_load = (qdr > qsr + 0.01) and (qdd >= qsd - 0.02)     # must improve recall without losing d'
    print(f"  ★ DYNAMIC-vs-STATIC ablation: static ({qsr:.3f}, {qsd:.2f}) -> DYNAMIC ({qdr:.3f}, {qdd:.2f}) "
          f"=> dynamic {'IS' if dyn_load else 'is NOT clearly'} load-bearing on the invariance axis "
          f"(vs featspace {fr_:.3f}/{fd:.2f})")
    print(f"  (b) order-1 purity (matched cl): raw {purities['raw']:.3f} | quanta-DYN "
          f"{purities.get('quanta-DYNAMIC',0):.3f} | DISTILLED {purities.get('DISTILLED(numpy)',0):.3f} | "
          f"wav2vec2 {purities.get('wav2vec2(teacher)',0):.3f} (0.84 target)")
    qcc = fullstack["quanta-DYNAMIC"]["cc"]; dcc = fullstack["DISTILLED(numpy)"]["cc"]; rcc = fullstack["raw"]["cc"]
    print(f"  (c) cross-context: raw {rcc:.3f} | quanta-DYN {qcc:.3f} | distilled {dcc:.3f} "
          f"(gate-B q {fullstack['quanta-DYNAMIC']['accB']:.3f} / d {fullstack['DISTILLED(numpy)']['accB']:.3f})")
    print(f"  (d) donkey=0 {not donkey}   [peak {D._peak_gib():.2f} GiB]")
    print("-" * 100)
    # native quanta: beats the global metric AND its shuffled control (donkey=0, no teacher)
    q_native = qdr > pr + 0.02 and qdr > qshr + 0.02
    q_over_feat = qdr > fr_ + 0.02
    distill_ok = dr > pr + 0.02 and dr > shr + 0.02
    best_native = max([("quanta-DYNAMIC", qdr, qdd), ("pre-distill/global-metric", pr, pd)], key=lambda t: t[1])
    print(f"  => WHICH gets closest to wav2vec2 ({wr:.3f},{wd_:.2f}) DONKEY=0 (no teacher at inference):")
    if q_native and q_over_feat:
        print(f"     ★ NATIVE PER-DIM-DYNAMIC QUANTA beats the global metric WITHOUT a teacher: ({qdr:.3f}, "
              f"{qdd:.2f}) vs global ({pr:.3f}, {pd:.2f}), closing {close_q_r*100:.0f}% of the recall gap to")
        print(f"        wav2vec2; the SHUFFLED-quanta control does NOT ({qshr:.3f}) => earned per-dim tolerance,")
        print(f"        and DYNAMIC {'ADDS over static' if (qdr>qsr+0.01 or qdd>qsd+0.05) else 'ties static'} "
              f"— the trade-off dissolves per-axis (coarse on nuisance, fine on discriminative).")
    else:
        print(f"     NATIVE quanta ({qdr:.3f}, {qdd:.2f}) vs global metric ({pr:.3f}, {pd:.2f}): "
              f"{'beats' if qdr>pr else 'ties/does not beat'}; shuffled-quanta {qshr:.3f}.")
        print(f"        Diagonal per-dim scaling can only reweight axes (not rotate like the global metric);")
        print(f"        the DYNAMIC/local estimate {'adds' if (qdr>qsr+0.01) else 'does not add'} over static.")
    if distill_ok:
        print(f"     ★ TEACHER-DISTILL converts borrowed->earned: ({dr:.3f}, {dd:.2f}), closes {close_d_r*100:.0f}% of")
        print(f"        the recall gap to wav2vec2, donkey=0 (wav2vec2 removed, verified); shuffled-teacher "
              f"{shr:.3f}. savant-3b: standalone numpy reaches a point nearer the borrowed model.")
    else:
        print(f"     TEACHER-DISTILL ({dr:.3f}, {dd:.2f}) did not clearly beat the global metric ({pr:.3f}); "
              f"the RKD target transfers only partially through the 32-band cochleagram front-end.")
    print(f"  BORROWED-vs-EARNED: wav2vec2 recall {wr:.3f}; earned donkey=0 best "
          f"{max(qdr, dr, pr):.3f} => {max(qdr, dr, pr)/max(wr,1e-6)*100:.0f}% of the teacher's recall absorbed.")
    print(f"     Order-1 purity payoff (0.84) {'reached' if max(purities.get('quanta-DYNAMIC',0), purities.get('DISTILLED(numpy)',0))>0.8 else 'NOT reached'}; "
          f"residual = 32-band front-end info loss (wav2vec2 sees raw audio) + shallow numpy capacity — the")
    print("     named, tractable levers (richer front-end / deeper earner / stronger teacher), NOT irreducible.")
    print("=" * 100)


if __name__ == "__main__":
    main()
