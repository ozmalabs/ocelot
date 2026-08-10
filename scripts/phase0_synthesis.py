"""PHASE 0 — SPEECH SYNTHESIS fail-fast: borrow piper, map a real speaker, FFT-compare synth vs real HELD-OUT words.

The jabberwock's design + the creator's metric: piper is the BOOTSTRAP; the real test is on RECORDED speech with HELD-OUT
words and an FFT COMPARE. Map ONE LibriSpeech speaker X -> nearest piper voice (WavLM speaker-discriminative search over
VCTK's 109 indices + singles), duration-match prosody (length_scale), synth X's HELD-OUT words, and FFT-compare each synth
word to X's REAL recording of it -- vs OTHER speakers' real recordings of the same word (the control). No adaptation, no
fine-tune: does retrieval+prosody land the synth SPECTRALLY closer to the target speaker than to others?

FFT compare = cosine-DTW distance over L2-normalised log-magnitude STFT frames (spectral-shape = timbre+content over time).
PRE-COMMITTED BAR: KEEP if on a MAJORITY of held-out words d_self = fft(synth_X, real_X(w)) < d_other = min_Y fft(synth_X,
real_Y(w)) -- the synth verifies as X spectrally (borrow-piper has legs; build prosody+adaptation). KILL if synth-X is
routinely closer to some other speaker -> piper's discrete grid is too coarse for an arbitrary identity -> need adaptive TTS.
Jabberwock's prediction: DENT (right person among N, content ok; below within-speaker band).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.phase0_synthesis
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
import torchaudio
from piper import PiperVoice, SynthesisConfig

from scripts.phase0_learned_latent import dtw
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

PIPER = os.path.expanduser("~/.cache/ozma/piper_voices")
VCTK = os.path.join(PIPER, "en_GB-vctk-medium.onnx")
SINGLES = ["en_US-lessac-medium", "en_US-amy-medium", "en_US-ryan-medium",
           "en_US-hfc_male-medium", "en_US-hfc_female-medium", "en_US-kusal-medium", "en_GB-alan-medium"]
PROBE = "the birch canoe slid on the smooth planks"
N_WORDS = 25
WAVLM_LAYER = 6

_v = {}
def _voice(path):
    if path not in _v:
        _v[path] = PiperVoice.load(path)
    return _v[path]


def synth(path, text, speaker_id=None, length_scale=1.0):
    cfg = SynthesisConfig(speaker_id=speaker_id, length_scale=float(length_scale))
    try:
        ch = list(_voice(path).synthesize(text, cfg))
    except Exception:
        return None
    if not ch:
        return None
    au = np.concatenate([c.audio_int16_array for c in ch]).astype(np.float32) / 32768.0
    sr = ch[0].sample_rate
    return torchaudio.functional.resample(torch.from_numpy(au), sr, 16000).numpy()


_wl = None
def wavlm(x):
    global _wl
    if _wl is None:
        _wl = torchaudio.pipelines.WAVLM_BASE.get_model().eval()
    x = np.asarray(x, np.float32)
    if x.size < 400:
        x = np.pad(x, (0, 400))
    with torch.inference_mode():
        f, _ = _wl.extract_features(torch.from_numpy(x)[None])
    e = f[WAVLM_LAYER][0].mean(0).numpy()
    return e / (np.linalg.norm(e) + 1e-9)


_win = torch.hann_window(400)
def logmag(x):
    x = torch.from_numpy(np.asarray(x, np.float32))
    X = torch.stft(x, n_fft=512, hop_length=160, win_length=400, window=_win, return_complex=True)
    M = np.log(np.abs(X.numpy()).T + 1e-6)
    n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


def fft_dist(a, b):
    if a is None or b is None or len(a) < 160 or len(b) < 160:
        return 1e9
    return dtw(logmag(a), logmag(b))


def main():
    print("=" * 100)
    print("PHASE 0 — synthesis fail-fast: borrow piper, map a real speaker, FFT-compare synth vs real held-out words")
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
    print(f"  target speaker X = {target}; control speakers = {others}")

    # X reference audio (~12s) for mapping; and X's words (real segments)
    def words_of(sp, cap_utt=999):
        out = defaultdict(list); nu = 0; ref = []
        for (f, t) in by_spk[sp]:
            x, fs = load_flac(f); x = np.asarray(x, np.float64); nu += 1
            if nu <= 3 and sum(len(r) for r in ref) < 12 * 16000:
                ref.append(x)
            try:
                for (w, t0, t1) in align_utt(x, fs, t):
                    if len(w) >= MINW and (t1 - t0) >= 0.12:
                        out[w].append(x[int(t0 * fs):int(t1 * fs)])
            except Exception:
                pass
            if nu >= cap_utt:
                break
        return out, (np.concatenate(ref) if ref else np.zeros(16000))

    Xwords, Xref = words_of(target)
    other_words = {}
    for sp in others:
        ow, _ = words_of(sp, cap_utt=40); other_words[sp] = ow

    # ---- MAP: nearest piper voice to X (WavLM speaker space), preferring VCTK's 109 indices ----
    print("  [map] embedding X reference + searching ~115 piper voices for the nearest...", flush=True)
    xemb = wavlm(Xref[: 12 * 16000])
    cands = [("VCTK", VCTK, sid) for sid in range(109)] + [("S", os.path.join(PIPER, s + ".onnx"), None) for s in SINGLES]
    best = None
    for (kind, path, sid) in cands:
        au = synth(path, PROBE, speaker_id=sid)
        if au is None or au.size < 8000:
            continue
        c = float(wavlm(au) @ xemb)
        if best is None or c > best[0]:
            best = (c, kind, path, sid)
    _, bkind, bpath, bsid = best
    print(f"  [map] nearest voice: {bkind} {os.path.basename(bpath)} speaker_id={bsid}  (WavLM cos {best[0]:.3f})\n", flush=True)

    # ---- held-out words: spoken by X AND >=1 control speaker; synth (duration-matched) + FFT compare ----
    held = [w for w in Xwords if any(w in other_words[sp] for sp in others)][:N_WORDS]
    print(f"  [test] {len(held)} held-out words spoken by X and >=1 control speaker; synth + FFT compare...\n", flush=True)

    wins = 0; total = 0; margins = []
    for w in held:
        realX = max(Xwords[w], key=len)
        # duration-match: synth at 1.0, then rescale length_scale to the real duration
        a0 = synth(bpath, w, speaker_id=bsid)
        if a0 is None:
            continue
        ls = max(0.5, min(2.0, (len(realX) / 16000) / (len(a0) / 16000 + 1e-6)))
        sa = synth(bpath, w, speaker_id=bsid, length_scale=ls)
        if sa is None:
            continue
        d_self = fft_dist(sa, realX)
        d_other = min((fft_dist(sa, max(other_words[sp][w], key=len))
                       for sp in others if w in other_words[sp]), default=1e9)
        total += 1; win = d_self < d_other; wins += win
        margins.append(d_other - d_self)
        mark = "OK" if win else "x "
        print(f"    [{mark}] {w:<12} d(synth,realX)={d_self:.3f}  d(synth,realY)={d_other:.3f}  margin {d_other-d_self:+.3f}")

    rate = 100 * wins / total if total else 0.0
    print("\n" + "=" * 100)
    print(f"  mapped voice {bkind}/{bsid}; {total} held-out words:")
    print(f"    synth verifies as X (d_self < d_other):  {rate:.0f}%  ({wins}/{total})")
    print(f"    mean FFT margin (d_other - d_self):       {np.mean(margins):+.3f}")
    print("-" * 100)
    if rate >= 60:
        print(f"  KEEP — borrow-piper has legs: the mapped voice + duration match puts the synth SPECTRALLY closer to the target")
        print(f"  speaker than to others on {rate:.0f}% of held-out words (FFT verify). Identity-bearing -> build prosody (F0 contour)")
        print("  + light adaptation toward within-speaker. (Honest: this is the DENT — right person, not yet indistinguishable.)")
    elif rate >= 45:
        print(f"  WEAK — {rate:.0f}% FFT-verify (~chance for a few speakers). The mapped voice is in the neighbourhood but the discrete")
        print("  grid is coarse; prosody + adaptation may lift it, or the grid is too sparse. Borderline; the agent's call.")
    else:
        print(f"  KILL — {rate:.0f}%: synth-X is routinely closer to another speaker spectrally. Piper's discrete voice grid is too")
        print("  coarse to reach an arbitrary LibriSpeech identity by retrieval; need a speaker-adaptive / zero-shot cloning TTS.")
    print("=" * 100)


if __name__ == "__main__":
    main()
