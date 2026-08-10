#!/usr/bin/env python3
"""TWO EYES SUPER-RESOLVE ON THE REAL 2-D az×el RETINA (block 177000-177999).

Closes Rung 5's largest remaining caveat (`VISION_TWO_EYES_REGISTRATION_RESULTS.
md` §6). Two low-res 2-D photon eyes, eye B offset from eye A by a real
sub-receptor AZIMUTH amount the kernel is NOT told, both view ONE flat 2-D
textured wall. For EACH elevation row independently we ESTIMATE the row's offset
with the UNCHANGED Rung-5b cross-frame-phase estimator and FUSE that row with the
UNCHANGED Rung-5 `multilook_superres` kernel. The 2-D fused field recovers a
supra-Nyquist azimuth harmonic neither 2-D eye represents alone (H1/H2), and the
per-row estimates AGREE with the single true offset (SEPARABILITY — the real
claim): the 2-D problem decomposes into independent rows.

The eyes/fusion/registration are the PROVEN pieces (`domains.two_eye_superres_2d`
→ the graph-native 2-D `GraphEye`; `domains.two_eye_superres.SuperResFuser` →
the `multilook_superres` kernel; `domains.two_eye_register.estimate_offset_phase`
→ the blessed numpy sensor). This script only builds the texture, loops the
proven 1-D pieces over rows, and SCORES. NO agent decision. NO Rust built.

Pre-registered in `VISION_TWO_EYES_2D_PREREG.md`.

Run:  python3 scripts/two_eye_superres_2d_measure.py
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

from domains.two_eye_superres import SuperResFuser  # noqa: E402
from domains.two_eye_superres_2d import sample_eye_2d  # noqa: E402
from domains.two_eye_register import estimate_offset_phase  # noqa: E402
from scripts.two_eye_superres_measure import (  # noqa: E402
    transduce, recon_error, rel_k0_error, supported_nyquist)

BLOCK = 177000
S = 100                    # finer unit: 1/100 receptor (declared §13 residual)
TRUE_DELTA = 0.5           # the eye pair's real sub-receptor AZIMUTH offset
PERTURB = 0.25             # the deliberately-wrong perturbation for control C1
N_TEXTURED = 6             # textured elevation rows (independent reg problems)
N = 8                      # azimuth receptors (period P = N)
K0 = 6                     # supra-Nyquist target (single-Nyquist 4 < 6 < fused 8)
N_FINE = 64
RIDGE = 1e-6


def make_texture_2d(rng, *, N=N, k0=K0, n_textured=N_TEXTURED):
    """A flat 2-D wall, period P=N in azimuth, with `n_textured` rows carrying
    WELL-SAMPLED anchors (k=1,2,3, all below single-Nyquist N/2) that dominate
    plus a MODEST supra-Nyquist target k0 (aliases in one eye) — each row with its
    OWN random phases (⇒ genuinely independent per-row registration problems) —
    followed by ONE FLAT row (all amplitudes 0, constant luminance) for the
    no-texture control C4. Returns `(tex, P, flat_row)`: `tex(x, row)` and the
    index of the flat row."""
    P = float(N)
    base = 120.0
    comps = [(1, 55.0), (2, 40.0), (3, 30.0)]
    a0 = 12.0
    phases = {}       # phases[row][k]
    ph0 = {}
    for r in range(n_textured):
        phases[r] = {k: rng.uniform(0, 2 * math.pi) for k, _ in comps}
        ph0[r] = rng.uniform(0, 2 * math.pi)
    flat_row = n_textured                     # the extra flat row

    def tex(x, row):
        if row >= n_textured:                 # the flat row — pure DC
            return base
        v = base
        for k, a in comps:
            v += a * math.cos(2 * math.pi * k * x / P + phases[row][k])
        v += a0 * math.cos(2 * math.pi * k0 * x / P + ph0[row])
        return v

    return tex, P, flat_row


def _fuse(pos, val, *, period, cap):
    """One fresh graph-native fusion (a SuperResolvedField per condition)."""
    return SuperResFuser(enabled=True).fuse(
        pos, val, n_fine=N_FINE, period=period, ridge=RIDGE,
        k_max=supported_nyquist(pos, cap))


def _ac_std(field):
    """AC standard deviation of a reconstruction (departure from its own mean) —
    the fabricated-detail metric for the flat row (C4)."""
    a = np.asarray(field, dtype=np.float64)
    return float(np.std(a - a.mean()))


def separability_arm(rng, *, true_delta=TRUE_DELTA):
    """The headline arm. Two 2-D eyes view ONE wall; eye B sits at the TRUE
    azimuth offset. Per elevation row: register (estimate the offset from the
    two rows' activations alone) → fuse with the ESTIMATE. Score per row + the
    aggregate 2-D field, and the per-row offset SPREAD (separability)."""
    tex, P, flat_row = make_texture_2d(rng)
    n_el = flat_row + 1                        # textured rows + the flat row
    cap = N                                    # fused Nyquist harmonic
    fine = np.arange(N_FINE) * P / N_FINE

    # Two REAL 2-D GraphEyes view the SAME wall; eye B at the TRUE offset. The
    # kernel is NOT told the offset — we DISCARD eye B's true positions and keep
    # only its measured per-cell activations.
    posA, actA = sample_eye_2d(tex, n_az=N, n_el=n_el, offset=0.0)
    _posB_true, actB = sample_eye_2d(tex, n_az=N, n_el=n_el, offset=true_delta)

    rows = []
    for row in range(n_el):
        gt = transduce(np.array([tex(x, row) for x in fine]))   # dense true field
        # REGISTER: estimate the offset from this row's two activation clouds.
        delta_est, bt, _diag = estimate_offset_phase(
            actA[row], actB[row], S=S, N=N, k0=K0)
        posB_est = [float(c) + delta_est for c in range(N)]

        r_single = _fuse(posA, actA[row], period=P, cap=cap)
        r_est = _fuse(posA + posB_est, actA[row] + actB[row], period=P, cap=cap)
        r_pert_hi = _fuse(posA + [float(c) + delta_est + PERTURB for c in range(N)],
                          actA[row] + actB[row], period=P, cap=cap)
        r_pert_lo = _fuse(posA + [float(c) + delta_est - PERTURB for c in range(N)],
                          actA[row] + actB[row], period=P, cap=cap)

        e_single = recon_error(r_single, gt)
        e_est = recon_error(r_est, gt)
        rows.append({
            "row": row, "is_flat": row >= flat_row,
            "delta_est": delta_est, "bt_fine": bt,
            "reg_err": abs(delta_est - true_delta) if row < flat_row else None,
            "err_single": e_single, "err_fused_est": e_est,
            "err_fused_pert_hi": recon_error(r_pert_hi, gt),
            "err_fused_pert_lo": recon_error(r_pert_lo, gt),
            "gain_est_over_single": e_single / max(e_est, 1e-30),
            "pert_hi_over_est": recon_error(r_pert_hi, gt) / max(e_est, 1e-30),
            "pert_lo_over_est": recon_error(r_pert_lo, gt) / max(e_est, 1e-30),
            "k0_relerr_single": rel_k0_error(r_single, gt, K0, N_FINE),
            "k0_relerr_fused_est": rel_k0_error(r_est, gt, K0, N_FINE),
            "fused_ac_std": _ac_std(r_est),
        })

    tex_rows = [r for r in rows if not r["is_flat"]]
    deltas = [r["delta_est"] for r in tex_rows]
    sum_single = sum(r["err_single"] for r in tex_rows)
    sum_fused = sum(r["err_fused_est"] for r in tex_rows)
    return {
        "true_delta": true_delta, "N": N, "k0": K0, "n_textured": N_TEXTURED,
        "flat_row": flat_row, "S": S, "n_fine": N_FINE, "ridge": RIDGE,
        "single_nyquist_harmonic": N / 2, "fused_nyquist_harmonic": N,
        "rows": rows,
        "delta_est_per_row": deltas,
        "separability_spread": (max(deltas) - min(deltas)) if deltas else None,
        "separability_std": float(np.std(deltas)) if deltas else None,
        "reg_err_max": max(r["reg_err"] for r in tex_rows),
        "aggregate_gain": sum_single / max(sum_fused, 1e-30),
        "per_row_gain_min": min(r["gain_est_over_single"] for r in tex_rows),
        "k0_relerr_fused_max": max(r["k0_relerr_fused_est"] for r in tex_rows),
        "k0_relerr_single_min": min(r["k0_relerr_single"] for r in tex_rows),
        "pert_min_over_est": min(
            min(r["pert_hi_over_est"], r["pert_lo_over_est"]) for r in tex_rows),
    }


def zero_offset_arm(rng):
    """C2 — the Rung-5 falsifier in 2-D. Two IDENTICAL 2-D eyes (true offset 0):
    every row's estimate must collapse to ~0 and show NO gain."""
    tex, P, flat_row = make_texture_2d(rng)
    n_el = flat_row + 1
    cap = N
    fine = np.arange(N_FINE) * P / N_FINE

    posA, actA = sample_eye_2d(tex, n_az=N, n_el=n_el, offset=0.0)
    _posB, actB = sample_eye_2d(tex, n_az=N, n_el=n_el, offset=0.0)

    rows = []
    for row in range(flat_row):                # textured rows only
        gt = transduce(np.array([tex(x, row) for x in fine]))
        delta_est, bt, _diag = estimate_offset_phase(
            actA[row], actB[row], S=S, N=N, k0=K0)
        posB_est = [float(c) + delta_est for c in range(N)]
        e_single = recon_error(_fuse(posA, actA[row], period=P, cap=cap), gt)
        e_est = recon_error(
            _fuse(posA + posB_est, actA[row] + actB[row], period=P, cap=cap), gt)
        rows.append({
            "row": row, "delta_est": delta_est, "abs_delta_est": abs(delta_est),
            "gain_est_over_single": e_single / max(e_est, 1e-30),
        })
    return {
        "true_delta": 0.0, "rows": rows,
        "abs_delta_est_max": max(r["abs_delta_est"] for r in rows),
        "gain_min": min(r["gain_est_over_single"] for r in rows),
        "gain_max": max(r["gain_est_over_single"] for r in rows),
    }


def main():
    reg = separability_arm(np.random.default_rng(BLOCK))
    zero = zero_offset_arm(np.random.default_rng(BLOCK + 1))
    flat = next(r for r in reg["rows"] if r["is_flat"])

    checks = {
        # H1 — registration accurate per row.
        "H1_all_rows_registration_accurate": reg["reg_err_max"] <= 0.05,
        # SEPARABILITY — the per-row estimates agree.
        "SEP_spread_bound": reg["separability_spread"] <= 0.05,
        "SEP_std_bound": reg["separability_std"] <= 0.03,
        # H2 — 2-D super-res holds under the estimate.
        "H2_aggregate_gain": reg["aggregate_gain"] > 4.0,
        "H2_every_row_gain": reg["per_row_gain_min"] > 4.0,
        "H2_k0_resolved_fused": reg["k0_relerr_fused_max"] < 0.25,
        "H2_k0_aliased_single": reg["k0_relerr_single_min"] > 0.60,
        # C1 — perturbed offset degrades, every row.
        "C1_perturb_degrades": reg["pert_min_over_est"] >= 2.0,
        # C2 — zero-offset falsifier, every row.
        "C2_zero_offset_estimate_collapses": zero["abs_delta_est_max"] <= 0.02,
        "C2_zero_offset_no_gain":
            0.8 <= zero["gain_min"] and zero["gain_max"] <= 1.25,
        # C4 — flat row fabricates no detail.
        "C4_flat_row_no_fabrication": flat["fused_ac_std"] <= 1e-4,
        "C4_flat_row_zero_offset": abs(flat["delta_est"]) == 0.0,
    }
    result = {
        "block": BLOCK,
        "engine": _engine_line(),
        "separability": reg,
        "zero_offset": zero,
        "flat_row": flat,
        "checks": checks,
        "all_pass": all(checks.values()),
    }
    out_path = os.path.join(ROOT, "results", "two_eye_superres_2d.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=1)

    print("== TWO EYES SUPER-RESOLVE ON THE REAL 2-D RETINA (block 177000) ==")
    print(f"2-D wall: N={N} azimuth, {reg['n_textured']} textured rows + 1 flat, "
          f"k0={K0} (single-Nyq {reg['single_nyquist_harmonic']}, fused-Nyq "
          f"{reg['fused_nyquist_harmonic']}); true δ_az={reg['true_delta']}")
    print("-- per elevation ROW (the same 1-D estimator + fuser, independently) --")
    for r in reg["rows"]:
        tag = "FLAT" if r["is_flat"] else "TEX "
        re = "  --  " if r["reg_err"] is None else f"{r['reg_err']:.4f}"
        print(f"  row {r['row']} [{tag}]  δ_est={r['delta_est']:+.4f}  "
              f"reg_err={re}  gain={r['gain_est_over_single']:7.2f}×  "
              f"k0(s={r['k0_relerr_single']:.3f}/f={r['k0_relerr_fused_est']:.3f})"
              f"  ac_std={r['fused_ac_std']:.2e}")
    print("-- SEPARABILITY (headline 2) --")
    print(f"  per-row δ_est = {[round(d,4) for d in reg['delta_est_per_row']]}")
    print(f"  spread(max-min) = {reg['separability_spread']:.4f}  "
          f"std = {reg['separability_std']:.4f}  reg_err_max = {reg['reg_err_max']:.4f}")
    print("-- H2 (super-res holds in 2-D under the estimate) --")
    print(f"  AGGREGATE 2-D gain fused/single = {reg['aggregate_gain']:.2f}×   "
          f"per-row min gain = {reg['per_row_gain_min']:.2f}×")
    print(f"  k0 relerr  single_min={reg['k0_relerr_single_min']:.3f} (aliased)  "
          f"fused_max={reg['k0_relerr_fused_max']:.3f} (resolved)")
    print(f"  PERTURB ±{PERTURB}: min degrade over rows = "
          f"{reg['pert_min_over_est']:.1f}× (must ≥ 2×)")
    print("-- C2 zero-offset falsifier (2-D) --")
    print(f"  |δ_est|_max={zero['abs_delta_est_max']:.4f}  "
          f"gain∈[{zero['gain_min']:.3f},{zero['gain_max']:.3f}] (≈1 ⇒ no gain)")
    print("-- C4 no-texture (flat) row --")
    print(f"  fused AC std = {flat['fused_ac_std']:.2e} (must ≤ 1e-4)  "
          f"δ_est={flat['delta_est']:+.4f}")
    print("CHECKS:")
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print(f"ALL PASS: {result['all_pass']}")
    print("wrote", out_path)
    return 0 if result["all_pass"] else 1


def _engine_line():
    try:
        from domains.engine_provenance import engine_provenance
        return engine_provenance()
    except Exception as exc:  # pragma: no cover
        return {"error": str(exc)}


if __name__ == "__main__":
    sys.exit(main())
