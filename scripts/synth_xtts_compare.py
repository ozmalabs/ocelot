"""XTTS pipeline, step 3/3 — COMPARE (main venv): FFT-compare XTTS clones vs the real held-out target.

The validated rig: cosine-DTW over L2-normalised log-mag STFT frames. Per word: d_self = fft(synth, realX), d_other =
min_Y fft(synth, realY) [cross-speaker control], within = fft(realX, realX2) [the speaker's own 0.040 band]. The jabberwock's
bar for the cloning TTS: success = the synth pulled INSIDE X's within-speaker band, not merely verify>others. Reports:
verify-rate (d_self<d_other) AND whether median synth-to-realX is within the within-speaker band.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.synth_xtts_compare
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

from scripts.phase0_synthesis import logmag, fft_dist   # the validated FFT-compare (resamples not needed; all 16k/24k handled below)
import torch
import torchaudio

OUT = os.environ.get("XTTS_DATA", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_data")


def load16k(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    if sr != 16000:
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy()
    return x


def fdist(a, b):
    if a is None or b is None or len(a) < 320 or len(b) < 320:
        return 1e9
    return fft_dist(a, b)


def main():
    print("=" * 100)
    print("XTTS-v2 (B580) CLONE vs REAL held-out target — FFT compare on the validated within/between rig")
    print("=" * 100)
    with open(os.path.join(OUT, "manifest.json")) as fh:
        man = json.load(fh)
    print(f"  target {man['target']}; {len(man['words'])} held-out words\n")

    selfs, others, withins, verts = [], [], [], []
    for m in man["words"]:
        w = m["word"]
        sp = os.path.join(OUT, f"synth_{w}.wav")
        if not os.path.exists(sp):
            continue
        syn = load16k(sp); rx = load16k(os.path.join(OUT, m["realX"]))
        dY = [load16k(os.path.join(OUT, p)) for p in m["realY"]]
        d_self = fdist(syn, rx)
        d_other = min((fdist(syn, y) for y in dY), default=1e9)
        win = fdist(rx, load16k(os.path.join(OUT, m["realX2"]))) if "realX2" in m else None
        selfs.append(d_self); others.append(d_other); verts.append(int(d_self < d_other))
        if win is not None:
            withins.append(win)
        mark = "OK" if d_self < d_other else "x "
        wb = f" within {win:.3f}" if win is not None else ""
        print(f"    [{mark}] {w:<12} synth->realX {d_self:.3f}  synth->realY {d_other:.3f}{wb}")

    selfs = np.array(selfs); others = np.array(others)
    vrate = 100 * np.mean(verts) if verts else 0
    med_self = np.median(selfs); med_within = np.median(withins) if withins else float("nan")

    print("\n" + "=" * 100)
    print(f"  {len(selfs)} cloned words, target {man['target']}:")
    print(f"    FFT-verify (synth closer to realX than realY):  {vrate:.0f}%")
    print(f"    median synth->realX  {med_self:.3f}   vs   real within-speaker band  {med_within:.3f}")
    print(f"    ratio synth/within: {med_self/max(med_within,1e-6):.2f}x   (1.0x = INSIDE the speaker's own band = indistinguishable)")
    print("-" * 100)
    if vrate >= 70 and med_self <= med_within * 1.3:
        print(f"  INDISTINGUISHABLE (FFT) — XTTS clone verifies as X ({vrate:.0f}%) AND lands within ~the speaker's own band")
        print(f"  ({med_self:.3f} vs {med_within:.3f}). The cloning forward model captures the speaker — analysis-by-synthesis is on.")
    elif vrate >= 70:
        print(f"  STRONG CLONE, not yet inside the band — verifies {vrate:.0f}% (the right person), median synth->realX {med_self:.3f} vs")
        print(f"  within {med_within:.3f} ({med_self/max(med_within,1e-6):.1f}x). Recognisably X but a residual gap (XTTS 24k/word-mode). A")
        print("  strong forward model for AbS; tighten with longer context / matched conditions.")
    else:
        print(f"  WEAK — verify {vrate:.0f}% / {med_self/max(med_within,1e-6):.1f}x the band. Even XTTS doesn't FFT-match this target here;")
        print("  check word-mode artefacts / reference quality / the FFT compare's sensitivity to the 24k synth vs 16k real.")
    print("=" * 100)


if __name__ == "__main__":
    main()
