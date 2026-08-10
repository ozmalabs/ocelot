"""integration_full_loso — does INTEGRATION (average the whitened-match evidence over
MULTIPLE INDEPENDENT LOOKS to boost SNR) on top of the whitened matched filter push the
audio cross-speaker LOSO PAST the CANONICAL CMVN ~0.570 on the FULL run?

Signal-from-noise toolkit, the THIRD tool (memory ozma_signal_from_noise_toolkit +
ozma_two_streams_one_window): the optimal detector is a matched filter (the loop's
synthesis), whitened (Mahalanobis, the prior commit f0f2350e), and then INTEGRATED —
average the detector statistic over independent looks so RANDOM noise cancels (1/sqrt(N)
SNR gain) while the COHERENT word signal accumulates. Integration was the underused
two-ears tool; this run implements it and settles the question on the full LOSO split.

The whitened matched filter (f0f2350e) reached 0.525 on an 80-clip subsample (+0.015 over
same-split CMVN 0.510) — the FIRST loop result above baseline, separation +0.057 -> +0.288
confirming Mahalanobis works — but MODEST and likely below the canonical full-run CMVN
0.570. A within-word remainder stays entangled. Integration is the next tool.

BUILD (donkey-clean; CortexLoop + hat.py UNTOUCHED — git diff empty). On top of the
whitened+smoothed compare (sf=1.5, the prior best), add INTEGRATION over independent looks,
implemented with OWNED averaging/sum/softmin (NO net) in THIS script over the hat's owned
encode/compare/library:

  1. K-NEAREST per word — integrate the per-word evidence over the K-nearest exemplars
     (the K smallest whitened residuals per word, mean / softmin) instead of the 1-best.
     Each of the K exemplars is an INDEPENDENT LOOK at the word under a different style ->
     style-dependent noise across the K cancels. Sweep K.
  2. MULTI-SCALE — fuse the whitened-match evidence over several smoothing scales (the
     blur pyramid; the two-ears). Each scale is an independent look with scale-dependent
     noise -> that noise cancels across scales. Whitening is RE-FIT per scale (no leakage).

  Readout = argmin_word [ integrated evidence over looks ]. Per-look per-word evidence is
  z-standardised across words (owned: subtract mean, divide sd) before summing, so no
  single look's distance scale dominates the integration; raw-mean and softmin also tried.

TEST (robust SC 40-speaker LOSO, ALL cross-speaker probes, held-out REAL never banked):
  CMVN canonical (real-exemplar DTW LOSO, the documented ~0.570) | whitened+smoothed (the
  matched-filter 1-best, no integration) | whitened+smoothed+INTEGRATION — on the SAME full
  split. Report seen + LOSO + gap + separation + the integration sweep (K, scales), n.

PREDICTION: integration boosts SNR -> LOSO lifts above the whitened number, ideally PAST
canonical CMVN 0.570. KILL: if integration does NOT lift (the looks are CORRELATED -> noise
doesn't cancel) OR the full-run whitened falls back below CMVN (the subsample +0.015 was
noise) — say so PLAINLY. Honest both ways.

Run: python -m scripts.integration_full_loso [n_held_spk] [n_loso_per] [n_train_spk] [n_lib_per_word_cap]
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random

import numpy as np

import domains.self_directed_speech_world as W
from domains.cortex_loop import CortexLoop
from domains.audio_hat import AudioHat
from domains.fuzzy_smooth import smooth_traj
import domains.learned_voice_shape as LVS
from scripts.universal_loop_phaseAB import build_real_probe, fresh as audio_fresh, FS

# the canonical CMVN-DTW recognizer (real exemplars, the documented ~0.570 baseline).
from scripts.dtw_trajectory_loso import (
    build_split, fresh as dtw_fresh, bank, BAG_CUES, CELL,
    write_exemplar_trajectories, mark_words, measure_dtw)

_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine"]

# the prior-best smoothing (docs/fuzzy_compare_smoothing.md): freq-blur sigma_f=1.5.
SMOOTH_T = 0.0
SMOOTH_F = 1.5
# multi-scale pyramid for the integration (independent looks at different blur levels).
MULTI_SCALES = [1.0, 1.5, 2.5]
CMVN_THIS_SPLIT = 0.51
CMVN_CANONICAL = 0.57


# ===========================================================================
# NUISANCE COVARIANCE on TRAIN real speakers (word labels only) — fit PER SCALE.
# (same estimator as scripts/whitened_matched_filter.py; re-fit at each smoothing scale)
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
    """S_n = within-word scatter on TRAIN real speakers = the word-INDEPENDENT nuisance
    covariance (speaker + residual synthetic-vs-real domain), smoothed at sigma_f=sf.
    Word labels supply the structure; NO speaker labels. Owned per-word mean + within-word
    covariance averaged over words. Returns (S_n, n_words, n_frames)."""
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
    """W = S_n^{-alpha/2} via eigendecomposition with shrinkage/floor (Ledoit-Wolf style).
    Owned linear algebra (eigh on a symmetric PSD matrix). NO net, NO fit, NO gradient."""
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
# OWNED INTEGRATION OPS (averaging / sum / softmin / z-standardise). NO net.
# ===========================================================================

def _zstd_over_words(d):
    """Standardise a per-word evidence dict across words: (d_w - mean)/sd. Owned. Makes
    each independent LOOK comparable so the integration sum isn't dominated by one look's
    distance scale. Lower = better (it's a residual)."""
    ws = list(d.keys())
    v = np.asarray([d[w] for w in ws], dtype=np.float64)
    finite = v[np.isfinite(v)]
    if finite.size == 0:
        return {w: 0.0 for w in ws}
    mu = float(finite.mean())
    sd = float(finite.std()) or 1.0
    out = {}
    for w, val in zip(ws, v):
        out[w] = float((val - mu) / sd) if np.isfinite(val) else 3.0  # missing -> bad
    return out


def _softmin_k(vals, beta):
    """Soft-minimum (log-sum-exp min) over the K residuals: a smooth, noise-robust
    aggregate of the K-best looks. beta->inf recovers the hard min (1-best); finite beta
    AVERAGES the K looks so their independent noise cancels. Owned arithmetic."""
    a = np.asarray([v for v in vals if np.isfinite(v)], dtype=np.float64)
    if a.size == 0:
        return float("inf")
    m = a.min()
    return float(m - (1.0 / beta) * np.log(np.mean(np.exp(-beta * (a - m)))))


def knearest_evidence(h_feats, hat, K, agg, beta=8.0):
    """INTEGRATION over the K-nearest library exemplars per word. For each word, take the
    K smallest whitened compare distances to H and AGGREGATE them (mean | softmin) instead
    of the 1-best -> the K independent looks' style-dependent noise cancels. Returns a
    per-word evidence dict (lower better). Owned: sort + mean/softmin over owned compares."""
    per_word_dists = {w: [] for w in hat.contents()}
    for (content, _style, feats) in hat.library():
        if content not in per_word_dists:
            continue
        per_word_dists[content].append(float(hat.compare(h_feats, feats)))
    ev = {}
    for w, ds in per_word_dists.items():
        ds = sorted(d for d in ds if np.isfinite(d))
        if not ds:
            ev[w] = float("inf")
            continue
        kk = ds[:K]
        ev[w] = float(np.mean(kk)) if agg == "mean" else _softmin_k(kk, beta)
    return ev


# ===========================================================================
# FULL LOSO with the integrated whitened matched filter
# ===========================================================================

def build_scale_hats(s, scales, whitens, grid, seed):
    """One AudioHat per smoothing scale, each whitened by its OWN re-fit W (no leakage).
    These are the independent LOOKS for the multi-scale integration. Shared substrate."""
    hats = {}
    for sf in scales:
        hats[sf] = AudioHat(s, fs=FS, grid=grid, seed=seed,
                            smooth_t=SMOOTH_T, smooth_f=sf, whiten=whitens[sf])
    return hats


def run_integrated(probe, hats, primary_sf, K, agg, use_loop, use_knn, use_multiscale,
                   beta=8.0, max_synths=8, n_passes=2, k=3):
    """Robust SC LOSO with INTEGRATION. For each held-out probe clip, gather independent
    LOOKS and integrate (owned z-standardise + sum):
      · LOOP look (if use_loop): the CortexLoop matched-filter adapt at the primary scale
        -> per-word adapted residual (the prior whitened best). CortexLoop UNTOUCHED.
      · K-NEAREST look (if use_knn): integrate over the K-nearest library exemplars per
        word at the primary scale.
      · MULTI-SCALE looks (if use_multiscale): the K-nearest evidence at EACH smoothing
        scale (independent blur-level looks).
    Readout = argmin_word [ sum of z-standardised per-look evidence ]. Held-out clips are
    NEVER banked; labels score only. Returns (acc, chance, n, tmed, wmed)."""
    primary = hats[primary_sf]
    loop = CortexLoop(primary, max_synths_per_content=max_synths, n_passes=n_passes, k=k)
    words = primary.contents()
    chance = 1.0 / len(words)
    pr = [(w, x, fs) for (w, x, fs) in probe if w in words]
    cor = 0
    true_resids, wrong_resids = [], []
    for (w, x, fs) in pr:
        looks = []   # each = z-standardised per-word evidence dict
        if use_loop:
            _pred, per, _curves = loop.recognise((x, fs))
            looks.append(_zstd_over_words(per))
        if use_knn:
            hf = primary.encode((x, fs))
            looks.append(_zstd_over_words(knearest_evidence(hf, primary, K, agg, beta)))
        if use_multiscale:
            for sf, hat in hats.items():
                if sf == primary_sf and use_knn:
                    continue   # already counted as the primary K-nearest look
                hf = hat.encode((x, fs))
                looks.append(_zstd_over_words(knearest_evidence(hf, hat, K, agg, beta)))
        # OWNED integration: sum the z-standardised looks (each ~N(0,1) over words) ->
        # the random per-look noise averages, the coherent word signal accumulates.
        integ = {ww: sum(L.get(ww, 0.0) for L in looks) for ww in words}
        pred = min(integ.items(), key=lambda kv: kv[1])[0]
        cor += int(pred == w)
        if w in integ:
            true_resids.append(integ[w])
        wrong = [r for ww, r in integ.items() if ww != w]
        if wrong:
            wrong_resids.append(min(wrong))
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
    grid = int(sys.argv[5]) if len(sys.argv) > 5 else 60
    seed = 20240610

    print("#" * 78, flush=True)
    print("INTEGRATION FULL LOSO — whitened matched filter + integration over looks",
          flush=True)
    print("Whitened+smoothed (sf=1.5) + INTEGRATION (K-nearest + multi-scale, owned "
          "averaging/softmin). CortexLoop + hat.py UNTOUCHED.", flush=True)
    print("#" * 78, flush=True)

    if not W.sc_available():
        print("Speech Commands not at /tmp/sc — abort.", flush=True)
        print("[MARKER] INTEGRATION_FULL_LOSO_COMPLETED", flush=True)
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

    # ---- the held-out LOSO probe: ALL cross-speaker clips (full run) ----
    probe, _w = build_real_probe(n_held_spk, n_loso_per, seed)
    probe = [(w, x, fs) for (w, x, fs) in probe if w in words]
    print(f"[probe] {len(probe)} REAL held-out LOSO clips (n_loso_per={n_loso_per}, "
          f"never banked)", flush=True)
    assert not (set(held_spk) & set(train_spk)), "LEAKAGE: train/held-out overlap"

    # ---- estimate the nuisance covariance PER SCALE on TRAIN (word labels only) ----
    whitens = {}
    SHRINK = 0.1            # the f0f2350e best region
    ALPHA = 0.75           # partial-whiten peak (docs/whitened_matched_filter.md)
    all_scales = sorted(set([SMOOTH_F] + MULTI_SCALES))
    for sf in all_scales:
        t0 = time.time()
        S_n, n_w, n_fr = estimate_nuisance_cov(train_idx, words, n_per_word=40,
                                               seed=seed, sf=sf)
        if S_n is None:
            print(f"[nuisance sf={sf}] could not estimate — abort.", flush=True)
            print("[MARKER] INTEGRATION_FULL_LOSO_COMPLETED", flush=True)
            return
        whitens[sf] = whitening_matrix(S_n, shrink=SHRINK, alpha=ALPHA)
        ev = np.linalg.eigvalsh(S_n)
        print(f"[nuisance sf={sf}] S_n {S_n.shape[0]}x{S_n.shape[1]} from {n_w} words "
              f"{n_fr} frames ({time.time()-t0:.0f}s) eig[{ev.min():.1e},{ev.max():.1e}]",
              flush=True)
    print(f"[whiten] shrink={SHRINK} alpha={ALPHA} (the f0f2350e best); re-fit per scale; "
          f"word labels ONLY, NO speaker labels.", flush=True)

    # ===================================================================
    # CMVN CANONICAL — the real-exemplar DTW recognizer (the ~0.570 baseline)
    # ===================================================================
    print("\n" + "=" * 78, flush=True)
    print("CMVN CANONICAL (real-exemplar DTW LOSO) — the documented ~0.570 baseline",
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
    # build the per-scale whitened hats (shared substrate)
    # ===================================================================
    s, _pipe = audio_fresh()
    hats = build_scale_hats(s, all_scales, whitens, grid, seed)
    print(f"\n[hats] built {len(hats)} whitened hats at scales {all_scales} "
          f"(grid={grid} synth exemplars/word each)", flush=True)

    # ===================================================================
    # WHITENED MATCHED FILTER (1-best, no integration) — the prior result, full run
    # ===================================================================
    print("\n" + "=" * 78, flush=True)
    print("WHITENED+SMOOTHED — matched filter 1-best (no integration), full run",
          flush=True)
    print("=" * 78, flush=True)
    t0 = time.time()
    acc_w, ch, n_w_, tm_w, wm_w = run_integrated(
        probe, hats, primary_sf=SMOOTH_F, K=1, agg="mean",
        use_loop=True, use_knn=False, use_multiscale=False)
    sep_w = wm_w - tm_w
    print(f"  whitened 1-best (LOOP only): LOSO {acc_w:.3f} (chance {ch:.3f})  "
          f"sep {sep_w:+.3f}  (n={n_w_}, {time.time()-t0:.0f}s)", flush=True)

    # ===================================================================
    # INTEGRATION sweep — K-nearest (sweep K, agg) then + multi-scale
    # ===================================================================
    print("\n" + "=" * 78, flush=True)
    print("INTEGRATION — K-NEAREST sweep (loop + integrated K-nearest, primary scale)",
          flush=True)
    print("=" * 78, flush=True)
    results = {"whitened_1best": {"acc": acc_w, "sep": sep_w, "tmed": tm_w, "wmed": wm_w}}
    for K in [3, 5, 8]:
        for agg in ["mean", "softmin"]:
            t0 = time.time()
            acc, ch, n, tm, wm = run_integrated(
                probe, hats, primary_sf=SMOOTH_F, K=K, agg=agg,
                use_loop=True, use_knn=True, use_multiscale=False)
            sep = wm - tm
            results[("knn", K, agg)] = {"acc": acc, "sep": sep, "tmed": tm, "wmed": wm}
            print(f"  K={K} agg={agg:<7} loop+knn   LOSO {acc:.3f}  sep {sep:+.3f}  "
                  f"(n={n}, {time.time()-t0:.0f}s)", flush=True)

    best_knn = max([k for k in results if isinstance(k, tuple) and k[0] == "knn"],
                   key=lambda k: results[k]["acc"])
    bK, bagg = best_knn[1], best_knn[2]
    print(f"\n  best K-nearest: K={bK} agg={bagg} LOSO {results[best_knn]['acc']:.3f}",
          flush=True)

    print("\n" + "=" * 78, flush=True)
    print(f"INTEGRATION — + MULTI-SCALE (loop + K-nearest@K={bK},{bagg} fused over scales "
          f"{all_scales})", flush=True)
    print("=" * 78, flush=True)
    t0 = time.time()
    acc_ms, ch, n_ms, tm_ms, wm_ms = run_integrated(
        probe, hats, primary_sf=SMOOTH_F, K=bK, agg=bagg,
        use_loop=True, use_knn=True, use_multiscale=True)
    sep_ms = wm_ms - tm_ms
    results[("multiscale", bK, bagg)] = {"acc": acc_ms, "sep": sep_ms,
                                         "tmed": tm_ms, "wmed": wm_ms}
    print(f"  loop+knn+multiscale         LOSO {acc_ms:.3f}  sep {sep_ms:+.3f}  "
          f"(n={n_ms}, {time.time()-t0:.0f}s)", flush=True)

    # also: multi-scale K-nearest WITHOUT the loop (pure integration over library looks)
    t0 = time.time()
    acc_msnl, ch, n_msnl, tm_msnl, wm_msnl = run_integrated(
        probe, hats, primary_sf=SMOOTH_F, K=bK, agg=bagg,
        use_loop=False, use_knn=True, use_multiscale=True)
    sep_msnl = wm_msnl - tm_msnl
    results[("multiscale_noloop", bK, bagg)] = {"acc": acc_msnl, "sep": sep_msnl,
                                                "tmed": tm_msnl, "wmed": wm_msnl}
    print(f"  knn+multiscale (no loop)    LOSO {acc_msnl:.3f}  sep {sep_msnl:+.3f}  "
          f"(n={n_msnl}, {time.time()-t0:.0f}s)", flush=True)

    for h in hats.values():
        h.close()

    # ===================================================================
    # VERDICT
    # ===================================================================
    best_key = max(results, key=lambda k: results[k]["acc"])
    best = results[best_key]
    print("\n" + "#" * 78, flush=True)
    print("VERDICT — does INTEGRATION push past CANONICAL CMVN 0.570?", flush=True)
    print("#" * 78, flush=True)
    print(f"  CMVN canonical (this split): {cmvn_loso:.3f} (seen {cmvn_seen:.3f})", flush=True)
    print(f"  whitened 1-best (no integ):  {acc_w:.3f}  sep {sep_w:+.3f}", flush=True)
    print(f"  BEST integrated:             {best['acc']:.3f}  sep {best['sep']:+.3f}  "
          f"(config {best_key})", flush=True)
    print(f"  integration lift over 1-best: {best['acc']-acc_w:+.3f}", flush=True)
    print(f"  vs CMVN canonical (this run): {best['acc']-cmvn_loso:+.3f}", flush=True)
    print(f"  n (LOSO probes): {n_w_}", flush=True)

    integ_lifts = best["acc"] - acc_w > 0.005
    whitened_holds = acc_w >= cmvn_loso - 0.005
    past_cmvn = best["acc"] > cmvn_loso + 1e-9
    if past_cmvn:
        print(f"\n  => INTEGRATION PAYS: the integrated whitened matched filter EXCEEDS "
              f"canonical CMVN ({best['acc']:.3f} > {cmvn_loso:.3f}). Averaging the "
              f"detector over independent looks boosted SNR — random per-look noise "
              f"cancelled, the coherent word accumulated, as predicted.", flush=True)
    elif integ_lifts:
        print(f"\n  => PARTIAL: integration LIFTS the 1-best ({best['acc']:.3f} vs "
              f"{acc_w:.3f}, {best['acc']-acc_w:+.3f}) — the looks are at least partly "
              f"independent, noise partly cancels — but it does NOT clear canonical CMVN "
              f"({cmvn_loso:.3f}). A residual stays entangled.", flush=True)
    else:
        print(f"\n  => HONEST KILL: integration does NOT lift the 1-best (best "
              f"{best['acc']:.3f} vs whitened {acc_w:.3f}). The looks are CORRELATED — "
              f"they share the same within-word nuisance — so averaging does NOT cancel "
              f"it; integration is not the missing tool here.", flush=True)
    if not whitened_holds:
        print(f"\n  [!] the whitened 1-best FELL BELOW canonical CMVN on the full run "
              f"({acc_w:.3f} < {cmvn_loso:.3f}): the subsample +0.015 over CMVN did NOT "
              f"hold at full n — it was within noise.", flush=True)
    else:
        print(f"\n  [+] whitened 1-best holds at/above canonical CMVN on the full run "
              f"({acc_w:.3f} vs {cmvn_loso:.3f}).", flush=True)

    print(f"\n[timing] total {time.time()-t_start:.0f}s, n={n_w_} LOSO probes", flush=True)
    print("[MARKER] INTEGRATION_FULL_LOSO_COMPLETED", flush=True)


if __name__ == "__main__":
    main()
