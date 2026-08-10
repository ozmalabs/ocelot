"""COMPREHENSION-GRAIN DEVELOPMENT ARC — the staged developmental loop, measured by COMPREHENSION.

THE METRIC-SATURATION FINDING (commit 9de5b7cb) mandated this. The PER-FRAME phone-accuracy metric is
SATURATED: real-supervised ceiling ~0.094 ~= the XTTS cap ~0.103 -> NO headroom; the per-phone CAREGIVER->REAL
band OFFSET is real but the per-frame metric cannot reward closing it, and per-frame self-training DRIFTS.
So recognition development MUST move to the SEQUENCE/COMPREHENSION grain, where there IS headroom and the
per-phone offset IS penalised. This file assembles the VALIDATED pieces into the human-development shape —
each grain GROUNDS before the next builds — and measures COMPREHENSION (content-word recognition on real
held-out dev-clean) at each stage, folding in the two named levers.

THE STAGED ARC (each stage grounds before the next builds):
  STAGE 0  UNGROUNDED MODEL : M seeded from a FEW exemplars (the agent's poor early own-production) -> a poor
                              theta_0; comprehension is the floor.
  STAGE A  MODEL GROUNDING  : ground the ONE inventory theta against HEARD speech (train-clean) through the
                              HELD collapse cognition (native_surprise), using WHOLE-UTTERANCE FORCED
                              ALIGNMENT (DTW frames->transcript phones against the current model) — the named
                              fix for the noisy per-frame argmax that drifted. theta -> theta*; the per-phone
                              OFFSET to real falls; model-alone comprehension RISES.
  STAGE B  COGNITIVE GROUND : the word/meaning layer grounds THROUGH the grounded model (the validated coupled
                              decode, cognitive_over_model_speech). The cognitive word-transition prior (held
                              run_collapse, grown by on_gap) supplies top-down context; the posterior =
                              acoustic-evidence(through M) + lam*prior. Coupled comprehension RISES again.

THE NAMED LEVERS, folded in and tested AT THE COMPREHENSION GRAIN:
  WHOLE-UTTERANCE LEVER : ground theta via whole-utterance FORCED ALIGNMENT vs via the noisy PER-FRAME ARGMAX
                          self-labelling. Does better grounding now HELP comprehension where per-frame
                          self-training drifted?
  OFFSET-PAYS-OFF       : reduce the per-phone CAREGIVER->REAL offset (invisible/flat to per-frame) — does it
                          now HELP comprehension (where it is penalised)? Comprehension vs offset across
                          grounding qualities.

LEVER 1 — THE FEATURE SPACE (the raw-band DTW was the bottleneck: its oracle ceiling ~= the achieved arc).
The whole arc is re-run in THREE frame spaces — RAW-BAND vs the agent's EARNED PHONE-DISCRIMINANT (PCA->LDA,
fit on train-clean phone-aligned frames, earned, no borrowed net) vs a RANDOM projection of the same dim
(discriminative control: the earned discriminant, not dimensionality, must do the work). Recognising in the
earned LDA space RAISES the oracle ceiling and lifts the arc. donkey=0: the DECISION stays the held DtwTo Term,
now evaluated in the earned space.

GATES (donkey=0, honest):
  MAIN     — the arc CLIMBS: comprehension RISES through STAGE 0 -> A -> B (where per-frame was flat-capped),
             vs chance and vs an oracle (real-dev-centroid) ceiling.
  LEVER 1  — CEILING RISES (LDA oracle > raw-band oracle) + ARC CLIMBS HIGHER (LDA STAGE A > raw-band STAGE A)
             + DISCRIMINATIVE (LDA > random projection of the same dim).
  LEVER 2  — a RICHER earned feature: sweep the CONTEXTUAL-LDA window W (+-W frames of coarticulatory context,
             still LINEAR so DtwTo geometry is preserved). FINDING (committed f4f0c26b): context helps to an
             optimum at W=5 then SATURATES (W8 degrades); the LINEAR feature plateaus -> the binding ceiling
             is the SUB-PART PARSE (fixed flat-start over fixed 39 monophones).
  LEVER 3  — a LEARNED SUB-PART PARSE (this run): split each phone into K identity-bearing SUB-PHONE STATES
             (39xK inventory), INFER the per-frame parse by Viterbi/EM (forced-align frames to the expanded
             sub-part sequence under the current model, re-fit, iterate) instead of fixed flat-start, fit the
             LDA on the INFERRED sub-part labels. K-sweep (K=1 monophone -> 2,3,5). Does the richer inferred
             inventory RAISE the oracle above 0.321 and lift the arc above 0.342 (proving the PARSE, not a
             floor, was the lever)? Controls: inferred parse vs FIXED flat-start vs RANDOM sub-parts. If it
             PLATEAUS/OVERFITS, that is the DATA-bound boundary (more held data to fit the richer parse).
  COMPOSE  — the full system (FA-grounded model + cognitive top-down) beats the pieces alone (model-alone,
             prior-alone, per-frame-pseudo-label-grounded).
  WHOLE-UTT— FA-grounded comprehension > per-frame-argmax-grounded comprehension (+ lower offset).
  OFFSET   — lower per-phone offset -> higher comprehension (the per-frame-invisible lever pays off here).
  DISCRIM  — real-grounded > shuffled-grounded; top-down (lam>0) > prior-blind (lam=0). SPLIT: ground/learn on
             train-clean, lam selected on a held-out train-clean slice, TEST on dev-clean (no leakage).

donkey=0: M render = numpy adapter; the DECISION = held DtwTo Term; SURPRISE = held native_collapse term;
the cognitive predictor = held run_collapse + counted transitions grown by on_gap; no LLM, no borrowed net,
no gradient. XTTS unused (the few-exemplar seed is the bootstrap proxy for own-voice production, which is the
separately-validated babble path cb402364).

Run (smoke): PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/comprehension_grain_development.py [--quick]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict

import substrate_rs as _srs
from scripts.native_collapse import native_surprise
from scripts.jabberwock_subword_recognizer import _load_ph, ctx
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.dynamic_sequence_speech_abs import render_dynamic, dtw, majority_lexicon, FUNC
from scripts.speech_one_model_plug import flatstart_assign, _conf_softmax, collect_targets_few
from scripts.cognitive_over_model_speech import (cognitive_collapse, _ordered_stream, _windows,
                                                 coupled_comprehension)

_S = _srs.Substrate()


# ============================================================================
# FEATURE SPACE — the comprehension recogniser runs in whatever frame space the
# words are given in. The raw-band DTW was the BOTTLENECK (its oracle ceiling
# ~0.19 == the achieved arc): swap in the agent's EARNED PHONE-DISCRIMINANT (LDA)
# feature, fit on TRAIN-clean phone-aligned frames (earned, no borrowed net), to
# RAISE the ceiling the arc climbs toward. A RANDOM projection of the SAME output
# dim is the discriminative control (the earned discriminant, not dimensionality,
# must do the work). donkey=0: enc = PCA->LDA on held data; the DECISION stays the
# held DtwTo Term, now evaluated in the earned space.
# ============================================================================

def fit_lda_encoder(cal_words, W=5, cap=60000, Pdim=80, rng=None):
    """EARNED CONTEXTUAL phone-discriminant encoder: stack +-W frames (temporal context / coarticulation)
    -> proportional-aligned (frame-context, phone) pairs from TRAIN-clean -> PCA->LDA (the agent's
    WithinScatter discriminant). LINEAR, so the DtwTo geometry is preserved. W=0 = single-frame; wider W =
    more coarticulatory context. Returns (enc_full(M), dim): enc_full maps band frames -> L2-normalised LDA
    frame-sequence (length preserved)."""
    X, Y = [], []
    for w, fr, ph in cal_words:
        cx = ctx(fr, W); n = len(cx); P = len(ph)
        for i in range(n):
            X.append(cx[i]); Y.append(ph[int(i * P / n)])
        if len(X) >= cap:
            break
    X = np.asarray(X, float)
    phones = sorted(set(Y)); nP = len(phones)
    Pd = max(2, min(Pdim, X.shape[0] - nP - 1))
    mu, Wp = _fit_pca(X, Pd)
    Wl = _fit_lda((X - mu) @ Wp, Y, k=min(Pd, nP - 1))
    dim = Wl.shape[1]

    def enc_full(M):
        Z = ctx(np.asarray(M, float), W)
        Yp = ((Z - mu) @ Wp) @ Wl
        return Yp / np.clip(np.linalg.norm(Yp, axis=1, keepdims=True), 1e-9, None)
    return enc_full, dim


def random_encoder(M_example, dim, rng, W=5):
    """RANDOM projection of the SAME +-W context frames to the SAME output dim (discriminative control:
    matched context window AND matched dimensionality, NO earned discriminant)."""
    cdim = ctx(np.asarray(M_example, float), W).shape[1]
    R = rng.standard_normal((cdim, dim)) / np.sqrt(cdim)

    def enc_rand(M):
        Z = ctx(np.asarray(M, float), W) @ R
        return Z / np.clip(np.linalg.norm(Z, axis=1, keepdims=True), 1e-9, None)
    return enc_rand


# ============================================================================
# LEVER 3 — a LEARNED SUB-PART PARSE (BPL-style richer INFERRED inventory). The
# binding ceiling was the FIXED flat-start parse over FIXED 39 monophones. Here
# each phone is split into K identity-bearing SUB-PHONE STATES (39xK sub-parts),
# the per-frame parse is INFERRED by Viterbi/EM (forced-align frames to the
# expanded sub-part sequence under the current model, re-fit, ITERATE) instead of
# fixed flat-start, and the LDA discriminant is fit on the INFERRED sub-part
# labels (a richer feature). donkey=0: inventory + parse = the agent's OWN
# EM/Viterbi (forced_align = the held DTW-monotonic alignment) on held train-clean;
# no borrowed net/LLM/gradient-net. K=1 == the monophone baseline.
# ============================================================================

def expand_seq(ph, K):
    """Expand a phone sequence into its SUB-PART sequence: each phone p -> p#0,..,p#(K-1) (onset..coda)."""
    return [f"{p}#{k}" for p in ph for k in range(K)]


def _init_subparts(O, ph, K):
    """FLAT-START sub-part parse: proportional frame->phone, then split each phone's contiguous frame-run
    into K equal contiguous sub-states (the fixed-parse control + the EM init)."""
    n = len(O); P = len(ph)
    if P == 0:
        return []
    pos = [min(int(i * P / n), P - 1) for i in range(n)]
    byj = defaultdict(list)
    for i in range(n):
        byj[pos[i]].append(i)
    labels = [None] * n
    for j, frames in byj.items():
        m = len(frames)
        for t, i in enumerate(frames):
            labels[i] = f"{ph[j]}#{min(K - 1, int(t * K / m))}"
    return labels


def _random_subparts(O, ph, K, rng):
    """DEGENERATE control: keep phone identity but assign the sub-state index at RANDOM (no contiguous
    onset/nucleus/coda structure) — tests that the INFERRED sub-part structure, not the extra classes, works."""
    return [f"{l.split('#')[0]}#{int(rng.integers(K))}" for l in _init_subparts(O, ph, K)]


def subpart_em(words, K, em_iters):
    """VITERBI/EM training of the sub-part inventory in band space: init flat-start sub-split -> centroids;
    then ITERATE: forced-align (held DTW-monotonic) each word's frames to its expanded sub-part sequence
    under the current centroids, re-fit the centroids. Returns the inferred sub-part band centroids."""
    acc = defaultdict(list)
    for O, ph in words:
        for i, l in enumerate(_init_subparts(O, ph, K)):
            acc[l].append(O[i])
    theta = {l: np.mean(v, 0) for l, v in acc.items() if v}
    for _ in range(em_iters):
        gm = np.mean(list(theta.values()), 0); acc = defaultdict(list)
        for O, ph in words:
            lab = forced_align(O, expand_seq(ph, K), theta, gm)
            for i, l in enumerate(lab):
                acc[l].append(O[i])
        theta = {l: np.mean(v, 0) for l, v in acc.items() if len(v) >= 2}
    return theta


def build_subpart_feature(cal_g, K, mode, W, em_iters, cap, rng, em_cap=4000):
    """Build the EARNED sub-part discriminant: infer the per-frame sub-part labels (mode = viterbi / flat /
    random) and fit PCA->LDA on them (39xK classes). Returns (enc, dim, n_classes)."""
    words = [(np.asarray(fr, float), ph) for (w, fr, ph) in cal_g[:em_cap]]
    if mode == "viterbi":
        theta = subpart_em(words, K, em_iters); gm = np.mean(list(theta.values()), 0)
        labeler = lambda O, ph: forced_align(O, expand_seq(ph, K), theta, gm)
    elif mode == "flat":
        labeler = lambda O, ph: _init_subparts(O, ph, K)
    else:
        labeler = lambda O, ph: _random_subparts(O, ph, K, rng)
    X, Y = [], []
    for (w, fr, ph) in cal_g:
        O = np.asarray(fr, float); cx = ctx(O, W); lab = labeler(O, ph)
        for i in range(len(cx)):
            X.append(cx[i]); Y.append(lab[i])
        if len(X) >= cap:
            break
    X = np.asarray(X, float); classes = sorted(set(Y)); nC = len(classes)
    Pd = max(2, min(80, X.shape[0] - nC - 1))
    mu, Wp = _fit_pca(X, Pd)
    Wl = _fit_lda((X - mu) @ Wp, Y, k=min(Pd, nC - 1)); dim = Wl.shape[1]

    def enc(M):
        Z = ctx(np.asarray(M, float), W); Yp = ((Z - mu) @ Wp) @ Wl
        return Yp / np.clip(np.linalg.norm(Yp, axis=1, keepdims=True), 1e-9, None)
    return enc, dim, nC


def transform_words(words, feat):
    """Re-express each word's frames in the feature space (feat: band frames -> feature frames)."""
    return [(w, feat(np.asarray(fr, float)), ph) for (w, fr, ph) in words]


# ============================================================================
# ALIGNERS — the three frame->phone assignments that GROUND theta. Each yields a
# different grounding QUALITY (and so a different per-phone OFFSET): the named
# whole-utterance lever (FA) vs the noisy per-frame self-labelling (PF) vs the
# transcript-order flat-start (FLAT).
# ============================================================================

def flat_assign(O, ph, theta, gm):
    """FLAT-START: proportional transcript-order alignment (ignores the acoustics WITHIN the word)."""
    return flatstart_assign(O, ph)


def forced_align(O, ph, theta, gm):
    """WHOLE-UTTERANCE FORCED ALIGNMENT: monotonic DTW of the whole utterance's frames onto its transcript
    phone sequence, cost = ||frame - theta[phone]||^2 against the CURRENT model. Uses the transcript AND the
    acoustics (the named fix for the noisy per-frame argmax). As theta improves the alignment sharpens ->
    cleaner per-phone clouds -> theta tracks the real cluster means (the offset closes)."""
    n, P = len(O), len(ph)
    if P == 0:
        return []
    if P == 1 or n <= P:                                            # too few frames to visit each unit -> proportional
        return [ph[min(int(i * P / max(n, 1)), P - 1)] for i in range(n)]
    tgt = np.stack([theta.get(p, gm) for p in ph])                 # (P, B)
    C = ((O[:, None, :] - tgt[None]) ** 2).sum(2)                  # (n, P) local cost
    INF = 1e18
    D = np.full((n, P), INF); back = np.zeros((n, P), np.int8)
    D[0, 0] = C[0, 0]
    for i in range(1, n):
        D[i, 0] = D[i - 1, 0] + C[i, 0]                            # stay on phone 0
        prev = D[i - 1]
        for j in range(1, P):
            if prev[j] <= prev[j - 1]:
                D[i, j] = C[i, j] + prev[j]                        # stay on phone j
            else:
                D[i, j] = C[i, j] + prev[j - 1]; back[i, j] = 1    # advance from j-1
    a = [None] * n; j = P - 1
    for i in range(n - 1, -1, -1):
        a[i] = ph[j]
        if i > 0 and back[i, j] == 1:
            j -= 1
    return a


def perframe_assign(O, ph, theta, gm):
    """PER-FRAME ARGMAX self-labelling: each frame -> nearest theta phone, IGNORING the transcript. The noisy
    pseudo-label that drifted in babble_domain_adapt (per-frame argmax ~0.14 < self-training viability)."""
    phl = sorted(theta.keys())
    T = np.stack([theta[p] for p in phl])
    idx = ((O[:, None, :] - T[None]) ** 2).sum(2).argmin(1)
    return [phl[k] for k in idx]


# ============================================================================
# MODEL GROUNDING — refine the ONE inventory theta against HEARD speech through
# the HELD collapse cognition (native_surprise). Same structure-addition as
# speech_one_model_plug.ground_targets (counted running mean = grow Gamma; ADD
# unseen phones), parametrised by the ALIGNER so the whole-utterance lever and
# its per-frame control share one grounding loop.
# ============================================================================

def ground_model(theta0, durs0, words, assign_fn, passes=3, sigma=2.0):
    theta = {p: v.copy() for p, v in theta0.items()}
    durs = dict(durs0); cnt = {p: 1.0 for p in theta}; traj = []
    for _ in range(passes):
        phl = sorted(theta.keys()); gm = np.mean(list(theta.values()), 0)
        tot_s, n = 0.0, 0
        for w, fr, ph in words:
            O = np.asarray(fr, float)
            assign = assign_fn(O, ph, theta, gm)
            by = defaultdict(list)
            for i, p in enumerate(assign):
                by[p].append(O[i])
            for p, frames in by.items():
                obs = np.mean(frames, 0)
                if p not in theta:                                  # GROW the inventory (grow Gamma)
                    theta[p] = obs.copy(); cnt[p] = 1.0; durs[p] = float(len(frames)); phl = sorted(theta.keys())
                    continue
                conf = _conf_softmax(obs, theta, phl, p, sigma)
                tot_s += native_surprise(_S, conf); n += 1          # HELD native surprise term
                theta[p] = (cnt[p] * theta[p] + obs) / (cnt[p] + 1.0); cnt[p] += 1.0   # counted mean
                durs[p] = 0.9 * durs.get(p, len(frames)) + 0.1 * len(frames)
        traj.append(tot_s / max(n, 1))
    return theta, durs, traj


# ============================================================================
# OFFSET — the diagnosed CAREGIVER->REAL per-phone band offset. Computed against
# the REAL dev per-phone centroids (the band space theta lives in). Lower offset =
# theta sits closer to the real cluster means.
# ============================================================================

def dev_centroids(words, assign_fn=None, theta=None):
    """Real per-phone band means. assign_fn=None -> flat-start; else forced-align against `theta` (the best
    estimate of the true cluster means, the oracle reference)."""
    acc = defaultdict(list)
    for w, fr, ph in words:
        O = np.asarray(fr, float)
        a = flatstart_assign(O, ph) if assign_fn is None else assign_fn(O, ph, theta, np.mean(list(theta.values()), 0))
        for i, p in enumerate(a):
            acc[p].append(O[i])
    return {p: np.mean(v, 0) for p, v in acc.items() if len(v) > 2}


def offset_to(theta, ref):
    sh = [p for p in theta if p in ref]
    return float(np.mean([np.linalg.norm(theta[p] - ref[p]) for p in sh])) if sh else float("nan")


def comp(test_utts, vocab, lexicon, theta, durs, model, top_word, uni, lam):
    return coupled_comprehension(test_utts, vocab, lexicon, theta, durs, model, top_word, uni, lam=lam)


def run_arc(label, feat, raw_gw, raw_dev, raw_val, lexicon, vocab, chance, model, top_word, uni,
            quick, rng, t0):
    """Run the full staged arc IN ONE FEATURE SPACE (feat: band frames -> feature frames). Returns the
    per-stage comprehension + lever numbers. Transformed words are local (GC'd on return) to bound memory."""
    gw = transform_words(raw_gw, feat)
    dev_words = transform_words(raw_dev, feat)
    val_words = transform_words(raw_val, feat)
    N0 = 8 if quick else 12

    # STAGE 0 seed (poor early own-production) -> STAGE A grounding (flat-start init, FA / per-frame refine)
    seed = [gw[i] for i in rng.permutation(len(gw))[:N0]]
    theta0, durs0 = collect_targets_few(seed)
    theta_fl, durs_fl, _ = ground_model(theta0, durs0, gw, flat_assign, passes=3)
    theta_fa, durs_fa, traj_fa = ground_model(theta_fl, durs_fl, gw, forced_align, passes=2)
    theta_pf, durs_pf, _ = ground_model(theta_fl, durs_fl, gw, perframe_assign, passes=2)
    phs_all = sorted({p for _w, _f, ph in gw for p in ph})
    permd = list(rng.permutation(phs_all)); pmap = {phs_all[i]: permd[i] for i in range(len(phs_all))}
    gw_shuf = [(w, fr, [pmap.get(p, p) for p in ph]) for (w, fr, ph) in gw]
    theta_sh, durs_sh, _ = ground_model(theta_fl, durs_fl, gw_shuf, forced_align, passes=2)

    # OFFSET vs FA-aligned dev means (the best estimate of the true per-phone means, in THIS space)
    devc = dev_centroids(dev_words, forced_align, theta_fa)
    off0 = offset_to(theta0, devc); off_fa = offset_to(theta_fa, devc)
    off_fl = offset_to(theta_fl, devc); off_pf = offset_to(theta_pf, devc)

    test_dev = [_ordered_stream(dev_words)]
    test_val = [_ordered_stream(val_words)]

    # lam selection on the held-out train-clean slice (no dev leakage)
    lams = [0.0, 0.25, 0.5, 1.0]
    val_scores = [comp(test_val, vocab, lexicon, theta_fa, durs_fa, model, top_word, uni, l)["coupled_acc"]
                  for l in lams]
    lam_star = lams[int(np.argmax(val_scores))]

    # the staged arc + controls on dev
    r0 = comp(test_dev, vocab, lexicon, theta0, durs0, model, top_word, uni, 0.0)
    rA = comp(test_dev, vocab, lexicon, theta_fa, durs_fa, model, top_word, uni, 0.0)
    rB = comp(test_dev, vocab, lexicon, theta_fa, durs_fa, model, top_word, uni, lam_star)
    durs_oracle = {p: durs_fa.get(p, float(np.mean(list(durs_fa.values())))) for p in devc}
    rC = comp(test_dev, vocab, lexicon, devc, durs_oracle, model, top_word, uni, lam_star)
    rA_fl = comp(test_dev, vocab, lexicon, theta_fl, durs_fl, model, top_word, uni, 0.0)
    rA_pf = comp(test_dev, vocab, lexicon, theta_pf, durs_pf, model, top_word, uni, 0.0)
    rA_sh = comp(test_dev, vocab, lexicon, theta_sh, durs_sh, model, top_word, uni, 0.0)

    pts = [("theta_0", off0, r0['model_alone_acc']), ("per-frame", off_pf, rA_pf['model_alone_acc']),
           ("flat", off_fl, rA_fl['model_alone_acc']), ("FA", off_fa, rA['model_alone_acc'])]
    corr = float(np.corrcoef([p[1] for p in pts], [p[2] for p in pts])[0, 1])

    d = dict(label=label, stage0=r0['model_alone_acc'], stageA=rA['model_alone_acc'], stageB=rB['coupled_acc'],
             oracle=rC['coupled_acc'], lam_star=lam_star, n=rA['n'], chance=chance,
             fa_comp=rA['model_alone_acc'], fl_comp=rA_fl['model_alone_acc'], pf_comp=rA_pf['model_alone_acc'],
             shuf=rA_sh['model_alone_acc'], prior_alone=rB['prior_alone_acc'],
             off0=off0, off_fa=off_fa, off_fl=off_fl, off_pf=off_pf, corr=corr,
             whole_utt=(rA['model_alone_acc'] > rA_pf['model_alone_acc'] + 0.005),
             real_beats_shuf=(rA['model_alone_acc'] > rA_sh['model_alone_acc'] + 0.01),
             phones=len(theta_fa))
    print(f"\n  [{label}]  STAGE 0 {d['stage0']:.3f} -> A {d['stageA']:.3f} -> B {d['stageB']:.3f}  "
          f"| oracle {d['oracle']:.3f} | offset FA {off_fa:.3f}(corr {corr:+.2f}) | "
          f"FA>{d['pf_comp']:.3f}pf | shuf {d['shuf']:.3f} | lam* {lam_star} | n={d['n']}  "
          f"[{time.time()-t0:.0f}s]", flush=True)
    return d


def main():
    quick = "--quick" in sys.argv
    t0 = time.time(); rng = np.random.default_rng(0)
    print("=" * 104)
    print("COMPREHENSION-GRAIN DEVELOPMENT ARC — LEVER 3: LEARNED SUB-PART PARSE (K-sweep, inferred inventory)")
    print("  SPLIT: infer/fit/ground train-clean; lam on held-out train-clean slice; TEST dev-clean")
    print("=" * 104, flush=True)

    cal = _load_ph("train-clean-100_*.pkl", 4 if quick else 12)
    dev = _load_ph("dev-clean_*.pkl", 3 if quick else 8)
    lexicon = majority_lexicon(cal + dev)
    cidx = rng.permutation(len(cal)); n_g = int(0.85 * len(cal))
    cal_g = [cal[i] for i in cidx[:n_g]]; cal_v = [cal[i] for i in cidx[n_g:]]

    dev_count = Counter(w for w, _f, _p in dev)
    vocab = sorted([w for w, c in dev_count.items()
                    if w not in FUNC and len(w) >= 4 and c >= (4 if quick else 6) and w in lexicon])
    vocab = vocab[: (18 if quick else 28)]
    chance = 1.0 / len(vocab)

    # raw subsets shared across spaces (capped for memory/time: grounding small, dev/val bounded)
    NG = 200 if quick else 500
    raw_gw = cal_g[:NG]
    raw_dev = dev[: (3000 if quick else 14000)]
    raw_val = cal_v[: (3000 if quick else 5000)]
    print(f"  stream: cal_ground={len(cal_g)}  cal_val={len(cal_v)}  dev={len(dev)} words; "
          f"grounding {len(raw_gw)}, dev-test {len(raw_dev)}, val {len(raw_val)}", flush=True)
    print(f"  vocabulary (meaning units): {len(vocab)} words  (chance {chance:.3f})  e.g. {vocab[:6]}", flush=True)

    # COGNITIVE layer (word strings -> space-agnostic; computed once)
    cal_seqs = _windows([w for w, _f, _p in cal_g], 8)
    model, g1, g2, learned = cognitive_collapse(cal_seqs)
    cal_words = [w for w, _f, _p in cal_g]
    top_word = Counter(cal_words).most_common(1)[0][0]; uni = Counter(cal_words)
    print(f"  COGNITIVE collapse-grounding (word grain): pass-1 GAPS={g1} -> learned {learned} transitions; "
          f"pass-2 GAPS={g2}   [{time.time()-t0:.0f}s]", flush=True)

    # LEVER 3 — a LEARNED SUB-PART PARSE: split each phone into K identity-bearing sub-phone states (39xK
    # inventory), INFER the per-frame parse by Viterbi/EM (not fixed flat-start), fit the LDA on the inferred
    # sub-part labels. W is fixed at the lever-2 optimum (+-5). K=1 (flat) = the monophone-LDA baseline 0.321.
    # The richer INFERRED inventory is the lever the whole earn-not-borrow arc converges on. donkey=0.
    W = 5
    cap = 20000 if quick else 60000
    em_iters = 2 if quick else 3
    K_vit = [2, 3] if quick else [2, 3, 5]
    K_CTRL = 3                                            # K at which the parse-quality controls are run
    # configs: monophone anchor (K=1 flat), inferred sub-parts (K=2,3,5 viterbi), + parse-quality controls.
    configs = [("K1-flat(mono)", 1, "flat")]
    configs += [(f"K{K}-vit", K, "viterbi") for K in K_vit]
    configs += [(f"K{K_CTRL}-flat", K_CTRL, "flat"), (f"K{K_CTRL}-rand", K_CTRL, "random")]

    results = {}; meta = {}
    for label, K, mode in configs:
        enc, dim, nC = build_subpart_feature(cal_g, K, mode, W, em_iters, cap, rng)
        lex_sub = {w: expand_seq(seq, K) for w, seq in lexicon.items()}
        gw_sub = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in raw_gw]
        dev_sub = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in raw_dev]
        val_sub = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in raw_val]
        meta[label] = (K, mode, nC, dim)
        results[label] = run_arc(label, enc, gw_sub, dev_sub, val_sub, lex_sub, vocab, chance,
                                 model, top_word, uni, quick, rng, t0)
        print(f"      ({label}: K={K} {mode}, {nC} sub-parts, LDA dim {dim})", flush=True)

    mono = results["K1-flat(mono)"]                      # monophone-LDA anchor (~0.321)
    vit_labels = [f"K{K}-vit" for K in K_vit]
    best_K = max(K_vit, key=lambda K: results[f"K{K}-vit"]["oracle"])   # best inferred inventory by oracle
    best = results[f"K{best_K}-vit"]
    best_arc_K = max(K_vit, key=lambda K: results[f"K{K}-vit"]["stageA"])
    best_arc = results[f"K{best_arc_K}-vit"]
    ctrl_vit = results[f"K{K_CTRL}-vit"]; ctrl_flat = results[f"K{K_CTRL}-flat"]; ctrl_rand = results[f"K{K_CTRL}-rand"]

    print("\n" + "=" * 104)
    print("  LEARNED-SUB-PART-PARSE COMPARISON (comprehension on held-out dev-clean):")
    print(f"  {'config':16s} | {'STAGE0':>7} {'STAGE A':>8} {'STAGE B':>8} | {'oracle':>7} | "
          f"{'offset-corr':>11} | {'FA':>6} {'pf':>6} {'shuf':>6} | {'subparts':>8}")
    for label, _, _ in configs:
        r = results[label]; _K, _m, nC, _d = meta[label]
        print(f"  {label:16s} | {r['stage0']:>7.3f} {r['stageA']:>8.3f} {r['stageB']:>8.3f} | {r['oracle']:>7.3f} | "
              f"{r['corr']:>+11.2f} | {r['fa_comp']:>6.3f} {r['pf_comp']:>6.3f} {r['shuf']:>6.3f} | {nC:>8d}")
    print(f"  chance {chance:.3f} | n={mono['n']}")
    print("-" * 104)
    print("  K-SWEEP (inferred sub-parts/phone -> oracle ceiling / achieved STAGE A):")
    print(f"    K=1 (mono, flat) : oracle {mono['oracle']:.3f}  arc {mono['stageA']:.3f}  [the baseline]")
    for K in K_vit:
        r = results[f"K{K}-vit"]
        tag = "  <- best oracle" if K == best_K else ("  <- best arc" if K == best_arc_K else "")
        print(f"    K={K} (viterbi)    : oracle {r['oracle']:.3f}  arc {r['stageA']:.3f}{tag}")
    print("-" * 104)

    # ============================ GATES ====================================================
    ceiling_rises = best["oracle"] > mono["oracle"] + 0.01      # richer INFERRED inventory raises the oracle
    arc_climbs = best_arc["stageA"] > mono["stageA"] + 0.01     # ... and lifts the achieved arc vs monophone
    inferred_beats_flat = ctrl_vit["stageA"] > ctrl_flat["stageA"] + 0.005   # learned parse > fixed flat-start
    inferred_beats_rand = ctrl_vit["stageA"] > ctrl_rand["stageA"] + 0.005   # inferred structure > random subparts
    offset_holds = best_arc["corr"] < -0.5
    whole_utt_holds = best_arc["whole_utt"]
    print("  VERDICT (lever 3 — a LEARNED SUB-PART PARSE: richer INFERRED identity-bearing inventory):")
    print(f"    (a) CEILING RISES — best inferred oracle (K{best_K}) {best['oracle']:.3f} "
          f"({'> ' if ceiling_rises else '~= '}monophone {mono['oracle']:.3f})  => "
          f"{'HOLDS' if ceiling_rises else 'PLATEAU'}")
    print(f"    (b) ARC CLIMBS vs monophone — best arc (K{best_arc_K}) {best_arc['stageA']:.3f} "
          f"({'> ' if arc_climbs else '~= '}mono {mono['stageA']:.3f})  => {'HOLDS' if arc_climbs else 'PLATEAU'}")
    print(f"    (c) DISCRIMINATIVE (K={K_CTRL}) — INFERRED parse {ctrl_vit['stageA']:.3f} > FIXED flat-start "
          f"{ctrl_flat['stageA']:.3f} ({inferred_beats_flat}) AND > RANDOM sub-parts {ctrl_rand['stageA']:.3f} "
          f"({inferred_beats_rand}); real>shuffled grounding (best): {best_arc['real_beats_shuf']}")
    print(f"    (d) LEVERS STILL HOLD (best) — offset-pays-off corr {best_arc['corr']:+.2f} (<-0.5: {offset_holds}); "
          f"whole-utt FA {best_arc['fa_comp']:.3f} > per-frame {best_arc['pf_comp']:.3f}: {whole_utt_holds}")
    print(f"    (e) donkey=0: inventory+parse = agent's OWN Viterbi/EM (forced_align = held DTW-monotonic) on "
          f"held train-clean; DECISION=held DtwTo Term; no borrowed net/LLM/gradient-net.")
    if ceiling_rises and arc_climbs and (inferred_beats_flat or inferred_beats_rand):
        v = (f"WIN — a LEARNED sub-part parse RAISES the ceiling and LIFTS the arc (best K{best_arc_K}: arc "
             f"{best_arc['stageA']:.3f}, oracle {best['oracle']:.3f} vs monophone {mono['oracle']:.3f}); the "
             f"PARSE (inferred inventory), not a floor, was the lever.")
    elif best["oracle"] <= mono["oracle"] + 0.01:
        v = (f"PLATEAU/OVERFIT — the richer INFERRED inventory does NOT raise the oracle on the available data "
             f"(best K{best_K} oracle {best['oracle']:.3f} ~= monophone {mono['oracle']:.3f}). The sub-part "
             f"inventory is DATA-BOUND at this scale = the earn-not-borrow-is-data boundary. NEXT LEVER: MORE "
             f"held data to fit the richer parse (BPL learns its library from data) — tractable, not irreducible.")
    else:
        v = (f"MIXED — the inferred oracle rose (K{best_K} {best['oracle']:.3f}) but the achieved arc did not "
             f"clear monophone; the grounding/recogniser, not the inventory, now binds.")
    print(f"  => {v}")
    print("=" * 104, flush=True)
    print(f"  total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
