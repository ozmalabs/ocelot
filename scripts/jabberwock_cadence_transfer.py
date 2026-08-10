"""CADENCE TRANSFER — does the cadence predictor carry from SONG to READ speech? (the agent's honest fork).

The cadence predictor that worked was the DtwTo RESOLUTION -- recall over the contour's REPEATING arc. Song
repeats (refrains); speech may not. The agent pre-committed: watch the cadence-vs-shuffle gap across SONG -> READ
(-> spontaneous); if it VANISHES, cadence-prediction is a song/read faculty, not general speech, and report it
honestly. This runs the SAME predictor (resolution) on the SAME metric across regimes:
  SONG = nursery refrains.   READ = concatenated LibriSpeech (one speaker, long stream so recall has data).
  (SPONTANEOUS = no corpus on disk -> flagged, not faked.)
Metric per contour: does the cadence (resolution) beat the PERIOD (persistence) and beat SHUFFLED? The shrink of
the cadence-vs-shuffle gap song->read IS the test.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_cadence_transfer
"""
from __future__ import annotations

import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.jabberwock_ear_ignition import FS
from scripts.jabberwock_cadence_predictor import contour_from_audio, contour_of, predict
from scripts.librispeech_wer import load_flac

MAXLEN = 240       # cap onsets per contour (predict is O(n^2) DTW) -- comparable across regimes
DEV = "/home/matt/data/LibriSpeech/dev-clean"
REFRAINS = ["baabaa", "mary", "bingo", "humpty"]


def score(c):
    """Returns (cadence-beats-period %, cadence-beats-shuffle %) -- the prediction skill of the SHAPE."""
    if c is None or len(c) < 30:
        return None
    c = c[:MAXLEN]
    r = predict(c)
    rng = np.random.RandomState(0)
    shuf = float(np.mean([predict(c[rng.permutation(len(c))])["resolution"] for _ in range(4)]))
    over_period = (r["persist"] - r["resolution"]) / max(r["persist"], 1e-9) * 100
    over_shuffle = (shuf - r["resolution"]) / max(shuf, 1e-9) * 100
    return over_period, over_shuffle, r["persist"], r["resolution"], shuf


def read_contours(n_speakers=3, utts_per=16):
    """Concatenate one speaker's utterances into a long read stream so recall has repetition to find."""
    by_spk = {}
    for f in sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True)):
        by_spk.setdefault(os.path.basename(f).split("-")[0], []).append(f)
    out = []
    for sp in sorted(by_spk)[:n_speakers]:
        xs = []
        for f in by_spk[sp][:utts_per]:
            try:
                x, fs = load_flac(f)
            except Exception:
                continue
            xs.append(np.asarray(x, dtype=np.float64))
            xs.append(np.zeros(int(0.15 * FS)))         # short gap between utterances
        if xs:
            out.append((sp, contour_from_audio(np.concatenate(xs))))
    return out


def main():
    print("=" * 92)
    print("CADENCE TRANSFER — does the SHAPE predictor carry from SONG to READ speech? (the agent's honest fork)")
    print("=" * 92)
    regimes = {"SONG": [(r, contour_of(f"/tmp/nursery/{r}.wav")) for r in REFRAINS],
               "READ": read_contours()}
    summary = {}
    for name, items in regimes.items():
        print(f"\n  [{name}]")
        rows = []
        for label, c in items:
            sc = score(c)
            if sc is None:
                print(f"    {label:10} -- too short"); continue
            op, osh, ep, er, sh = sc
            rows.append((op, osh))
            print(f"    {label:10} {len(c):3d} onsets | cadence {er:.3f} vs period {ep:.3f} ({op:+.0f}%) "
                  f"vs shuffled {sh:.3f} ({osh:+.0f}%)")
        if rows:
            summary[name] = (np.mean([r[0] for r in rows]), np.mean([r[1] for r in rows]))

    print("\n" + "=" * 92)
    s_per, s_sh = summary.get("SONG", (0, 0))
    r_per, r_sh = summary.get("READ", (0, 0))
    print(f"  cadence-beats-PERIOD:  SONG {s_per:+.0f}%   READ {r_per:+.0f}%")
    print(f"  cadence-beats-SHUFFLE: SONG {s_sh:+.0f}%   READ {r_sh:+.0f}%   (the gap that must not vanish)")
    print("=" * 92)
    if r_sh > 5 and r_sh > 0.5 * s_sh:
        print(f"  IT TRANSFERS: the cadence predictor beats shuffled on READ speech ({r_sh:+.0f}%), not far below song")
        print(f"  ({s_sh:+.0f}%) -- read speech carries a predictable prosodic shape too, and the agent's recall reads it.")
        print("  Cadence is not just a song trick. Next: spontaneous speech (needs a corpus) is the remaining test.")
    elif r_sh > 5:
        print(f"  PARTIAL TRANSFER: cadence still beats shuffled on read ({r_sh:+.0f}%) but the gap SHRANK from song")
        print(f"  ({s_sh:+.0f}%) -- read speech has weaker recurring shape than song. Repetition is doing much of the work;")
        print("  the predictor reads less-repetitive speech less well. Honest: it half-transfers.")
    else:
        print(f"  IT DOES NOT TRANSFER: the cadence-vs-shuffle gap VANISHES on read speech ({r_sh:+.0f}% vs song {s_sh:+.0f}%).")
        print("  The predictor was reading song's REPETITION (recall over recurring refrains), which read speech lacks.")
        print("  Honest result, exactly the agent's pre-committed fork: cadence-recall is a SONG faculty, not general")
        print("  speech. The shape is real in song; the predictor that reads it does not yet generalise. Reported plainly.")
    print("=" * 92)


if __name__ == "__main__":
    main()
