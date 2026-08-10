"""RICHER GESTURAL-TARGET REPRESENTATION for dynamic-sequence speech AbS — the named lever.

08e9c843 VALIDATED the reframe: a DYNAMIC sequence-level generator-inversion (min-jerk
coarticulation trajectory through per-phone gestural TARGETS, held DtwTo sequence decode) is
~4x more DATA-EFFICIENT than the discriminative MLP/LDA and beats it at every N. Its honest
caveat named the REMAINING lever: the gestural-TARGET REPRESENTATION. A single mean point per
phone (LDA centroid) only reaches ~0.18 word-acc @36-way (data-efficient but absolutely LOW).
This script LIFTS the absolute accuracy by ENRICHING the target, while testing whether the
~4x data-efficiency SURVIVES (the reframe must not collapse into "needs more data").

We hold the dynamic-sequence GENERATOR (min-jerk + coarticulatory undershoot) and the held
DtwTo + argmin DECISION FIXED, and vary ONLY the per-phone target representation:

  BASELINE (08e9c843)  — LDA-mean: one point per phone = mean of its frames in the earned
                         PCA->LDA phone-discriminant space. (single control point per phone)
  (A) DYNAMIC TARGET   — a phone is a short GESTURE onset->nucleus->offset (3 sub-centroids),
                         NOT a point: captures WITHIN-phone dynamics (stop burst+transition,
                         diphthong movement). The renderer lays 3 control points per phone.
  (C) NONLINEAR SPACE  — earned RANDOM-FOURIER-FEATURE lift (cos(Wx+b), W,b random-init,
                         from-scratch RBF map; no torch/grads) BEFORE the LDA: a deeper earned
                         discriminant space than linear LDA (the jabberwock_phone_capacity lever).
  (D) ARTICULATORY     — target COMPOSED from distinctive features (voicing/place/manner/vowel
                         height-back-round) via a SHARED earned linear map B (ridge least-sq
                         from few exemplars): tgt(p)=feat(p)@B. Parameters are SHARED across
                         phones -> the structurally data-efficient enrichment. Plus a HYBRID
                         shrinkage tgt = blend(empirical, feature-predicted) by exemplar count.
  COMBO                — dynamic sub-trajectory (A) in the RFF space (C) with feature-shrinkage
                         (D) on each sub-point's center. All three stacked.

GATES (controls; donkey=0; a WIN needs BOTH absolute-lift AND preserved data-efficiency):
  MAIN-LIFT     — does a richer target lift word-acc above the LDA-mean baseline? (ablation A/C/D)
  MAIN-EFFIC.   — data-practicality curve (word-acc vs N): the richest target must STILL beat the
                  discriminative baseline at small N (flatter+higher) = ~4x efficiency PRESERVED.
                  A richer target that lifts absolute but COLLAPSES efficiency is an honest TRADEOFF.
  DISCRIMINATIVE— A beats its static-collapse(=baseline); C beats untrained/random-RFF; D beats a
                  SCRAMBLED phone->feature map. The enrichment must carry real signal.
  EARN-NOT-BORROW/donkey=0 — targets earned from held phonebank (RFF random-init, feature map
                  least-sq fit; distinctive features = phonological vocabulary, no weights/LLM);
                  DECISION = held DtwTo Term + argmin (graph-native).

Run (smoke):  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/richer_gestural_target_speech_abs.py --quick
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict

from scripts.jabberwock_subword_recognizer import _load_ph, ctx, norm_edit
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.dynamic_sequence_speech_abs import (
    majority_lexicon, collect_targets, _smooth, classify_render, decode_perframe,
    word_by_edit, eval_set, FUNC,
)


# ---------------------------------------------------------------- distinctive-feature table --
# ARPAbet/CMU phone -> articulatory distinctive features (phonological vocabulary, like
# domains/phonology.py: voicing/sibilance/manner). Earned knowledge, not weights / not an LLM.
# Vowels carry continuous height/back/round; consonants carry manner+place+voicing.
_PHON = {
    # vowels: height(0=low..1=high), back(0=front..1=back), round
    "AA": dict(vowel=1, voiced=1, height=0.0, back=1.0, rnd=0),
    "AE": dict(vowel=1, voiced=1, height=0.1, back=0.0, rnd=0),
    "AH": dict(vowel=1, voiced=1, height=0.5, back=0.5, rnd=0),
    "AO": dict(vowel=1, voiced=1, height=0.3, back=1.0, rnd=1),
    "AW": dict(vowel=1, voiced=1, height=0.3, back=0.5, rnd=0, diph=1),
    "AY": dict(vowel=1, voiced=1, height=0.3, back=0.3, rnd=0, diph=1),
    "EH": dict(vowel=1, voiced=1, height=0.4, back=0.0, rnd=0),
    "ER": dict(vowel=1, voiced=1, height=0.5, back=0.5, rnd=0, rhotic=1),
    "EY": dict(vowel=1, voiced=1, height=0.7, back=0.0, rnd=0, diph=1),
    "IH": dict(vowel=1, voiced=1, height=0.8, back=0.0, rnd=0),
    "IY": dict(vowel=1, voiced=1, height=1.0, back=0.0, rnd=0),
    "OW": dict(vowel=1, voiced=1, height=0.7, back=1.0, rnd=1, diph=1),
    "OY": dict(vowel=1, voiced=1, height=0.5, back=0.7, rnd=1, diph=1),
    "UH": dict(vowel=1, voiced=1, height=0.8, back=1.0, rnd=1),
    "UW": dict(vowel=1, voiced=1, height=1.0, back=1.0, rnd=1),
    # stops
    "B": dict(stop=1, voiced=1, labial=1),
    "P": dict(stop=1, voiced=0, labial=1),
    "D": dict(stop=1, voiced=1, alveolar=1),
    "T": dict(stop=1, voiced=0, alveolar=1),
    "G": dict(stop=1, voiced=1, velar=1),
    "K": dict(stop=1, voiced=0, velar=1),
    # affricates
    "CH": dict(affric=1, voiced=0, postalv=1),
    "JH": dict(affric=1, voiced=1, postalv=1),
    # fricatives
    "F": dict(fric=1, voiced=0, labial=1),
    "V": dict(fric=1, voiced=1, labial=1),
    "TH": dict(fric=1, voiced=0, dental=1),
    "DH": dict(fric=1, voiced=1, dental=1),
    "S": dict(fric=1, voiced=0, alveolar=1, sib=1),
    "Z": dict(fric=1, voiced=1, alveolar=1, sib=1),
    "SH": dict(fric=1, voiced=0, postalv=1, sib=1),
    "ZH": dict(fric=1, voiced=1, postalv=1, sib=1),
    "HH": dict(fric=1, voiced=0, glottal=1),
    # nasals
    "M": dict(nasal=1, voiced=1, labial=1),
    "N": dict(nasal=1, voiced=1, alveolar=1),
    "NG": dict(nasal=1, voiced=1, velar=1),
    # liquids / glides
    "L": dict(liquid=1, voiced=1, alveolar=1),
    "R": dict(liquid=1, voiced=1, alveolar=1, rhotic=1),
    "W": dict(glide=1, voiced=1, labial=1, back=1.0),
    "Y": dict(glide=1, voiced=1, palatal=1),
}
_FKEYS = sorted({k for d in _PHON.values() for k in d})


def _featvec(p):
    """phone -> distinctive-feature vector (+ bias). Unknown phone -> bias-only."""
    d = _PHON.get(p, {})
    return np.array([float(d.get(k, 0.0)) for k in _FKEYS] + [1.0])


# ---------------------------------------------------------------- earned encoder (PCA[->RFF]->LDA)
class Encoder:
    """EARNED phone-discriminant encoder. linear: PCA->LDA (the 08e9c843 baseline space).
    nonlinear: PCA->random-Fourier-features->LDA (the deeper earned space, lever C)."""
    def __init__(self, nonlinear=False, rff_dim=600, seed=0):
        self.nonlinear = nonlinear; self.rff_dim = rff_dim; self.seed = seed

    def _rff(self, Z):
        return np.cos(Z @ self.Wr + self.br) * np.sqrt(2.0 / self.Wr.shape[1])

    def fit(self, X, Y):
        self.phones = sorted(set(Y)); nP = len(self.phones)
        P = min(80, X.shape[0] - nP - 1)
        self.mu, self.Wp = _fit_pca(X, P)
        Z = (X - self.mu) @ self.Wp
        if self.nonlinear:
            rng = np.random.default_rng(self.seed)
            s = Z[rng.choice(len(Z), min(1500, len(Z)), replace=False)]
            med = np.median(np.linalg.norm(s[:400, None] - s[None, :400], axis=2)) + 1e-9
            gamma = 1.0 / (2 * med ** 2)
            self.Wr = rng.normal(0, np.sqrt(2 * gamma), size=(P, self.rff_dim))
            self.br = rng.uniform(0, 2 * np.pi, size=self.rff_dim)
            Z = self._rff(Z)
        self.Wl = _fit_lda(Z, Y, k=min(Z.shape[1], nP - 1))
        return self

    def __call__(self, Zin):
        Z = (np.asarray(Zin) - self.mu) @ self.Wp
        if self.nonlinear:
            Z = self._rff(Z)
        R = Z @ self.Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)


def frame_pairs(words):
    """per-frame (context, phone) flat-start pairs (the encoder + target training set)."""
    X, Y = [], []
    for w, fr, ph in words:
        cx = ctx(fr); n = len(cx); P = len(ph)
        for i in range(n):
            X.append(cx[i]); Y.append(ph[int(i * P / n)])
    return np.asarray(X), Y


# ---------------------------------------------------------------- target builders (the LEVER) --
def emp_targets(enc, X, Y, S=1):
    """empirical per-phone target in the encoder space. S=1 -> mean point (baseline). S=3 ->
    onset/nucleus/offset sub-centroids (lever A: within-phone gesture). Returns dict + counts.
    Phone frames are taken IN ORDER so the sub-thirds capture the within-phone trajectory."""
    E = enc(X)
    by = defaultdict(list)
    for i, p in enumerate(Y):
        by[p].append(i)
    tgt = {}; cnt = {}
    for p, idx in by.items():
        Ep = E[idx]; cnt[p] = len(idx)
        if S == 1:
            tgt[p] = Ep.mean(0)[None, :]
        else:
            parts = np.array_split(Ep, S)              # in-order thirds = onset/nucleus/offset
            tgt[p] = np.stack([(q.mean(0) if len(q) else Ep.mean(0)) for q in parts])
    return tgt, cnt, E


def feature_map(tgt_mean, cnt, scramble=False, seed=0, ridge=1.0):
    """EARN a SHARED linear map B: feat(phone)@B ~= empirical centroid. Weighted ridge least-sq
    over the SEEN phones (weight=sqrt(count) so well-estimated phones dominate). The shared
    parameters are the structural data-efficiency: a rarely-/never-seen phone still gets a
    target from its features. `scramble` permutes the phone->feature assignment (the control)."""
    phones = sorted(tgt_mean.keys())
    feats = [_featvec(p) for p in phones]
    if scramble:
        perm = np.random.default_rng(seed).permutation(len(phones))
        feats = [feats[j] for j in perm]
    F = np.stack(feats)                                 # (P x m)
    T = np.stack([tgt_mean[p] for p in phones])         # (P x dim)
    w = np.sqrt(np.array([cnt[p] for p in phones], float))
    Fw = F * w[:, None]; Tw = T * w[:, None]
    m = F.shape[1]
    B = np.linalg.solve(Fw.T @ Fw + ridge * np.eye(m), Fw.T @ Tw)   # (m x dim)
    return B


def feat_targets(B, phones_all):
    """feature-composed target for EVERY phone (lever D, pure): tgt(p)=feat(p)@B."""
    return {p: (_featvec(p) @ B)[None, :] for p in phones_all}


def hybrid_targets(tgt_emp_mean, cnt, B, phones_all, tau=20.0):
    """shrinkage hybrid (lever D): blend empirical mean with feature-prediction by exemplar
    count, w = n/(n+tau). Few exemplars -> lean on the shared feature map; many -> trust data."""
    out = {}
    for p in phones_all:
        pred = _featvec(p) @ B
        n = cnt.get(p, 0)
        if n == 0:
            out[p] = pred[None, :]
        else:
            w = n / (n + tau)
            out[p] = (w * tgt_emp_mean[p][0] + (1.0 - w) * pred)[None, :]
    return out


def combo_targets(tgt_sub, cnt, B, phones_all, tau=20.0):
    """COMBO: dynamic sub-trajectory (A) with its CENTER feature-shrunk (D); built in whatever
    space tgt_sub lives in (use the RFF space => +C). Preserves within-phone deltas, regularizes
    the center toward the shared feature prediction."""
    out = {}
    for p in phones_all:
        sub = tgt_sub.get(p)
        pred = _featvec(p) @ B
        n = cnt.get(p, 0)
        if sub is None:
            out[p] = pred[None, :]; continue
        center = sub.mean(0)
        w = n / (n + tau)
        new_center = w * center + (1.0 - w) * pred
        out[p] = sub - center[None, :] + new_center[None, :]    # keep deltas, move center
    return out


# ---------------------------------------------------------------- the GENERATOR (FIXED) -------
def render_traj(seq, tgt, durs, gmean, dmean, undershoot=0.35):
    """The 08e9c843 dynamic min-jerk + coarticulatory-undershoot generator, GENERALISED to a
    per-phone target that may be a SHORT SUB-TRAJECTORY (S>=1 control points). For S=1 it
    reproduces render_dynamic exactly (single mid-phone control point). The generator is held
    FIXED across all enrichments — only `tgt` (the representation) changes."""
    K = len(seq)
    if K == 0:
        return np.zeros((2, len(gmean)))
    subs = [np.atleast_2d(tgt.get(p, gmean[None, :])) for p in seq]
    reps = [s.mean(0) for s in subs]
    d = [max(1.0, durs.get(p, dmean)) for p in seq]
    starts = np.cumsum([0.0] + d); M = max(2, int(round(starts[-1])))
    cc, cp = [], []
    for k in range(K):
        s = subs[k]; S = len(s)
        left = reps[k - 1] if k > 0 else reps[k]
        right = reps[k + 1] if k < K - 1 else reps[k]
        u = undershoot / (1.0 + d[k] / 3.0)
        for j in range(S):
            cc.append(starts[k] + (j + 0.5) / S * d[k])
            cp.append((1.0 - u) * s[j] + 0.5 * u * left + 0.5 * u * right)
    E = np.stack(cp); centers = np.array(cc); t = np.arange(M)
    traj = np.stack([np.interp(t, centers, E[:, b]) for b in range(E.shape[1])], 1)
    return _smooth(traj, max(3, int(0.6 * dmean)))


def make_recog(enc, tgt, durs, dmean, vocab_seqs):
    """build a recogniser: render each vocab word's trajectory through `tgt`, decode an observed
    word by argmin DTW(enc(ctx(O)), rendered). DECISION = held DtwTo + argmin (graph-native)."""
    gm = np.mean([v.mean(0) for v in tgt.values()], 0)
    rend = [render_traj(s, tgt, durs, gm, dmean).tolist() for s in vocab_seqs]
    return lambda O: classify_render(enc(ctx(O)), rend)


def discriminative(enc, X, Y, vocab_seqs):
    """DISCRIMINATIVE baseline: per-phone LDA centroid -> per-frame argmax -> collapse -> word
    by edit (the existing sub-word recogniser). The data-hungry comparison for efficiency."""
    E = enc(X); phones = sorted(set(Y))
    cent = np.stack([E[[i for i in range(len(Y)) if Y[i] == p]].mean(0) for p in phones])
    cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)

    def decode(M):
        idx = (enc(ctx(M)) @ cent.T).argmax(1)
        seq, prev = [], -1
        for k in idx:
            if k != prev:
                seq.append(phones[k]); prev = k
        return seq
    return lambda O: word_by_edit(decode(O), vocab_seqs)


# ---------------------------------------------------------------- main ------------------------
def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 100)
    print("RICHER GESTURAL-TARGET REPRESENTATION — dynamic-seq AbS, lever ablation (A/C/D/combo)")
    print("=" * 100, flush=True)

    cal_pool = _load_ph("train-clean-100_*.pkl", 6 if quick else 14)
    dev = _load_ph("dev-clean_*.pkl", 4 if quick else 10)
    lex = majority_lexicon(cal_pool + dev)
    dev_by_word = defaultdict(list)
    for w, fr, ph in dev:
        if w not in FUNC and len(w) >= 4 and w in lex and len(lex[w]) >= 3:
            dev_by_word[w].append(np.asarray(fr, float))
    K_EX = 8 if quick else 12
    vocab = sorted([w for w, exs in dev_by_word.items() if len(exs) >= K_EX])
    vocab = vocab[:24 if quick else 36]
    vocab_seqs = [lex[w] for w in vocab]
    phones_all = sorted({p for s in vocab_seqs for p in s})
    test = []
    for wi, w in enumerate(vocab):
        for O in dev_by_word[w][:K_EX]:
            test.append((O, wi, lex[w], vocab_seqs))
    chance = 1.0 / len(vocab)
    print(f"  cal pool {len(cal_pool)}  dev {len(dev)}  vocab {len(vocab)} (chance {chance:.3f})  "
          f"test {len(test)}  phones {len(phones_all)}  [{time.time()-t0:.0f}s]", flush=True)

    rng = np.random.default_rng(0)
    cal_idx = rng.permutation(len(cal_pool))
    Ns = [25, 50, 100, 200] if quick else [25, 50, 100, 200, 400, 800]

    def build(N):
        words = [cal_pool[i] for i in cal_idx[:N]]
        _t, durs = collect_targets(words)
        dmean = float(np.mean(list(durs.values())))
        X, Y = frame_pairs(words)
        encL = Encoder(False).fit(X, Y)
        encR = Encoder(True).fit(X, Y)
        return words, durs, dmean, X, Y, encL, encR

    def recognisers_at(N, want):
        """build the requested named recognisers at calibration size N."""
        words, durs, dmean, X, Y, encL, encR = build(N)
        out = {}
        # LDA-mean baseline (08e9c843)
        tL1, cntL, _ = emp_targets(encL, X, Y, S=1)
        tLmean = {p: tL1[p] for p in tL1}
        if "baseline" in want:
            out["baseline"] = make_recog(encL, tL1, durs, dmean, vocab_seqs)
        if "A" in want:                                  # dynamic sub-trajectory in LDA space
            tA, _, _ = emp_targets(encL, X, Y, S=3)
            out["A"] = make_recog(encL, tA, durs, dmean, vocab_seqs)
        if "C" in want:                                  # RFF nonlinear space, single point
            tR1, cntR, _ = emp_targets(encR, X, Y, S=1)
            out["C"] = make_recog(encR, tR1, durs, dmean, vocab_seqs)
        if "D" in want or "Dhyb" in want:                # feature-composed / hybrid in LDA space
            tmean = {p: tL1[p][0] for p in tL1}
            B = feature_map(tmean, cntL)
            if "D" in want:
                out["D"] = make_recog(encL, feat_targets(B, phones_all), durs, dmean, vocab_seqs)
            if "Dhyb" in want:
                out["Dhyb"] = make_recog(
                    encL, hybrid_targets(tL1, cntL, B, phones_all), durs, dmean, vocab_seqs)
        if "combo" in want:                              # A in C space + D shrinkage
            tRsub, cntR, _ = emp_targets(encR, X, Y, S=3)
            tRmean = {p: tRsub[p].mean(0) for p in tRsub}
            BR = feature_map(tRmean, cntR)
            out["combo"] = make_recog(
                encR, combo_targets(tRsub, cntR, BR, phones_all), durs, dmean, vocab_seqs)
        if "discrim" in want:
            out["discrim"] = discriminative(encL, X, Y, vocab_seqs)
        return out

    # ---- ABLATION at a representative small N ------------------------------------------------
    Nab = 100
    print(f"\n  ABLATION at N={Nab} (word acc / phone-edit acc) vs the LDA-mean baseline:")
    recs = recognisers_at(Nab, {"baseline", "A", "C", "D", "Dhyb", "combo", "discrim"})
    base_w = None
    order = [("baseline", "BASELINE LDA-mean (08e9c843)"), ("A", "(A) dynamic sub-traj  "),
             ("C", "(C) RFF nonlinear space"), ("D", "(D) feature-composed   "),
             ("Dhyb", "(D) feature-hybrid     "), ("combo", "COMBO A+C+D            "),
             ("discrim", "discriminative baseline")]
    abl = {}
    for key, label in order:
        w, p = eval_set(test, recs[key])
        abl[key] = w
        if key == "baseline":
            base_w = w
        d = "" if key == "baseline" else f"  (delta {w-base_w:+.3f})"
        print(f"    {label}: {w:.3f} / {p:.3f}{d}   [{time.time()-t0:.0f}s]", flush=True)
    best_key = max(("A", "C", "D", "Dhyb", "combo"), key=lambda k: abl[k])
    print(f"  -> best enrichment: {best_key} ({abl[best_key]:.3f})  vs baseline {base_w:.3f} "
          f"(lift {abl[best_key]-base_w:+.3f})", flush=True)

    # ---- DISCRIMINATIVE controls (enrichment carries signal) at N=Nab -----------------------
    print(f"\n  DISCRIMINATIVE controls at N={Nab} (the enrichment must carry real signal):")
    words, durs, dmean, X, Y, encL, encR = build(Nab)
    #  A vs its static collapse (= baseline LDA-mean): already have both
    print(f"   (A) dynamic sub-traj {abl['A']:.3f}  vs  static-collapse(=baseline) {abl['baseline']:.3f}"
          f"   => within-phone dynamics help: {abl['A'] > abl['baseline']}")
    #  C vs untrained random-RFF (random LDA projection, no label fit)
    encU = Encoder(True); encU.phones = encR.phones
    encU.mu, encU.Wp, encU.Wr, encU.br = encR.mu, encR.Wp, encR.Wr, encR.br
    encU.Wl = np.random.default_rng(7).normal(0, 1, encR.Wl.shape)   # random proj, NO LDA fit
    tU1, cntU, _ = emp_targets(encU, X, Y, S=1)
    cu_w, _ = eval_set(test, make_recog(encU, tU1, durs, dmean, vocab_seqs))
    print(f"   (C) RFF (LDA-fit)    {abl['C']:.3f}  vs  untrained random-RFF {cu_w:.3f}"
          f"   => earned nonlinear space helps: {abl['C'] > cu_w + 0.02}")
    #  D vs scrambled phone->feature map
    tL1, cntL, _ = emp_targets(encL, X, Y, S=1)
    tmean = {p: tL1[p][0] for p in tL1}
    Bs = feature_map(tmean, cntL, scramble=True, seed=5)
    ds_w, _ = eval_set(test, make_recog(encL, feat_targets(Bs, phones_all), durs, dmean, vocab_seqs))
    print(f"   (D) feature-composed {abl['D']:.3f}  vs  scrambled-feature map {ds_w:.3f}"
          f"   => distinctive-feature structure carries signal: {abl['D'] > ds_w + 0.02}")

    # ---- MAIN: data-practicality curve (efficiency PRESERVED?) ------------------------------
    # baseline (08e9c843) vs the best-ABSOLUTE enrichment vs the data-efficiency candidate
    # (Dhyb = feature-shrinkage, the structurally cheap target) vs the discriminative MLP/LDA.
    print(f"\n  MAIN — DATA-PRACTICALITY (word acc vs N): baseline vs best vs Dhyb vs discrim")
    print(f"  {'N':>5} | {'baseline':>9} | {best_key+' (best)':>13} | {'Dhyb':>7} | {'discrim':>9}  "
          f"(chance {chance:.3f})")
    curve = []
    for N in Ns:
        ts = time.time()
        r = recognisers_at(N, {"baseline", best_key, "Dhyb", "discrim"})
        b_w = eval_set(test, r["baseline"])[0]
        x_w = eval_set(test, r[best_key])[0]
        h_w = eval_set(test, r["Dhyb"])[0]
        d_w = eval_set(test, r["discrim"])[0]
        curve.append((N, b_w, x_w, d_w, h_w))
        print(f"  {N:>5} | {b_w:>9.3f} | {x_w:>13.3f} | {h_w:>7.3f} | {d_w:>9.3f}   "
              f"[{time.time()-ts:.0f}s]", flush=True)

    # ---- VERDICT ----------------------------------------------------------------------------
    print("\n" + "=" * 100)
    s = curve[0]; big = curve[-1]
    eff_small = s[2] - s[3]          # richest - discrim at smallest N
    print(f"  baseline curve: " + "  ".join(f"{c[0]}:{c[1]:.2f}" for c in curve))
    print(f"  best({best_key}) curve: " + "  ".join(f"{c[0]}:{c[2]:.2f}" for c in curve))
    print(f"  Dhyb     curve: " + "  ".join(f"{c[0]}:{c[4]:.2f}" for c in curve))
    print(f"  discrim  curve: " + "  ".join(f"{c[0]}:{c[3]:.2f}" for c in curve))
    print(f"  ABSOLUTE LIFT (N={Nab}): baseline {base_w:.3f} -> best({best_key}) {abl[best_key]:.3f}  "
          f"({abl[best_key]-base_w:+.3f})")
    print(f"  EFFICIENCY at smallest N={s[0]}: richest {s[2]:.3f} vs discrim {s[3]:.3f}  "
          f"(richest beats discrim small-N: {eff_small > 0.0})")
    print(f"  donkey=0: targets EARNED from held phonebank (RFF random-init, feature map least-sq; "
          f"distinctive features = phonological vocabulary); DECISION = held DtwTo + argmin. "
          f"No LLM, no borrowed net.")
    print("=" * 100, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
