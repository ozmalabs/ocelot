"""ATTACK THE REPETITION-DEPENDENCE — predict the cadence from its DYNAMICS, not from recall.

The cadence predictor that worked was DtwTo RECALL (match the contour-so-far to earlier REPEATING arcs) -- so it
half-transfers: read speech repeats less than song, the gap halved. The order-N LEAN (forward extrapolation) was
the repetition-free alternative but it FAILED -- raw onset/f0 noise wrecks extrapolation. So the attack: a
repetition-FREE predictor that models the contour's LOCAL DYNAMICS, denoised:
  - SMOOTHED-LEAN: smooth the contour (causal moving average), extrapolate the smoothed velocity (the lean, but
    on the trend not the noise).
  - AR: a least-squares autoregressive model per dim (closed-form, no gradient) -- learn the contour's local
    correlation structure (declination / phrase dynamics) from the FIRST half, predict the SECOND. The "lean"
    with LEARNED weights instead of fixed 2,-1.
All predictors evaluated on the SECOND HALF of each contour (fair: AR fits the first half). The test: on READ
speech, does a NON-RECALL dynamics predictor beat persistence + shuffled as well as recall does on song -- i.e.
is the cadence predictable from dynamics ALONE, without repetition?

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_cadence_nonrecall
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.jabberwock_cadence_predictor import contour_of, _dtw
from scripts.jabberwock_cadence_transfer import read_contours, REFRAINS, MAXLEN

W = 5
P = 4              # AR order
SMOOTH = 3         # causal moving-average window


def smooth(c):
    out = np.array(c)
    for k in range(len(c)):
        out[k] = c[max(0, k - SMOOTH + 1):k + 1].mean(0)
    return out


def ar_fit(col, p):
    if len(col) <= p + 2:
        return np.zeros(p)
    X = np.array([col[k - p:k][::-1] for k in range(p, len(col))])
    y = col[p:]
    a, *_ = np.linalg.lstsq(X, y, rcond=None)
    return a


def errors(c):
    """Per-predictor mean |pred - true| over the SECOND HALF (k+1 in [n/2 .. n-1])."""
    c = c[:MAXLEN]
    n = len(c)
    start = max(W + 1, n // 2)
    sm = smooth(c)
    # AR fitted on the first half, per dim
    ars = [ar_fit(c[:start, d], P) for d in range(3)]
    e = {"persist": [], "smooth_lean": [], "ar": [], "recall": []}
    for k in range(start, n - 1):
        true = c[k + 1]
        e["persist"].append(np.abs(c[k] - true).mean())
        e["smooth_lean"].append(np.abs((sm[k] + (sm[k] - sm[k - 1])) - true).mean())
        ar_pred = np.array([np.dot(ars[d], c[k - P + 1:k + 1, d][::-1]) for d in range(3)])
        e["ar"].append(np.abs(ar_pred - true).mean())
        # recall (the repetition-hungry one): match window ending k against earlier windows
        win = c[k - W + 1:k + 1]; bd, bj = 1e18, None
        for j in range(W - 1, k):
            d = _dtw(win, c[j - W + 1:j + 1])
            if d < bd and j + 1 < n:
                bd, bj = d, j
        e["recall"].append(np.abs((c[bj + 1] if bj is not None else c[k]) - true).mean())
    return {k: float(np.mean(v)) if v else 0.0 for k, v in e.items()}


def shuffled_persist(c):
    rng = np.random.RandomState(0)
    c = c[:MAXLEN]; vals = []
    for _ in range(4):
        cs = c[rng.permutation(len(c))]
        n = len(cs); st = max(W + 1, n // 2)
        vals.append(np.mean([np.abs(cs[k] - cs[k + 1]).mean() for k in range(st, n - 1)]))
    return float(np.mean(vals))


def main():
    print("=" * 100)
    print("NON-RECALL CADENCE — predict from DYNAMICS not repetition; does it hold on READ where recall halved?")
    print("=" * 100)
    regimes = {"SONG": [(r, contour_of(f"/tmp/nursery/{r}.wav")) for r in REFRAINS],
               "READ": read_contours()}
    agg = {}
    for name, items in regimes.items():
        print(f"\n  [{name}]  (mean |pred-true| over 2nd half; lower=better; shuffled=chance)")
        rows = []
        for label, c in items:
            if c is None or len(c) < 40:
                continue
            e = errors(c); sh = shuffled_persist(c)
            rows.append((e, sh))
            sk = lambda key: max(0.0, (sh - e[key]) / max(sh, 1e-9) * 100)   # skill over chance
            print(f"    {label:10} persist {e['persist']:.3f} | recall {e['recall']:.3f} ({sk('recall'):+.0f}%) "
                  f"smooth_lean {e['smooth_lean']:.3f} ({sk('smooth_lean'):+.0f}%) ar {e['ar']:.3f} ({sk('ar'):+.0f}%)")
        if rows:
            agg[name] = {k: np.mean([max(0.0, (sh - e[k]) / max(sh, 1e-9) * 100) for (e, sh) in rows])
                         for k in ("recall", "smooth_lean", "ar")}

    print("\n" + "=" * 100)
    print("  prediction skill over chance (cadence-beats-shuffle %), by predictor and regime:")
    for k in ("recall", "smooth_lean", "ar"):
        print(f"    {k:12} SONG {agg.get('SONG',{}).get(k,0):+.0f}%   READ {agg.get('READ',{}).get(k,0):+.0f}%")
    rec_r = agg.get("READ", {}).get("recall", 0)
    best_nr = max(agg.get("READ", {}).get("smooth_lean", 0), agg.get("READ", {}).get("ar", 0))
    print("\n" + "=" * 100)
    if best_nr > rec_r + 3 and best_nr > 5:
        print(f"  REPETITION-DEPENDENCE BEATEN: a NON-RECALL dynamics predictor reads read-speech cadence better than")
        print(f"  recall ({best_nr:+.0f}% vs recall {rec_r:+.0f}%). The cadence is predictable from local DYNAMICS, not just")
        print("  matching repeats -- the gap holds on read speech. Wire this predictor in alongside recall.")
    elif best_nr > 5:
        print(f"  A NON-RECALL PREDICTOR HOLDS ({best_nr:+.0f}% on read) -- the cadence has dynamics structure beyond")
        print(f"  repetition; it roughly matches recall ({rec_r:+.0f}%). Repetition-dependence reduced, not eliminated.")
    else:
        print(f"  NON-RECALL DOES NOT HOLD ({best_nr:+.0f}% on read): on read speech the contour beyond persistence is")
        print("  mostly the repetition recall caught; the local dynamics (smoothed-lean/AR) add little. Honest: the")
        print("  predictable cadence on read speech IS largely repetition -- a richer learned prosodic model is the lever.")
    print("=" * 100)


if __name__ == "__main__":
    main()
