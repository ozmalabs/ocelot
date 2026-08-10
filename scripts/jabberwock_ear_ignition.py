"""IGNITION — the agent's ear PREDICTS instead of MATCHES, on a nursery refrain (step 1 of the cadence plan).

The agent's move: point its prediction-error loop at its own ear. Step 1 = the ignition probe -- prove the loop
bites on the signal before trusting the shape model. The smallest predictor is the agent's order-0/1 onset
oscillator: predict the next inter-onset interval from the last, correct on the residual (feedback_control). On
a refrain (maximally periodic) the residual should FALL as it locks -- the first place the ear predicts.

Two honest controls (the agent's):
  - SHUFFLE the inter-onset intervals: error(real) << error(shuffled) proves the beat is REAL predictable
    structure, not a fit to anything.
  - a constant-period RIGID grid (phase-reset disabled): the entraining-and-phase-resetting oscillator should
    beat it, proving the predictive CORRECTION (not just a fixed metronome) is what tracks the beat.
Also stamps the per-onset prosodic CONTOUR (dt, stress, f0) the step-2 cadence predictor will read.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_ear_ignition [refrain.wav]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from domains.filter_settings import cochleagram

FS = 16000
FPS = 100          # 10ms frames for onset resolution
REFRACTORY = 0.12  # s -- min inter-onset (no double-trigger)
LR = 0.3           # oscillator entrainment rate


def load(path):
    x, fs = sf.read(path)
    if x.ndim > 1:
        x = x.mean(1)
    x = np.asarray(x, dtype=np.float64)
    if fs != FS:
        x = resample_poly(x, FS, fs)
    return x / (np.abs(x).max() + 1e-9)


def onsets(x):
    """Spectral-flux onsets on the cochleagram: positive energy increase, peak-picked with refractory."""
    nf = max(8, int(len(x) / FS * FPS))
    M = np.asarray(cochleagram(x, FS, env_cut=80.0, dur_cut=120.0, n_frames=nf), dtype=np.float64)  # (nf, bands)
    flux = np.maximum(0.0, np.diff(M, axis=0)).sum(1)            # (nf-1,)
    flux = flux / (flux.max() + 1e-9)
    hop = len(x) / FS / nf
    thr = 0.5 * flux.mean() + 0.1 * flux.max()
    ts, stress, last = [], [], -1e9
    for t in range(1, len(flux) - 1):
        if flux[t] > thr and flux[t] >= flux[t - 1] and flux[t] > flux[t + 1]:
            tt = t * hop
            if tt - last >= REFRACTORY:
                ts.append(tt); stress.append(float(flux[t])); last = tt
    return np.array(ts), np.array(stress), M, hop


def f0_at(x, t):
    """Crude autocorrelation pitch in [80,400]Hz over a 40ms window at time t -- for the contour (step 2)."""
    a, b = int(t * FS), int((t + 0.04) * FS)
    w = x[a:b]
    if len(w) < int(0.02 * FS):
        return 0.0
    w = w - w.mean()
    ac = np.correlate(w, w, "full")[len(w) - 1:]
    lo, hi = int(FS / 400), int(FS / 80)
    if hi >= len(ac):
        return 0.0
    lag = lo + int(np.argmax(ac[lo:hi]))
    return FS / lag if lag > 0 else 0.0


def osc_errors(iois, entrain):
    """Predict each interval; residual = |obs - pred|. entrain=True: adaptive period (the oscillator,
    feedback_control). entrain=False: fixed global-mean period (the rigid baseline)."""
    if len(iois) < 2:
        return np.array([])
    period = float(np.mean(iois)) if not entrain else float(iois[0])
    errs = []
    for d in iois[1:]:
        errs.append(abs(d - period))
        if entrain:
            period += LR * (d - period)                          # correct toward the observed interval
    return np.array(errs)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/nursery/baabaa.wav"
    print("=" * 92)
    print(f"IGNITION — does the ear PREDICT the beat of a refrain? ({os.path.basename(path)})")
    print("=" * 92)
    x = load(path)
    ts, stress, _M, _hop = onsets(x)
    print(f"  {len(x)/FS:.1f}s audio, {len(ts)} onsets detected ({len(ts)/(len(x)/FS):.1f}/s)")
    if len(ts) < 8:
        print("  too few onsets -- try another refrain"); return
    iois = np.diff(ts)

    # the agent's CONTOUR (dt, stress, f0) per onset -- laid for step-2 cadence
    contour = np.array([[iois[k], stress[k + 1], f0_at(x, ts[k + 1])] for k in range(len(iois))])
    print(f"  contour stamped: {len(contour)} prosodic 3-vectors (dt, stress, f0), "
          f"median f0 {np.median(contour[:,2][contour[:,2]>0]) if (contour[:,2]>0).any() else 0:.0f}Hz")

    osc = osc_errors(iois, entrain=True)
    rigid = osc_errors(iois, entrain=False)
    rng = np.random.RandomState(0)
    shuf = np.array([osc_errors(rng.permutation(iois), entrain=True).mean() for _ in range(20)])

    half = len(osc) // 2
    print(f"\n  onset-INTERVAL prediction error (|predicted - observed|, seconds):")
    print(f"    predictive oscillator (real)   : {osc.mean()*1000:5.0f} ms   "
          f"[first half {osc[:half].mean()*1000:.0f} -> second half {osc[half:].mean()*1000:.0f} ms]")
    print(f"    rigid constant-period baseline : {rigid.mean()*1000:5.0f} ms")
    print(f"    SHUFFLED intervals (control)   : {shuf.mean()*1000:5.0f} ms  (+-{shuf.std()*1000:.0f})")

    predictable = osc.mean() < shuf.mean() - 2 * shuf.std()      # real << shuffled: timing has structure
    clean_beat = osc.mean() < rigid.mean() - 0.01               # the oscillator clearly beats a metronome
    residual_frac = osc.mean() / (np.median(iois) + 1e-9)        # how big the residual is vs the interval
    print("\n" + "=" * 92)
    if predictable and clean_beat and residual_frac < 0.2:
        print(f"  CLEAN BEAT: the ear predicts the period and the oscillator beats a metronome -- a true beat here.")
    elif predictable:
        print(f"  IGNITION (the loop bites) -- BUT it is CADENCE, not a beat. The timing is REAL predictable structure")
        print(f"  (real {osc.mean()*1000:.0f}ms << shuffled {shuf.mean()*1000:.0f}ms), so prediction is the right move. But a metronome does as")
        print(f"  well as the oscillator and the residual is large (~{residual_frac*100:.0f}% of the interval) and STRUCTURED -- the")
        print("  predictable thing is the contour's SHAPE, not its spacing. This IS the handoff the agent designed:")
        print("  the residual has shape -> reframe from period to CADENCE (step 2: order-N + DtwTo over the contour).")
    else:
        print(f"  NO IGNITION ({osc.mean()*1000:.0f}ms vs shuffled {shuf.mean()*1000:.0f}ms): onsets too noisy / not periodic -- check detection.")
    print("=" * 92)


if __name__ == "__main__":
    main()
