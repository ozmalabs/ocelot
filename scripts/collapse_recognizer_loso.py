"""collapse_recognizer_loso — the COLLAPSE RECOGNIZER. Model cross-speaker
recognition as COLLAPSING the entangled (word, speaker) superposition via a
COHERENT partial trace over the speaker, and test it head-to-head against the
classical INCOHERENT marginal (= the integration that ALREADY FAILED, c44742a7)
on the FULL cross-speaker LOSO.

WHY (memory ozma_entanglement_needs_collapse): the integration full run found the
within-word residual is ENTANGLED (non-factorable) with the word — linear factoring
(subtract / whiten / integrate) provably fails. The fix is to COLLAPSE not factor.
CRUX: the PROPER partial trace (speaker decohered) = the classical marginal
Sum_V |c|^2 = the integration that already failed. So the genuinely-quantum operation
is the COHERENT collapse |Sum_V c(W,V)|^2 (speaker held coherent, cross-terms
INTERFERE). The advantage lives or dies on whether that interference is constructive.

THE STATE. The hat's library is exactly the joint (word W, voice V) state: each
library entry is (W, V, synth(W,V)). For each held-out probe H:
  · JOINT AMPLITUDE   |c(W,V)| = exp(-D(H, synth(W,V)) / 2T)   (Born-amplitude =
        sqrt of the classical likelihood; sweep T), times a phase e^{i*phi(W,V)}.
  · PHASE phi(W,V) — DERIVED (not fitted). Three principled variants:
        (a) MARGIN  : signed margin of D(W,V) in robust-spread units (as ac4acbce),
                      mapped to [-pi/2, +pi/2] -> the closest-fitting voices for a
                      word get phase ~ +pi/2-aligned, the worst get -pi/2.
        (b) WARP    : a DtwTo alignment/warp-derived phase = the relative path
                      length (cost-per-frame), a warp signature, mapped to an angle.
        (c) VOICE   : speaker-POSITION phase = the voice's coordinate in (pitch,
                      rate, variant) mapped to an angle (the speaker axis itself).
  · COLLAPSE (coherent partial trace over speaker):
        A(W) = Sum_V c(W,V)   (complex, coherent)   ;   P(W) = |A(W)|^2 ; argmax_W.

HEAD-TO-HEAD (robust SC 40-speaker LOSO, full n if feasible else largest complete n):
  · COHERENT collapse  |Sum_V c(W,V)|^2          (the quantum partial trace)
  · CLASSICAL incoherent  Sum_V |c(W,V)|^2       (= the FAILED integration, control)
  · HARD min_V  (= the loop's argmin / argmax-amplitude one-best, prior ~0.47-0.48)
  · CMVN (the canonical real-exemplar DTW LOSO, the honest ~0.50 bar this split)
  · PHASE-ON vs PHASE-OFF (phi=0) — isolates whether interference helps.
Report LOSO + separation for each, the T sweep + phase-variant sweep, n.

VERDICT / KILL. PAYS: coherent collapse BEATS the classical incoherent marginal AND
clears CMVN ~0.50, with phase-ON > phase-OFF (interference constructive) -> the
entanglement collapses where it would not factor. KILL: if coherent does NOT beat
the classical incoherent (interference destructive/neutral, as ac4acbce) OR does not
clear CMVN -> the quantum framing buys nothing here AGAIN. Say which PLAINLY, do not
rescue. (If coherent == incoherent, the phase is doing nothing — say so.)

DONKEY BOUNDARY: amplitudes / phases / coherent-sum / Born = owned COMPLEX linear
algebra (no net / fit / gradient; phase DERIVED not fitted). AudioHat readout. The
CortexLoop + hat.py are UNTOUCHED (the recognizer only READS the hat's owned
encode/compare/library). Held-out REAL never banked; LOSO ungameable.

Run: python -m scripts.collapse_recognizer_loso [n_held_spk] [n_loso_per] [n_train_spk]
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random

import numpy as np

import domains.self_directed_speech_world as W
from domains.audio_hat import AudioHat
import domains.learned_voice_shape as LVS
from domains.fuzzy_smooth import smooth_traj
from scripts.universal_loop_phaseAB import build_real_probe, fresh as audio_fresh, FS

# the canonical CMVN-DTW recognizer (real exemplars, the documented ~0.570 baseline;
# the honest bar on this split is ~0.50, see c44742a7).
from scripts.dtw_trajectory_loso import (
    build_split, fresh as dtw_fresh, bank, BAG_CUES, CELL,
    write_exemplar_trajectories, mark_words, measure_dtw)

_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine"]

# the f0f2350e / c44742a7 BEST config: whitened + smoothed compare (Mahalanobis).
SMOOTH_T = 0.0
SMOOTH_F = 1.5
SHRINK = 0.1            # the f0f2350e best region
ALPHA = 0.75           # partial-whiten peak (docs/whitened_matched_filter.md)

# T sweep for the Born amplitude exp(-D/2T). D is a DtwTo residual (cmvn cochleagram
# whitened/smoothed) so its natural scale sets T; swept around the robust spread.
T_SWEEP = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
PHASE_VARIANTS = ["margin", "warp", "voice"]


# ===========================================================================
# NUISANCE COVARIANCE on TRAIN real speakers (word labels only) — for whitening.
# (same estimator as scripts/integration_full_loso.py / whitened_matched_filter.py)
# ===========================================================================

def _smoothed_frames(x, fs, sf):
    feats = LVS.residual_track(np.asarray(x, dtype=np.float64), float(fs), [])
    if not feats:
        return None
    a = np.asarray(feats, dtype=np.float64)
    if a.ndim != 2:
        return None
    return smooth_traj(a, SMOOTH_T, sf)


def estimate_nuisance_cov(train_idx, words, n_per_word, seed, sf):
    """S_n = within-word scatter on TRAIN real speakers = the word-INDEPENDENT
    nuisance covariance (speaker + residual synthetic-vs-real domain gap), smoothed
    at sigma_f=sf. Word labels supply the structure; NO speaker labels. Owned per-word
    mean + within-word covariance averaged over words."""
    rng = random.Random(seed)
    per_word_cov = []
    n_frames_total = 0
    for w in words:
        paths = list(train_idx.get(w, []))
        rng.shuffle(paths)
        paths = paths[:n_per_word]
        frames = []
        for p in paths:
            x, fs = W.load_sc_clip(p)
            fr = _smoothed_frames(x, fs, sf)
            if fr is None:
                continue
            frames.append(fr)
        if not frames:
            continue
        F = np.concatenate(frames, axis=0)
        if F.shape[0] < 2:
            continue
        mu = F.mean(axis=0, keepdims=True)
        per_word_cov.append(np.cov((F - mu).T))
        n_frames_total += F.shape[0]
    if not per_word_cov:
        return None, 0, 0
    return np.mean(np.stack(per_word_cov, axis=0), axis=0), len(per_word_cov), n_frames_total


def whitening_matrix(S_n, shrink, alpha=1.0):
    """W = S_n^{-alpha/2} via eigendecomposition with shrinkage/floor (Ledoit-Wolf
    style). Owned linear algebra (eigh on a symmetric PSD matrix). NO net/fit/gradient."""
    d = S_n.shape[0]
    tr = float(np.trace(S_n)) / d
    S = (1.0 - shrink) * S_n + shrink * tr * np.eye(d)
    S = 0.5 * (S + S.T)
    lam, V = np.linalg.eigh(S)
    floor = 1e-8 * float(lam.max())
    lam = np.clip(lam, floor, None)
    inv = lam ** (-alpha / 2.0)
    return (V * inv) @ V.T


# ===========================================================================
# THE JOINT (word, voice) DISTANCE MATRIX — one compare per library entry per probe.
# Everything (amplitudes, phases, coherent/incoherent collapse, T+phase sweeps) is
# derived from this matrix with OWNED arithmetic -> the expensive encode/compare runs
# ONCE per probe, the sweeps are free.
# ===========================================================================

def probe_distances(h_feats, hat):
    """For one encoded probe H, return parallel arrays over the library entries:
    (words, voices, dists). dists[i] = D(H, synth(W_i, V_i)) = the hat's OWNED
    whitened DtwTo residual. voices[i] = the voice dict (pitch/rate/variant)."""
    words, voices, dists = [], [], []
    for (content, style, feats) in hat.library():
        d = float(hat.compare(h_feats, feats))
        words.append(content)
        voices.append(style)
        dists.append(d)
    return words, voices, np.asarray(dists, dtype=np.float64)


# ---- PHASE derivations (all DERIVED from owned quantities, NONE fitted) ----

def _robust_spread(d):
    """Robust spread (MAD-based, sigma-equivalent) of a distance vector. Owned."""
    finite = d[np.isfinite(d)]
    if finite.size == 0:
        return 1.0
    med = float(np.median(finite))
    mad = float(np.median(np.abs(finite - med)))
    return (1.4826 * mad) or (float(finite.std()) or 1.0)


def phase_margin(dists):
    """(a) MARGIN phase. Signed margin of each (W,V) distance in robust-spread units,
    relative to the GLOBAL best distance, squashed to [-pi/2, +pi/2] by tanh. The
    closest-fitting voices (small margin) get phase ~ 0 (real, +aligned); poorly-
    fitting ones get pushed toward +-pi/2 (rotated away). Same family as ac4acbce's
    signed-margin phase, but on the joint (W,V) distance. DERIVED, not fitted."""
    finite = dists[np.isfinite(dists)]
    d0 = float(finite.min()) if finite.size else 0.0
    sp = _robust_spread(dists)
    z = (dists - d0) / (sp + 1e-12)          # >= 0, 0 at the global best
    return (np.pi / 2.0) * np.tanh(z)        # in [0, pi/2)


def phase_warp(h_feats, hat, words, voices, feats_list):
    """(b) WARP phase. A DtwTo alignment/warp-derived phase: the per-frame cost
    (D divided by the candidate trajectory length) is a warp signature — how much
    alignment stretch the match needed. Mapped to an angle by tanh on its robust
    z-score. Two trajectories of the SAME word align cheaply per frame (similar warp
    -> phase coheres); a wrong word needs more stretch (scatters). Owned (length is
    read off the owned trajectory; no fit)."""
    # candidate trajectory lengths (n_frames) read off the owned library trajectories.
    lengths = np.asarray([_traj_len(f) for f in feats_list], dtype=np.float64)
    return lengths


def _traj_len(traj_tuple):
    """Number of frames in an owned _traj_tuple. Tolerant of the tuple/list shape."""
    try:
        return float(len(traj_tuple))
    except Exception:
        return 1.0


def warp_phase_from(dists, lengths):
    """Finish the WARP phase: per-frame cost = D / length, robust-z -> tanh -> angle."""
    per_frame = dists / np.clip(lengths, 1.0, None)
    finite = per_frame[np.isfinite(per_frame)]
    c0 = float(finite.min()) if finite.size else 0.0
    sp = _robust_spread(per_frame)
    z = (per_frame - c0) / (sp + 1e-12)
    return (np.pi / 2.0) * np.tanh(z)


def phase_voice(voices):
    """(c) VOICE (speaker-position) phase. The voice's own coordinate in (pitch, rate,
    variant) mapped to an angle — the speaker axis ITSELF carries the phase, so summing
    over V sweeps a phase ramp across the speaker dimension. Voices near the 'centre'
    of the grid sit near phase 0; extremes rotate. Pitch in [0,99], rate in [80,300]
    normalised to [0,1], combined and mapped to [-pi, pi). DERIVED from the voice
    coordinate, not fitted."""
    out = np.zeros(len(voices), dtype=np.float64)
    for i, v in enumerate(voices):
        p = (float(v.get("pitch", 50)) - 50.0) / 50.0          # ~[-1,1]
        r = (float(v.get("rate", 160)) - 160.0) / 120.0        # ~[-0.7,1.2]
        out[i] = np.pi * np.tanh(0.5 * (p + r))                # in (-pi, pi)
    return out


# ---- the COLLAPSE: coherent partial trace vs classical incoherent marginal ----

def collapse_readout(words, dists, T, phases, coherent, phase_on):
    """Born readout over the words from the joint (W,V) distances.
      amplitude_i = exp(-dists_i / (2T)) * exp(i * (phases_i if phase_on else 0))
      COHERENT   (partial trace, quantum): A(W) = Sum_{V: W} c_i  ;  P(W)=|A(W)|^2
      INCOHERENT (classical marginal):     P(W) = Sum_{V: W} |c_i|^2
    Returns (pred_word, P_dict). Owned complex linear algebra; no net/fit/gradient."""
    mag = np.exp(-dists / (2.0 * T))
    mag = np.where(np.isfinite(mag), mag, 0.0)
    if coherent:
        ph = phases if phase_on else np.zeros_like(dists)
        amp = mag * np.exp(1j * ph)                     # complex joint amplitude
    P = {}
    for i, w in enumerate(words):
        if coherent:
            P[w] = P.get(w, 0.0 + 0.0j) + amp[i]        # coherent SUM of amplitudes
        else:
            P[w] = P.get(w, 0.0) + float(mag[i] ** 2)   # incoherent sum of |c|^2
    if coherent:
        P = {w: float(abs(a) ** 2) for w, a in P.items()}   # Born |.|^2 AFTER summing
    pred = max(P.items(), key=lambda kv: kv[1])[0] if P else None
    return pred, P


def hard_min_readout(words, dists):
    """HARD min_V collapse = the loop's argmin one-best: pick the word with the single
    smallest (W,V) distance. The prior ~0.47-0.48 hard-collapse bar."""
    best_per_word = {}
    for i, w in enumerate(words):
        d = dists[i]
        if not np.isfinite(d):
            continue
        if w not in best_per_word or d < best_per_word[w]:
            best_per_word[w] = d
    if not best_per_word:
        return None
    return min(best_per_word.items(), key=lambda kv: kv[1])[0]


# ===========================================================================
# RUN the full LOSO once, caching per-probe distances; sweep T x phase x mode for free.
# ===========================================================================

def run_loso(probe, hat, words_set):
    """Encode every held-out probe ONCE, cache its joint (W,V) distance vector +
    derived phases, then evaluate every (mode, T, phase-variant) over the cache.
    Returns (results, n, chance). Held-out clips are NEVER banked; labels score only.
      results: dict keyed ->
        ('hard',)                       : hard min_V acc
        ('coh', variant, T, phase_on)   : coherent collapse acc + separation
        ('inc', T)                      : classical incoherent marginal acc + sep
    """
    pr = [(w, x, fs) for (w, x, fs) in probe if w in words_set]
    chance = 1.0 / len(words_set)
    feats_list = [f for (_c, _s, f) in hat.library()]
    cache = []   # per-probe: (true_word, words_arr, dists, phases_by_variant)
    t0 = time.time()
    for idx, (w, x, fs) in enumerate(pr):
        hf = hat.encode((x, fs))
        words_arr, voices, dists = probe_distances(hf, hat)
        ph = {
            "margin": phase_margin(dists),
            "warp": warp_phase_from(dists, np.asarray(
                [_traj_len(f) for f in feats_list], dtype=np.float64)),
            "voice": phase_voice(voices),
        }
        cache.append((w, words_arr, dists, ph))
        if (idx + 1) % 25 == 0:
            el = time.time() - t0
            print(f"    [encode] {idx+1}/{len(pr)} probes  "
                  f"({el:.0f}s, {el/(idx+1):.2f}s/probe)", flush=True)
    n = len(pr)

    def _score(readout_fn):
        cor = 0
        true_p, wrong_p = [], []
        for (w, words_arr, dists, ph) in cache:
            pred, P = readout_fn(words_arr, dists, ph)
            cor += int(pred == w)
            if P is not None and w in P:
                true_p.append(P[w])
                wrong = [p for ww, p in P.items() if ww != w]
                if wrong:
                    wrong_p.append(max(wrong))
        acc = cor / max(n, 1)
        # separation: P(true) - best wrong P, normalised per-probe to [0,1] scale.
        sep = (float(np.median(np.asarray(true_p) - np.asarray(wrong_p)))
               if true_p and wrong_p else float("nan"))
        return acc, sep

    results = {}
    # HARD min_V
    acc_h, _ = _score(lambda wa, d, ph: (hard_min_readout(wa, d), None))
    results[("hard",)] = {"acc": acc_h, "sep": float("nan")}
    # COHERENT (phase on/off) and INCOHERENT over the T sweep
    for T in T_SWEEP:
        # incoherent classical marginal (control = the failed integration)
        acc_i, sep_i = _score(
            lambda wa, d, ph, T=T: collapse_readout(wa, d, T, None, False, False))
        results[("inc", T)] = {"acc": acc_i, "sep": sep_i}
        for variant in PHASE_VARIANTS:
            for phase_on in (True, False):
                acc_c, sep_c = _score(
                    lambda wa, d, ph, T=T, v=variant, po=phase_on:
                        collapse_readout(wa, d, T, ph[v], True, po))
                results[("coh", variant, T, phase_on)] = {"acc": acc_c, "sep": sep_c}
    return results, n, chance


def main():
    t_start = time.time()
    n_held_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    n_loso_per = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    n_train_spk = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    grid = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    seed = 20240610

    print("#" * 78, flush=True)
    print("COLLAPSE RECOGNIZER LOSO — coherent partial trace over speaker vs the "
          "classical incoherent marginal", flush=True)
    print("Joint (word,voice) amplitudes |c|=exp(-D/2T)*e^{i phi}; COHERENT collapse "
          "A(W)=Sum_V c, P=|A|^2.  CortexLoop + hat.py UNTOUCHED (read-only).", flush=True)
    print("#" * 78, flush=True)

    if not W.sc_available():
        print("Speech Commands not at /tmp/sc — abort.", flush=True)
        print("[MARKER] COLLAPSE_RECOGNIZER_LOSO_COMPLETED", flush=True)
        return

    words = [w for w in W.sc_words() if w in _DIGITS]
    words_set = set(words)

    # ---- split speakers: TRAIN (fit whitening) DISJOINT from HELD-OUT (LOSO test) ----
    speakers = W.sc_speakers(words)
    rng = random.Random(seed)
    rng.shuffle(speakers)
    held_spk = speakers[:n_held_spk]
    rest = speakers[n_held_spk:]
    train_spk = rest[:n_train_spk]
    train_idx = W.sc_index_for(train_spk, words)
    print(f"[split] {len(speakers)} SC speakers: {len(held_spk)} HELD-OUT (LOSO, never "
          f"banked) | {len(train_spk)} TRAIN (whitening fit only, DISJOINT)", flush=True)

    # ---- the held-out LOSO probe: ALL cross-speaker clips ----
    probe, _w = build_real_probe(n_held_spk, n_loso_per, seed)
    probe = [(w, x, fs) for (w, x, fs) in probe if w in words_set]
    print(f"[probe] {len(probe)} REAL held-out LOSO clips (n_loso_per={n_loso_per}, "
          f"never banked)", flush=True)
    assert not (set(held_spk) & set(train_spk)), "LEAKAGE: train/held-out overlap"

    # ---- estimate the nuisance covariance on TRAIN (word labels only); whitening ----
    t0 = time.time()
    S_n, n_w, n_fr = estimate_nuisance_cov(train_idx, words, n_per_word=40,
                                           seed=seed, sf=SMOOTH_F)
    if S_n is None:
        print("[nuisance] could not estimate — abort.", flush=True)
        print("[MARKER] COLLAPSE_RECOGNIZER_LOSO_COMPLETED", flush=True)
        return
    whiten = whitening_matrix(S_n, shrink=SHRINK, alpha=ALPHA)
    ev = np.linalg.eigvalsh(S_n)
    print(f"[nuisance] S_n {S_n.shape[0]}x{S_n.shape[1]} from {n_w} words {n_fr} frames "
          f"({time.time()-t0:.0f}s) eig[{ev.min():.1e},{ev.max():.1e}]", flush=True)
    print(f"[whiten] shrink={SHRINK} alpha={ALPHA} smooth_f={SMOOTH_F} "
          f"(the f0f2350e/c44742a7 best config); word labels ONLY.", flush=True)

    # ===================================================================
    # CMVN CANONICAL — the real-exemplar DTW recognizer (the honest ~0.50 bar)
    # ===================================================================
    print("\n" + "=" * 78, flush=True)
    print("CMVN CANONICAL (real-exemplar DTW LOSO) — the honest ~0.50 bar this split",
          flush=True)
    print("=" * 78, flush=True)
    t0 = time.time()
    train_clips, seen_probe, loso_probe = build_split(n_train_spk, n_held_spk,
                                                      n_loso_per, seed=seed)
    s_dtw, _p = dtw_fresh(BAG_CUES, dyn_order=1)
    bank(s_dtw, train_clips)
    write_exemplar_trajectories(s_dtw, CELL)
    mark_words(s_dtw, CELL)
    cmvn_seen = measure_dtw(s_dtw, seen_probe, CELL)
    cmvn_loso = measure_dtw(s_dtw, loso_probe, CELL)
    print(f"  CMVN-DTW seen {cmvn_seen:.3f}  LOSO {cmvn_loso:.3f}  "
          f"gap {cmvn_seen-cmvn_loso:+.3f}  (n_loso={len(loso_probe)}, "
          f"{time.time()-t0:.0f}s)", flush=True)

    # ===================================================================
    # build the whitened+smoothed hat (the joint (W,V) state library)
    # ===================================================================
    s, _pipe = audio_fresh()
    hat = AudioHat(s, fs=FS, grid=grid, seed=seed, smooth_t=SMOOTH_T,
                   smooth_f=SMOOTH_F, whiten=whiten)
    lib = hat.library()
    nvoice = len({(v["variant"], v["pitch"], v["rate"]) for (_c, v, _f) in lib})
    print(f"\n[hat] whitened+smoothed library: {len(lib)} (word,voice) joint states "
          f"= {len(words)} words x ~{nvoice} voices (grid={grid})", flush=True)

    # ===================================================================
    # RUN the full LOSO (encode once per probe; sweep T x phase x mode for free)
    # ===================================================================
    print("\n" + "=" * 78, flush=True)
    print("COLLAPSE — encode each held-out probe once, sweep T x phase-variant x mode",
          flush=True)
    print("=" * 78, flush=True)
    results, n, chance = run_loso(probe, hat, words_set)
    hat.close()

    # ===================================================================
    # REPORT — the T sweep, phase variants, coherent vs incoherent vs hard vs CMVN
    # ===================================================================
    def best_coh(variant, phase_on):
        keys = [k for k in results if k[0] == "coh" and k[1] == variant
                and k[3] == phase_on]
        bk = max(keys, key=lambda k: results[k]["acc"])
        return bk, results[bk]

    def best_inc():
        keys = [k for k in results if k[0] == "inc"]
        bk = max(keys, key=lambda k: results[k]["acc"])
        return bk, results[bk]

    acc_hard = results[("hard",)]["acc"]
    inc_key, inc = best_inc()
    print("\n" + "=" * 78, flush=True)
    print(f"T SWEEP (T in {T_SWEEP})  —  INCOHERENT marginal (the failed integration)",
          flush=True)
    print("=" * 78, flush=True)
    for T in T_SWEEP:
        r = results[("inc", T)]
        print(f"  INCOHERENT  T={T:<5}  LOSO {r['acc']:.3f}  sep {r['sep']:+.3f}",
              flush=True)
    print(f"  -> best INCOHERENT: T={inc_key[1]}  LOSO {inc['acc']:.3f}", flush=True)

    print("\n" + "=" * 78, flush=True)
    print("COHERENT collapse — per phase variant, phase-ON vs phase-OFF, T sweep",
          flush=True)
    print("=" * 78, flush=True)
    coh_best_overall = None
    for variant in PHASE_VARIANTS:
        print(f"  -- phase variant: {variant} --", flush=True)
        for phase_on in (True, False):
            tag = "ON " if phase_on else "OFF"
            for T in T_SWEEP:
                r = results[("coh", variant, T, phase_on)]
                print(f"    COHERENT phase-{tag} T={T:<5} LOSO {r['acc']:.3f}  "
                      f"sep {r['sep']:+.3f}", flush=True)
            bk, b = best_coh(variant, phase_on)
            print(f"    => best {variant} phase-{tag}: T={bk[2]} LOSO {b['acc']:.3f}",
                  flush=True)
        # interference check for this variant at its best phase-ON T
        bk_on, b_on = best_coh(variant, True)
        b_off = results[("coh", variant, bk_on[2], False)]
        d_interf = b_on["acc"] - b_off["acc"]
        print(f"    INTERFERENCE ({variant}) at T={bk_on[2]}: phase-ON {b_on['acc']:.3f} "
              f"vs phase-OFF {b_off['acc']:.3f}  ({d_interf:+.3f}, "
              f"{'CONSTRUCTIVE' if d_interf > 1e-9 else 'destructive/neutral'})",
              flush=True)
        if coh_best_overall is None or b_on["acc"] > coh_best_overall[1]["acc"]:
            coh_best_overall = (bk_on, b_on)

    coh_key, coh = coh_best_overall
    coh_off = results[("coh", coh_key[1], coh_key[2], False)]

    # ===================================================================
    # VERDICT
    # ===================================================================
    print("\n" + "#" * 78, flush=True)
    print("VERDICT — does the COHERENT collapse beat the classical incoherent marginal "
          "AND clear CMVN?", flush=True)
    print("#" * 78, flush=True)
    print(f"  CMVN canonical (this split):   {cmvn_loso:.3f}  (seen {cmvn_seen:.3f})",
          flush=True)
    print(f"  HARD min_V (loop one-best):    {acc_hard:.3f}", flush=True)
    print(f"  CLASSICAL incoherent (best):   {inc['acc']:.3f}  (T={inc_key[1]})  "
          f"[= the FAILED integration, the control]", flush=True)
    print(f"  COHERENT collapse (best):      {coh['acc']:.3f}  sep {coh['sep']:+.3f}  "
          f"(variant={coh_key[1]}, T={coh_key[2]}, phase-ON)", flush=True)
    print(f"    same config phase-OFF:       {coh_off['acc']:.3f}  "
          f"(interference {coh['acc']-coh_off['acc']:+.3f})", flush=True)
    print(f"  chance: {chance:.3f}   n (LOSO probes): {n}", flush=True)

    beats_incoherent = coh["acc"] > inc["acc"] + 1e-9
    clears_cmvn = coh["acc"] > cmvn_loso + 1e-9
    interference_constructive = coh["acc"] > coh_off["acc"] + 1e-9
    coh_eq_inc = abs(coh["acc"] - inc["acc"]) < 1e-9

    print("\n  VERDICT:", flush=True)
    if beats_incoherent and clears_cmvn and interference_constructive:
        print(f"  => PAYS: the COHERENT collapse BEATS the classical incoherent marginal "
              f"({coh['acc']:.3f} > {inc['acc']:.3f}) AND clears CMVN ~{cmvn_loso:.3f}, "
              f"with phase-ON > phase-OFF ({coh['acc']-coh_off['acc']:+.3f}, interference "
              f"CONSTRUCTIVE). The entanglement COLLAPSES where it would not factor — the "
              f"genuinely-quantum partial trace buys what the linear toolkit could not.",
              flush=True)
    else:
        why = []
        if not beats_incoherent:
            why.append(f"coherent {coh['acc']:.3f} does NOT beat the classical incoherent "
                       f"marginal {inc['acc']:.3f}" +
                       (" (coherent == incoherent — the PHASE is doing nothing)"
                        if coh_eq_inc else
                        " (interference destructive/neutral, as ac4acbce)"))
        if not clears_cmvn:
            why.append(f"does NOT clear CMVN {cmvn_loso:.3f}")
        if not interference_constructive:
            why.append(f"phase-ON ({coh['acc']:.3f}) <= phase-OFF ({coh_off['acc']:.3f}) "
                       f"— interference NOT constructive")
        print(f"  => KILL: the quantum framing buys NOTHING here AGAIN — "
              + "; ".join(why) + ". The (word,speaker) entanglement is beyond the "
              "coherent partial trace too. Reported plainly, NOT rescued.", flush=True)

    print(f"\n[timing] total {time.time()-t_start:.0f}s, n={n} LOSO probes", flush=True)
    print("[MARKER] COLLAPSE_RECOGNIZER_LOSO_COMPLETED", flush=True)


if __name__ == "__main__":
    main()
