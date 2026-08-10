#!/usr/bin/env python3
"""TWO EYES, ESTIMATED OFFSET → SUPER-RESOLUTION (block 176000-176999).

Closes Rung 5's largest caveat. Rung 5 (block 175000) proved two-eye
super-resolution by multi-look de-aliasing but with a KNOWN sub-receptor offset
handed to the fusion. Here the offset is ESTIMATED from the two eyes' OWN
overlapping data (`domains.two_eye_register`, reusing the proven 149000
`subcell_register.bilinear_upsample`), the estimate is fed into the UNCHANGED
Rung-5 `multilook_superres` kernel, and the super-resolution win is shown to
STILL HOLD — the eye super-resolves WITHOUT being told the offset.

The FUSION is graph-native (the `multilook_superres` Rust kernel +
`retinal_mint_superres` rule, via `domains.two_eye_superres`); REGISTRATION is a
mechanical numpy sensor (the blessed `subcell_register` / `vector_field` class);
this script only builds the texture, drives the sensors, and SCORES the results.

Pre-registered in `VISION_TWO_EYES_REGISTRATION_PREREG.md`.

Run:  python3 scripts/two_eye_registration_measure.py
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
from domains.two_eye_register import (  # noqa: E402
    estimate_offset, estimate_offset_phase)
from scripts.two_eye_superres_measure import (  # noqa: E402
    transduce, recon_error, rel_k0_error, supported_nyquist)

BLOCK = 176000
S = 100                    # finer unit: 1/100 receptor (declared §13 residual)
TRUE_DELTA = 0.5           # the eye pair's real sub-receptor offset (unknown to the kernel)
PERTURB = 0.25             # the deliberately-wrong perturbation for control C1


def make_texture(rng, N, k0):
    """A flat-wall luminance texture, period P=N, with WELL-SAMPLED low harmonics
    that DOMINATE (k=1,2,3 — the registration anchors, all below single-Nyquist
    N/2=4) plus a MODEST supra-Nyquist harmonic k0 (single-Nyquist 4 < k0 <
    fused-Nyquist 8) — the de-aliasing target that ALIASES in one eye.
    Registration locks on the dominant well-sampled structure; the modest aliased
    contamination gives a small, bounded bias. Amplitudes/phases from the seed."""
    P = float(N)
    base = 120.0
    comps = [(1, 55.0), (2, 40.0), (3, 30.0)]
    phases = {k: rng.uniform(0, 2 * math.pi) for k, _ in comps}
    a0 = 12.0
    ph0 = rng.uniform(0, 2 * math.pi)

    def tex(x):
        v = base
        for k, a in comps:
            v += a * math.cos(2 * math.pi * k * x / P + phases[k])
        v += a0 * math.cos(2 * math.pi * k0 * x / P + ph0)
        return v

    return tex, P, a0, ph0


def _fuse(pos, val, *, n_fine, period, ridge, cap):
    """One fresh graph-native fusion (a SuperResolvedField per condition)."""
    return SuperResFuser(enabled=True).fuse(
        pos, val, n_fine=n_fine, period=period, ridge=ridge,
        k_max=supported_nyquist(pos, cap))


def _register(actA, actB, *, method, N, k0):
    """Dispatch to the offset estimator. `phase` is the corrected mechanism
    (cross-frame phase on non-aliased bins); `sad` is v1 (amplitude-SAD reuse of
    subcell's bilinear_upsample — corrupted by the aliased target)."""
    if method == "phase":
        return estimate_offset_phase(actA, actB, S=S, N=N, k0=k0)
    if method == "sad":
        return estimate_offset(actA, actB, S=S)
    raise ValueError(method)


def registration_arm(rng, *, N=8, k0=6, n_fine=64, ridge=1e-6,
                     true_delta=TRUE_DELTA, method="phase"):
    """The headline arm. Estimate the offset from the two eyes' data, fuse with
    the ESTIMATE, and score against a single eye + the perturbed-offset control.
    `method="phase"` is the gated (corrected) mechanism; `method="sad"` is the
    v1 amplitude-SAD reference (reported as the FAIL diagnostic)."""
    tex, P, a0, ph0 = make_texture(rng, N, k0)
    cap = N                                              # fused Nyquist harmonic
    fine = np.arange(n_fine) * P / n_fine
    gt = transduce(np.array([tex(x) for x in fine]))     # dense true field

    # Two real GraphEyes view the SAME wall; eye B sits at the TRUE offset. The
    # kernel is NOT told the offset — we DISCARD eye B's true positions and only
    # keep its measured activations.
    posA, actA = sample_eye(tex, n_az=N, offset=0.0)
    _posB_true, actB = sample_eye(tex, n_az=N, offset=true_delta)

    # REGISTER: estimate the offset from the two activation clouds alone.
    delta_est, bt, reg_diag = _register(actA, actB, method=method, N=N, k0=k0)
    reg_err = abs(delta_est - true_delta)

    # Fuse with the ESTIMATED eye-B positions (the kernel's only knowledge of B).
    posB_est = [float(i) + delta_est for i in range(N)]
    posB_known = [float(i) + true_delta for i in range(N)]   # reference only

    def fuse(pos, val):
        return _fuse(pos, val, n_fine=n_fine, period=P, ridge=ridge, cap=cap)

    r_single = fuse(posA, actA)
    r_est = fuse(posA + posB_est, actA + actB)
    r_known = fuse(posA + posB_known, actA + actB)          # Rung-5 reference

    # C1 — perturbed offset (deliberately wrong): must degrade.
    r_pert_hi = fuse(posA + [float(i) + delta_est + PERTURB for i in range(N)],
                     actA + actB)
    r_pert_lo = fuse(posA + [float(i) + delta_est - PERTURB for i in range(N)],
                     actA + actB)

    err = {
        "single": recon_error(r_single, gt),
        "fused_est": recon_error(r_est, gt),
        "fused_known": recon_error(r_known, gt),
        "fused_pert_hi": recon_error(r_pert_hi, gt),
        "fused_pert_lo": recon_error(r_pert_lo, gt),
    }
    return {
        "method": method,
        "N": N, "k0": k0, "n_fine": n_fine, "ridge": ridge, "S": S,
        "true_delta": true_delta, "k0_amp": a0,
        "single_nyquist_harmonic": N / 2, "fused_nyquist_harmonic": N,
        "delta_est": delta_est, "bt_fine": bt, "reg_err": reg_err,
        "reg_diag": reg_diag,
        "err": err,
        "gain_est_over_single": err["single"] / max(err["fused_est"], 1e-30),
        "gain_known_over_single": err["single"] / max(err["fused_known"], 1e-30),
        "pert_hi_over_est": err["fused_pert_hi"] / max(err["fused_est"], 1e-30),
        "pert_lo_over_est": err["fused_pert_lo"] / max(err["fused_est"], 1e-30),
        "k0_relerr_single": rel_k0_error(r_single, gt, k0, n_fine),
        "k0_relerr_fused_est": rel_k0_error(r_est, gt, k0, n_fine),
    }


def zero_offset_arm(rng, *, N=8, k0=6, n_fine=64, ridge=1e-6):
    """C2 — the Rung-5 falsifier, now on the ESTIMATE. Two IDENTICAL eyes
    (true offset 0): the estimate must collapse to ~0 and show NO gain."""
    tex, P, _a0, _ph0 = make_texture(rng, N, k0)
    cap = N
    fine = np.arange(n_fine) * P / n_fine
    gt = transduce(np.array([tex(x) for x in fine]))

    posA, actA = sample_eye(tex, n_az=N, offset=0.0)
    _posB, actB = sample_eye(tex, n_az=N, offset=0.0)        # eye B at ZERO offset

    delta_est, bt, _diag = estimate_offset_phase(actA, actB, S=S, N=N, k0=k0)
    posB_est = [float(i) + delta_est for i in range(N)]

    def fuse(pos, val):
        return _fuse(pos, val, n_fine=n_fine, period=P, ridge=ridge, cap=cap)

    r_single = fuse(posA, actA)
    r_est = fuse(posA + posB_est, actA + actB)
    err_single = recon_error(r_single, gt)
    err_est = recon_error(r_est, gt)
    return {
        "true_delta": 0.0, "delta_est": delta_est, "bt_fine": bt,
        "abs_delta_est": abs(delta_est),
        "err_single": err_single, "err_fused_est": err_est,
        "gain_est_over_single": err_single / max(err_est, 1e-30),
    }


def main():
    # PRIMARY (corrected) mechanism: the offset as a CROSS-FRAME PHASE.
    reg = registration_arm(np.random.default_rng(BLOCK), method="phase")
    # v1 REFERENCE: the amplitude-SAD subcell reuse (the committed FAIL / named
    # constraint) — SAME texture/seed, reported for the contrast.
    reg_sad = registration_arm(np.random.default_rng(BLOCK), method="sad")
    zero = zero_offset_arm(np.random.default_rng(BLOCK + 1))

    checks = {
        # H1 — registration accuracy.
        "H1_registration_accurate": reg["reg_err"] <= 0.05,
        # H2 — super-res holds under the estimated offset.
        "H2_fusion_beats_single": reg["gain_est_over_single"] > 4.0,
        "H2_k0_resolved_fused": reg["k0_relerr_fused_est"] < 0.25,
        "H2_k0_aliased_single": reg["k0_relerr_single"] > 0.60,
        # C1 — perturbed offset degrades (load-bearing).
        "C1_perturb_hi_degrades": reg["pert_hi_over_est"] >= 2.0,
        "C1_perturb_lo_degrades": reg["pert_lo_over_est"] >= 2.0,
        # C2 — zero-offset falsifier on the estimate.
        "C2_zero_offset_estimate_collapses": zero["abs_delta_est"] <= 0.02,
        "C2_zero_offset_no_gain":
            0.8 <= zero["gain_est_over_single"] <= 1.25,
    }
    result = {
        "block": BLOCK,
        "engine": _engine_line(),
        "registration": reg,               # PRIMARY: cross-frame phase (gated)
        "registration_sad_v1": reg_sad,    # v1 amplitude-SAD reference (FAIL)
        "zero_offset": zero,
        "checks": checks,
        "all_pass": all(checks.values()),
    }
    out_path = os.path.join(ROOT, "results", "two_eye_registration.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=1)

    print("== TWO EYES, ESTIMATED OFFSET → SUPER-RESOLUTION (block 176000) ==")
    print(f"[v1 SAD reference — FAIL] est δ={reg_sad['delta_est']:.4f} "
          f"err={reg_sad['reg_err']:.4f}  gain(EST)/single="
          f"{reg_sad['gain_est_over_single']:.2f}× "
          f"(aliased-target corrupts amplitude-SAD)")
    print("-- corrected mechanism: OFFSET AS A CROSS-FRAME PHASE --")
    print(f"REGISTER  true δ={reg['true_delta']}  est δ={reg['delta_est']:.4f}  "
          f"(bt={reg['bt_fine']} finer units, S={S})  err={reg['reg_err']:.4f}")
    e = reg["err"]
    print(f"  err  single={e['single']:.3e}  fused(EST)={e['fused_est']:.3e}  "
          f"fused(known)={e['fused_known']:.3e}")
    print(f"  gain fused(EST)/single = {reg['gain_est_over_single']:.2f}×   "
          f"(known-offset ref = {reg['gain_known_over_single']:.2f}×)")
    print(f"  k0 relerr  single={reg['k0_relerr_single']:.3f} (aliased)  "
          f"fused(EST)={reg['k0_relerr_fused_est']:.3f} (resolved)")
    print(f"  PERTURB ±{PERTURB}:  err(+)={e['fused_pert_hi']:.3e} "
          f"({reg['pert_hi_over_est']:.1f}× est)   err(−)={e['fused_pert_lo']:.3e} "
          f"({reg['pert_lo_over_est']:.1f}× est)  — must degrade")
    print(f"ZERO-OFFSET falsifier: est δ={zero['delta_est']:.4f} "
          f"(|δ|={zero['abs_delta_est']:.4f})  gain={zero['gain_est_over_single']:.3f}× "
          f"(≈1 ⇒ no gain)")
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
