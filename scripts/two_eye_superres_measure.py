#!/usr/bin/env python3
"""TWO EYES → SUPER-RESOLUTION by MULTI-LOOK DE-ALIASING (Rung 5, block 175000).

Measures the pre-registered claim of `VISION_TWO_EYES_PREREG.md`. Two low-res
photon eyes offset by a KNOWN sub-receptor amount view ONE flat textured surface
carrying a spatial harmonic ABOVE a single eye's receptor-Nyquist. The FUSION is
graph-native (`multilook_superres` Rust kernel + `retinal_mint_superres` rule,
driven through `domains.two_eye_superres`); this script only builds textures,
reads the minted reconstructions, and SCORES them against the known dense field
(measurement, not an agent decision).

SPATIAL headline + THE ZERO-OFFSET FALSIFIER, then the TEMPORAL headline (the
identical kernel with positions as TIMES — space-offset ≡ time-offset — two eyes
on INDEPENDENT async clocks sampling the union of their event times).

Run:  python3 scripts/two_eye_superres_measure.py
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble(strict=False)

import numpy as np  # noqa: E402

from domains.two_eye_superres import SuperResFuser, sample_eye  # noqa: E402

BLOCK = 175000
DARK = 0.15          # rod dark_current (must match _RECEPTORS["rod"])
HALF = 1024.0        # rod half_saturation


def transduce(v):
    """Naka-Rushton rod transduction at the peak wavelength (gauss factor 1),
    adaptation 0 — byte-matching the Rust `photon_transduce`. `v` is photon
    count (or continuous intensity for the dense ground truth)."""
    caught = np.asarray(v, dtype=np.float64) + DARK
    return caught / (caught + HALF)


def make_texture(rng, N, k0):
    """A flat-wall luminance texture, period P=N receptors, carrying a LOW
    harmonic (k=2, resolvable by one eye) and a HIGH harmonic k0 with
    single-eye-Nyquist (N/2) < k0 < fused-Nyquist (N) — the target that
    ALIASES in a single eye. Amplitudes/phases drawn from the block seed."""
    P = float(N)
    base = 120.0
    a_lo, a_hi = 45.0, 45.0
    ph_lo = rng.uniform(0, 2 * math.pi)
    ph_hi = rng.uniform(0, 2 * math.pi)

    def tex(x):
        return (base
                + a_lo * math.cos(2 * math.pi * 2 * x / P + ph_lo)
                + a_hi * math.cos(2 * math.pi * k0 * x / P + ph_hi))

    return tex, P, k0, a_hi, ph_hi


def recon_error(recon, gt):
    r = np.asarray(recon, dtype=np.float64)
    return float(np.mean((r - gt) ** 2))


def rel_k0_error(recon, gt, k0, n_fine):
    """Relative error of the k0 Fourier component of the reconstruction vs the
    ground truth (the aliased-target criterion). A single eye cannot represent
    k0, so its reconstruction has ~0 energy there → relative error ≈ 1."""
    r = np.fft.rfft(np.asarray(recon, dtype=np.float64))
    g = np.fft.rfft(np.asarray(gt, dtype=np.float64))
    if k0 >= r.shape[0]:
        return float("nan")
    denom = abs(g[k0])
    if denom < 1e-12:
        return float("nan")
    return float(abs(r[k0] - g[k0]) / denom)


def supported_nyquist(positions, cap):
    """The highest harmonic a set of samples supports = (#DISTINCT positions)//2,
    capped at the fused Nyquist. A mechanical count of the KNOWN sample geometry
    (I/O framing, not a graph decision): fitting more harmonics than distinct
    samples support is ill-posed. Zero-offset gives NO new distinct positions, so
    it supports the SAME Nyquist as one eye — the falsifier falls out of the
    count, not a hand-set knob."""
    distinct = len({round(float(p), 9) for p in positions})
    return int(min(cap, distinct // 2))


def spatial_arm(rng, N=8, k0=6, n_fine=64, ridge=1e-6):
    tex, P, k0, a_hi, ph_hi = make_texture(rng, N, k0)
    cap = N                                      # fused Nyquist harmonic
    fine = np.arange(n_fine) * P / n_fine
    gt = transduce(np.array([tex(x) for x in fine]))   # dense true field

    posA, actA = sample_eye(tex, n_az=N, offset=0.0)     # eye A
    posB5, actB5 = sample_eye(tex, n_az=N, offset=0.5)   # eye B, sub-receptor offset
    posB0, actB0 = sample_eye(tex, n_az=N, offset=0.0)   # eye B, ZERO offset (control)

    # A FRESH fuser per condition: one substrate accumulates SuperResolvedField
    # nodes, so each reconstruction must be read from its own clean graph. The
    # band-limit is the Nyquist the DISTINCT samples support (computed from the
    # known positions) — the single fixed reconstruction principle; the offset
    # is what turns N distinct positions into 2N.
    def fuse1(pos, val):
        return SuperResFuser(enabled=True).fuse(
            pos, val, n_fine=n_fine, period=P, ridge=ridge,
            k_max=supported_nyquist(pos, cap))

    # single eye
    r_single = fuse1(posA, actA)
    # fused, sub-receptor offset 0.5 (THE WIN)
    r_off = fuse1(posA + posB5, actA + actB5)
    # fused, ZERO offset (THE FALSIFIER — two identical eyes)
    r_zero = fuse1(posA + posB0, actA + actB0)
    # naive 2x: single eye + linear-interp midpoints (double the samples, no
    # second real look)
    xm = [posA[i] + 0.5 for i in range(N - 1)]
    ym = [0.5 * (actA[i] + actA[i + 1]) for i in range(N - 1)]
    r_naive = fuse1(posA + xm, actA + ym)

    err = {
        "single": recon_error(r_single, gt),
        "fused_off": recon_error(r_off, gt),
        "fused_zero": recon_error(r_zero, gt),
        "naive2x": recon_error(r_naive, gt),
    }
    return {
        "N": N, "k0": k0, "n_fine": n_fine, "ridge": ridge,
        "single_nyquist_harmonic": N / 2, "fused_nyquist_harmonic": N,
        "err": err,
        "gain_fused_over_single": err["single"] / max(err["fused_off"], 1e-30),
        "gain_fused_over_naive2x": err["naive2x"] / max(err["fused_off"], 1e-30),
        "gain_zero_over_single": err["single"] / max(err["fused_zero"], 1e-30),
        "k0_relerr_single": rel_k0_error(r_single, gt, k0, n_fine),
        "k0_relerr_fused": rel_k0_error(r_off, gt, k0, n_fine),
    }


def sample_eye_temporal(signal_fn, times, *, exposure=1.0):
    """One GraphEye (n_az=1) driven on ITS OWN sequence of `times` — its own
    clock. Each tick submits one exposure of the time-varying stimulus and reads
    the receptor's transduced activation. Returns (times, activations). Two such
    eyes on disjoint `times` are two INDEPENDENT async clocks (no shared tick);
    the fusion reads the UNION of their event times."""
    from domains.two_eye_superres import ROD_CENTER_NM
    from domains.photon_eye import GraphEye
    eye = GraphEye(n_az=1, adapt_rate=0.0,
                   context={"synchronous": True, "worker_capacity": 1})
    eye.build()
    acts = []
    for t in times:
        count = int(round(max(0.0, float(exposure) * float(signal_fn(t)))))
        eye.submit_photons([{"column": 0, "wavelength_nm": ROD_CENTER_NM, "count": count}])
        eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
        rod = eye._receptors[(0, "rod")]
        acts.append(float(eye.substrate.node(rod)["attrs"].get("activation", 0.0)))
    eye.stop()
    return list(times), acts


def temporal_arm(rng, M=8, k0=6, n_fine=64, ridge=1e-6):
    """Two eyes on independent async clocks recover a temporal frequency that
    aliases in one clock. The IDENTICAL Rust kernel, positions = TIMES."""
    P = float(M)
    base = 120.0
    ph_lo = rng.uniform(0, 2 * math.pi)
    ph_hi = rng.uniform(0, 2 * math.pi)

    def sig(t):
        return (base
                + 45.0 * math.cos(2 * math.pi * 2 * t / P + ph_lo)
                + 45.0 * math.cos(2 * math.pi * k0 * t / P + ph_hi))

    cap = M
    fine = np.arange(n_fine) * P / n_fine
    gt = transduce(np.array([sig(x) for x in fine]))

    tA = [float(i) for i in range(M)]                    # clock A: ticks 0,1,..
    tB5 = [float(i) + 0.5 for i in range(M)]             # clock B: async +0.5
    tB0 = [float(i) for i in range(M)]                   # clock B: in phase (control)

    _, aA = sample_eye_temporal(sig, tA)
    _, aB5 = sample_eye_temporal(sig, tB5)
    _, aB0 = sample_eye_temporal(sig, tB0)

    def fuse1(pos, val):
        return SuperResFuser(enabled=True).fuse(
            pos, val, n_fine=n_fine, period=P, ridge=ridge,
            k_max=supported_nyquist(pos, cap))

    r_single = fuse1(tA, aA)
    r_off = fuse1(tA + tB5, aA + aB5)
    r_zero = fuse1(tA + tB0, aA + aB0)

    err = {
        "single": recon_error(r_single, gt),
        "fused_off": recon_error(r_off, gt),
        "fused_zero": recon_error(r_zero, gt),
    }
    return {
        "M": M, "k0": k0, "n_fine": n_fine, "ridge": ridge,
        "independent_async_clocks": {"clockA": tA, "clockB_async": tB5,
                                     "shared_tick": sorted(set(tA) & set(tB5))},
        "err": err,
        "gain_fused_over_single": err["single"] / max(err["fused_off"], 1e-30),
        "gain_zero_over_single": err["single"] / max(err["fused_zero"], 1e-30),
    }


def main():
    rng = np.random.default_rng(BLOCK)
    spatial = spatial_arm(rng)
    temporal = temporal_arm(rng)

    # Pre-registered PASS criteria (VISION_TWO_EYES_PREREG.md).
    checks = {
        "1_fusion_beats_single": spatial["gain_fused_over_single"] > 4.0,
        "2_fusion_beats_naive2x": spatial["gain_fused_over_naive2x"] > 2.0,
        "3_zero_offset_no_gain":
            0.8 <= spatial["gain_zero_over_single"] <= 1.25,
        "4_aliased_target":
            (spatial["k0_relerr_fused"] < 0.20
             and spatial["k0_relerr_single"] > 0.60),
        "5_temporal_async_beats_one_clock":
            temporal["gain_fused_over_single"] > 4.0,
        "6_temporal_zero_offset_no_gain":
            0.8 <= temporal["gain_zero_over_single"] <= 1.25,
    }
    result = {
        "block": BLOCK,
        "engine": engine_provenance_line(),
        "spatial": spatial,
        "temporal": temporal,
        "checks": checks,
        "all_pass": all(checks.values()),
    }
    out_path = os.path.join(ROOT, "results", "two_eye_superres.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=1)

    print("== TWO EYES → SUPER-RESOLUTION (block 175000) ==")
    print(f"SPATIAL  N={spatial['N']} k0={spatial['k0']} "
          f"(single-Nyquist {spatial['single_nyquist_harmonic']}, "
          f"fused-Nyquist {spatial['fused_nyquist_harmonic']})")
    e = spatial["err"]
    print(f"  err  single={e['single']:.3e}  fused(0.5)={e['fused_off']:.3e}  "
          f"naive2x={e['naive2x']:.3e}  fused(0.0)={e['fused_zero']:.3e}")
    print(f"  gain fused/single = {spatial['gain_fused_over_single']:.2f}×   "
          f"fused/naive2x = {spatial['gain_fused_over_naive2x']:.2f}×   "
          f"ZERO-OFFSET gain = {spatial['gain_zero_over_single']:.3f}× (≈1 ⇒ no gain)")
    print(f"  k0 relerr  single={spatial['k0_relerr_single']:.3f} (aliased)  "
          f"fused={spatial['k0_relerr_fused']:.3f} (resolved)")
    print(f"TEMPORAL M={temporal['M']} k0={temporal['k0']} — two INDEPENDENT async clocks, "
          f"shared ticks: {temporal['independent_async_clocks']['shared_tick']}")
    te = temporal["err"]
    print(f"  err  single={te['single']:.3e}  fused(async 0.5)={te['fused_off']:.3e}  "
          f"fused(0.0)={te['fused_zero']:.3e}")
    print(f"  gain async/single = {temporal['gain_fused_over_single']:.2f}×   "
          f"ZERO-OFFSET gain = {temporal['gain_zero_over_single']:.3f}× (≈1 ⇒ no gain)")
    print("CHECKS:")
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print(f"ALL PASS: {result['all_pass']}")
    return 0 if result["all_pass"] else 1


def engine_provenance_line():
    try:
        from domains.engine_provenance import engine_provenance
        return engine_provenance()
    except Exception as exc:  # pragma: no cover
        return {"error": str(exc)}


if __name__ == "__main__":
    sys.exit(main())
