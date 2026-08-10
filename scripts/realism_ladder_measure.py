#!/usr/bin/env python3
"""THE REALISM-DEGRADATION LADDER — is real-video free-fall physics blocked by
the CLIP or the METHOD? (block 150000-150999).

The chain 145000-149000 proved every MECHANISM synthetically (order-N, the robust
witness, aperture decoupling, sub-cell cross-frame registration) but the real
free-fall clip never recovered a physical acceleration. 149000's killer
diagnostic: two OVERLAPPING windows of the same real fall recovered
OPPOSITE-SIGN acceleration (+1 vs -2) — the recovered coefficient was
REGISTRATION NOISE, not physical g. Named suspects for the real clip: motion
blur, ruler occlusion, short trajectory (7 frames), noisy carve anchor.

This rung ISOLATES which one. It reuses the IDEAL SUB-CELL ORACLE from 149000
(`render_subcell_fall` + `subcell_position_stream` + `graph_mint`, all imported
UNCHANGED — the coarse/physics path is byte-identical by construction: this is a
NEW file that only READS those functions) and DEGRADES it toward the real clip
ALONG ONE AXIS AT A TIME, sweeping each level (a DECLARED §13 residual, never
tuned) to find the BREAKING POINT.

THE SUCCESS CRITERION IS PHYSICS, NOT A THRESHOLD (§13-clean) — it is 149000's
replication test. A genuine free fall has ONE constant acceleration of ONE SIGN.
So the method "recovers physical acceleration" on a degraded oracle IFF:
  P1 (order+sign): the full run mints order-2 with nonzero coeff of the CORRECT
     sign (downward => target_fine > 0).
  P2 (replication): TWO overlapping windows of the same fall each mint order-2
     with nonzero coeff, and AGREE IN SIGN (the exact test that killed 149000 —
     tolerance-free).
  P3 (magnitude): |coeff_full - target_fine| within the finer-unit ROUNDING
     ENVELOPE. This tolerance FALLS OUT, it is not tuned: the position stream is
     INTEGER finer units, so each true position is rounded to +/-0.5 finer unit;
     a single second difference d2 = [1,-2,1].p has worst-case rounding error
     0.5 * (|1|+|-2|+|1|) = 2 finer units. TOL_FINE = 2 is that L1 envelope. The
     BINDING criterion for the break point is P1 & P2 (tolerance-free, = 149000);
     P3 is reported as corroboration.

The break point on an axis = the smallest degradation level at which P1 & P2
first fails. We report the full sweep so the transition is visible, then LOCATE
THE REAL CLIP on each axis and name the axis/axes it is PAST the break on.

INVARIANT AUDIT (§ frame/continuum, kept from 149000): sub-cell precision lives
ONLY in the cross-frame integer offset (`register_residual_offset` returns
FINER-UNIT INTEGERS); NO float is ever written into an in-frame coordinate. The
degradation renderers below READ ONLY pixel arrays and emit pixel arrays / integer
anchors — no agent decision, no `if` over graph state; every order-N verdict
stays the seed rule inside `graph_mint`.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

# Reuse the 149000 oracle + pipeline UNCHANGED (importing runs engine_preamble).
from scripts.subcell_crossframe_measure import (        # noqa: E402
    render_subcell_fall, subcell_position_stream, graph_mint, accel_coeff, d2i,
    decode_grey, quantize, carve_track_indexed, longest_run_indexed,
    S, SEARCH_CELLS, CLIP,
)
from domains.engine_provenance import provenance_line, provenance_stamp  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── DECLARED §13 RESIDUALS (swept, never tuned) ──────────────────────────────
A_CELL   = 0.2          # the oracle's known injected accel (cells/frame^2). target_fine = A_CELL*S.
BASE_N   = 8            # base trajectory length for axes B-E (149000's oracle length).
CY0      = 10.0
GH, GW, OBJ = 200, 64, 24
TEXLO    = 64           # texture low (contrast: 64..255 over background 0).
TEXSEED  = 150000       # fixed across levels within an axis: ONLY the degradation varies.
TARGET_FINE = A_CELL * S
# rounding envelope (falls out — see docstring P3); NOT a tuned tolerance.
TOL_FINE = 2

# per-axis stochastic-degradation seeds (declared residuals, like texseed):
SEED_NOISE  = 150100    # axis D additive sensor noise rng
SEED_JITTER = 150200    # axis E carve-anchor jitter rng

# swept levels (declared residuals):
LEVELS_A = [12, 10, 8, 7, 6, 5]           # trajectory length (frames)
LEVELS_B = [0, 1, 2, 3, 4, 6]             # motion-blur extent (cells / rows)
LEVELS_C = [0, 2, 4, 6, 8, 12]            # occluder bar width (rows) across the path
LEVELS_D = [0, 10, 20, 40, 80, 120]       # additive sensor-noise sigma (grey levels)
LEVELS_E = [0, 1, 2, 3]                    # carve-anchor jitter (+/- cells)


# ─────────────────────────── the physics (single-sign) test ──────────────────

def _sign(x):
    if x is None:
        return 0
    return 1 if x > 0 else (-1 if x < 0 else 0)


def physics_test(frames, run):
    """Run the 149000 pipeline on the full run AND on two overlapping windows;
    return the coeffs and the tolerance-free P1&P2 physics verdict + P3 corrob."""
    py_full, _, _ = subcell_position_stream(frames, run)
    c_full = accel_coeff(graph_mint(py_full)[1])
    runA, runB = run[:-1], run[1:]              # overlapping windows, offset by 1 frame
    pyA, _, _ = subcell_position_stream(frames, runA)
    cA = accel_coeff(graph_mint(pyA)[1])
    pyB, _, _ = subcell_position_stream(frames, runB)
    cB = accel_coeff(graph_mint(pyB)[1])
    tsign = _sign(TARGET_FINE)
    p1 = (c_full is not None and c_full != 0 and _sign(c_full) == tsign)
    p2 = (cA is not None and cB is not None and cA != 0 and cB != 0
          and _sign(cA) == tsign and _sign(cB) == tsign)
    p3 = (c_full is not None and abs(c_full - TARGET_FINE) <= TOL_FINE)
    return {
        "coeff_full": c_full, "coeff_winA": cA, "coeff_winB": cB,
        "d2_full": d2i(py_full), "py_full": py_full,
        "P1_order_sign": bool(p1), "P2_replication_sign": bool(p2),
        "P3_magnitude": bool(p3),
        "PASS": bool(p1 and p2),                 # binding = tolerance-free P1&P2
        "PASS_with_magnitude": bool(p1 and p2 and p3),
    }


def given_anchors(true_top, n):
    """GIVEN integer anchors from the rounded true top (isolates method from carve)."""
    return [{"fi": t, "cy": float(round(true_top[t])), "cx": float(GW // 2),
             "count": float(OBJ * OBJ), "id": 1} for t in range(n)]


def clean_frames(n, texseed=TEXSEED):
    return render_subcell_fall(a_cell=A_CELL, n_frames=n, cy0=CY0, gh=GH, gw=GW,
                               obj=OBJ, texseed=texseed, texlo=TEXLO)


# ─────────────────────────── degradation renderers (pixel-only) ──────────────

def blur_vertical(frames, extent_rows):
    """Linear motion blur ALONG THE DIRECTION OF FALL (rows). Box kernel of
    `extent_rows` rows convolved down each column. Pixel read/write only."""
    if extent_rows <= 0:
        return frames
    k = np.ones(extent_rows, dtype=np.float64) / extent_rows
    out = np.empty_like(frames)
    for i in range(frames.shape[0]):
        f = frames[i]
        # convolve each column (axis 0) with the vertical kernel, 'same' length.
        out[i] = np.apply_along_axis(lambda col: np.convolve(col, k, mode="same"), 0, f)
    return out


def occlude_bar(frames, true_top, width_rows):
    """A STATIC bright horizontal bar the falling ball passes BEHIND. Placed so
    the ball crosses it mid-fall (rows near the trajectory centre), drawn ON TOP
    of every frame => where the ball overlaps the bar it is occluded and the
    bright bar (>= texture) enters the count-brightest template. Pixel-only."""
    if width_rows <= 0:
        return frames
    mid = 0.5 * (true_top[0] + true_top[-1]) + OBJ / 2.0
    r0 = int(round(mid - width_rows / 2.0))
    r1 = r0 + width_rows
    cx0 = (GW - OBJ) // 2
    out = frames.copy()
    val = 255.0                                  # bright ruler line, static
    out[:, max(0, r0):min(GH, r1), cx0:cx0 + OBJ] = val
    return out


def add_noise(frames, sigma, seed):
    """Additive Gaussian sensor noise, clipped to [0,255]. Pixel-only."""
    if sigma <= 0:
        return frames
    rng = np.random.default_rng(seed)
    out = frames + rng.normal(0.0, sigma, size=frames.shape)
    return np.clip(out, 0.0, 255.0)


def jitter_anchors(run, amp, seed):
    """Perturb the INTEGER carve anchor (cy) by a random integer in [-amp,+amp]
    per frame — the real carve's centroid jitter. INTEGER in, INTEGER out; no
    float ever enters an in-frame coordinate."""
    if amp <= 0:
        return run
    rng = np.random.default_rng(seed)
    out = []
    for r in run:
        j = int(rng.integers(-amp, amp + 1))
        rr = dict(r)
        rr["cy"] = float(int(round(r["cy"])) + j)   # stays integer
        out.append(rr)
    return out


# ─────────────────────────────── the ladder ──────────────────────────────────

def ladder():
    axes = {}

    # A. TRAJECTORY LENGTH ----------------------------------------------------
    rows = []
    for n in LEVELS_A:
        fr, top = clean_frames(n)
        run = given_anchors(top, n)
        pt = physics_test(fr, run)
        rows.append({"level": n, **pt})
    axes["A_trajectory_length"] = {"unit": "frames", "levels": LEVELS_A, "rows": rows}

    # B. MOTION BLUR ----------------------------------------------------------
    rows = []
    fr0, top0 = clean_frames(BASE_N)
    run0 = given_anchors(top0, BASE_N)
    for m in LEVELS_B:
        fr = blur_vertical(fr0, m)
        pt = physics_test(fr, run0)
        rows.append({"level": m, **pt})
    axes["B_motion_blur"] = {"unit": "blur_rows", "levels": LEVELS_B, "rows": rows}

    # C. OCCLUSION ------------------------------------------------------------
    rows = []
    for w in LEVELS_C:
        fr = occlude_bar(fr0, top0, w)
        pt = physics_test(fr, run0)
        rows.append({"level": w, **pt})
    axes["C_occlusion"] = {"unit": "bar_rows", "levels": LEVELS_C, "rows": rows}

    # D. CONTRAST / ADDITIVE NOISE -------------------------------------------
    rows = []
    for sg in LEVELS_D:
        fr = add_noise(fr0, sg, SEED_NOISE)
        pt = physics_test(fr, run0)
        rows.append({"level": sg, **pt})
    axes["D_noise"] = {"unit": "sensor_sigma", "levels": LEVELS_D, "rows": rows}

    # E. CARVE-ANCHOR NOISE ---------------------------------------------------
    rows = []
    for j in LEVELS_E:
        run = jitter_anchors(run0, j, SEED_JITTER)
        pt = physics_test(fr0, run)
        rows.append({"level": j, **pt})
    axes["E_anchor_jitter"] = {"unit": "cells_pm", "levels": LEVELS_E, "rows": rows}

    return axes


def break_points(axes):
    """First (smallest-degradation) level where P1&P2 fails, per axis. For axis A
    (length) 'more degraded' means SHORTER, so we walk the declared order (which
    is descending length) and report the first failing level."""
    bp = {}
    for name, ax in axes.items():
        first_fail = None
        for r in ax["rows"]:
            if not r["PASS"]:
                first_fail = r["level"]
                break
        clean_pass = ax["rows"][0]["PASS"]
        bp[name] = {"unit": ax["unit"], "clean_level_passes": clean_pass,
                    "first_fail_level": first_fail}
    return bp


# ─────────────────── locate the REAL clip on each axis ───────────────────────

def real_clip_location():
    """Measure the real 149000 clip's ACTUAL value on each degradation axis, then
    (in the doc) state which axes it is PAST the break point on. Uses the 149000
    primary config. Carve ids are a cross-process HashMap artifact => this block
    is INFORMATIONAL; the ladder headline is the deterministic oracle above."""
    ss, dur, fps, gw, gh, block, label = 55.0, 20.0, 2.0, 128, 640, 6, "real_128x640_b6_2fps"
    grey = decode_grey(ss, dur, fps, gw, gh)
    fq = quantize(grey)
    track = carve_track_indexed(fq, gh, gw, block)
    run = longest_run_indexed(track)
    info = {"label": label, "grid": [gw, gh], "block": block, "fps": fps,
            "n_decoded_frames": int(fq.shape[0]), "run_len": len(run)}
    if len(run) >= 4:
        cyf = [r["cy"] for r in run]
        cxf = [r["cx"] for r in run]
        info["carve_cy_float"] = [round(v, 2) for v in cyf]
        # A. trajectory length
        info["axis_A_trajectory_len_frames"] = len(run)
        # B. per-frame velocity => upper-bound intra-frame smear (cells/frame)
        vy = np.abs(np.diff(np.asarray(cyf)))
        info["axis_B_velocity_cells_per_frame"] = {
            "mean": round(float(vy.mean()), 3), "max": round(float(vy.max()), 3)}
        # D. object-background contrast in the carved region
        counts = [r["count"] for r in run]
        # sample ball mean vs frame background mean around a mid run frame
        midr = run[len(run) // 2]
        fi = midr["fi"]
        cy, cx, cnt = int(round(midr["cy"])), int(round(midr["cx"])), int(midr["count"])
        half = int(np.ceil(np.sqrt(max(cnt, 1)))) + 2
        H, W = grey[fi].shape
        rs = np.clip(np.arange(cy - half, cy + half + 1), 0, H - 1)
        cs = np.clip(np.arange(cx - half, cx + half + 1), 0, W - 1)
        win = grey[fi][np.ix_(rs, cs)].astype(np.float64)
        k = int(min(max(cnt, 1), win.size))
        thr = np.partition(win.ravel(), win.size - k)[win.size - k]
        ball = win[win >= thr]
        bg = grey[fi].astype(np.float64).mean()
        info["axis_D_contrast"] = {
            "ball_mean": round(float(ball.mean()), 1),
            "background_mean": round(float(bg), 1),
            "contrast_frac": round(float(abs(ball.mean() - bg) / 255.0), 3),
            "carve_count_series": [int(c) for c in counts],
            "carve_count_cv": round(float(np.std(counts) / max(np.mean(counts), 1)), 3)}
        # E. carve-anchor jitter: residual of the carve cy from a smooth quadratic fit
        t = np.arange(len(cyf), dtype=np.float64)
        A = np.vstack([t * t, t, np.ones_like(t)]).T
        coef, *_ = np.linalg.lstsq(A, np.asarray(cyf), rcond=None)
        resid = np.asarray(cyf) - A @ coef
        info["axis_E_anchor_jitter"] = {
            "quad_fit_coeffs": [round(float(c), 4) for c in coef],
            "residual_std_cells": round(float(np.std(resid)), 3),
            "residual_max_abs_cells": round(float(np.max(np.abs(resid))), 3),
            "cx_range_cells": round(float(np.max(cxf) - np.min(cxf)), 3)}
        # the physics test on the REAL clip (the 149000 sign-flip, replicated here)
        info["physics_test"] = physics_test(grey, run)
    else:
        info["note"] = "run < 4 — no witness"
    return info


def main():
    load0 = os.getloadavg()
    t0 = time.time()
    axes = ladder()
    bp = break_points(axes)
    result = {
        "block": "150000-150999",
        "engine_provenance": provenance_stamp(),
        "provenance_line": provenance_line(),
        "S": S, "search_cells": SEARCH_CELLS,
        "target_fine": TARGET_FINE, "tol_fine": TOL_FINE, "a_cell": A_CELL,
        "declared_residuals": {
            "base_n": BASE_N, "texseed": TEXSEED, "seed_noise": SEED_NOISE,
            "seed_jitter": SEED_JITTER,
            "levels": {"A": LEVELS_A, "B": LEVELS_B, "C": LEVELS_C,
                       "D": LEVELS_D, "E": LEVELS_E}},
        "ladder": axes,
        "break_points": bp,
        "loadavg_start": list(load0),
    }
    print("=== REALISM-DEGRADATION LADDER (target_fine=%.1f, S=%d, tol_fine=%d) ==="
          % (TARGET_FINE, S, TOL_FINE))
    for name, ax in axes.items():
        print("--- %s (%s) ---" % (name, ax["unit"]))
        for r in ax["rows"]:
            print("  level=%-4s full=%-5s A=%-5s B=%-5s  P1=%d P2=%d P3=%d PASS=%d"
                  % (r["level"], r["coeff_full"], r["coeff_winA"], r["coeff_winB"],
                     r["P1_order_sign"], r["P2_replication_sign"], r["P3_magnitude"], r["PASS"]))
        print("  BREAK: clean_passes=%s first_fail_level=%s"
              % (bp[name]["clean_level_passes"], bp[name]["first_fail_level"]))

    if os.environ.get("LADDER_REAL", "1") == "1":
        result["real_clip"] = real_clip_location()
        rc = result["real_clip"]
        print("=== REAL CLIP LOCATION (%s) ===" % rc["label"])
        print("  run_len:", rc.get("run_len"))
        if "physics_test" in rc:
            print("  A traj len:", rc["axis_A_trajectory_len_frames"])
            print("  B velocity cells/f:", rc["axis_B_velocity_cells_per_frame"])
            print("  D contrast:", rc["axis_D_contrast"]["contrast_frac"],
                  "count_cv:", rc["axis_D_contrast"]["carve_count_cv"])
            print("  E anchor jitter resid_std cells:", rc["axis_E_anchor_jitter"]["residual_std_cells"])
            pt = rc["physics_test"]
            print("  REAL physics_test: full=%s A=%s B=%s PASS=%s"
                  % (pt["coeff_full"], pt["coeff_winA"], pt["coeff_winB"], pt["PASS"]))

    result["loadavg_end"] = list(os.getloadavg())
    result["wall_sec"] = round(time.time() - t0, 1)
    outp = os.path.join(ROOT, "results", "realism_ladder_measure.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", outp, "wall=%.1fs" % result["wall_sec"])


if __name__ == "__main__":
    main()
