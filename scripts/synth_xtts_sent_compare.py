"""XTTS SENTENCE pipeline, step 3/3 — COMPARE (main venv): does the cloned voice verify as the target on NATURAL speech?

WavLM speaker-centroid verification (robust, the decisive voice test): cos(synth_sentence, X_centroid) vs cos(., Y_centroid)
+ the real within-X band. Plus same-sentence FFT (synth vs X's real recording of that sentence) vs the within-speaker
sentence-FFT band. Success = the clone verifies as X AND lands in/near X's own within-speaker band.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import soundfile as sf
import torch
import torchaudio

from scripts.phase0_synthesis import wavlm, logmag, fft_dist

OUT = os.environ.get("XTTS_SENT", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_sent")


def load16(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    if sr != 16000:
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy()
    return x


def main():
    print("=" * 100)
    print("XTTS-v2 (B580) cloned SENTENCES vs real target — WavLM speaker verify + same-sentence FFT")
    print("=" * 100)
    with open(os.path.join(OUT, "manifest.json")) as fh:
        man = json.load(fh)
    target = man["target"]

    Xemb = [wavlm(load16(os.path.join(OUT, p))) for p in man["enrollX"]]
    Xc = np.mean(Xemb, 0); Xc /= np.linalg.norm(Xc) + 1e-9
    Yc = {}
    for sp, ps in man["enrollY"].items():
        e = np.mean([wavlm(load16(os.path.join(OUT, p))) for p in ps], 0); Yc[sp] = e / (np.linalg.norm(e) + 1e-9)
    # within-X band: pairwise cos among enroll-X
    within_cos = [float(Xemb[i] @ Xemb[j]) for i in range(len(Xemb)) for j in range(i + 1, len(Xemb))]
    # within-X FFT band: pairwise sentence FFT among enroll-X
    Xwav = [load16(os.path.join(OUT, p)) for p in man["enrollX"]]
    within_fft = [fft_dist(Xwav[i], Xwav[j]) for i in range(min(4, len(Xwav))) for j in range(i + 1, min(4, len(Xwav)))]

    verts, scos, ocos, fft_self = [], [], [], []
    print(f"  target {target}; {len(man['synth'])} cloned sentences; X-centroid from {len(man['enrollX'])} real sentences\n")
    for m in man["synth"]:
        sp = os.path.join(OUT, f"synth_sent{m['id']}.wav")
        if not os.path.exists(sp):
            continue
        syn = load16(sp); es = wavlm(syn)
        c_self = float(es @ Xc); c_other = max(float(es @ Yc[s]) for s in Yc)
        verts.append(int(c_self > c_other)); scos.append(c_self); ocos.append(c_other)
        rx = load16(os.path.join(OUT, m["realX"]))
        fft_self.append(fft_dist(syn, rx))
        mark = "OK" if c_self > c_other else "x "
        print(f"    [{mark}] sent{m['id']:<2} cos(synth,X) {c_self:+.3f}  cos(synth,Y) {c_other:+.3f}   sameFFT {fft_self[-1]:.3f}")

    vr = 100 * np.mean(verts) if verts else 0
    med_s = np.median(scos); med_o = np.median(ocos); med_w = np.median(within_cos)
    med_fs = np.median(fft_self); med_wf = np.median(within_fft) if within_fft else float("nan")
    print("\n" + "=" * 100)
    print(f"  WavLM speaker-verify (clone closer to X than any other speaker):  {vr:.0f}%")
    print(f"    cos(synth, X) median {med_s:+.3f}   vs cos(synth, otherY) {med_o:+.3f}   |  real within-X cos {med_w:+.3f}")
    print(f"    speaker-recovery: {100*max(0,(med_s-med_o))/max(med_w-med_o,1e-6):.0f}% of the within-vs-between gap")
    print(f"  same-sentence FFT: synth->realX {med_fs:.3f}  vs real within-X sentence FFT {med_wf:.3f}  ({med_fs/max(med_wf,1e-6):.2f}x)")
    print("-" * 100)
    if vr >= 80 and med_s >= med_o + 0.5 * (med_w - med_o):
        print(f"  CLONE VERIFIES AS X — on natural sentences the XTTS clone sits much closer to X ({med_s:+.2f}) than to other")
        print(f"  speakers ({med_o:+.2f}), recovering most of the way to the within-X band ({med_w:+.2f}). The single-word result")
        print("  WAS the confound; the cloning forward model captures the speaker. Analysis-by-synthesis is on — the 90% is fit.")
    elif vr >= 70:
        print(f"  STRONG CLONE — verifies as X {vr:.0f}%, cos(synth,X) {med_s:+.2f} > other {med_o:+.2f}, but short of the within band")
        print(f"  ({med_w:+.2f}). The voice is recognisably X (sentences fixed the single-word confound); residual gap to 'own recording'.")
    else:
        print(f"  STILL WEAK ({vr:.0f}%, cos {med_s:+.2f} vs other {med_o:+.2f}) — even sentence-level XTTS doesn't verify as this")
        print("  target. Check reference quality / XPU numerics / speaker difficulty; the clone isn't capturing the voice.")
    print("=" * 100)


if __name__ == "__main__":
    main()
