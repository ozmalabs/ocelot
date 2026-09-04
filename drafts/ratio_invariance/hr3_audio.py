"""H-R3 — AUDIO transfer: does the SAME rung recover carrier/speaker-scale
invariance on a REAL signal body?

PREREG H-R3 (usefulness in shape, real body): on the AUDIO scale-frame case the
stack already proves ratios cancel the carrier (source/filter separation,
log-multiplicative); the INDUCTION faculty recovers the speaker/carrier-scale
invariance ACROSS a population of utterances WITHOUT it being hand-built.
CONFIRMED iff the induced ratio-invariant separates carrier-scale from content
on the audio population as the held audio ratio machinery does by construction.

TWO REAL-BODY CASES (source/filter separation, log-multiplicative):

  CASE A — HARMONIC-SERIES ratio under the F0 CARRIER (clean, reliable).
    A voiced sound is a glottal harmonic complex: spectral peaks at F0, 2·F0,
    3·F0, ... The per-speaker F0 (the glottal clock, measured by the REAL Rust
    `f0_autocorr`) is the CARRIER that varies across the population. The RATIO
    between harmonic peaks (peak2 : peak1 == 2:1, peak3:peak1 == 3:1) is FIXED
    regardless of F0 — the carrier cancels. The op is fed the INDEPENDENTLY
    peak-picked harmonic frequencies (real spectrum, NOT k·F0 computed by hand)
    and must recover the 2:1 invariance across the whole speaker population.

  CASE B — VOWEL FORMANT ratio under the VOCAL-TRACT SCALE (the harder real
    case, honestly reported). A vowel's identity is its formant PATTERN; across
    speakers the whole pattern scales with vocal-tract length. F2:F1 is the
    vowel-identity invariant. Formants are extracted by the REAL Rust
    `allpole_ear` (LPC). This case exposes the PRICE: the induction is only as
    good as the formant TRACKER — where LPC tracking is clean the ratio is
    recovered, where it grabs the wrong pole the population floors. Reported
    with the per-speaker extraction so the boundary is visible, not hidden.

DISCIPLINE: real synthesized waveforms; features from real DSP (Rust
`f0_autocorr` / `allpole_ear` + a boundary FFT peak-pick — admissible I/O
translation, no agent logic); per-speaker carrier random/unknown to the op; the
op sees ONLY extracted integer frames; NEGATIVE CONTROLS floor.

Run:  PYTHONPATH=.:runners/dsl/python python3 drafts/ratio_invariance/hr3_audio.py
"""
from __future__ import annotations

import json
import math
import random

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import substrate_rs._native as N                   # noqa: E402  (real audio prims)
from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

FS = 16000
DUR = 0.30
RES_HZ = 10          # observation-resolution grid (spectral bin quantization)

# Frame axes: axis-0 (coord:a) spans [0, low_peak], axis-1 (coord:b) spans
# [0, high_peak]. Per-axis extents are the two extracted frequencies; the op's
# cross-coordinate ratio is high:low — the carrier-invariant relation.
DIM_TYPES = ["pred", "coord:a", "coord:b", "val"]


def boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    s.add_node("ShapeSignature", {
        "name": "audio_probe",
        "signature": json.dumps([["pk", 100, 200, 1]]),
        "kind": "faculty", "faculty": "audio_probe",
        "dim_types": list(DIM_TYPES),
    })
    return s, ag, native


def synth_harmonic(f0, dur=DUR, fs=FS, seed=0):
    """A REAL glottal harmonic complex at F0 (1/h source tilt, random phases)."""
    rng = random.Random(seed)
    n = int(fs * dur)
    t = np.arange(n) / fs
    x = np.zeros(n)
    nh = int((fs / 2) / f0)
    for h in range(1, nh + 1):
        x += (1.0 / h) * np.sin(2 * math.pi * f0 * h * t + rng.uniform(0, 2 * math.pi))
    m = np.max(np.abs(x)) or 1.0
    return x / m


def synth_vowel(f0, formants, dur=DUR, fs=FS, seed=0):
    """A REAL vowel-like waveform: glottal harmonic source shaped by formant
    resonators (each boosts harmonics near its centre)."""
    rng = random.Random(seed)
    n = int(fs * dur)
    t = np.arange(n) / fs
    x = np.zeros(n)
    nh = int((fs / 2) / f0)
    for h in range(1, nh + 1):
        fh = f0 * h
        gain = 0.0
        for fc in formants:
            bw = 80.0 + 0.05 * fc
            gain += 1.0 / (1.0 + ((fh - fc) / (bw / 2)) ** 2)
        amp = gain / h
        if amp < 1e-3:
            continue
        x += amp * np.sin(2 * math.pi * fh * t + rng.uniform(0, 2 * math.pi))
    m = np.max(np.abs(x)) or 1.0
    return x / m


def spectral_peaks(x, fmax, n_take, res=RES_HZ, floor=0.05):
    """INDEPENDENT peak-pick of the lowest `n_take` strong spectral peaks below
    `fmax` from the REAL magnitude spectrum (Hanning-windowed rFFT — admissible
    boundary DSP). Quantized to the observation-resolution grid `res`. This does
    NOT compute k*F0 by hand — it reads the peaks the actual spectrum shows."""
    w = np.hanning(len(x))
    X = np.abs(np.fft.rfft(x * w))
    f = np.fft.rfftfreq(len(x), 1.0 / FS)
    thr = floor * X.max()
    pk = []
    for i in range(2, len(X) - 2):
        if X[i] > X[i - 1] and X[i] >= X[i + 1] and X[i] > thr and f[i] < fmax:
            pk.append((f[i], X[i]))
    pk.sort()   # by frequency (lowest first)
    got = [int(round(fc / res) * res) for (fc, _) in pk[:n_take]]
    return got


def frame_box(a, b):
    """Two-axis extent box: axis-0 spans [0,a], axis-1 spans [0,b]."""
    return [["pk", 0, 0, 1], ["pk", int(a), int(b), 1]]


def induce(native, frames, resolution=0, field=""):
    return native.evaluate(
        {"type": "RatioInduce",
         "population": {"type": "Lit", "value": frames},
         "resolution": resolution,
         "field": field},
        {})


def parse_ratios(out):
    flat = list(out.get("ratios") or ())
    return [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]


def case_a_harmonic(native):
    print("\n" + "-" * 74)
    print("CASE A — HARMONIC-SERIES ratio under the F0 CARRIER (peak2:peak1 = 2:1)")
    print("-" * 74)
    # population of speakers: random per-speaker F0 (the carrier); same 2:1
    # harmonic-series invariant by physics.
    f0s = [98, 123, 147, 181, 220, 262]
    frames = []
    for i, f0 in enumerate(f0s):
        x = synth_harmonic(f0, seed=i)
        f0_meas = N.f0_autocorr([float(v) for v in x], FS)   # REAL carrier readout
        pks = spectral_peaks(x, fmax=3 * f0 + 30, n_take=2)   # low two harmonics
        if len(pks) < 2:
            print(f"    spk{i}: peak extraction failed ({pks})")
            continue
        frames.append(frame_box(pks[0], pks[1]))
        print(f"    spk{i}: F0_planted={f0:4d}Hz  F0_measured(Rust)={f0_meas:6.1f}Hz  "
              f"peaks(Hz)={pks}  peak2/peak1={pks[1]/pks[0]:.3f}")
    out = induce(native, frames, resolution=RES_HZ)
    tr = parse_ratios(out)
    recovered = (tuple(tr[0][1:]) if tr else None)
    ok = bool(out.get("explained")) and recovered == (2, 1)
    print(f"\n    RatioInduce: explained={out.get('explained')} "
          f"latent={out.get('latent_name')} ratio triples={tr} "
          f"n_frames={out.get('n_frames')}")
    print(f"    recovered high:low = {recovered}  (planted 2:1)  -> "
          f"{'CARRIER-INVARIANCE RECOVERED' if ok else 'MISS'}")
    return ok, out, tr


def case_b_formant(native):
    print("\n" + "-" * 74)
    print("CASE B — VOWEL FORMANT ratio under VOCAL-TRACT SCALE (F2:F1, the hard case)")
    print("-" * 74)
    base = [700.0, 1220.0, 2600.0]
    speakers = [(110, 1.00), (130, 0.96), (155, 0.92), (185, 0.88)]
    frames = []
    for i, (f0, vt) in enumerate(speakers):
        fmts = [f * vt for f in base]
        x = synth_vowel(f0, fmts, seed=200 + i)
        f0_meas = N.f0_autocorr([float(v) for v in x], FS)
        # F1,F2 = two lowest LPC peaks via the REAL Rust allpole_ear
        f1f2 = lpc_two_lowest(x)
        if f1f2 is None:
            print(f"    spk{i}: LPC extraction failed")
            continue
        f1, f2 = f1f2
        frames.append(frame_box(f1, f2))
        print(f"    spk{i}: F0={f0_meas:5.1f}Hz vt={vt:.2f}  LPC (F1,F2)=({f1},{f2})  "
              f"F2/F1={f2/f1:.3f}")
    out = induce(native, frames, resolution=RES_HZ)
    tr = parse_ratios(out)
    print(f"\n    RatioInduce: explained={out.get('explained')} "
          f"latent={out.get('latent_name')} ratio triples={tr} "
          f"n_frames={out.get('n_frames')}")
    # honest verdict: recovered iff explained AND the F2/F1 spread is genuinely
    # a common scale (the op says so). This case EXPOSES the price.
    return bool(out.get("explained")), out, tr


def lpc_two_lowest(x, fs=FS, res=RES_HZ):
    nbands, nwin, order = 64, 6, 14
    ear = N.allpole_ear([float(v) for v in x], fs, nbands, nwin, order)
    prof = [0.0] * nbands
    for w in range(nwin):
        for b in range(nbands):
            prof[b] += ear[w * nbands + b]
    lo, hi = 150.0, 3800.0
    centres = [lo * (hi / lo) ** (b / (nbands - 1)) for b in range(nbands)]
    peaks = []
    for b in range(1, nbands - 1):
        if prof[b] > prof[b - 1] and prof[b] >= prof[b + 1]:
            peaks.append((centres[b], prof[b]))
    if len(peaks) < 2:
        return None
    pmax = max(p for (_, p) in peaks)
    prom = sorted(fc for (fc, p) in peaks if p >= 0.05 * pmax)
    if len(prom) < 2:
        return None
    q = lambda f: int(round(f / res) * res)
    return q(prom[0]), q(prom[1])


def negative_controls(native):
    print("\n" + "-" * 74)
    print("NEGATIVE CONTROLS — populations with NO common scale must FALSIFY")
    print("-" * 74)
    # (1) genuinely different high:low ratios (not a common carrier scale)
    frames = [frame_box(a, b) for (a, b) in [(100, 200), (100, 300), (100, 250), (100, 170)]]
    out1 = induce(native, frames, resolution=RES_HZ)
    ok1 = out1.get("explained") is False
    print(f"    mixed high:low ratios explained = {out1.get('explained')}  "
          f"{'OK (floored)' if ok1 else 'MISS'}")
    # (2) different vowels via real LPC
    vowels = {"a": [700, 1220, 2600], "i": [300, 2300, 3000], "u": [350, 800, 2400]}
    vf = []
    for i, (vw, fmts) in enumerate(vowels.items()):
        x = synth_vowel(140, [float(f) for f in fmts], seed=300 + i)
        ff = lpc_two_lowest(x)
        if ff:
            vf.append(frame_box(*ff))
    out2 = induce(native, vf, resolution=RES_HZ)
    ok2 = out2.get("explained") is False
    print(f"    different vowels explained = {out2.get('explained')}  "
          f"{'OK (floored)' if ok2 else 'MISS'}")
    return ok1 and ok2


def main():
    print("ENGINE:", provenance_line())
    print("=" * 74)
    print("H-R3  AUDIO — carrier/speaker-scale invariance recovered on a REAL body")
    print("=" * 74)
    s, ag, native = boot()

    a_ok, a_out, a_tr = case_a_harmonic(native)
    b_ok, b_out, b_tr = case_b_formant(native)
    neg_ok = negative_controls(native)

    print("\n" + "=" * 74)
    print("H-R3 VERDICT")
    print("=" * 74)
    print(f"  CASE A harmonic-carrier invariance (2:1 recovered): {a_ok}")
    print(f"  CASE B vowel-formant invariance (explained):        {b_ok}")
    print(f"  negative controls floor:                            {'PASS' if neg_ok else 'FAIL'}")
    # H-R3 CONFIRMED on the clean-carrier case + floors; CASE B reported as the
    # price boundary (extraction-limited), not required for confirmation.
    confirmed = a_ok and neg_ok
    print(f"  H-R3 CONFIRMED (carrier-scale invariance on real signal + floors): {confirmed}")
    print(f"  CASE B is reported as the PRICE boundary: the induction inherits the")
    print(f"  formant tracker's reliability (usefulness-at-a-price in shape).")
    return confirmed


if __name__ == "__main__":
    main()
