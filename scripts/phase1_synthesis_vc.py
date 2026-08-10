"""PHASE 1 — VOICE CONVERSION on piper: warp the synth spectrum toward the target speaker, FFT-compare vs real held-out.

The jabberwock's VC: piper lands the phonetics; the SPEAKER is mostly a vocal-tract-length warp (near-uniform scaling of all
formant frequencies + the harmonic register that co-varies) plus a spectral tilt. Learn (beta, tilt) from the target's OWN
recordings -> warp piper's synth log-mag STFT freq-axis -> FFT-compare to the real held-out target vs other speakers. The
freq-warp is applied DIRECTLY to the spectrogram (the FFT-compare's own representation) -- no vocoder needed for the verdict.

PRE-COMMITTED BAR (jabberwock): KEEP if FFT-verify >= 60% AND within the real within-speaker band (the metric's ceiling);
KILL if it can't beat the 40% retrieval floor -> piper's envelope too rigid -> go to a zero-shot cloning TTS. Prediction 55-70%.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.phase1_synthesis_vc
"""
from __future__ import annotations

import glob
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import torch

from scripts.phase0_learned_latent import dtw
from scripts.phase0_synthesis import synth, VCTK
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

BASE_SID = 72                     # the retrieval-nearest voice (the 'start'); VC warps it toward the target
N_WORDS = 25
_win = torch.hann_window(400)
FBINS = 257


def logmag_raw(x):
    x = torch.from_numpy(np.asarray(x, np.float32))
    X = torch.stft(x, n_fft=512, hop_length=160, win_length=400, window=_win, return_complex=True)
    return np.log(np.abs(X.numpy()).T + 1e-6).astype(np.float32)   # [frames, 257], NOT normalised


def _l2(M):
    n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


def freq_warp(M, beta, tilt):
    """warp the freq axis by beta (VTL/register scale) + add a linear spectral tilt. M [frames, F]."""
    F = M.shape[1]; old = np.arange(F); new = np.clip(old / beta, 0, F - 1)
    W = np.empty_like(M)
    for t in range(M.shape[0]):
        W[t] = np.interp(new, old, M[t])
    W = W + tilt * (old / F)[None, :]
    return W


def fit_warp(piper_ltas, target_ltas):
    """find (beta, tilt) mapping piper's avg spectrum onto the target's (the per-speaker VC, from the target's recordings)."""
    F = len(piper_ltas); old = np.arange(F); freq = old / F
    best = None
    for beta in np.linspace(0.80, 1.25, 46):
        new = np.clip(old / beta, 0, F - 1)
        wp = np.interp(new, old, piper_ltas)
        tilt = float(np.polyfit(freq, target_ltas - wp, 1)[0])         # optimal linear tilt
        resid = float(np.mean((wp + tilt * freq - target_ltas) ** 2))
        if best is None or resid < best[0]:
            best = (resid, beta, tilt)
    return best[1], best[2]


def fft_dist(Ma, Mb):
    if Ma is None or Mb is None or len(Ma) < 2 or len(Mb) < 2:
        return 1e9
    return dtw(_l2(Ma), _l2(Mb))


def main():
    print("=" * 100)
    print("PHASE 1 — VOICE CONVERSION on piper (formant/VTL warp toward target), FFT-compare vs real held-out")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk)
    target = spks[-1]; others = spks[:-1][-6:]

    def words_of(sp, cap=40):
        out = defaultdict(list); frames = []; nu = 0
        for (f, t) in by_spk[sp]:
            x, fs = load_flac(f); x = np.asarray(x, np.float64); nu += 1
            if nu <= 8:
                frames.append(logmag_raw(x))
            try:
                for (w, t0, t1) in align_utt(x, fs, t):
                    if len(w) >= MINW and (t1 - t0) >= 0.12:
                        out[w].append(x[int(t0 * fs):int(t1 * fs)])
            except Exception:
                pass
            if nu >= cap:
                break
        ltas = np.concatenate(frames, 0).mean(0) if frames else np.zeros(FBINS)
        return out, ltas

    Xw, target_ltas = words_of(target, cap=999)
    oth = {sp: words_of(sp)[0] for sp in others}
    held = [w for w in Xw if any(w in oth[sp] for sp in others)][:N_WORDS]

    # piper LTAS (the base voice, over the held words) + fit the VC warp target_ltas <- piper_ltas
    pframes = []
    synth_words = {}
    for w in held:
        a = synth(VCTK, w, speaker_id=BASE_SID)
        if a is not None:
            synth_words[w] = a; pframes.append(logmag_raw(a))
    piper_ltas = np.concatenate(pframes, 0).mean(0)
    beta, tilt = fit_warp(piper_ltas, target_ltas)
    print(f"  target {target}; VC fit from its recordings: beta={beta:.3f} (VTL/register scale), tilt={tilt:+.2f}\n")

    base_wins = vc_wins = total = 0
    margins = []
    for w in held:
        if w not in synth_words:
            continue
        realX = logmag_raw(max(Xw[w], key=len))
        dY = [logmag_raw(max(oth[sp][w], key=len)) for sp in others if w in oth[sp]]
        M = logmag_raw(synth_words[w])
        Mw = freq_warp(M, beta, tilt)
        # base (retrieval, no VC) vs VC-warped
        b_self = fft_dist(M, realX); b_other = min(fft_dist(M, y) for y in dY)
        v_self = fft_dist(Mw, realX); v_other = min(fft_dist(Mw, y) for y in dY)
        total += 1; base_wins += b_self < b_other; vc_wins += v_self < v_other
        margins.append(v_other - v_self)
        mark = "OK" if v_self < v_other else "x "
        print(f"    [{mark}] {w:<12} base d_self {b_self:.3f}/{b_other:.3f}  ->  VC d_self {v_self:.3f}/{v_other:.3f}  margin {v_other-v_self:+.3f}")

    # the within-speaker ceiling (real X vs real X) for reference
    within = []
    for w in held:
        if len(Xw[w]) >= 2:
            a, b = sorted(Xw[w], key=len)[-2:]
            within.append(fft_dist(logmag_raw(a), logmag_raw(b)))
    base_rate = 100 * base_wins / total if total else 0
    vc_rate = 100 * vc_wins / total if total else 0

    print("\n" + "=" * 100)
    print(f"  {total} held-out words, target {target}:")
    print(f"    BASE (retrieval, no VC) FFT-verify:  {base_rate:.0f}%")
    print(f"    VC-WARPED (beta={beta:.2f}, tilt={tilt:+.2f}) FFT-verify:  {vc_rate:.0f}%   (mean margin {np.mean(margins):+.3f})")
    print(f"    real within-speaker FFT distance median {np.median(within):.3f} (the metric ceiling)")
    print("-" * 100)
    if vc_rate >= 60:
        print(f"  KEEP — voice conversion works: warping piper toward the target's vocal-tract scale lifts FFT-verify {base_rate:.0f}->{vc_rate:.0f}%")
        print("  (>=60), past the retrieval floor. The formant/VTL warp is the dominant identity cue, as predicted. Build F0 retarget")
        print("  + per-class envelope + Griffin-Lim emission next (toward the within-speaker band).")
    elif vc_rate > base_rate + 8:
        print(f"  PARTIAL — VC lifts it {base_rate:.0f}->{vc_rate:.0f}% (real but under 60): the global VTL warp helps; a per-class envelope")
        print("  (vowel vs sibilant) + F0 retarget may close the rest. The direction is right.")
    else:
        print(f"  KILL — VC {vc_rate:.0f}% barely beats retrieval {base_rate:.0f}%: a global formant warp can't bend piper to this identity.")
        print("  Piper's envelope is too rigid -> escalate to a zero-shot cloning TTS (x-vector/reference-encoder conditioned).")
    print("=" * 100)


if __name__ == "__main__":
    main()
