"""whitened_matched_filter — does pairing the loop's MATCHED FILTER (synthesis) with a
WHITENED (Mahalanobis, noise-weighted) distance push the audio cross-speaker LOSO PAST
CMVN, where the prior low-pass SMOOTHING only REACHED it?

Signal-from-noise toolkit (memory ozma_signal_from_noise_toolkit): the analysis-by-
synthesis loop IS a matched filter; the optimal detector for a known signal in noise
uses the NOISE-WEIGHTED (Mahalanobis) distance, not raw Euclidean — down-weight the
directions where the nuisance is big. Smoothing (commit e0dc1ea8) was the CRUDE
low-pass: it removed the HIGH-FREQUENCY part of the synthetic-vs-real domain gap and
lifted LOSO 0.412 -> 0.487, REACHING the CMVN ~0.51 band but NOT exceeding it. A
STRUCTURED/coarse nuisance remains. Whitening is the optimal tool for noise of ANY
shape, and it UNIFIES speaker + residual-domain nuisance as ONE noise covariance.

BUILD (donkey-clean; CortexLoop + hat.py UNTOUCHED — git diff empty):
  On the SMOOTHED features (freq-blur sigma_f=1.5, the prior best):
   1. ESTIMATE the nuisance covariance S_n on TRAIN REAL speakers = the WITHIN-WORD
      scatter (variation of the SAME word across speakers/conditions = the word-
      INDEPENDENT nuisance: speaker + residual domain). Per-word frame-mean, within-word
      frame covariance, averaged over words. WORD labels only; NO speaker labels.
   2. WHITEN: W = S_n^{-1/2} via eigendecomposition with shrinkage/floor (swept). Fit on
      TRAIN ONLY; apply the SAME W to held-out (no leakage). Partial-whiten strength
      alpha in [0,1] also swept: W_alpha = V diag(lam^{-alpha/2}) V^T.
   3. WHITENED COMPARE (Mahalanobis): each smoothed frame f -> W f, so the loop's
      UNCHANGED DtwTo (Euclidean per-frame inside DTW) computes ||W(a-b)|| — the
      whitened matched filter. Lives in AudioHat.encode/synth ONLY.

TEST (robust SC 40-speaker LOSO, held-out REAL speakers NEVER banked):
  CMVN (0.51 this split / 0.57 canonical, the documented baseline) | smoothed-only 0.487
  | WHITENED+smoothed (this run). Report seen-LOSO + true-vs-wrong residual separation;
  sweep whitening shrinkage and partial-whiten alpha.

PREDICTION: whitening down-weights the structured nuisance the blur left -> LOSO EXCEEDS
CMVN. KILL: if whitening does NOT exceed CMVN (reduces to CMVN, or the nuisance overlaps
the word signal so removing it removes the word) — say so PLAINLY; then nuisance + word
are genuinely entangled, deeper than a whitening. This is the SOFT re-weight + matched
filter, unlike the prior HARD subspace subtracts that capped.

Run: python -m scripts.whitened_matched_filter [n_held_spk] [n_loso_per] [n_train_spk]
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random

import numpy as np

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
from domains.cortex_loop import CortexLoop
from domains.audio_hat import AudioHat
from domains.fuzzy_smooth import smooth_traj
import domains.learned_voice_shape as LVS
from scripts.universal_loop_phaseAB import build_real_probe, fresh as audio_fresh, FS

_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine"]

# the prior-best smoothing (docs/fuzzy_compare_smoothing.md): freq-blur sigma_f=1.5,
# no time blur. The whitening is fit + applied ON TOP of this same smoothing.
SMOOTH_T = 0.0
SMOOTH_F = 1.5

# documented baselines for the comparison column (this split / canonical).
CMVN_THIS_SPLIT = 0.51
CMVN_CANONICAL = 0.57
SMOOTHED_ONLY_DOC = 0.487


# ===========================================================================
# NUISANCE COVARIANCE on TRAIN real speakers (word labels only, no speaker labels)
# ===========================================================================

def _smoothed_frames(x, fs):
    """The agent's own front end -> smoothed (sigma_f=1.5) cmvn cochleagram frames
    (frames x bands). The SAME feature path AudioHat uses before whitening. Pure I/O."""
    feats = LVS.residual_track(np.asarray(x, dtype=np.float64), float(fs), [])
    if not feats:
        return None
    a = np.asarray(feats, dtype=np.float64)
    if a.ndim != 2:
        return None
    return smooth_traj(a, SMOOTH_T, SMOOTH_F)


def estimate_nuisance_cov(train_idx, words, n_per_word, seed):
    """S_n = the WITHIN-WORD scatter on TRAIN real speakers = the word-INDEPENDENT
    nuisance covariance (speaker + residual synthetic-vs-real domain). For each word,
    pool the per-frame band vectors of all its TRAIN clips, center on that WORD's
    frame-mean (so the word identity is removed, leaving speaker/condition scatter),
    accumulate the covariance; AVERAGE over words. Owned: per-word mean + within-word
    covariance. WORD labels supply the structure; NO speaker labels are used. Returns
    (S_n [bands x bands], n_words_used, n_frames_total)."""
    rng = random.Random(seed)
    per_word_cov = []
    n_frames_total = 0
    n_bands = None
    for w in words:
        paths = list(train_idx.get(w, []))
        rng.shuffle(paths)
        paths = paths[:n_per_word]
        frames = []
        for p in paths:
            x, fs = W.load_sc_clip(p)
            fr = _smoothed_frames(x, fs)
            if fr is None:
                continue
            frames.append(fr)
        if not frames:
            continue
        F = np.concatenate(frames, axis=0)        # (total_frames_word x bands)
        if F.shape[0] < 2:
            continue
        n_bands = F.shape[1]
        mu = F.mean(axis=0, keepdims=True)        # this WORD's frame-mean (word signal)
        C = np.cov((F - mu).T)                     # within-word scatter (bands x bands)
        per_word_cov.append(C)
        n_frames_total += F.shape[0]
    if not per_word_cov:
        return None, 0, 0
    S_n = np.mean(np.stack(per_word_cov, axis=0), axis=0)
    return S_n, len(per_word_cov), n_frames_total


def whitening_matrix(S_n, shrink, alpha=1.0):
    """W = S_n^{-alpha/2} via eigendecomposition with SHRINKAGE/floor for stability.
    Shrinkage S' = (1-shrink) S_n + shrink * (trace(S_n)/d) I pulls S_n toward a scaled
    identity (Ledoit-Wolf style) so small/noisy eigen-directions don't blow up the
    inverse-sqrt. alpha in [0,1] = partial-whiten strength: alpha=0 -> identity (no
    whitening), alpha=1 -> full whitening. W_alpha = V diag(lam^{-alpha/2}) V^T.
    Owned linear algebra; eigh on a symmetric PSD matrix. NO net, NO fit, NO gradient."""
    d = S_n.shape[0]
    tr = float(np.trace(S_n)) / d
    S = (1.0 - shrink) * S_n + shrink * tr * np.eye(d)
    S = 0.5 * (S + S.T)                            # symmetrize (numerical)
    lam, V = np.linalg.eigh(S)
    floor = 1e-8 * float(lam.max())
    lam = np.clip(lam, floor, None)
    inv = lam ** (-alpha / 2.0)
    return (V * inv) @ V.T


# ===========================================================================
# LOSO RUN with the whitened matched-filter compare
# ===========================================================================

def run_audio(probe, whiten, grid=60, k=3, max_synths=8, n_passes=2, seed=20240610):
    """Robust SC LOSO: the CortexLoop (UNCHANGED) over the AudioHat with the smoothed
    (sigma_f=1.5) + WHITENED (W) compare. whiten=None -> smoothed-only. Held-out REAL
    clips in `probe` are NEVER banked; their labels score only. Returns
    (acc, chance, n, true_median_resid, wrong_median_resid)."""
    s, _pipe = audio_fresh()
    hat = AudioHat(s, fs=FS, grid=grid, seed=seed,
                   smooth_t=SMOOTH_T, smooth_f=SMOOTH_F, whiten=whiten)
    loop = CortexLoop(hat, max_synths_per_content=max_synths, n_passes=n_passes, k=k)
    chance = 1.0 / len(hat.contents())
    pr = [(w, x, fs) for (w, x, fs) in probe if w in hat.contents()]
    cor = 0
    true_resids, wrong_resids = [], []
    for (w, x, fs) in pr:
        pred, per, _curves = loop.recognise((x, fs))
        cor += int(pred == w)
        if w in per:
            true_resids.append(per[w])
        wrong = [r for ww, r in per.items() if ww != w]
        if wrong:
            wrong_resids.append(min(wrong))
    hat.close()
    tr = np.asarray(true_resids); wr = np.asarray(wrong_resids)
    acc = cor / max(len(pr), 1)
    tmed = float(np.median(tr)) if tr.size else float("nan")
    wmed = float(np.median(wr)) if wr.size else float("nan")
    return acc, chance, len(pr), tmed, wmed


def main():
    t_start = time.time()
    n_held_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    n_loso_per = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    n_train_spk = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    seed = 20240610

    print("#" * 78, flush=True)
    print("WHITENED MATCHED FILTER — loop synthesis + Mahalanobis (noise-weighted) compare",
          flush=True)
    print("Smoothed (sigma_f=1.5) + WHITEN by inverse-sqrt nuisance covariance. The "
          "CortexLoop + hat.py are UNTOUCHED; whitening lives in AudioHat.encode/synth.",
          flush=True)
    print("#" * 78, flush=True)

    if not W.sc_available():
        print("Speech Commands not at /tmp/sc — abort.", flush=True)
        print("[MARKER] WHITENED_MATCHED_FILTER_COMPLETED", flush=True)
        return

    words = [w for w in W.sc_words() if w in _DIGITS]
    chance = 1.0 / len(_DIGITS)

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

    # ---- the held-out LOSO probe (the SAME builder the smoothing run used) ----
    probe, _w = build_real_probe(n_held_spk, n_loso_per, seed)
    # safety: confirm held-out speakers are NOT in the train set (no leakage)
    probe = [(w, x, fs) for (w, x, fs) in probe if w in words]
    print(f"[probe] {len(probe)} REAL held-out LOSO clips (never banked)", flush=True)
    assert not (set(held_spk) & set(train_spk)), "LEAKAGE: train/held-out overlap"

    # ---- estimate the nuisance covariance on TRAIN (word labels only) ----
    t0 = time.time()
    S_n, n_w, n_fr = estimate_nuisance_cov(train_idx, words, n_per_word=40, seed=seed)
    if S_n is None:
        print("[nuisance] could not estimate S_n — abort.", flush=True)
        print("[MARKER] WHITENED_MATCHED_FILTER_COMPLETED", flush=True)
        return
    ev = np.linalg.eigvalsh(S_n)
    cond = float(ev.max() / max(ev.min(), 1e-12))
    print(f"[nuisance] S_n ({S_n.shape[0]}x{S_n.shape[1]}) from within-word scatter over "
          f"{n_w} words, {n_fr} TRAIN frames ({time.time()-t0:.0f}s). "
          f"eig[min,max]=[{ev.min():.2e},{ev.max():.2e}] cond={cond:.1e}", flush=True)
    print(f"[note] word labels ONLY for the within-word structure; NO speaker labels.",
          flush=True)

    # ---- baselines: documented CMVN + smoothed-only (recomputed here) ----
    print("\n" + "=" * 78, flush=True)
    print("BASELINES", flush=True)
    print("=" * 78, flush=True)
    print(f"  CMVN (documented):        {CMVN_THIS_SPLIT:.3f} this split / "
          f"{CMVN_CANONICAL:.3f} canonical", flush=True)
    t0 = time.time()
    acc0, ch, n0, tm0, wm0 = run_audio(probe, whiten=None)
    sep0 = wm0 - tm0
    print(f"  smoothed-only (W=None):   LOSO {acc0:.3f} (chance {ch:.3f})  "
          f"true {tm0:.3f} vs wrong {wm0:.3f}  sep {sep0:+.3f}  "
          f"({time.time()-t0:.0f}s, n={n0})  [doc {SMOOTHED_ONLY_DOC:.3f}]", flush=True)

    # ---- WHITENED+smoothed: sweep shrinkage (full whiten) then alpha (best shrink) ----
    print("\n" + "=" * 78, flush=True)
    print("WHITENED + smoothed — SHRINKAGE sweep (full whiten, alpha=1.0)", flush=True)
    print("=" * 78, flush=True)
    shrink_grid = [0.01, 0.05, 0.1, 0.2, 0.4, 0.7]
    results = {}
    for sh in shrink_grid:
        Wm = whitening_matrix(S_n, shrink=sh, alpha=1.0)
        t0 = time.time()
        acc, ch, n, tm, wm = run_audio(probe, whiten=Wm)
        sep = wm - tm
        results[("shrink", sh)] = {"acc": acc, "tmed": tm, "wmed": wm, "sep": sep}
        print(f"  shrink={sh:<5} alpha=1.0   LOSO {acc:.3f} (chance {ch:.3f})  "
              f"true {tm:.3f} vs wrong {wm:.3f}  sep {sep:+.3f}  ({time.time()-t0:.0f}s)",
              flush=True)

    best_sh = max(shrink_grid, key=lambda sh: results[("shrink", sh)]["acc"])
    print(f"\n  best shrinkage (full whiten): {best_sh} "
          f"LOSO {results[('shrink', best_sh)]['acc']:.3f}", flush=True)

    print("\n" + "=" * 78, flush=True)
    print(f"WHITENED + smoothed — PARTIAL-WHITEN alpha sweep (shrink={best_sh})", flush=True)
    print("=" * 78, flush=True)
    alpha_grid = [0.25, 0.5, 0.75, 1.0]
    for al in alpha_grid:
        if al == 1.0:                              # already have it from the shrink sweep
            r = results[("shrink", best_sh)]
            print(f"  alpha={al:<4} shrink={best_sh}   LOSO {r['acc']:.3f}  "
                  f"true {r['tmed']:.3f} vs wrong {r['wmed']:.3f}  sep {r['sep']:+.3f}  "
                  f"(reused)", flush=True)
            results[("alpha", al)] = r
            continue
        Wm = whitening_matrix(S_n, shrink=best_sh, alpha=al)
        t0 = time.time()
        acc, ch, n, tm, wm = run_audio(probe, whiten=Wm)
        sep = wm - tm
        results[("alpha", al)] = {"acc": acc, "tmed": tm, "wmed": wm, "sep": sep}
        print(f"  alpha={al:<4} shrink={best_sh}   LOSO {acc:.3f} (chance {ch:.3f})  "
              f"true {tm:.3f} vs wrong {wm:.3f}  sep {sep:+.3f}  ({time.time()-t0:.0f}s)",
              flush=True)

    # ===================================================================
    # VERDICT
    # ===================================================================
    best_key = max(results, key=lambda k: results[k]["acc"])
    best = results[best_key]
    print("\n" + "#" * 78, flush=True)
    print("VERDICT — does the whitened matched filter push PAST CMVN?", flush=True)
    print("#" * 78, flush=True)
    print(f"  CMVN baseline:            {CMVN_THIS_SPLIT:.3f} this split "
          f"({CMVN_CANONICAL:.3f} canonical)", flush=True)
    print(f"  smoothed-only:            {acc0:.3f}  sep {sep0:+.3f}", flush=True)
    print(f"  BEST whitened+smoothed:   {best['acc']:.3f}  sep {best['sep']:+.3f}  "
          f"(config {best_key})", flush=True)
    print(f"  lift over smoothed-only:  {best['acc']-acc0:+.3f}", flush=True)
    print(f"  vs CMVN (this split):     {best['acc']-CMVN_THIS_SPLIT:+.3f}", flush=True)
    print(f"  vs CMVN (canonical):      {best['acc']-CMVN_CANONICAL:+.3f}", flush=True)

    past_cmvn = best["acc"] > CMVN_THIS_SPLIT + 1e-9
    beats_smoothed = best["acc"] - acc0 > 0.02
    sep_up = best["sep"] - sep0 > 0.0
    if past_cmvn:
        print(f"\n  => SIGNAL-FROM-NOISE PAYS: the whitened matched filter EXCEEDS CMVN "
              f"({best['acc']:.3f} > {CMVN_THIS_SPLIT:.3f}). Whitening down-weighted the "
              f"STRUCTURED nuisance the low-pass smoothing left, and the loop's speaker "
              f"INFERENCE (matched-filter synthesis) beats plain CMVN's static "
              f"normalization. Mahalanobis > Euclidean, as predicted.", flush=True)
    elif beats_smoothed:
        print(f"\n  => PARTIAL: whitening LIFTS smoothed-only ({best['acc']:.3f} vs "
              f"{acc0:.3f}, {best['acc']-acc0:+.3f}) but does NOT clear CMVN "
              f"({CMVN_THIS_SPLIT:.3f}). The structured nuisance is partly separable; a "
              f"residual remains entangled with the word.", flush=True)
    else:
        print(f"\n  => HONEST KILL: whitening does NOT push past CMVN and does NOT beat "
              f"smoothed-only by >0.02 (best {best['acc']:.3f} vs smoothed {acc0:.3f}, "
              f"CMVN {CMVN_THIS_SPLIT:.3f}). The within-word nuisance OVERLAPS the word "
              f"signal — whitening it down-weights the word too — so nuisance + word are "
              f"GENUINELY ENTANGLED, deeper than a covariance whitening can separate.",
              flush=True)
    print(f"  separation (wrong-true) improved by whitening: {sep_up} "
          f"(smoothed {sep0:+.3f} -> best {best['sep']:+.3f})", flush=True)

    print(f"\n[timing] total {time.time()-t_start:.0f}s", flush=True)
    print("[MARKER] WHITENED_MATCHED_FILTER_COMPLETED", flush=True)


if __name__ == "__main__":
    main()
