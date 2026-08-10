"""PITCH+RHYTHM order-N perception front-end for a clip's SALIENT BUILD.

THE FIX (read scripts/shares_shape_demo.py for the diagnosis it replaces):
the energy front-end signed the ENERGY envelope of the salient build. A build
can score high order-N shape_salience yet have a NON-MONOTONE energy rank
signature, so a short cartoon "tada" and a long orchestral crescendo did NOT
become clean shape-neighbours (4 energy variants = whack-a-mole). The STABLE
signal of a build is its PITCH (rising) and its RHYTHM (beats tightening), not
its energy. So this front-end SIGNS pitch+rhythm.

WHAT IS HELD (Rust) vs WHAT IS WORLD-ADAPTER (this file):
  * RHYTHM primitive           -> srs.stft (-> spectral flux -> onset density)
  * PITCH primitive            -> srs.f0_yin (voicing-gated per-frame f0 Hz) +
                                  spectral-centroid trend (off the same held stft)
  * order-N SHAPE signature    -> Substrate.shape_signature (gain-invariant rank)
  * salience ranker (locator)  -> Substrate.shape_salience
  * neighbour distance + thr   -> Substrate.shape_signature_distance / _threshold
  * the shares_shape edge wiring + spread -> Substrate.add_salient_shape / spread
This file: raw-waveform loading (ffmpeg), composing the held primitives into a
trajectory, handing that trajectory to the held shape operator. No agent
decision, no ML, no threshold tuning.

LOCATING THE BUILD — by the RHYTHM signal itself, not energy. The energy
locator found the loudest local peak; for StoryBots that is NOT the intro tada.
The build is where beats TIGHTEN: onset density rises to a climax. So:
  1. climax = peak of the coarsely-smoothed onset-density curve.
  2. ramp = the trough->peak RISE into that climax, at the timescale (1..30s)
     whose density ramp is most DIRECTED (highest shape_salience). The ramp
     ENDS at the density peak (a pure rise, not the post-climax settle).
  3. an onset-CONTENT gate: the ramp must carry real onsets (absolute flux
     rise above the clip's noise floor) — a flat tone / silence has ~zero
     spectral flux and is rejected as "no build" (NOT a tuned shape threshold).

The build's SHAPE SIGNATURE = the order-N shape of pitch AND rhythm. Both rise
for a real build. Concatenation keeps the channels distinct. NOTE (honest, see
report): on a cartoon tada + an orchestral crescendo the RHYTHM channel is the
clean stable signal; the PITCH channel (f0_yin / centroid) is noisy on dense
polyphony, so it is provided but its contribution is reported separately.
"""
from __future__ import annotations
import subprocess, tempfile, wave
import numpy as np

import sys
sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
from substrate_rs import Substrate, _native as srs   # f0_yin / stft are native free fns

CHAN = 12          # per-channel signature length

# STFT framing for flux / centroid (held srs.stft).
_WIN, _HOP = 1024, 256
_HALF = _WIN // 2


# --------------------------------------------------------------------------
# world adapter: load a clip as 16 kHz mono float (ffmpeg = the fetch oracle).
# --------------------------------------------------------------------------
def _load(src: str, max_s: float = 90.0):
    wav = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", str(max_s),
                    "-i", src, "-ar", "16000", "-ac", "1", wav], check=True)
    w = wave.open(wav); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    return x, sr


def _resample(seg, n=CHAN):
    e = np.linspace(0, len(seg), n + 1).astype(int)
    return np.array([seg[e[k]:max(e[k] + 1, e[k + 1])].mean() for k in range(n)])


# --------------------------------------------------------------------------
# RHYTHM: held srs.stft -> half-wave-rectified spectral flux -> onset density.
# Returns the smoothed normalised density curve AND the raw (unnormalised)
# flux (for the onset-content gate), plus hop seconds.
# --------------------------------------------------------------------------
def _flux_density(x, sr, smooth_s):
    flat = srs.stft(list(x.astype("float32")), _WIN, _HOP)
    if not flat:
        return None, None, _HOP / sr
    spec = np.array(flat, dtype=np.float64).reshape(-1, _HALF)
    if spec.shape[0] < 8:
        return None, None, _HOP / sr
    raw_flux = np.maximum(np.diff(spec, axis=0), 0.0).sum(axis=1)  # onset strength
    dens = raw_flux / (raw_flux.max() + 1e-9)
    k = max(3, int(smooth_s * sr / _HOP))
    dens = np.convolve(dens, np.ones(k) / k, mode="same")
    return dens, raw_flux, _HOP / sr


# --------------------------------------------------------------------------
# LOCATE the build by the rhythm signal — trough->peak onset-density RISE.
# --------------------------------------------------------------------------
def locate_build(x, sr):
    """Return (t0, t1, rhythm_ramp) — the trough->peak onset-density rise into
    the climax, at the most-directed timescale, gated to require real onset
    content. rhythm_ramp is the CHAN-length normalised density trajectory of the
    build (the rhythm channel). Returns (None,None,None) if no build."""
    coarse, raw_flux, hs = _flux_density(x, sr, 1.5)
    fine, _, _ = _flux_density(x, sr, 0.3)
    if coarse is None or fine is None:
        return None, None, None
    # onset-content gate: a real build needs sustained onsets, not a near-silent
    # tone (whose normalised flux is pure noise floor). Reject if the clip's raw
    # flux scale is negligible.
    flux_scale = float(raw_flux.max())
    if flux_scale < 1.0:                       # ~no onset transients at all
        return None, None, None
    pi = int(np.argmax(coarse))               # the climax (beats densest)
    best = (-1.0, None)
    for span_s in (1, 2, 3, 4, 6, 8, 12, 20, 30):
        span = int(span_s / hs)
        lo = max(0, pi - span)
        tr = lo + int(np.argmin(fine[lo:pi + 1]))
        # END the ramp at the fine-density PEAK in [tr, pi] -> a pure RISE
        # (trough -> climax), excluding any post-climax settle.
        fp = tr + int(np.argmax(fine[tr:pi + 1]))
        if fp - tr < 6:
            continue
        # onset-content gate per-ramp: the density must actually RISE from a low
        # trough to a real peak (in raw flux terms), not be noise-floor wobble.
        ramp_raw = raw_flux[tr:fp + 1]
        if ramp_raw.max() < 0.10 * flux_scale or ramp_raw.max() - ramp_raw.min() < 0.05 * flux_scale:
            continue
        ramp = _resample(fine[tr:fp + 1])
        sal = Substrate.shape_salience(ramp.tolist())
        if sal > best[0]:
            best = (sal, (tr * hs, fp * hs, ramp))
    if best[1] is None:
        return None, None, None
    t0, t1, ramp = best[1]
    return t0, t1, ramp


# --------------------------------------------------------------------------
# PITCH over the build into the climax: f0_yin contour + spectral-centroid
# trend (both off held primitives). Measured over the most-directed window
# ending at the climax — pitch builds on a broader timescale than the beats.
# --------------------------------------------------------------------------
def pitch_contour(x, sr, t_climax, n=CHAN):
    """Return (centroid_traj, f0_traj) over the directed window ending at the
    climax. Centroid off held srs.stft; f0 off held srs.f0_yin (voicing-gated,
    forward-filled). Each picks the timescale of highest shape_salience."""
    flat = srs.stft(list(x.astype("float32")), _WIN, _HOP)
    spec = np.array(flat, dtype=np.float64).reshape(-1, _HALF)
    freqs = np.arange(_HALF) * sr / _WIN
    mag = spec + 1e-9
    cen = (mag * freqs).sum(1) / mag.sum(1)
    ks = max(1, int(0.5 * sr / _HOP))
    cen = np.convolve(cen, np.ones(ks) / ks, mode="same")
    hs = _HOP / sr
    pi = int(t_climax / hs)

    def best_window(curve, idx_to_time):
        best = (-1.0, None)
        for span_s in (2, 4, 8, 12, 20, 30):
            lo = max(0, pi - int(span_s / hs))
            if pi - lo < 6:
                continue
            seg = _resample(curve[lo:pi + 1], n)
            sal = Substrate.shape_salience(seg.tolist())
            if sal > best[0]:
                best = (sal, seg)
        return best[1]

    cen_traj = best_window(cen, hs)

    # f0 contour (held srs.f0_yin), forward-filled over voiced frames.
    frame, fhop = 2048, 512
    f0 = []
    i = 0
    while i + frame <= len(x):
        f0.append(srs.f0_yin(list(x[i:i + frame].astype("float32")), sr, 65.0, 1200.0, 0.15))
        i += fhop
    f0 = np.array(f0, dtype=np.float64)
    last = 0.0
    fl = np.zeros_like(f0)
    for j, v in enumerate(f0):
        if v > 0:
            last = v
        fl[j] = last
    if (fl > 0).any():
        fl[fl == 0] = fl[fl > 0][0]
    fpi = int(t_climax / (fhop / sr))
    f0_traj = None
    if fl.size and fpi > 6:
        best = (-1.0, None)
        for span_s in (2, 4, 8, 12, 20, 30):
            lo = max(0, fpi - int(span_s / (fhop / sr)))
            if fpi - lo < 6:
                continue
            seg = _resample(fl[lo:fpi + 1], n)
            sal = Substrate.shape_salience(seg.tolist())
            if sal > best[0]:
                best = (sal, seg)
        f0_traj = best[1]
    return cen_traj, f0_traj


# --------------------------------------------------------------------------
# the front-end: clip -> per-channel + combined order-N shape signatures.
# --------------------------------------------------------------------------
def pitch_rhythm_signature(src: str):
    """Return (info) with the rhythm / pitch / combined shape signatures, or
    info['reason'] if no build. The shape_signature calls are the HELD order-N
    operator; everything here is world-adapter composition of held primitives."""
    x, sr = _load(src)
    t0, t1, ramp = locate_build(x, sr)
    if ramp is None:
        return {"reason": "no onset-bearing build located"}
    cen, f0 = pitch_contour(x, sr, t1)
    rhythm_sig = Substrate.shape_signature(ramp.tolist())
    pitch_sig = Substrate.shape_signature(cen.tolist()) if cen is not None else None
    f0_sig = Substrate.shape_signature(f0.tolist()) if f0 is not None else None
    combined = (list(pitch_sig) + list(rhythm_sig)) if pitch_sig is not None else None
    return {
        "win": (t0, t1),
        "rhythm": ramp.tolist(), "rhythm_sig": list(rhythm_sig),
        "pitch_centroid": cen.tolist() if cen is not None else None,
        "pitch_sig": list(pitch_sig) if pitch_sig is not None else None,
        "f0": f0.tolist() if f0 is not None else None,
        "f0_sig": list(f0_sig) if f0_sig is not None else None,
        "combined_sig": combined,
    }
