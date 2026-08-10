"""RICHER M — close the agent's-own-voice gap with a MULTIMODAL, CONTEXT-COARTICULATED model M.

CONTEXT (commit 307c9488, scripts/babble_own_model_grounded.py). The agent's OWN production model M
(held render_dynamic = gestural plan -> min-jerk coarticulated cochlear trajectory) produces its babble;
XTTS is a SPARSE GROUNDING STEP ONLY (corrects the inventory theta), absent at inference. M-babble
transfer to real LibriSpeech rose 0.010 (ungrounded) -> ~0.067 (full single-centroid grounded) vs the
XTTS-trained-directly ceiling ~0.103 (~= the per-frame metric ceiling ~0.10-0.13).

THE NAMED REMAINING GAP: M's forward-model is OVER-IDEALIZED — it renders every utterance of a phone
through a SINGLE per-phone centroid theta[p] + an isotropic global scatter, with a SYMMETRIC fixed
coarticulatory undershoot. Real phones are MULTIMODAL (allophones / context / speaker) and their
realization + undershoot is CONTEXT-DEPENDENT. THIS BUILD enriches M on exactly those two axes,
keeping the held min-jerk motor model (NOT a new synth), and grounds the richness against the caregiver.

THE TWO ENRICHMENTS (genuine additions over the single-centroid baseline):
  (1) MULTIMODAL K-CENTROID theta — replace the single per-phone centroid with K grounded modes/phone
      (GMM-like). Grounded against the caregiver through the HELD collapse cognition: per-phone
      observations are clustered into K modes (k-means init), then refined by COUNTED structure-add
      (online assignment -> running-mean update = grow Gamma) with the HELD native SURPRISE term tracking
      the grounding. M then SAMPLES among the K modes (weighted by mode counts) when it babbles -> the
      corpus carries the caregiver's real WITHIN-PHONE multimodality, not an isotropic blob.
  (2) RICHER COARTICULATION — M's trajectory targets become CONTEXT-DEPENDENT: which of the K modes is
      realized is selected by the neighbour context (the allophone nearest the neighbours' targets), and
      the min-jerk undershoot is ASYMMETRIC (neighbour-duration-weighted: pulled more toward the shorter
      neighbour). Still the held min-jerk motor model (render trajectory + low-pass = bounded jerk),
      enriched.

GATE (controls, donkey=0, honest):
  MAIN          — M-babble transfer with multimodal-theta + richer-coartic vs the single-centroid
                  baseline vs the XTTS-direct ceiling. How much of the remaining gap closes?
  ABLATION      — K in {1,2,4,8} x coarticulation {OFF=symmetric-baseline, ON=context+asymmetric}: which
                  lever contributes what, where K saturates.
  DISCRIMINATIVE— multimodal theta grounded against the REAL caregiver beats DEGENERATE random-K modes
                  (richness carries real signal, not just params); richer-coartic beats a STATIC-target
                  collapse (step render, no trajectory).
  XTTS-NOT-REQUIRED — grounding sparse (N_ground caregiver clips << M-babble corpus); no torch/TTS
                  imported here; M (render) is the bulk producer.

EARN / donkey=0: PRODUCTION = held render_dynamic motor model (enriched, numpy adapter as every AbS
script); GROUNDING = held collapse cognition (native surprise + counted structure-add, now K-mode);
RECOGNISER = the agent's own from-scratch PCA->LDA + per-phone centroids. XTTS only the sparse grounding
target (wavs off disk -> the agent's own cochleagram). No LLM / borrowed net / gradient.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/babble_richer_m.py [--quick]
"""
from __future__ import annotations
import os
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np

import substrate_rs as _srs
from scripts.dynamic_sequence_speech_abs import _smooth
from scripts.speech_one_model_plug import ground_targets, flatstart_assign
from scripts.native_collapse import native_surprise
from scripts.babble_transfer import (
    em_train, per_frame_acc, build_eval, load_real_samples, load_synth_samples, CMU39,
)
from scripts.jabberwock_reads_oov_from_phones import phones as cmu_phones
# REUSE the baseline loop's helpers verbatim (apples-to-apples single-centroid reference) ------------
from scripts.babble_own_model_grounded import (
    VOCAB, babble_lexicon, load_caregiver, crude_theta, caregiver_scatter, render_babble,
)

_S = _srs.Substrate()  # held substrate for the native SURPRISE term


# ============================================================================
# (1) MULTIMODAL K-CENTROID GROUNDING — held collapse cognition, K modes/phone.
# ============================================================================
def _collect_phone_obs(grounding_words):
    """one observation per (utterance, phone) = the per-phone frame-mean within an utterance (same unit
    the single-centroid grounding uses). The SPREAD of these across utterances is the within-phone
    multimodality (allophone / context / speaker) the K modes will capture. Also returns mean durations."""
    by = defaultdict(list)
    dur = defaultdict(list)
    for w, fr, ph in grounding_words:
        O = np.asarray(fr, float)
        assign = flatstart_assign(O, ph)
        d = defaultdict(list)
        for i, p in enumerate(assign):
            d[p].append(O[i])
        for p, frs in d.items():
            by[p].append(np.mean(frs, 0))
            dur[p].append(len(frs))
    durs = {p: float(np.mean(v)) for p, v in dur.items()}
    return by, durs


def _kmeans(X, K, iters=8, seed=0):
    """tiny k-means -> up to K within-phone modes + their occupancy counts (the mode weights)."""
    rng = np.random.default_rng(seed)
    if len(X) <= K:
        return X.copy(), np.ones(len(X))
    C = X[rng.choice(len(X), K, replace=False)].copy()
    lab = np.zeros(len(X), int)
    for _ in range(iters):
        lab = ((X[:, None, :] - C[None]) ** 2).sum(2).argmin(1)
        for k in range(K):
            m = X[lab == k]
            if len(m):
                C[k] = m.mean(0)
    cnt = np.array([max(1, int((lab == k).sum())) for k in range(K)], float)
    return C, cnt


def _conf_softmax_k(obs, modes, phl, p_true, sigma):
    """recognition confidence at the true phone = softmax over the inventory of the NEAREST-MODE squared
    distance (numpy adapter measurement, as the held AbS scripts compute distances); the SURPRISE on it
    is the held native Rust term."""
    d2 = np.array([((modes[q] - obs) ** 2).sum(1).min() for q in phl])
    w = np.exp(-(d2 - d2.min()) / (2.0 * sigma * sigma))
    z = w.sum()
    return float(w[phl.index(p_true)] / z) if z > 0 else 0.0


def ground_targets_k(theta0, durs0, grounding_words, K, passes=3, sigma=2.0, seed=0):
    """EXTERNAL grounding of a MULTIMODAL inventory through the held collapse cognition. Per-phone
    observations are clustered into K modes (k-means init); each pass re-assigns every observation to its
    nearest mode and REFINES that mode toward the observation by a COUNTED running mean (structure-add =
    grow Gamma; NOT a gradient), with the held native SURPRISE term tracking the grounding. Phones unseen
    in grounding fall back to theta0's single centroid.

    Returns (modes:{p->(Kp,D)}, cnt:{p->(Kp,)}, durs, surprise_trajectory)."""
    by, durs_obs = _collect_phone_obs(grounding_words)
    modes, cnt = {}, {}
    durs = dict(durs0)
    for p, obsl in by.items():
        C, cc = _kmeans(np.asarray(obsl), K, seed=seed)
        modes[p] = C
        cnt[p] = cc
        durs[p] = durs_obs.get(p, durs0.get(p, 5.0))
    for p, v in theta0.items():          # phones M had but grounding lacked: keep the single centroid
        if p not in modes:
            modes[p] = np.asarray(v)[None, :].copy()
            cnt[p] = np.ones(1)
    phl = sorted(modes.keys())
    traj = []
    for _it in range(passes):
        tot_s, n = 0.0, 0
        for p, obsl in by.items():
            for obs in obsl:
                k = int(((modes[p] - obs) ** 2).sum(1).argmin())   # assign to nearest mode
                tot_s += native_surprise(_S, _conf_softmax_k(obs, modes, phl, p, sigma))
                n += 1
                modes[p][k] = (cnt[p][k] * modes[p][k] + obs) / (cnt[p][k] + 1.0)  # counted add
                cnt[p][k] += 1.0
        traj.append(tot_s / max(n, 1))
    return modes, cnt, durs, traj


# ============================================================================
# (2) RICHER COARTICULATION — context-dependent mode selection + asymmetric
#     neighbour-weighted undershoot, on the held min-jerk motor model.
# ============================================================================
def _sample_mode(C, cc, rng):
    """sample a mode weighted by occupancy (the corpus carries the caregiver's multimodal spread)."""
    if len(C) == 1:
        return C[0]
    return C[rng.choice(len(C), p=cc / cc.sum())]


def _context_select(ph, modes, gmean):
    """RICHER COARTICULATION (which allophone): left-to-right, pick the phone's mode NEAREST the neighbour
    context (mean of the already-selected left target and the right phone's mean) — the realized allophone
    tracks its neighbours, as in real coarticulation."""
    K = len(ph)
    cand = [modes.get(p, gmean[None, :]) for p in ph]
    sel = []
    for k in range(K):
        C = cand[k]
        if len(C) == 1:
            sel.append(C[0])
            continue
        left = sel[k - 1] if k > 0 else C.mean(0)
        right = cand[k + 1].mean(0) if k < K - 1 else C.mean(0)
        anchor = 0.5 * (left + right)
        sel.append(C[((C - anchor) ** 2).sum(1).argmin()])
    return sel


def _render_from_canon(canon, d, dmean, undershoot, coartic):
    """The held min-jerk motor model rendering a per-position target list. undershoot pulls each target
    toward its neighbours (the bounded-jerk low-pass = articulatory inertia). coartic OFF = the ORIGINAL
    SYMMETRIC undershoot (baseline render_dynamic); coartic ON = ASYMMETRIC, neighbour-duration-weighted
    (pulled more toward the shorter neighbour, which undershoots more)."""
    K = len(canon)
    eff = []
    for k in range(K):
        if K == 1:
            eff.append(canon[k])
            continue
        left = canon[k - 1] if k > 0 else canon[k]
        right = canon[k + 1] if k < K - 1 else canon[k]
        u = undershoot / (1.0 + d[k] / 3.0)
        if coartic:
            wl = 1.0 / (1.0 + (d[k - 1] if k > 0 else d[k]) / 3.0)
            wr = 1.0 / (1.0 + (d[k + 1] if k < K - 1 else d[k]) / 3.0)
            s = wl + wr + 1e-9
            eff.append((1.0 - u) * canon[k] + u * (wl / s) * left + u * (wr / s) * right)
        else:
            eff.append((1.0 - u) * canon[k] + 0.5 * u * left + 0.5 * u * right)
    starts = np.cumsum([0.0] + list(d))
    M = max(2, int(round(starts[-1])))
    centers = np.array([(starts[k] + starts[k + 1]) / 2.0 for k in range(K)])
    E = np.stack(eff)
    t = np.arange(M)
    traj = np.stack([np.interp(t, centers, E[:, b]) for b in range(E.shape[1])], 1)
    return _smooth(traj, max(3, int(0.6 * dmean)))


def _render_static(canon, d, dmean):
    """STATIC-TARGET COLLAPSE (the coartic discriminative): a step function of the targets, no trajectory,
    no undershoot, no min-jerk — the ablation that throws away the motor model entirely."""
    blocks = [np.tile(canon[k], (max(1, int(round(d[k]))), 1)) for k in range(len(canon))]
    return np.vstack(blocks) if blocks else np.zeros((2, len(canon[0])))


def render_babble_k(lex, modes, cnt, durs, gstd, coartic, sigma=0.2, reps=2, seed=1, static=False):
    """M PRODUCES its OWN babble from the MULTIMODAL inventory. For each chosen word: duration + undershoot
    jitter + `reps` draws give within-class variation; the K modes give within-phone MULTIMODALITY
    (sampled when coartic OFF; context-SELECTED when coartic ON); a small residual gstd scatter adds
    fine within-mode spread. All FREE-labelled (M chose the phone seqs). -> [(word, M, None, phones)]."""
    rng = np.random.default_rng(seed)
    gmean = np.mean([modes[p].mean(0) for p in modes], 0)
    dmean = float(np.mean(list(durs.values())))
    dur_mults = [0.85, 1.0, 1.2]
    undershoots = [0.2, 0.35, 0.5]
    samples = []
    for w, ph in lex.items():
        for dm in dur_mults:
            d = [max(1.0, durs.get(p, dmean) * dm) for p in ph]
            for us in undershoots:
                for _ in range(reps):
                    if coartic:
                        canon = _context_select(ph, modes, gmean)
                    else:
                        canon = [_sample_mode(modes.get(p, gmean[None, :]),
                                              cnt.get(p, np.ones(1)), rng) for p in ph]
                    if static:
                        M = _render_static(canon, d, dmean)
                    else:
                        M = _render_from_canon(canon, d, dmean, us, coartic)
                    if sigma > 0:
                        M = M + rng.standard_normal(M.shape) * sigma * gstd[None, :]
                    if M.shape[0] >= len(ph):
                        samples.append((w, np.asarray(M, float), None, list(ph)))
    return samples


def degenerate_modes(modes, scale_mean, scale_std, seed=7):
    """DISCRIMINATIVE control: same K-mode SHAPE but RANDOM per-mode targets at the global frame scale
    (no caregiver identity). If the multimodal lift is real signal (not just more params), grounded
    modes >> these degenerate modes."""
    rng = np.random.default_rng(seed)
    return {p: (scale_mean + rng.standard_normal(C.shape) * scale_std).astype(float)
            for p, C in modes.items()}


def transfer_of(samples, Xe, Ye, shared, label):
    t = time.time()
    acc = per_frame_acc(em_train(samples), Xe, Ye, shared)
    print(f"  [{label:34s}] {len(samples):5d} renders -> real per-frame acc = {acc:.3f}"
          f"   [{time.time()-t:.0f}s]", flush=True)
    return acc


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 100)
    print("RICHER M — multimodal K-centroid theta + context coarticulation closes the own-voice gap (donkey=0)")
    print("=" * 100, flush=True)

    shared = CMU39
    lex = babble_lexicon()
    all_phones = sorted({p for ph in lex.values() for p in ph})
    print(f"  M's chosen repertoire: {len(lex)} words over {len(all_phones)} phones", flush=True)

    real_dev = load_real_samples("dev-clean_*.pkl", 6 if quick else 8)[:1200 if quick else 1500]
    Xe, Ye = build_eval(real_dev, shared)
    maj = Counter(Ye).most_common(1)[0]
    chance = 1.0 / len(shared)
    print(f"  REAL dev eval: {len(real_dev)} words, {len(Ye)} frames; chance {chance:.3f}, "
          f"majority('{maj[0]}') {maj[1]/len(Ye):.3f}", flush=True)

    n_ground = 120 if quick else 250
    xtts_care = load_caregiver("xtts", n_ground)
    print(f"  caregiver grounding clips (SPARSE, a STEP): XTTS {len(xtts_care)}", flush=True)
    allfr = np.concatenate([M for _w, M, _ph in xtts_care])
    scale_mean, scale_std = allfr.mean(0), allfr.std(0)
    theta0, durs0 = crude_theta(all_phones, scale_mean, scale_std)
    gstd_x = caregiver_scatter(xtts_care)
    passes = 2 if quick else 3
    Ks = [1, 2, 4, 8]

    results = {}

    # ---- BASELINE (the published single-centroid path, verbatim) -----------------------------------
    print("-" * 100)
    print("  BASELINE — single-centroid grounding + original render (the 0.067 reference path):", flush=True)
    th_b, du_b, _tb = ground_targets(theta0, durs0, xtts_care, passes=passes)
    samp_b = render_babble(lex, th_b, du_b, gstd_x)
    base = transfer_of(samp_b, Xe, Ye, shared, "single-centroid baseline")
    results[("baseline", 1, "orig")] = base

    # ---- ABLATION GRID: K x coarticulation ---------------------------------------------------------
    print("-" * 100)
    print("  ABLATION — multimodal K x coarticulation {OFF=symmetric, ON=context+asymmetric}:", flush=True)
    grid = {}
    last_traj = None
    for K in Ks:
        modes, cnt, durs, traj = ground_targets_k(theta0, durs0, xtts_care, K, passes=passes)
        last_traj = traj
        for coartic in (False, True):
            samp = render_babble_k(lex, modes, cnt, durs, gstd_x, coartic)
            acc = transfer_of(samp, Xe, Ye, shared,
                              f"K={K} coartic={'ON ' if coartic else 'OFF'}")
            grid[(K, coartic)] = acc
    print(f"      (K=8 grounding surprise trajectory {['%.3f' % s for s in last_traj]})", flush=True)

    # best enriched cell
    bestK, bestC = max(grid, key=lambda kc: grid[kc])
    best = grid[(bestK, bestC)]

    # ---- DISCRIMINATIVE controls ------------------------------------------------------------------
    print("-" * 100)
    print("  DISCRIMINATIVE — richness carries real signal, coartic beats static collapse:", flush=True)
    modes4, cnt4, durs4, _ = ground_targets_k(theta0, durs0, xtts_care, 4, passes=passes)
    deg = degenerate_modes(modes4, scale_mean, scale_std)
    samp_deg = render_babble_k(lex, deg, cnt4, durs4, gstd_x, coartic=True)
    acc_deg = transfer_of(samp_deg, Xe, Ye, shared, "DEGENERATE random-K modes (coartic ON)")
    samp_stat = render_babble_k(lex, modes4, cnt4, durs4, gstd_x, coartic=True, static=True)
    acc_stat = transfer_of(samp_stat, Xe, Ye, shared, "STATIC-collapse render (K=4)")

    # ---- REFERENCES -------------------------------------------------------------------------------
    print("-" * 100)
    print("  REFERENCE POINTS (NOT M's own babble — what M aims to approach):", flush=True)
    xtts_audio = load_synth_samples("xtts")
    ref_xtts = transfer_of(xtts_audio, Xe, Ye, shared, "[ref] XTTS-trained-DIRECTLY (audio)")
    real_train = load_real_samples("train-clean-100_*.pkl", 4 if quick else 6)[:3000 if quick else 4000]
    ref_real = transfer_of(real_train, Xe, Ye, shared, "[ref] real(EM) ceiling")

    # ---- SUMMARY + verdict ------------------------------------------------------------------------
    print("=" * 100)
    print("  ABLATION GRID (per-frame phone acc on REAL dev-clean):")
    print(f"    {'':10s} " + "  ".join(f"K={K:>2}" for K in Ks))
    for coartic in (False, True):
        row = "  ".join(f"{grid[(K, coartic)]:.3f}" for K in Ks)
        print(f"    coartic {'ON ' if coartic else 'OFF'}: {row}")
    print("-" * 100)
    print(f"    {'uniform chance':40s} {chance:.3f}")
    print(f"    {'majority-phone baseline':40s} {maj[1]/len(Ye):.3f}")
    print(f"    {'single-centroid baseline':40s} {base:.3f}")
    print(f"    {'BEST enriched (K=%d coartic=%s)' % (bestK, 'ON' if bestC else 'OFF'):40s} {best:.3f}")
    print(f"    {'DEGENERATE random-K modes':40s} {acc_deg:.3f}")
    print(f"    {'STATIC-collapse render':40s} {acc_stat:.3f}")
    print(f"    {'[ref] XTTS-trained-DIRECTLY':40s} {ref_xtts:.3f}")
    print(f"    {'[ref] real(EM)=ceiling':40s} {ref_real:.3f}")
    print("-" * 100)

    closed_base = (best - base) / max(ref_xtts - base, 1e-9)
    n_babble = len(samp_stat)
    print(f"  MAIN: M-babble single-centroid {base:.3f} -> richer-M {best:.3f} "
          f"(K={bestK}, coartic={'ON' if bestC else 'OFF'}); XTTS-direct {ref_xtts:.3f}.")
    print(f"        of the REMAINING baseline->XTTS gap, richer M closes {100*closed_base:.0f}%.")
    # K saturation
    onrow = [grid[(K, True)] for K in Ks]
    print(f"  ABLATION: coartic-ON across K={Ks} = {['%.3f' % a for a in onrow]} "
          f"(best K={Ks[int(np.argmax(onrow))]}); coartic ON beats OFF at best K: "
          f"{grid[(bestK, True)] >= grid[(bestK, False)]}")
    print(f"  DISCRIMINATIVE: grounded K-modes {grid[(4, True)]:.3f} >> degenerate random-K "
          f"{acc_deg:.3f}: {grid[(4, True)] > acc_deg + 0.02}; richer render {best:.3f} >> static "
          f"collapse {acc_stat:.3f}: {best > acc_stat + 0.02}")
    print(f"  XTTS-NOT-REQUIRED: grounding used {len(xtts_care)} XTTS clips (a STEP); M produced "
          f"{n_babble} renders -> ratio {n_babble/max(len(xtts_care),1):.1f}x. No torch/TTS imported.")
    print(f"  donkey=0: production=held render_dynamic (enriched); grounding=held collapse cognition "
          f"(native surprise + counted K-mode add); recogniser=own from-scratch. No LLM/net/gradient.")
    print("=" * 100)
    print(f"  total {time.time()-t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
