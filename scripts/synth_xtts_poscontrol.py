"""POSITIVE CONTROL — do the WavLM + FFT metrics correctly verify REAL held-out X (not synth)? Disentangle clone vs metric.

If real held-out X sentences verify as X cleanly (and X-centroid is well-separated from Y-centroids), the metrics are valid
and the XTTS clone genuinely underperforms. If real X ALSO fails, the metric (WavLM-base/L6 over sentences, or synth-domain)
is too crude to judge the clone.
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

from scripts.phase0_synthesis import wavlm, fft_dist

OUT = os.environ.get("XTTS_SENT", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_sent")


def load16(p):
    x, sr = sf.read(p, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    if sr != 16000:
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy()
    return x


def main():
    print("=" * 100)
    print("POSITIVE CONTROL — real held-out X vs centroids (is the metric valid?)")
    print("=" * 100)
    with open(os.path.join(OUT, "manifest.json")) as fh:
        man = json.load(fh)
    Xp = man["enrollX"]
    Xemb = [wavlm(load16(os.path.join(OUT, p))) for p in Xp]
    Yc = {}
    for sp, ps in man["enrollY"].items():
        e = np.mean([wavlm(load16(os.path.join(OUT, p))) for p in ps], 0); Yc[sp] = e / (np.linalg.norm(e) + 1e-9)

    # leave-one-out: each real X sentence vs X-centroid(rest) vs Y-centroids
    wins = []; sc = []; oc = []
    for i in range(len(Xemb)):
        rest = [Xemb[j] for j in range(len(Xemb)) if j != i]
        Xc = np.mean(rest, 0); Xc /= np.linalg.norm(Xc) + 1e-9
        c_self = float(Xemb[i] @ Xc); c_other = max(float(Xemb[i] @ Yc[s]) for s in Yc)
        wins.append(int(c_self > c_other)); sc.append(c_self); oc.append(c_other)
    # X-centroid vs Y-centroid separation
    Xc_all = np.mean(Xemb, 0); Xc_all /= np.linalg.norm(Xc_all) + 1e-9
    xy = [float(Xc_all @ Yc[s]) for s in Yc]
    # FFT: real X vs real X (within) vs real X vs real Y
    Xw = [load16(os.path.join(OUT, p)) for p in Xp]
    Yw = [load16(os.path.join(OUT, man["enrollY"][s][0])) for s in man["enrollY"]]
    fft_within = [fft_dist(Xw[i], Xw[j]) for i in range(3) for j in range(i + 1, 4)]
    fft_between = [fft_dist(Xw[0], y) for y in Yw]

    print(f"  REAL held-out X WavLM verify (leave-one-out): {100*np.mean(wins):.0f}%  ({sum(wins)}/{len(wins)})")
    print(f"    real cos(X, X-centroid) median {np.median(sc):+.3f}  vs cos(X, Y-centroid) {np.median(oc):+.3f}")
    print(f"    X-centroid vs Y-centroids cos: {[round(v,2) for v in xy]}  (low = speakers separated)")
    print(f"  REAL FFT: within-X median {np.median(fft_within):.3f}  vs between-X-Y median {np.median(fft_between):.3f}")
    print("-" * 100)
    real_ok = np.mean(wins) >= 0.8 and np.median(xy) < np.median(sc) - 0.05
    if real_ok:
        print("  METRIC VALID — real X verifies as X and X-centroid is separated from Y. So the XTTS clone GENUINELY underperforms")
        print("  (closer to others than to X). The clone isn't capturing this speaker; investigate reference/conditioning, not the metric.")
    else:
        print("  METRIC TOO CRUDE — even REAL X barely verifies / speakers aren't separated (WavLM-base L6 over sentences, or the")
        print("  synth-vs-real domain). The clone verdict is inconclusive; need a stronger speaker embedding (WavLM-Large / SV head).")
    print("=" * 100)


if __name__ == "__main__":
    main()
