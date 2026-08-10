"""SYNTHESIS Phase-0 DIAGNOSTIC — is the 28% a MAPPING failure, a METRIC failure, or the synth-vs-real DOMAIN gap?

The Phase-0 FFT verify was 28% (KILL). FFT distances were tiny (~0.05) with ±0.02 noise margins -> suspicious. Disentangle:
  (A) does the FFT compare separate REAL speakers on the SAME word?  same-speaker d(realX_a, realX_b) vs diff-speaker
      d(realX_a, realY). If same < diff reliably, the metric IS speaker-discriminative; if ~50%, it is CONTENT-dominated
      and the synth verdict is about the metric, not the mapping.
  (B) the synth-vs-real DOMAIN gap: is d(synth, real-anything) >> d(real, real)? If the synth sits far from ALL real speech
      (vocoder signature), the speaker signal is swamped by domain, not identity.
  (C) the synth verify rate (the Phase-0 number) for reference.
Mapped voice hardcoded to the Phase-0 winner (VCTK speaker_id=72) to skip the 115-voice search.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.phase0_synthesis_diag
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

from scripts.phase0_synthesis import synth, fft_dist, VCTK
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

MAP_SID = 72


def main():
    print("=" * 100)
    print("SYNTHESIS Phase-0 DIAGNOSTIC — mapping vs metric vs domain-gap")
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
        out = defaultdict(list); nu = 0
        for (f, t) in by_spk[sp]:
            x, fs = load_flac(f); x = np.asarray(x, np.float64); nu += 1
            try:
                for (w, t0, t1) in align_utt(x, fs, t):
                    if len(w) >= MINW and (t1 - t0) >= 0.12:
                        out[w].append(x[int(t0 * fs):int(t1 * fs)])
            except Exception:
                pass
            if nu >= cap:
                break
        return out

    Xw = words_of(target, cap=999)
    oth = {sp: words_of(sp) for sp in others}
    # words X said >=2x AND >=1 other speaker said
    held = [w for w in Xw if len(Xw[w]) >= 2 and any(w in oth[sp] for sp in others)][:25]
    print(f"  target {target}; {len(held)} words with >=2 X instances + >=1 control speaker\n")

    real_same, real_diff = [], []         # (A) metric validity on real
    synth_self, synth_other = [], []      # (C) synth verify
    dom_real, dom_synth = [], []          # (B) domain gap: real-real vs synth-real distances
    for w in held:
        xa, xb = sorted(Xw[w], key=len)[-2:]
        dY = [max(oth[sp][w], key=len) for sp in others if w in oth[sp]]
        d_xx = fft_dist(xa, xb)
        d_xy = min(fft_dist(xa, y) for y in dY)
        real_same.append(d_xx); real_diff.append(d_xy)
        dom_real.append(d_xx)
        a0 = synth(VCTK, w, speaker_id=MAP_SID)
        if a0 is None:
            continue
        ls = max(0.5, min(2.0, (len(xa) / 16000) / (len(a0) / 16000 + 1e-6)))
        sa = synth(VCTK, w, speaker_id=MAP_SID, length_scale=ls)
        ss = fft_dist(sa, xa); so = min(fft_dist(sa, y) for y in dY)
        synth_self.append(ss); synth_other.append(so)
        dom_synth.append(ss)

    real_same = np.array(real_same); real_diff = np.array(real_diff)
    synth_self = np.array(synth_self); synth_other = np.array(synth_other)
    real_disc = 100 * np.mean(real_same < real_diff)
    synth_ver = 100 * np.mean(synth_self < synth_other)

    print("=" * 100)
    print("  (A) METRIC VALIDITY on REAL speech (same word):")
    print(f"      same-speaker d(realX_a,realX_b) median {np.median(real_same):.3f}  vs  diff-speaker d(realX,realY) median {np.median(real_diff):.3f}")
    print(f"      real speaker-discrimination (same<diff): {real_disc:.0f}%   (50% = metric is CONTENT-dominated, can't tell speakers)")
    print("  (B) SYNTH-vs-REAL DOMAIN GAP:")
    print(f"      real-real distance median {np.median(dom_real):.3f}  vs  synth-real distance median {np.median(dom_synth):.3f}")
    print(f"      domain gap ratio (synth-real / real-real): {np.median(dom_synth)/max(np.median(dom_real),1e-6):.2f}x")
    print("  (C) SYNTH verify (Phase-0): {:.0f}%  (synth_self<synth_other)".format(synth_ver))
    print("-" * 100)
    if real_disc < 62:
        print(f"  THE METRIC IS THE PROBLEM — FFT spectral-shape barely separates REAL speakers ({real_disc:.0f}%): it is CONTENT-")
        print("  dominated (same word -> same spectrum), so the 28% synth verify says nothing about the mapping. Need a SPEAKER-")
        print("  DISCRIMINATIVE compare (spectral ENVELOPE / pitch-removed, or WavLM) before judging piper's voice grid.")
    elif np.median(dom_synth) / max(np.median(dom_real), 1e-6) > 2.0:
        print(f"  THE DOMAIN GAP IS THE PROBLEM — synth sits {np.median(dom_synth)/max(np.median(dom_real),1e-6):.1f}x farther from real than real-real:")
        print("  piper's vocoder signature swamps speaker identity. Match the channel (codec/MFCC-envelope compare) or judge in a")
        print("  representation robust to the synth-real gap, not raw FFT.")
    else:
        print(f"  THE MAPPING IS THE PROBLEM — the metric separates real speakers ({real_disc:.0f}%) and the domain gap is modest, yet")
        print(f"  synth verifies only {synth_ver:.0f}%: piper's discrete grid genuinely doesn't reach this identity. KILL stands -> adaptive TTS.")
    print("=" * 100)


if __name__ == "__main__":
    main()
