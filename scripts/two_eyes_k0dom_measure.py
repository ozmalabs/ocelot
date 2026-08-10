#!/usr/bin/env python3
"""TWO EYES, k0-DOMINANT WALL — does the ESTIMATED-offset gain approach the
KNOWN-offset ceiling? (block 178000-178999).

Tests the supervisor's recorded Rung-5b prediction
(`VISION_TWO_EYES_REGISTRATION_RESULTS.md` §6): the cross-frame-phase estimator
reads δ only from the CLEAN non-aliased bins {1,3} and is therefore IMMUNE to
the supra-Nyquist harmonic k0's amplitude, so a k0-DOMINANT wall should give
BOTH accurate registration AND a large gain — closing the modest 19.7× (estimated)
vs 683× (known-offset) gap measured at A≈12.

This is a PURE MEASUREMENT rung. It REUSES, byte-unchanged:
  * `domains.two_eye_register.estimate_offset_phase` — the Rung-5b estimator,
  * `domains.two_eye_superres.{SuperResFuser, sample_eye}` — the Rung-5 fusion,
  * `scripts.two_eye_superres_measure.{transduce, recon_error, rel_k0_error,
    supported_nyquist}` — the Rung-5 scoring.
Only the TEXTURE's k0 amplitude A is swept. NO Rust, NO new Term. Python is I/O
and measurement; every de-aliasing decision stays the Rust kernel + seed rule.

Pre-registered in `VISION_TWO_EYES_K0DOM_PREREG.md` (thresholds fixed before any
number). Anchor phases are drawn ONCE from seed 178000 and held FIXED across the
sweep, so ONLY A varies.

Run:  python3 scripts/two_eyes_k0dom_measure.py
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
from domains.two_eye_register import estimate_offset_phase  # noqa: E402
from scripts.two_eye_superres_measure import (  # noqa: E402
    transduce, recon_error, rel_k0_error, supported_nyquist)

BLOCK = 178000
S = 100                    # finer unit: 1/100 receptor (declared §13 residual)
TRUE_DELTA = 0.5           # the eye pair's real sub-receptor offset (unknown to the kernel)
PERTURB = 0.25             # the deliberately-wrong perturbation for control C_perturb

N = 8
K0 = 6
N_FINE = 64
RIDGE = 1e-6
BASE = 120.0
ANCHORS = [(1, 55.0), (2, 40.0), (3, 30.0)]   # well-sampled registration anchors

# The k0 amplitude sweep — below the modest 176000 case (A=12) up to k0-DOMINANT
# (A=192 >> the anchor sum 125). A_lo / A_hi are the pre-registered anchor points.
A_SWEEP = [6.0, 12.0, 24.0, 48.0, 96.0, 192.0]
A_LO = 12.0
A_HI = 192.0


def make_texture(a0, phases, ph0):
    """A flat-wall luminance texture: FIXED well-sampled anchors (k=1,2,3) whose
    phases are held across the sweep, plus the supra-Nyquist target k0 at the
    swept amplitude `a0`. The anchors dominate the CLEAN bins {1,3} the phase
    estimator reads; `a0` scales ONLY the k0 (bin-2-aliasing) energy."""
    P = float(N)

    def tex(x):
        v = BASE
        for k, a in ANCHORS:
            v += a * math.cos(2 * math.pi * k * x / P + phases[k])
        v += a0 * math.cos(2 * math.pi * K0 * x / P + ph0)
        return v

    return tex, P


def _fuse(pos, val, *, period, cap):
    """One fresh graph-native fusion (a SuperResolvedField per condition)."""
    return SuperResFuser(enabled=True).fuse(
        pos, val, n_fine=N_FINE, period=period, ridge=RIDGE,
        k_max=supported_nyquist(pos, cap))


def measure_A(a0, phases, ph0):
    """One point of the sweep: register at the ESTIMATE, fuse (estimated / known /
    perturbed), and score MSE vs the dense true field. Also the zero-offset
    falsifier at this same A."""
    tex, P = make_texture(a0, phases, ph0)
    cap = N                                              # fused Nyquist harmonic
    fine = np.arange(N_FINE) * P / N_FINE
    gt = transduce(np.array([tex(x) for x in fine]))     # dense true field

    # Two real GraphEyes view the SAME wall; eye B sits at the TRUE offset. The
    # kernel is NOT told the offset — DISCARD eye B's true positions, keep only
    # its measured activations.
    posA, actA = sample_eye(tex, n_az=N, offset=0.0)
    _posB_true, actB = sample_eye(tex, n_az=N, offset=TRUE_DELTA)

    # REGISTER: the UNCHANGED cross-frame-phase estimator (clean bins {1,3}).
    delta_est, bt, reg_diag = estimate_offset_phase(actA, actB, S=S, N=N, k0=K0)
    reg_err = abs(delta_est - TRUE_DELTA)
    # The CONTINUOUS phase read (pre-rounding) — the true immunity signal beneath
    # the stepped bt observable: how far the clean-bin phase drifts as k0 grows.
    delta_raw = reg_diag.get("delta_raw")
    reg_err_raw = abs(delta_raw - TRUE_DELTA) if delta_raw is not None else None

    posB_est = [float(i) + delta_est for i in range(N)]
    posB_known = [float(i) + TRUE_DELTA for i in range(N)]

    def fuse(pos, val):
        return _fuse(pos, val, period=P, cap=cap)

    r_single = fuse(posA, actA)
    r_est = fuse(posA + posB_est, actA + actB)
    r_known = fuse(posA + posB_known, actA + actB)          # ceiling reference
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

    # ── C_zero at this A: two IDENTICAL eyes (true offset 0) ──────────────────
    _posB0, actB0 = sample_eye(tex, n_az=N, offset=0.0)
    d0, bt0, _d = estimate_offset_phase(actA, actB0, S=S, N=N, k0=K0)
    posB0_est = [float(i) + d0 for i in range(N)]
    err_zero_single = recon_error(fuse(posA, actA), gt)
    err_zero_est = recon_error(fuse(posA + posB0_est, actA + actB0), gt)

    return {
        "A": a0,
        "delta_est": delta_est, "bt_fine": bt, "reg_err": reg_err,
        "delta_raw": delta_raw, "reg_err_raw": reg_err_raw,
        "reg_bins": reg_diag.get("bins"),
        "err": err,
        "gain_est_over_single": err["single"] / max(err["fused_est"], 1e-30),
        "gain_known_over_single": err["single"] / max(err["fused_known"], 1e-30),
        "pert_hi_over_est": err["fused_pert_hi"] / max(err["fused_est"], 1e-30),
        "pert_lo_over_est": err["fused_pert_lo"] / max(err["fused_est"], 1e-30),
        "k0_relerr_single": rel_k0_error(r_single, gt, K0, N_FINE),
        "k0_relerr_fused_est": rel_k0_error(r_est, gt, K0, N_FINE),
        "zero": {
            "abs_delta_est": abs(d0), "bt_fine": bt0,
            "err_single": err_zero_single, "err_fused_est": err_zero_est,
            "gain_est_over_single":
                err_zero_single / max(err_zero_est, 1e-30),
        },
    }


def run_sweep():
    # Anchor phases + k0 phase drawn ONCE from the block seed, then HELD across
    # the whole A sweep — only the amplitude varies.
    rng = np.random.default_rng(BLOCK)
    phases = {k: rng.uniform(0, 2 * math.pi) for k, _ in ANCHORS}
    ph0 = rng.uniform(0, 2 * math.pi)
    return [measure_A(a0, phases, ph0) for a0 in A_SWEEP]


def _at(sweep, a0):
    for p in sweep:
        if p["A"] == a0:
            return p
    raise KeyError(a0)


def evaluate(sweep):
    lo = _at(sweep, A_LO)
    hi = _at(sweep, A_HI)
    checks = {
        # Part 1 — IMMUNITY.
        "P1a_reg_err_bounded_all_A":
            all(p["reg_err"] <= 0.05 for p in sweep),
        "P1b_reg_err_no_growth":
            hi["reg_err"] <= lo["reg_err"] + 0.02,
        # Part 2 — GAIN RISES TOWARD THE CEILING.
        "P2a_gain_rises_off_modest":
            hi["gain_est_over_single"] >= 3.0 * lo["gain_est_over_single"],
        "P2b_gain_within_order_of_ceiling":
            hi["gain_est_over_single"] >= 0.10 * hi["gain_known_over_single"],
        # Controls.
        "C_ceiling_est_not_above_known":
            all(p["gain_est_over_single"] <= 2.0 * p["gain_known_over_single"]
                for p in sweep),
        "C_perturb_degrades_at_hi":
            min(hi["pert_hi_over_est"], hi["pert_lo_over_est"]) >= 2.0,
        "C_zero_no_gain_all_A":
            all(0.8 <= p["zero"]["gain_est_over_single"] <= 1.25
                for p in sweep),
    }
    part1 = checks["P1a_reg_err_bounded_all_A"] and checks["P1b_reg_err_no_growth"]
    part2 = (checks["P2a_gain_rises_off_modest"]
             and checks["P2b_gain_within_order_of_ceiling"])
    controls = (checks["C_ceiling_est_not_above_known"]
                and checks["C_perturb_degrades_at_hi"]
                and checks["C_zero_no_gain_all_A"])
    verdict = "CONFIRMED" if (part1 and part2) else "FALSIFIED"
    return checks, {
        "part1_immunity": part1,
        "part2_gain_rises": part2,
        "controls_hold": controls,
        "prediction": verdict,
    }


def _engine_line():
    try:
        from domains.engine_provenance import engine_provenance
        return engine_provenance()
    except Exception as exc:  # pragma: no cover
        return {"error": str(exc)}


def main():
    sweep = run_sweep()
    checks, summary = evaluate(sweep)
    result = {
        "block": BLOCK,
        "engine": _engine_line(),
        "config": {
            "N": N, "k0": K0, "n_fine": N_FINE, "ridge": RIDGE, "S": S,
            "base": BASE, "anchors": ANCHORS, "true_delta": TRUE_DELTA,
            "perturb": PERTURB, "A_sweep": A_SWEEP, "A_lo": A_LO, "A_hi": A_HI,
            "single_nyquist_harmonic": N / 2, "fused_nyquist_harmonic": N,
        },
        "sweep": sweep,
        "checks": checks,
        "summary": summary,
        "all_controls_hold": summary["controls_hold"],
    }
    out_path = os.path.join(ROOT, "results", "two_eye_k0dom.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=1)

    print("== TWO EYES, k0-DOMINANT WALL (block 178000) ==")
    print(f"  N={N} k0={K0} (single-Nyquist {N/2} < k0 < fused-Nyquist {N}), "
          f"anchors={ANCHORS}, δ_true={TRUE_DELTA}")
    print("  A       δ_est  δ_raw   reg_err  reg_err_raw   gain_est   gain_known   "
          "est/ceil   k0_re(single→est)   zero_gain   pert(min×)")
    for p in sweep:
        frac = p["gain_est_over_single"] / max(p["gain_known_over_single"], 1e-30)
        pmin = min(p["pert_hi_over_est"], p["pert_lo_over_est"])
        print(f"  {p['A']:6.0f}  {p['delta_est']:6.3f} {p['delta_raw']:6.3f}  "
              f"{p['reg_err']:7.4f}  {p['reg_err_raw']:10.4f}  "
              f"{p['gain_est_over_single']:9.2f}  {p['gain_known_over_single']:11.2f}  "
              f"{frac:8.4f}   {p['k0_relerr_single']:.3f}→{p['k0_relerr_fused_est']:.3f}      "
              f"{p['zero']['gain_est_over_single']:6.3f}    {pmin:8.1f}")
    print("CHECKS:")
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print(f"  part1_immunity   = {summary['part1_immunity']}")
    print(f"  part2_gain_rises = {summary['part2_gain_rises']}")
    print(f"  controls_hold    = {summary['controls_hold']}")
    print(f"PREDICTION: {summary['prediction']}")
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
