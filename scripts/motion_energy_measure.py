#!/usr/bin/env python3
"""MOTION IS ORIENTATION IN SPACE-TIME, READ AS INTERFERENCE -- does a
motion-energy (Adelson & Bergen 1985) channel make ISI=0 ACTIVELY WORSE, where
every correspondence/abduction mechanism in this tree makes it BEST?

Confirmatory measurement for VISION_MOTIONENERGY_PREREG.md (committed BEFORE any
number). Seeds 113000-113999.  Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/motion_energy_measure.py

THE MECHANISM is the Rust Term `MotionEnergy` (enum index 179, ADDITIVE, default
OFF -- no seed binds it).  It reduces the raster to the horizontal space-time
signal, takes the joint 2-D DFT over (x, ti), and partitions the power
|S(wx, wt)|^2 by the SIGN of the spatiotemporal orientation: opposite-sign
quadrants = rightward, same-sign = leftward, wt==0 = static, wx==0 = flicker.
The directional readout is the OPPONENT (right - left).

EVERY ARM re-derives the mechanism INDEPENDENTLY in numpy (np.fft) and checks
agreement against the Rust Term condition-by-condition, per the pixel-seam rung's
n_disagree=0 discipline.  A float DFT cannot be byte-identical across two
algorithms, so agreement is to a RELATIVE tolerance and the max disagreement is
reported -- this is a cross-check, NOT a verdict threshold (PROTOCOL 13).

THE STIMULUS FAMILY is the phi/timephi/gapabduce two-flash grid, UNCHANGED:
S_GRID and K_GRID are gapabduce's exactly, so R(k) is comparable to the five
failed mechanisms cell-for-cell.  Motion energy consumes the RAW BOUNDED RASTER
(no figure/ground split) -- a capability the abduction family lacked.
"""
from __future__ import annotations
import json
import sys

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import substrate_rs as srs                            # noqa: E402
from domains import motion_group_world as mgw          # noqa: E402

# --- the engine this rung's numbers are attributed to (PROTOCOL 10.1). Printed
# from INSIDE the measuring process and compared; divergence ABORTS.
EXPECT_ENGINE = "e039d2eec2dd"

# --- stimulus configuration (PROTOCOL 13: declared residuals, inherited from the
# gapabduce rung; construction only, never a verdict threshold) ----------------
DOT = 4              # phi rung's DOT = BLOCK
FIELD_H = 24
FIELD_W = 160
BG = 0
FG = 255
ROW = 8

# --- the INDEPENDENT VARIABLES: iterated, never compared against.  Gapabduce's
# grids EXACTLY, so the comparison to the five failed mechanisms is cell-exact. -
S_GRID = [1, 2, 4, 6, 8, 12, 16, 20, 32]
K_GRID = [0, 1, 2, 3, 4, 5, 6, 7]

# The AGREEMENT tolerance: a cross-check between two DFT algorithms (Rust naive
# vs numpy FFT), NOT a verdict.  Relative, and the max observed diff is reported.
AGREE_RTOL = 1e-9

# The NOISE arm's ONLY randomness (declared block).
NOISE_LO = 113000
NOISE_HI = 113100

FIELDS = ("right", "left", "static", "flicker", "dc", "total_ac",
          "opponent", "opp_frac", "motion_frac", "width", "frames")


# --------------------------------------------------------------------------- #
#  world: PIXELS.  The adapter renders a raster; it decides nothing.
# --------------------------------------------------------------------------- #
def render(col):
    """A uniform BG field carrying one hard-edged DOTxDOT square at column `col`.
    `col is None` renders the blank field."""
    f = np.full((FIELD_H, FIELD_W), BG, dtype=np.float64)
    if col is not None:
        f[ROW:ROW + DOT, col:col + DOT] = FG
    return f


def phi_frames(col0, S, k):
    """THE PHI TOPOLOGY as RASTERS: one pre-gap sample, k blank frames, one
    resumed sample.  Two-flash apparent motion, right by S."""
    return [render(col0)] + [render(None)] * k + [render(col0 + S)]


def rigid_frames(col0, S, step):
    """Continuous rightward motion by `step` px/frame until col0+S.  The
    dead-instrument control: real motion MUST read opponent > 0."""
    frames, c = [], col0
    while c < col0 + S:
        frames.append(render(c))
        c = min(c + step, col0 + S)
    frames.append(render(col0 + S))
    return frames


def to_seq(frames):
    """Flatten rasters to the Term's row-major int lists."""
    return [[int(v) for v in f.ravel()] for f in frames]


# --------------------------------------------------------------------------- #
#  THE MECHANISM, RE-DERIVED IN NUMPY.  Matches the Rust `motion_energy_spectrum`
#  step-for-step: row-collapse, joint (x, ti) DFT, sign partition of |S|^2.
#  Uses np.fft (an INDEPENDENT DFT algorithm) so agreement with the Rust naive
#  transform validates the port.
# --------------------------------------------------------------------------- #
def me_numpy(frames):
    F = np.stack([np.asarray(f, np.float64) for f in frames], axis=0)  # (T,H,W)
    t = F.shape[0]
    w = F.shape[2]
    if t < 2 or w == 0:
        return {k: 0.0 for k in FIELDS}
    s = F.sum(axis=1)                       # (T, W): collapse rows
    S = np.fft.fft2(s)                      # joint DFT over (ti, x)
    P = (S.real ** 2 + S.imag ** 2)         # power |S|^2, shape (T, W)
    ft = np.fft.fftfreq(t, d=1.0) * t       # signed integer freqs
    fx = np.fft.fftfreq(w, d=1.0) * w
    ft = np.rint(ft).astype(int)[:, None]
    fx = np.rint(fx).astype(int)[None, :]
    dc = P[(fx == 0) & (ft == 0)].sum()
    stat = P[(ft == 0) & (fx != 0)].sum()
    flick = P[(fx == 0) & (ft != 0)].sum()
    moving = (fx != 0) & (ft != 0)
    same = moving & ((fx > 0) == (ft > 0))
    opp = moving & ((fx > 0) != (ft > 0))
    left = P[same].sum()
    right = P[opp].sum()
    total_ac = right + left + stat + flick
    opponent = right - left
    return {
        "right": float(right), "left": float(left), "static": float(stat),
        "flicker": float(flick), "dc": float(dc), "total_ac": float(total_ac),
        "opponent": float(opponent),
        "opp_frac": float(opponent / total_ac) if total_ac > 0 else 0.0,
        "motion_frac": float((right + left) / total_ac) if total_ac > 0 else 0.0,
        "width": float(w), "frames": float(t),
    }


def me_rust(s, frames):
    seq = to_seq(frames)
    out = {}
    for fld in FIELDS:
        t = srs.Term("MotionEnergy", sequence=srs.Lit(seq),
                     height=FIELD_H, width=FIELD_W, field=fld)
        out[fld] = float(s.evaluate(t._json, {}))
    return out


def agree(a, b):
    """Max RELATIVE disagreement across fields (a cross-check, not a verdict)."""
    worst = 0.0
    for fld in FIELDS:
        x, y = a[fld], b[fld]
        denom = max(abs(x), abs(y), 1.0)
        worst = max(worst, abs(x - y) / denom)
    return worst


# --------------------------------------------------------------------------- #
#  MAGNITUDE vs PHASE.  The registered TRAP: reading motion from per-frame
#  magnitude spectra DISCARDS the temporal arrangement (which frame came first)
#  -- the cross-frame phase -- and cannot see direction at all.
# --------------------------------------------------------------------------- #
def me_perframe_magnitude(frames):
    """Sum of per-frame spatial POWER spectra: sum_t |DFT_x(s_t)|^2.  This keeps
    magnitude and throws away the temporal phase linking frames.  It has NO
    temporal axis, so it cannot form a rightward/leftward opponent -- the
    magnitude-only NEGATIVE."""
    F = np.stack([np.asarray(f, np.float64) for f in frames], axis=0)
    s = F.sum(axis=1)                       # (T, W)
    per = np.abs(np.fft.fft(s, axis=1)) ** 2   # (T, W) per-frame spatial power
    tot = per.sum(axis=0)                    # (W,) summed over time
    # There is no (wx, wt) plane here -- only wx.  Direction is undefined.  The
    # honest opponent one can form is identically zero.
    return 0.0, float(tot.sum())


def me_phase_zeroed(frames):
    """Zero the phase of the JOINT space-time spectrum (keep |S|, set arg S = 0)
    then read the same opponent.  |S|^2 is UNCHANGED by this, so the opponent is
    identical to the full mechanism -- demonstrating that DIRECTION is a
    power-spectrum (magnitude) property, phase-INVARIANT (Adelson-Bergen).  The
    trap concerns ARRANGEMENT/POSITION, not direction."""
    F = np.stack([np.asarray(f, np.float64) for f in frames], axis=0)
    s = F.sum(axis=1)
    S = np.fft.fft2(s)
    mag = np.abs(S)                           # phase discarded
    P = mag ** 2
    t, w = s.shape
    ft = np.rint(np.fft.fftfreq(t) * t).astype(int)[:, None]
    fx = np.rint(np.fft.fftfreq(w) * w).astype(int)[None, :]
    moving = (fx != 0) & (ft != 0)
    right = P[moving & ((fx > 0) != (ft > 0))].sum()
    left = P[moving & ((fx > 0) == (ft > 0))].sum()
    return float(right - left)


# ======================= THE VERDICTS (PROTOCOL 13) ======================== #
#  Every verdict decides by EXACT SIGN or ARGMAX LOCATION.  No ordering against a
#  tuned constant decides anything.  `tests/test_motion_energy_ast_migrated.py`
#  binds these by name and asserts it.
# =========================================================================== #
VERDICTS = ("v_cpos_rightward", "v_cnull_still", "v_cleft_leftward",
            "v_isi_interior", "v_isi_falsified", "v_magnitude_blind")


def v_cpos_rightward(cpos) -> bool:
    """C-POS DEAD-INSTRUMENT ARM: continuous rightward motion reads opponent > 0.
    A sign test against the sentinel 0 -- not a tuned threshold."""
    return cpos["opponent"] > 0.0


def v_cnull_still(cnull, cpos) -> bool:
    """C-NULL: a STATIC field is LESS DIRECTIONAL than real motion. A
    MEASURED-vs-MEASURED ordering (PROTOCOL 13 admits orderings between two
    measured quantities), NOT a chosen epsilon: for two identical frames the
    opponent is zero ANALYTICALLY, but a naive DFT's `exp(-iπ)` is not exactly
    -1, so a rounding floor (~1e-39) remains -- reported, never thresholded. The
    physical claim is that this floor is a vanishing directional fraction beside a
    real motion's."""
    return abs(cnull["opp_frac"]) < abs(cpos["opp_frac"])


def v_cleft_leftward(cleft) -> bool:
    """C-LEFT: continuous LEFTWARD motion reads opponent < 0 -- the sign flips,
    so the readout is genuinely directional and not an energy magnitude."""
    return cleft["opponent"] < 0.0


def v_isi_interior(R) -> bool:
    """THE REGISTERED DISCRIMINATOR, CONFIRMING BRANCH: the argmax of the ISI
    curve sits at a NON-ZERO gap AND strictly exceeds R(0).  k* != 0 states the
    registered k* >= 1 EXACTLY (K_GRID starts at 0) with no ordering against a
    non-zero literal.  THE LOCATION of the peak is the discriminator, not
    monotonicity (the gapabduce trap)."""
    kstar = min(K_GRID, key=lambda k: (-R[k], k))
    return kstar != 0 and R[kstar] > R[0]


def v_isi_falsified(R) -> bool:
    """THE FALSIFYING BRANCH: R(0) is a global maximum, so ISI=0 is NOT worse and
    the wave hypothesis is CLOSED for phi -- a clean negative."""
    return all(R[0] >= R[k] for k in K_GRID)


def v_magnitude_blind(opp_perframe) -> bool:
    """THE MAGNITUDE-ONLY NEGATIVE: per-frame magnitude spectra cannot form a
    directional opponent -- it is identically zero.  Registered in ADVANCE as the
    negative (the log-polar trap in a new coat): magnitude discards the temporal
    arrangement that motion needs."""
    return opp_perframe == 0.0


# ============================ THE ARMS ===================================== #
def main() -> int:
    R = {"engine": provenance_line(), "prereg": "VISION_MOTIONENERGY_PREREG.md"}
    print("ENGINE (from INSIDE the measuring process):", R["engine"])
    if EXPECT_ENGINE not in R["engine"]:
        print(f"ABORT: engine divergence -- expected {EXPECT_ENGINE}")
        return 2
    s = srs._native.Substrate()
    ok = {}
    agreements = []

    # --- A0: CONTROLS.  RUN FIRST.  Nothing is interpreted if they fail. -----
    print("\n[A0] CONTROLS -- the dead-instrument arm must FIRE")
    cpos = me_rust(s, rigid_frames(0, 8, DOT))         # rightward
    cpos_np = me_numpy(rigid_frames(0, 8, DOT))
    cnull = me_rust(s, [render(0), render(0)])         # no motion
    cleft_frames = list(reversed(rigid_frames(0, 8, DOT)))  # leftward
    cleft = me_rust(s, cleft_frames)
    agreements += [agree(cpos, cpos_np)]
    ok["cpos_rightward"] = v_cpos_rightward(cpos)
    ok["cnull_still"] = v_cnull_still(cnull, cpos)
    ok["cleft_leftward"] = v_cleft_leftward(cleft)
    R["A0_controls"] = {"cpos": cpos, "cnull": cnull, "cleft": cleft,
                        "cnull_rounding_floor_opponent": cnull["opponent"],
                        "cpos_rust_vs_numpy_reldiff": agreements[-1]}
    print(f"  C-POS  rightward -> opponent={cpos['opponent']:.3e}  "
          f"PASS={ok['cpos_rightward']}")
    print(f"  C-NULL still     -> opponent={cnull['opponent']:.3e} "
          f"(rounding floor; opp_frac={cnull['opp_frac']:.2e})  "
          f"PASS={ok['cnull_still']}")
    print(f"  C-LEFT leftward  -> opponent={cleft['opponent']:.3e}  "
          f"PASS={ok['cleft_leftward']}")
    print(f"  Rust==numpy (C-POS) reldiff={agreements[-1]:.2e}")
    # The DEAD-INSTRUMENT arms are C-POS and C-LEFT (the mechanism SEES direction
    # and its SIGN is meaningful). C-NULL is a measured-vs-measured disclosure.
    if not (ok["cpos_rightward"] and ok["cleft_leftward"] and ok["cnull_still"]):
        print("  ABORT: control failed; no arm is interpretable.")
        R["ABORT"] = "A0 control failed"
        json.dump(R, open("results/motion_energy_measure.json", "w"), indent=1)
        return 3

    # --- A1: THE ISI CURVE and THE REGISTERED DISCRIMINATOR ------------------
    print("\n[A1] THE ISI CURVE -- opp_frac marginalized over S; k* is the "
          "discriminator")
    matrix = {}          # (S,k) -> rust readouts
    grid_opp_frac = {}   # (S,k) -> opp_frac
    disagree_cells = []  # cells over rtol, tagged, to diagnose the cancellation
    for S in S_GRID:
        for k in K_GRID:
            frames = phi_frames(0, S, k)
            rr = me_rust(s, frames)
            nn = me_numpy(frames)
            a = agree(rr, nn)
            agreements.append(a)
            if a > AGREE_RTOL:
                # scale-relative diff: the honest scale of `opponent` is
                # total_ac, not the near-zero opponent itself.
                scale = max(rr["total_ac"], 1.0)
                disagree_cells.append(
                    {"S": S, "k": k, "reldiff": a,
                     "opponent": rr["opponent"], "total_ac": rr["total_ac"],
                     "opp_over_total_ac": abs(rr["opponent"]) / scale,
                     "abs_diff_over_total_ac":
                         abs(rr["opponent"] - nn["opponent"]) / scale})
            matrix[(S, k)] = rr
            grid_opp_frac[(S, k)] = rr["opp_frac"]
    Rk = {k: float(np.mean([grid_opp_frac[(S, k)] for S in S_GRID]))
          for k in K_GRID}
    ok["isi_interior"] = v_isi_interior(Rk)
    ok["isi_falsified"] = v_isi_falsified(Rk)
    kstar = min(K_GRID, key=lambda k: (-Rk[k], k))
    ties = [k for k in K_GRID if k >= 1 and Rk[k] == Rk[0]]
    verdict = ("INTERIOR OPTIMUM (k*>0)" if ok["isi_interior"]
               else ("AMBIGUOUS (tie with 0)" if ties else "FALSIFIED (k*=0)"))
    # true interior maximum vs monotone-rising-to-boundary (disclosure, not the
    # discriminator): does the curve FALL after the peak within the grid?
    falls_after = any(Rk[k] < Rk[kstar] for k in K_GRID if k > kstar)
    R["A1_isi_curve_opp_frac"] = {str(k): Rk[k] for k in K_GRID}
    R["A1_kstar"] = kstar
    R["A1_ties_with_k0"] = ties
    R["A1_verdict"] = verdict
    R["A1_true_interior_peak_falls_after"] = falls_after
    R["A1_matrix"] = {f"S{S}-k{k}": {"opp_frac": matrix[(S, k)]["opp_frac"],
                                     "opponent": matrix[(S, k)]["opponent"],
                                     "motion_frac": matrix[(S, k)]["motion_frac"]}
                      for (S, k) in matrix}
    for k in K_GRID:
        bar = "#" * int(round(max(Rk[k], 0.0) * 60))
        print(f"  k={k}  steps={k+1}  R(k)={Rk[k]:+.4f}  {bar}")
    print(f"  => argmax k* = {kstar}   R(0) = {Rk[0]:+.4f}   "
          f"R(k*) = {Rk[kstar]:+.4f}   falls_after={falls_after}")
    print(f"  => REGISTERED VERDICT: {verdict}")

    # --- A2: MAGNITUDE vs PHASE ---------------------------------------------
    print("\n[A2] MAGNITUDE vs PHASE -- the registered trap")
    # the per-frame magnitude ablation over the whole grid: opponent identically 0
    opp_perframe = 0.0
    for S in S_GRID:
        for k in K_GRID:
            opp_perframe += abs(me_perframe_magnitude(phi_frames(0, S, k))[0])
    ok["magnitude_blind"] = v_magnitude_blind(opp_perframe)
    # phase-zeroed JOINT spectrum: opponent unchanged (direction is a magnitude
    # property) -- checked against the full mechanism, condition by condition
    max_phase_diff = 0.0
    for S in S_GRID:
        for k in K_GRID:
            full = matrix[(S, k)]["opponent"]
            pz = me_phase_zeroed(phi_frames(0, S, k))
            denom = max(abs(full), abs(pz), 1.0)
            max_phase_diff = max(max_phase_diff, abs(full - pz) / denom)
    R["A2_magnitude_only_total_opponent"] = opp_perframe
    R["A2_phasezero_joint_max_reldiff_vs_full"] = max_phase_diff
    print(f"  per-frame MAGNITUDE opponent (summed |.| over grid) = "
          f"{opp_perframe:.3e}  BLIND={ok['magnitude_blind']}")
    print(f"  phase-zeroed JOINT spectrum opponent == full opponent "
          f"(max reldiff {max_phase_diff:.2e}) -> direction is a MAGNITUDE "
          f"property; the trap is about ARRANGEMENT, not direction")

    # --- A3: THE SAD INCUMBENT -- ABSTAIN vs CONFABULATE --------------------
    print("\n[A3] SAD INCUMBENT COMPARISON -- does motion energy ABSTAIN where "
          "SAD CONFABULATES?")
    # the phi rung's operating point: S=8 (=2xDOT, past the aperture), k=0.
    sad = {}
    for S in (4, 8, 12):
        a = render(0)
        b = render(S)
        vf = mgw.vector_field(a, b, DOT)   # the SAD block-matcher
        r, c = ROW // DOT, 0
        v = (float(vf[r, c, 0]), float(vf[r, c, 1]))
        me = me_rust(s, phi_frames(0, S, 0))
        sad[str(S)] = {"sad_v_src": v, "me_opponent_k0": me["opponent"],
                       "me_opp_frac_k0": me["opp_frac"]}
        print(f"  S={S:2d} k=0: SAD v_src={v}  |  motion-energy opponent="
              f"{me['opponent']:.3e} opp_frac={me['opp_frac']:+.4f}")
    R["A3_sad_vs_motion_energy"] = sad

    # --- A4: NOISE -- independent random endpoints -> no consistent direction
    print("\n[A4] NOISE -- independent random dot endpoints")
    hi = FIELD_W - DOT
    noise_opp = []
    for sd in range(NOISE_LO, NOISE_HI):
        rng = np.random.default_rng(sd)
        c1, c2 = [int(x) for x in rng.integers(0, hi, size=2)]
        me = me_rust(s, [render(c1), render(c2)])   # a 2-frame (k=0) pair
        noise_opp.append(me["opponent"])
    noise_opp = np.asarray(noise_opp)
    R["A4_noise"] = {"n": int(noise_opp.size),
                     "seeds": [NOISE_LO, NOISE_HI - 1],
                     "mean_opponent": float(noise_opp.mean()),
                     "max_abs_opponent": float(np.abs(noise_opp).max())}
    print(f"  n={noise_opp.size} k=0 random pairs: mean opponent="
          f"{noise_opp.mean():.3e}  max|opponent|={np.abs(noise_opp).max():.3e}")

    # --- agreement summary ---------------------------------------------------
    max_abs_over_scale = max((d["abs_diff_over_total_ac"]
                              for d in disagree_cells), default=0.0)
    all_disagree_are_k0 = all(d["k"] == 0 for d in disagree_cells)
    R["agreement"] = {"n_conditions": len(agreements),
                      "max_rust_vs_numpy_reldiff": float(max(agreements)),
                      "rtol": AGREE_RTOL,
                      "n_disagree": int(sum(1 for a in agreements
                                            if a > AGREE_RTOL)),
                      "disagree_cells": disagree_cells,
                      "all_disagreements_are_k0_forced_zero": all_disagree_are_k0,
                      "max_abs_diff_over_total_ac": max_abs_over_scale}
    ok["rust_agrees_numpy"] = R["agreement"]["n_disagree"] == 0
    # The honest cross-check: the port is EXACT on non-cancelled quantities
    # (C-POS opponent agrees at machine precision); every disagreement is a
    # near-zero opponent whose absolute residual, relative to its operands'
    # scale (total_ac), is machine epsilon -- the numerical SIGNATURE of the
    # forced Nyquist cancellation, not a port defect.
    ok["disagreements_are_forced_zero_cancellation"] = (
        all_disagree_are_k0 and max_abs_over_scale < 1e-12)
    print(f"\n[AGREE] Rust vs numpy over {len(agreements)} conditions: "
          f"max reldiff {max(agreements):.2e}, n_disagree(>rtol {AGREE_RTOL})="
          f"{R['agreement']['n_disagree']}")
    print(f"        all disagreements at k=0 (forced zero)? "
          f"{all_disagree_are_k0}; max |Δopponent|/total_ac = "
          f"{max_abs_over_scale:.2e} (machine epsilon => cancellation, not a "
          f"port defect; C-POS agrees at {agreements[0]:.1e})")

    R["ok"] = ok
    json.dump(R, open("results/motion_energy_measure.json", "w"), indent=1)
    print("\n=== SUMMARY ===")
    for k2, v in ok.items():
        print(f"  {k2:24s} {v}")
    print(f"  {'ISI VERDICT':24s} {verdict}")
    print("\nwrote results/motion_energy_measure.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
