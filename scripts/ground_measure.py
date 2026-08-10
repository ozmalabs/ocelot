#!/usr/bin/env python3
"""THE BLIND SPOT — grounded field vs sample array: the confirmatory measurement.

Pre-registration: VISION_GROUND_PREREG.md (committed BEFORE this run). Every arm
is DETERMINISTIC except the BLANK floor control, whose random surround values are
drawn from declared seeds 30000-30099. Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/ground_measure.py

Reports the four discrimination claims (grounding vs an interpolation control),
the instrument positive-controls, the scaling exponent, and §9 inertness. Either
answer is a result (PROTOCOL §7).
"""
from __future__ import annotations
import json
import math
import os
import time

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains import ground_world as gw  # noqa: E402

H = W = 16
BC = (8, 8)      # blind-spot centre (row, col) — a STRUCTURAL construction param
BR = 2.0         # blind-spot radius — the optic disc's size, a named knob (§13)


def world(interp=0.0, h=H, w=W, bc=BC, br=BR, ground=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_ground"])
    wd = WaveWorld(s, h=h, w=w, seed=0)
    anat = gw.add_grounded_field(wd, blind_center=bc, blind_radius=br)
    gw.set_ground_params(wd, ground=ground, interp=interp)
    return wd, anat


def blind_idx(anat):
    rs, cs = zip(*sorted(anat["blind"]))
    return np.array(rs), np.array(cs)


# --------------------------------------------------------------------------- #
#  H1 — STRUCTURE SURVIVES (grounding) vs BLUR (interpolation)
# --------------------------------------------------------------------------- #
def h1_structure():
    frame = np.zeros((H, W)); frame[8, :] = 1.0
    on_bar = sorted((r, c) for (r, c) in world()[1]["blind"] if r == 8)

    wg, ag = world(interp=0.0); gw.present(wg, ag, frame)
    fg = gw.belief_field(wg, ag)
    wi, ai = world(interp=1.0); gw.present(wi, ai, frame)
    fi = gw.belief_field(wi, ai)

    err_g = float(np.mean([abs(fg[r, c] - 1.0) for (r, c) in on_bar]))
    err_i = float(np.mean([abs(fi[r, c] - 1.0) for (r, c) in on_bar]))
    # step vs ramp: the max jump between adjacent on-bar cells (a step keeps the
    # bar value flat = small max-gradient along the bar; a ramp is monotone)
    prof_g = [float(fg[r, c]) for (r, c) in on_bar]
    prof_i = [float(fi[r, c]) for (r, c) in on_bar]
    # cross-bar sharpness at the hole centre: |bar - just-off-bar|
    sharp_g = float(fg[8, 8] - fg[7, 8]); sharp_i = float(fi[8, 8] - fi[7, 8])
    return dict(err_grounding=err_g, err_interp=err_i, profile_grounding=prof_g,
                profile_interp=prof_i, cross_sharpness_grounding=sharp_g,
                cross_sharpness_interp=sharp_i,
                PASS=(err_g <= 0.05 and err_i > 0.2))


# --------------------------------------------------------------------------- #
#  H2 — HOLE INVISIBLE under a consistent fill
# --------------------------------------------------------------------------- #
def h2_invisible():
    v = 0.7
    wg, ag = world(); gw.present(wg, ag, np.full((H, W), v))
    f = gw.belief_field(wg, ag); ri, ci = blind_idx(ag)
    seam = float(np.max(np.abs(f[ri, ci] - v)))
    nan = bool(np.any(np.isnan(f)))
    return dict(max_seam=seam, any_nan=nan, PASS=(seam <= 1e-6 and not nan))


# --------------------------------------------------------------------------- #
#  H3 — HIDDEN when covered, REVEALED + REVISED when the eye moves
# --------------------------------------------------------------------------- #
def h3_hidden_revealed():
    scene = np.zeros((H, W)); scene[8, 8] = 3.0      # marker entirely in the hole
    wg, ag = world()
    gw.present(wg, ag, scene)                         # covered fixation
    raw = gw.raw_sensor(wg, ag)
    fld = gw.belief_field(wg, ag)
    covered_gbel = float(fld[8, 8])
    marker_sensed_covered = not bool(np.isnan(raw[8, 8]))  # must be False (no data)
    # eye moves: shift the world so world(8,8) is seen by a SENSED retinal cell.
    gw.present(wg, ag, scene, eye_offset=(0, -4))     # retinal (8,12) now sees world(8,8)
    fld2 = gw.belief_field(wg, ag)
    revealed_gbel = float(fld2[8, 12])
    return dict(covered_marker_gbel=covered_gbel,
                marker_directly_sensed_when_covered=marker_sensed_covered,
                revealed_marker_gbel=revealed_gbel,
                PASS=(abs(covered_gbel) <= 1e-6 and not marker_sensed_covered
                      and abs(revealed_gbel - 3.0) <= 1e-6))


# --------------------------------------------------------------------------- #
#  H4 — AMBIGUOUS surround HELD OPEN, not confabulated
# --------------------------------------------------------------------------- #
def h4_ambiguity():
    f = np.zeros((H, W)); f[8, :] = 1.0; f[:, 8] = 2.0   # H bar (1) x V bar (2)
    wg, ag = world(); gw.present(wg, ag, f)
    fld = gw.belief_field(wg, ag); amb = gw.ambig(wg, ag); fil = gw.filled(wg, ag)
    ri, ci = blind_idx(ag)
    n_ambig = int(amb[ri, ci].sum())
    center_open = bool(amb[8, 8] > 0.5 and fil[8, 8] < 0.5)
    # the two contours still continue correctly away from the crossing
    h_ok = abs(fld[8, 6] - 1.0) <= 1e-6 and abs(fld[8, 10] - 1.0) <= 1e-6
    v_ok = abs(fld[6, 8] - 2.0) <= 1e-6 and abs(fld[10, 8] - 2.0) <= 1e-6

    # interpolation confabulates a single mean at the crossing
    wi, ai = world(interp=1.0); gw.present(wi, ai, f)
    interp_center = float(gw.belief_field(wi, ai)[8, 8])
    interp_open = bool(gw.ambig(wi, ai)[8, 8] > 0.5)

    # unambiguous control (H only) -> confident single value
    wc, ac = world(); fc = np.zeros((H, W)); fc[8, :] = 1.0; gw.present(wc, ac, fc)
    ctrl_center = float(gw.belief_field(wc, ac)[8, 8])
    ctrl_open = bool(gw.ambig(wc, ac)[8, 8] > 0.5)
    return dict(n_ambig_cells=n_ambig, center_held_open=center_open,
                H_continues=h_ok, V_continues=v_ok,
                interp_center=interp_center, interp_holds_open=interp_open,
                control_center=ctrl_center, control_holds_open=ctrl_open,
                PASS=(center_open and n_ambig == 1 and h_ok and v_ok
                      and not interp_open and abs(ctrl_center - 1.0) <= 1e-6
                      and not ctrl_open))


# --------------------------------------------------------------------------- #
#  POSITIVE CONTROLS (the instrument)
# --------------------------------------------------------------------------- #
def pos_controls():
    # (a) blind spot REAL: a marker inside is NOT directly sensed.
    scene = np.zeros((H, W)); scene[8, 8] = 5.0
    wg, ag = world(); gw.present(wg, ag, scene)
    blind_real = bool(np.isnan(gw.raw_sensor(wg, ag)[8, 8]))

    # (b) fill TRACKS the surround: move the bar (rows that CROSS the hole, which
    # spans rows 6-10 here); the bridge moves with it, the rest of the hole clean.
    tracks = []
    for row in (7, 8, 9):
        wr, ar = world(); fr = np.zeros((H, W)); fr[row, :] = 1.0
        gw.present(wr, ar, fr)
        fld = gw.belief_field(wr, ar)
        on = [(r, c) for (r, c) in ar["blind"] if r == row]
        off = [(r, c) for (r, c) in ar["blind"] if r != row]
        bridged = all(abs(fld[r, c] - 1.0) <= 1e-6 for (r, c) in on) if on else False
        clean = all(abs(fld[r, c]) <= 1e-6 for (r, c) in off) if off else True
        tracks.append(dict(row=row, bridged=bridged, surround_clean=clean))

    # (c) instrument alive: full coverage of the hole + surround-tracking witness.
    wg2, ag2 = world(); ff = np.zeros((H, W)); ff[8, :] = 1.0; gw.present(wg2, ag2, ff)
    ri, ci = blind_idx(ag2)
    coverage = float(gw.filled(wg2, ag2)[ri, ci].mean())

    # (d) BLANK floor: a surround with NO structure (a uniform random value) must
    # invent NO contour and NO ambiguity, on 100 declared seeds 30000-30099.
    minted = 0
    for sd in range(30000, 30100):
        rng = np.random.default_rng(sd)
        v = float(rng.uniform(0.1, 0.9))
        wb, ab = world(); gw.present(wb, ab, np.full((H, W), v))
        rb, cb = blind_idx(ab)
        if int(gw.contour(wb, ab)[rb, cb].sum()) > 0 or int(gw.ambig(wb, ab)[rb, cb].sum()) > 0:
            minted += 1
    return dict(blind_spot_is_real=blind_real, fill_tracks_surround=tracks,
                hole_coverage=coverage, blank_floor_minted=minted,
                PASS=(blind_real and all(t["bridged"] and t["surround_clean"] for t in tracks)
                      and coverage >= 0.999 and minted == 0))


# --------------------------------------------------------------------------- #
#  SCALING — LOCAL / O(N), not the O(N^2) drive
# --------------------------------------------------------------------------- #
def scaling():
    sizes = [16, 24, 32, 48, 64]; Ns = []; Ts = []
    for S in sizes:
        wd, anat = world(h=S, w=S, bc=(S // 2, S // 2))
        f = np.zeros((S, S)); f[S // 2, :] = 1.0
        gw.present(wd, anat, f)                       # warm
        reps = 5; t0 = time.perf_counter()
        for _ in range(reps):
            gw.present(wd, anat, f)
        Ts.append((time.perf_counter() - t0) / reps); Ns.append(S * S)
    p = float(np.polyfit(np.log(Ns), np.log(Ts), 1)[0])
    return dict(N=Ns, ms=[round(t * 1000, 3) for t in Ts], exponent=round(p, 3),
                PASS=(p <= 1.1))


# --------------------------------------------------------------------------- #
#  §9 — the seed ships INERT (ground=0 => no rule fires)
# --------------------------------------------------------------------------- #
def s9_inert():
    wd, anat = world(ground=0.0)      # default
    f = np.zeros((H, W)); f[8, :] = 1.0; gw.present(wd, anat, f)
    ri, ci = blind_idx(anat)
    filled_any = float(gw.filled(wd, anat)[ri, ci].sum())
    # ground=0 => the blind hole is never filled (stays 0) — inert.
    return dict(hole_filled_when_off=filled_any, PASS=(filled_any == 0.0))


def main():
    prov = provenance_line()
    print(prov)
    out = {"provenance": prov, "H1_structure": h1_structure(),
           "H2_invisible": h2_invisible(), "H3_hidden_revealed": h3_hidden_revealed(),
           "H4_ambiguity": h4_ambiguity(), "positive_controls": pos_controls(),
           "scaling": scaling(), "s9_inert": s9_inert()}
    for k, v in out.items():
        if isinstance(v, dict) and "PASS" in v:
            print(f"{'PASS' if v['PASS'] else 'FAIL':4}  {k}")
    print("\nH1 err grounding=%.4f interp=%.4f | cross-sharpness g=%.3f i=%.3f"
          % (out["H1_structure"]["err_grounding"], out["H1_structure"]["err_interp"],
             out["H1_structure"]["cross_sharpness_grounding"],
             out["H1_structure"]["cross_sharpness_interp"]))
    print("H2 seam=%.2e  H4 n_ambig=%d center_open=%s interp_center=%.2f"
          % (out["H2_invisible"]["max_seam"], out["H4_ambiguity"]["n_ambig_cells"],
             out["H4_ambiguity"]["center_held_open"], out["H4_ambiguity"]["interp_center"]))
    print("H3 covered=%.3f revealed=%.3f  scaling exp=%.3f  blank floor minted=%d/100"
          % (out["H3_hidden_revealed"]["covered_marker_gbel"],
             out["H3_hidden_revealed"]["revealed_marker_gbel"],
             out["scaling"]["exponent"], out["positive_controls"]["blank_floor_minted"]))
    allpass = all(v["PASS"] for v in out.values() if isinstance(v, dict) and "PASS" in v)
    print("\nALL PASS:", allpass)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    def _coerce(o):
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        raise TypeError(repr(o))
    with open(os.path.join(root, "results", "ground_measure.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=_coerce)
    return out


if __name__ == "__main__":
    main()
