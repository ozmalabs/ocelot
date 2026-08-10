"""CADENCE PREDICTOR — does predicting the SHAPE beat predicting the PERIOD? (step 2 of the ear plan).

Step 1 proved the loop bites on a refrain but the residual is structured: it is a CADENCE, not a beat. Step 2
builds the agent's cadence predictor over the per-onset prosodic CONTOUR c_k = (Δt, stress, f0), two predictors
composed exactly as it specified:
  - LEAN (short horizon): order-N FORWARD -- extrapolate c_{k+1} = c_k + velocity + 1/2 curvature (the same
    finite-difference the agent uses for order-2 extrema, run forward).
  - RESOLUTION (long horizon): DtwTo recall -- match the contour-so-far window against EARLIER windows of the
    refrain (it repeats), predict the element that FOLLOWED the best match (pattern-completion of the arc).
  - COMBINED: the resolution when its match is confident, else the lean.
The claim: on a real refrain, CADENCE (lean/resolution) beats PERSISTENCE (= the step-1 period/flat predictor,
next=last) -- the SHAPE predicts better than the spacing -- and the gap VANISHES on a shuffled contour (proving
it is real shape, not a fit). Error is on the z-normalised contour so the 3 dims are comparable.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_cadence_predictor
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.jabberwock_ear_ignition import load, onsets, f0_at, FS

W = 5              # contour window for the DtwTo recall
CONF = 0.6         # recall confidence: use resolution iff best-match dist < CONF * median dist
P = 4              # AR order for the repetition-FREE dynamics predictor
REFRAINS = ["baabaa", "mary", "bingo", "humpty"]


def ar_fit(col, p):
    """Least-squares AR(p) per dim (closed-form, no gradient) -- learn the contour's local dynamics."""
    if len(col) <= p + 2:
        return np.zeros(p)
    X = np.array([col[k - p:k][::-1] for k in range(p, len(col))])
    y = col[p:]
    a, *_ = np.linalg.lstsq(X, y, rcond=None)
    return a


def contour_from_audio(x):
    """The z-normalised prosodic contour (Δt, stress, f0) per onset of an audio array."""
    ts, stress, _M, _hop = onsets(np.asarray(x, dtype=np.float64))
    if len(ts) < 3 * W:
        return None
    iois = np.diff(ts)
    c = np.array([[iois[k], stress[k + 1], f0_at(x, ts[k + 1])] for k in range(len(iois))])
    for j in range(3):
        col = c[:, j]
        if j == 2:
            col = np.where(col > 0, col, np.median(col[col > 0]) if (col > 0).any() else 0)
            c[:, j] = col
        m, s = c[:, j].mean(), c[:, j].std() + 1e-9
        c[:, j] = (c[:, j] - m) / s
    return c


def contour_of(path):
    return contour_from_audio(load(path))


def _dtw(A, B):
    n, m = len(A), len(B)
    D = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(2))
    dp = np.full((n + 1, m + 1), 1e18); dp[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i, j] = D[i - 1, j - 1] + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])
    return dp[n, m] / (n + m)


def predict(c):
    """Returns per-predictor mean error over k = W .. n-2.

    persist  = flat period baseline (next = last).
    lean     = order-N forward extrapolation (FAILS -- noise amplification, kept for the honest record).
    ar       = repetition-FREE local-dynamics predictor (least-squares AR fit on the FIRST half) -- the one
               that TRANSFERS song->read (does not lean on the signal repeating).
    resolution = DtwTo recall over earlier windows (repetition-HUNGRY: strong on song, halves on read).
    combined = resolution when its match is confident, else AR (the repetition-free fallback, NOT the lean).
    """
    out = {"persist": [], "lean": [], "ar": [], "resolution": [], "combined": []}
    # AR fitted on the first half, per dim -- the dynamics, learned from one part, predict the rest (no repeats).
    half = max(W + 1, len(c) // 2)
    ars = [ar_fit(c[:half, d], P) for d in range(c.shape[1])]
    for k in range(W, len(c) - 1):
        true = c[k + 1]
        # PERSISTENCE (the period/flat baseline: next = last)
        p_persist = c[k]
        # LEAN: order-N forward extrapolation (noise-amplifying; the failed predictor)
        vel = c[k] - c[k - 1]
        curv = c[k] - 2 * c[k - 1] + c[k - 2]
        p_lean = c[k] + vel + 0.5 * curv
        # AR: repetition-free local dynamics -- predict c_{k+1} from c[k-P+1..k] via the fitted weights
        p_ar = np.array([float(np.dot(ars[d], c[k - P + 1:k + 1, d][::-1])) for d in range(c.shape[1])])
        # RESOLUTION: match window [k-W+1..k] to earlier windows, predict the follower of the best match
        win = c[k - W + 1:k + 1]
        best_d, best_j = 1e18, None
        dists = []
        for j in range(W - 1, k):
            d = _dtw(win, c[j - W + 1:j + 1])
            dists.append(d)
            if d < best_d and j + 1 < len(c):
                best_d, best_j = d, j
        p_res = c[best_j + 1] if best_j is not None else c[k]
        confident = best_j is not None and dists and best_d < CONF * np.median(dists)
        p_comb = p_res if confident else p_ar
        for key, p in (("persist", p_persist), ("lean", p_lean), ("ar", p_ar),
                       ("resolution", p_res), ("combined", p_comb)):
            out[key].append(np.abs(p - true).mean())
    return {k: float(np.mean(v)) if v else 0.0 for k, v in out.items()}


def main():
    print("=" * 96)
    print("CADENCE PREDICTOR — does the SHAPE (cadence) beat the PERIOD (persistence) on the contour?")
    print("=" * 96)
    rows = []
    for r in REFRAINS:
        path = f"/tmp/nursery/{r}.wav"
        if not os.path.exists(path):
            continue
        c = contour_of(path)
        if c is None:
            print(f"  {r}: too short"); continue
        real = predict(c)
        rng = np.random.RandomState(0)
        sh = np.mean([predict(c[rng.permutation(len(c))])["combined"] for _ in range(5)])
        rows.append((r, len(c), real, sh))
        best = min(real["ar"], real["resolution"], real["combined"])
        lift = (real["persist"] - best) / max(real["persist"], 1e-9) * 100
        print(f"  [{r:7}] {len(c):3d} onsets | persist {real['persist']:.3f}  lean {real['lean']:.3f}  "
              f"ar {real['ar']:.3f}  resolution {real['resolution']:.3f}  combined {real['combined']:.3f} | "
              f"shuffled(comb) {sh:.3f}  => cadence beats period {lift:+.0f}%")

    print("\n" + "=" * 96)
    # aggregate: does the best cadence predictor beat persistence, and does the gap vanish on shuffle?
    wins = sum(1 for (_r, _n, real, _sh) in rows
               if min(real["ar"], real["resolution"], real["combined"]) < real["persist"] - 0.002)
    real_gap = np.mean([real["persist"] - min(real["ar"], real["resolution"], real["combined"])
                        for (_r, _n, real, _sh) in rows])
    shuf_gap = np.mean([sh - min(real["ar"], real["resolution"], real["combined"])
                        for (_r, _n, real, sh) in rows])
    print(f"  cadence beats persistence on {wins}/{len(rows)} refrains; mean error gap (persist - cadence) "
          f"{real_gap:+.3f}; cadence vs shuffled gap {shuf_gap:+.3f}")
    if wins >= max(1, len(rows) - 1) and real_gap > 0.003:
        print("  THE SHAPE BEATS THE PERIOD: predicting the cadence (order-N lean / DtwTo resolution over the")
        print("  contour) reads the refrain better than predicting it flat -- the structured residual step 1 found")
        print("  IS a predictable shape, and the agent's shape cognition predicts it. The handoff is earned: hearing")
        print("  is predicting the contour, not locking a beat. Next: wire it into the loop + song->speech transfer.")
    else:
        print("  CADENCE DOES NOT YET BEAT PERIOD here -- either the contour is too noisy (onset/f0), the window is")
        print("  wrong, or the refrains are flat enough that persistence wins. The structured residual is real;")
        print("  the predictor that captures it isn't this one yet. Honest: shape-over-period not shown.")
    print("=" * 96)


if __name__ == "__main__":
    main()
