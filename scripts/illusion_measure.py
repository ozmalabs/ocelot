#!/usr/bin/env python3
"""THE RENDER MADE PRIMARY — the illusion battery (confirmatory measurement).

Pre-registration: VISION_ILLUSION_PREREG.md (committed BEFORE this run, §3). The
eye as ONE bidirectional predictive loop: the field is rendered TOP-DOWN from the
prior, the residual (input - render) corrects it, and the reconciliation weights
render vs input by input strength. An illusion is where the render WINS (input
weak/absent); a veridical percept is where the input wins (input strong). The
falsifiable signature is that ORDERING.

Two render engines, BOTH reused unchanged (NO new Rust, NO new seed rules):
  * SPATIAL  — seeds/vision_ground.json (grounded-field contour fill).
  * TEMPORAL — the BlinkBridge Term (apply_generator_k from the inferred generator).

Every arm is DETERMINISTIC except two floor controls: the spatial blank floor draws
100 seeds 32000-32099; the temporal false-motion floor draws 400 seeds 32100-32499
(declared in the prereg). Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python scripts/illusion_measure.py

NO Python decides a percept: the spatial percept (gbel) is produced by the
vision_ground RULES, the temporal percept (bridged) by the BlinkBridge Term. This
runner only CONSTRUCTS stimuli and READS percepts back (mechanical I/O, §0), and
COMPUTES metrics OVER the percepts (measurement, not decision).
"""
from __future__ import annotations
import json
import math
import os
import random
import time

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains import ground_world as gw  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

# =========================================================================== #
#  SPATIAL render engine (vision_ground) — the occluder is a no-data hole
# =========================================================================== #
H = W = 16
OCC = (8, 8)     # occluder centre (row, col) — a no-data region (the render fills it)
OR = 2.0         # occluder radius


def sworld(interp=0.0, occ=OCC, orad=OR, ground=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_ground"])
    wd = WaveWorld(s, h=H, w=W, seed=0)
    anat = gw.add_grounded_field(wd, blind_center=occ, blind_radius=orad)
    gw.set_ground_params(wd, ground=ground, interp=interp)
    return wd, anat


def occ_cells(anat, row=None, col=None):
    out = sorted((r, c) for (r, c) in anat["blind"]
                 if (row is None or r == row) and (col is None or c == col))
    return out


# =========================================================================== #
#  TEMPORAL render engine (BlinkBridge)
# =========================================================================== #
DT = ["pred", "coord:r", "coord:c", "val"]
DOT = [["cell", 0, 0, "red"]]


def trans(dv, cs):
    return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]


def moving(dv, n, base=DOT):
    out = [base]; cur = base
    for _ in range(n - 1):
        cur = trans(dv, cur); out.append(cur)
    return out


def norm(frame):
    return sorted(tuple(x) for x in (frame or []))


def tboot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("blink_bridge"), ag)
    s.set_attr(ag, "blink_bridge_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(DOT),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def trun(seq, enabled=True):
    s, ag, native = tboot()
    if not enabled:
        s.set_attr(ag, "blink_bridge_enabled", 0.0)
    o = s.add_node("Observation", {"frames": seq, "dim_types": DT,
                   "status": "blink_seq", "key": ["blink"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    return dict(status=at.get("status"), bridged=at.get("bridged"),
                diverged_at=at.get("diverged_at"), correction=at.get("correction"),
                constrained=at.get("constrained"), confidence=at.get("confidence"))


# =========================================================================== #
#  BATTERY A — SPATIAL: amodal / illusory-contour completion
# =========================================================================== #
def A_amodal():
    """A contour passing behind an occluder is completed as ONE contour; the
    bottom-up baseline (raw_sensor) shows two fragments."""
    frame = np.zeros((H, W)); frame[8, :] = 1.0
    span = occ_cells_row = occ_cells(sworld()[1], row=8)
    wg, ag = sworld(); gw.present(wg, ag, frame)
    gbel = gw.belief_field(wg, ag); raw = gw.raw_sensor(wg, ag)
    err = float(np.mean([abs(gbel[r, c] - 1.0) for (r, c) in span]))
    raw_is_nan = bool(all(np.isnan(raw[r, c]) for (r, c) in span))
    return dict(occluded_span=span,
                belief_completed=[round(float(gbel[r, c]), 3) for (r, c) in span],
                mean_abs_err=err, raw_sensor_all_nan=raw_is_nan,
                PASS=(err <= 0.05 and raw_is_nan))


def A_boundary_liberal():
    """The risked characterisation: a ONE-SIDED inducer (bar left of the occluder
    only, blank right) is STILL completed across the hole — the fill is
    boundary-liberal (confabulate-by-default), NOT alignment-gated. Reported, not
    gated on completion; the falsifiability lives in the veridical / floor arms."""
    f = np.zeros((H, W)); f[8, 0:6] = 1.0   # bar ends at the occluder's left edge
    wg, ag = sworld(); gw.present(wg, ag, f)
    gbel = gw.belief_field(wg, ag)
    span = occ_cells(ag, row=8)
    completed = [round(float(gbel[r, c]), 3) for (r, c) in span]
    all_filled = all(abs(v - 1.0) <= 1e-6 for v in completed)
    return dict(occluded_span=span, belief=completed,
                one_sided_completed=all_filled,
                note="boundary-liberal: any contour touching the hole is continued "
                     "across it (the spatial twin of the blink's fill-by-default)")


def A_veridical_visible_break():
    """A VISIBLE break (a 0-gap in the SENSED region, away from the occluder) is
    NOT completed — the input wins where it is strong and present."""
    f = np.zeros((H, W)); f[8, :] = 1.0; f[8, 2] = 0.0; f[8, 3] = 0.0
    wg, ag = sworld(); gw.present(wg, ag, f)
    gbel = gw.belief_field(wg, ag)
    break_seen = abs(gbel[8, 2]) <= 1e-6 and abs(gbel[8, 3]) <= 1e-6
    # the rest of the bar is still a bar (the break is local)
    bar_ok = abs(gbel[8, 0] - 1.0) <= 1e-6 and abs(gbel[8, 5] - 1.0) <= 1e-6
    return dict(gbel_row8_cols0_5=[round(float(gbel[8, c]), 3) for c in range(6)],
                visible_break_survives=break_seen, bar_elsewhere=bar_ok,
                PASS=(break_seen and bar_ok))


def A_render_is_prediction():
    """Rotate the inducer (H bar -> V bar): the completed contour rotates with it.
    The vertical bar is completed down the occluded COLUMN; the occluded ROW (no
    horizontal inducer) stays 0 — the render tracks the prior, it is a real
    prediction, not a fixed template."""
    f = np.zeros((H, W)); f[:, 8] = 1.0
    wg, ag = sworld(); gw.present(wg, ag, f)
    gbel = gw.belief_field(wg, ag)
    col_span = occ_cells(ag, col=8)
    row_span = occ_cells(ag, row=8)
    vbar = all(abs(gbel[r, c] - 1.0) <= 1e-6 for (r, c) in col_span)
    # occluded row cells that are NOT the vertical bar must be 0 (no H inducer)
    row_off = [(r, c) for (r, c) in row_span if c != 8]
    row_clean = all(abs(gbel[r, c]) <= 1e-6 for (r, c) in row_off)
    return dict(vbar_completed=vbar, occluded_row_off_bar_clean=row_clean,
                col_belief=[round(float(gbel[r, c]), 3) for (r, c) in col_span],
                row_belief=[round(float(gbel[r, c]), 3) for (r, c) in row_span],
                PASS=(vbar and row_clean))


def A_ambiguity_ordering():
    """An AMBIGUOUS crossing is HELD OPEN at the hole centre (not confabulated to a
    single mean), where an interpolation control invents one. The render does not
    over-commit against ambiguous evidence — the 'don't confabulate' side of the
    ordering. (Reuse of the blind-spot H4 mechanism.)"""
    f = np.zeros((H, W)); f[8, :] = 1.0; f[:, 8] = 2.0
    wg, ag = sworld(); gw.present(wg, ag, f)
    gbel = gw.belief_field(wg, ag); amb = gw.ambig(wg, ag)
    span = occ_cells(ag)
    n_ambig = int(sum(amb[r, c] for (r, c) in span))
    center_open = bool(amb[8, 8] > 0.5)
    h_ok = abs(gbel[8, 6] - 1.0) <= 1e-6 and abs(gbel[8, 10] - 1.0) <= 1e-6
    v_ok = abs(gbel[6, 8] - 2.0) <= 1e-6 and abs(gbel[10, 8] - 2.0) <= 1e-6
    wi, ai = sworld(interp=1.0); gw.present(wi, ai, f)
    interp_open = bool(gw.ambig(wi, ai)[8, 8] > 0.5)
    return dict(n_ambig_cells=n_ambig, center_held_open=center_open,
                H_continues=h_ok, V_continues=v_ok, interp_holds_open=interp_open,
                PASS=(center_open and n_ambig == 1 and h_ok and v_ok and not interp_open))


def A_floor_spatial():
    """H_floor_spatial: 100 random uniform surrounds with NO contour (seeds
    32000-32099) invent ZERO illusory contours and ZERO ambiguity in the hole."""
    minted = 0
    for sd in range(32000, 32100):
        rng = np.random.default_rng(sd)
        v = float(rng.uniform(0.1, 0.9))
        wb, ab = sworld(); gw.present(wb, ab, np.full((H, W), v))
        span = occ_cells(ab)
        if (sum(gw.contour(wb, ab)[r, c] for (r, c) in span) > 0
                or sum(gw.ambig(wb, ab)[r, c] for (r, c) in span) > 0):
            minted += 1
    return dict(n=100, seeds="32000-32099", minted=minted, PASS=(minted == 0))


# =========================================================================== #
#  BATTERY B — TEMPORAL: apparent motion
# =========================================================================== #
def B_apparent_motion():
    """A prefix of flashes establishing motion, then a temporal GAP: the render
    fills the object at the unshown intermediate positions (== the true motion);
    the bottom-up baseline (raw gap frames) is EMPTY (the object vanished)."""
    truth = moving((0, 1), 6)                        # dot moving right, cols 0..5
    seq = [truth[0], truth[1], [], [], [], truth[5]]  # gap at t2,t3,t4
    r = trun(seq)
    bridged = r["bridged"] or []
    fills_true = (len(bridged) == 3 and r["constrained"] == 1.0
                  and all(norm(bf) == norm(truth[2 + j]) for j, bf in enumerate(bridged)))
    baseline_empty = (seq[2] == [] and seq[3] == [] and seq[4] == [])
    # render disabled -> no bridge (bottom-up)
    off = trun(seq, enabled=False)
    return dict(bridged=bridged, fills_true_motion=fills_true,
                constrained=r["constrained"], correction=r["correction"],
                bottom_up_gap_empty=baseline_empty, render_off_bridged=off["bridged"],
                PASS=(fills_true and baseline_empty and off["bridged"] is None))


def B_veridical_temporal():
    """Input wins where it diverges strongly: a CONTRADICTING resume (object stops
    during the gap) produces a LARGE, GROWING correction (the surprise is NOT
    explained away); a fully-VISIBLE motion (gap=0) adds NO confabulated frames."""
    # contradiction: move for 4-frame prefix, STOP at blink onset, resume stopped
    def probe(gap):
        pre = moving((1, 0), 4)
        stopped = pre[3]
        return trun(pre + [[]] * gap + [stopped])
    rows = []
    for gap in (1, 2, 3, 5):
        rr = probe(gap)
        rows.append(dict(gap=gap, correction=rr["correction"],
                         diverged_at=rr["diverged_at"], confidence=rr["confidence"]))
    corr_grows = (all(a["correction"] <= b["correction"] for a, b in zip(rows, rows[1:]))
                  and rows[-1]["correction"] > rows[0]["correction"])
    all_diverge = all(d["diverged_at"] is not None and d["diverged_at"] >= 0 for d in rows)
    # fully-visible motion, no gap -> no confabulated frames
    vis = trun(moving((1, 0), 6))
    no_confab_when_visible = (vis["bridged"] is None or len(vis["bridged"]) == 0)
    return dict(contradiction_rows=rows, correction_grows=corr_grows,
                all_diverge=all_diverge, no_confab_when_fully_visible=no_confab_when_visible,
                PASS=(corr_grows and all_diverge and no_confab_when_visible))


def B_render_is_prediction():
    """Changing the velocity changes the predicted intermediate positions."""
    def bridged_for(dv):
        truth = moving(dv, 6)
        seq = [truth[0], truth[1], [], [], [], truth[5]]
        return trun(seq)["bridged"]
    b1 = bridged_for((0, 1))     # velocity (0,1)
    b2 = bridged_for((0, 2))     # velocity (0,2)
    differ = (b1 is not None and b2 is not None and norm(b1[0]) != norm(b2[0]))
    tracks = (b2 is not None and norm(b2[0]) == norm(moving((0, 2), 6)[2]))
    return dict(bridged_v01_t2=b1[0] if b1 else None,
                bridged_v02_t2=b2[0] if b2 else None,
                changes_with_velocity=differ, tracks_true_velocity=tracks,
                PASS=(differ and tracks))


def B_floor_temporal():
    """H_floor_temporal: 400 shuffled prefixes (seeds 32100-32499) each still
    confabulate a guess but 0 non-orbit shuffles are falsely marked constrained.
    A shuffle that lands MONOTONIC is a genuine orbit under G/G^-1 (may be honestly
    constrained); every other shuffle must read constrained=0."""
    def min_col(frame):
        return min(c[2] for c in frame)
    def is_monotonic(pref):
        cols = [min_col(f) for f in pref]
        return cols == sorted(cols) or cols == sorted(cols, reverse=True)
    base_orbit = moving((0, 1), 6)                   # 6 distinct frames
    false_constrained = 0; legit = 0; all_fill = True; examples = []
    for sd in range(32100, 32500):
        random.seed(sd)
        pref = base_orbit[:]; random.shuffle(pref)
        rr = trun(pref + [[], []])
        if rr["bridged"] is None:
            all_fill = False
        if rr["constrained"] == 1.0:
            if is_monotonic(pref):
                legit += 1
            else:
                false_constrained += 1
                if len(examples) < 3:
                    examples.append(sd)
    return dict(n=400, seeds="32100-32499", always_fills=all_fill,
                false_constrained=false_constrained, legitimate_orbits=legit,
                examples=examples, PASS=(false_constrained == 0 and all_fill))


# =========================================================================== #
#  CROSS-CUTTING
# =========================================================================== #
def X_reconciliation_uses_both(A_am, A_vb, B_am, B_vt):
    """The percept is NEITHER raw input NOR pure render:
      - != raw input: the render ADDS the completed contour (A_amodal, raw NaN) and
        the moving object (B_apparent_motion, raw gap empty).
      - != pure render: the veridical arms follow the INPUT (A visible break seen;
        B contradiction corrected)."""
    ne_raw = A_am["raw_sensor_all_nan"] and A_am["PASS"] and B_am["bottom_up_gap_empty"] and B_am["fills_true_motion"]
    ne_render = A_vb["visible_break_survives"] and B_vt["all_diverge"]
    return dict(percept_ne_raw_input=bool(ne_raw), percept_ne_pure_render=bool(ne_render),
                PASS=bool(ne_raw and ne_render))


def X_compute_spatial():
    """Spatial fill cost vs field size — LOCAL / O(N), not the O(N^2) drive."""
    sizes = [16, 24, 32, 48, 64]; Ns = []; Ts = []
    for S in sizes:
        s, ag = boot_core(); load_seeds_into(s, ag, ["vision_waves", "vision_ground"])
        wd = WaveWorld(s, h=S, w=S, seed=0)
        anat = gw.add_grounded_field(wd, blind_center=(S // 2, S // 2), blind_radius=OR)
        gw.set_ground_params(wd, ground=1.0, interp=0.0)
        f = np.zeros((S, S)); f[S // 2, :] = 1.0
        gw.present(wd, anat, f)                       # warm
        reps = 5; t0 = time.perf_counter()
        for _ in range(reps):
            gw.present(wd, anat, f)
        Ts.append((time.perf_counter() - t0) / reps); Ns.append(S * S)
    p = float(np.polyfit(np.log(Ns), np.log(Ts), 1)[0])
    return dict(N=Ns, ms=[round(t * 1000, 3) for t in Ts], exponent=round(p, 3),
                PASS=(p <= 1.3))


def X_compute_temporal():
    """Temporal bridge cost vs footprint cell count — LOCAL / <= linear."""
    sizes = []; times = []
    for scale in (1, 2, 4, 8, 16, 32):
        big = [["cell", r, 0, "red"] for r in range(4 * scale)]
        tr = moving((1, 0), 7, base=big)
        sq = [tr[0], tr[1], [], [], tr[4], tr[5], tr[6]]
        s, ag, native = tboot()
        reps = 30; t0 = time.perf_counter()
        for _ in range(reps):
            o = s.add_node("Observation", {"frames": sq, "dim_types": DT,
                           "status": "blink_seq", "key": ["blink"]})
            s.add_edge(ag, "observed", o)
            native.run_rules()
        dt = (time.perf_counter() - t0) / reps * 1000
        sizes.append(4 * scale); times.append(dt)
    lx = [math.log(n) for n in sizes]; ly = [math.log(t) for t in times]
    mx = sum(lx) / len(lx); my = sum(ly) / len(ly)
    p = sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx)
    return dict(cells=sizes, ms=[round(t, 4) for t in times], exponent=round(p, 3),
                PASS=(p <= 1.3))


def X_offday():
    """§9 — both seeds OFF by default are inert."""
    # spatial: ground=0 => hole never filled
    wd, anat = sworld(ground=0.0)
    f = np.zeros((H, W)); f[8, :] = 1.0; gw.present(wd, anat, f)
    span = occ_cells(anat)
    spatial_inert = float(sum(gw.filled(wd, anat)[r, c] for (r, c) in span)) == 0.0
    # temporal: blink_bridge_enabled=0 => no bridge
    truth = moving((0, 1), 6)
    off = trun([truth[0], truth[1], [], [], [], truth[5]], enabled=False)
    temporal_inert = off["bridged"] is None
    return dict(spatial_hole_filled_when_off=spatial_inert,
                temporal_bridged_when_off=off["bridged"],
                PASS=(spatial_inert and temporal_inert))


def main():
    prov = provenance_line()
    print(prov)
    R = {"provenance": prov}

    print("\n== BATTERY A — SPATIAL (amodal / illusory-contour, vision_ground) ==")
    R["A_amodal"] = A_amodal()
    R["A_boundary_liberal"] = A_boundary_liberal()
    R["A_veridical_visible_break"] = A_veridical_visible_break()
    R["A_render_is_prediction"] = A_render_is_prediction()
    R["A_ambiguity_ordering"] = A_ambiguity_ordering()
    R["A_floor_spatial"] = A_floor_spatial()

    print("== BATTERY B — TEMPORAL (apparent motion, BlinkBridge) ==")
    R["B_apparent_motion"] = B_apparent_motion()
    R["B_veridical_temporal"] = B_veridical_temporal()
    R["B_render_is_prediction"] = B_render_is_prediction()
    R["B_floor_temporal"] = B_floor_temporal()

    print("== CROSS-CUTTING ==")
    R["X_reconciliation_uses_both"] = X_reconciliation_uses_both(
        R["A_amodal"], R["A_veridical_visible_break"],
        R["B_apparent_motion"], R["B_veridical_temporal"])
    R["X_compute_spatial"] = X_compute_spatial()
    R["X_compute_temporal"] = X_compute_temporal()
    R["X_offday"] = X_offday()

    gated = {k: v for k, v in R.items() if isinstance(v, dict) and "PASS" in v}
    for k, v in gated.items():
        print(f"  {'PASS' if v['PASS'] else 'FAIL':4}  {k}")
    print(f"\n  A_amodal err={R['A_amodal']['mean_abs_err']:.4f} raw_all_nan={R['A_amodal']['raw_sensor_all_nan']}")
    print(f"  A_boundary_liberal one_sided_completed={R['A_boundary_liberal']['one_sided_completed']} (characterisation)")
    print(f"  A_veridical visible_break_survives={R['A_veridical_visible_break']['visible_break_survives']}")
    print(f"  A_floor minted={R['A_floor_spatial']['minted']}/100  B_floor false_constrained={R['B_floor_temporal']['false_constrained']}/400")
    print(f"  compute exponents: spatial={R['X_compute_spatial']['exponent']} temporal={R['X_compute_temporal']['exponent']}")

    all_pass = all(v["PASS"] for v in gated.values())
    R["render_is_primary_bidirectional_loop"] = all_pass
    print("\n" + "=" * 70)
    print(f"  THE RENDER IS PRIMARY — the eye is a bidirectional predictive loop "
          f"(bounded): {all_pass}")
    print("=" * 70)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _coerce(o):
        if isinstance(o, np.bool_):
            return bool(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        raise TypeError(repr(o))
    with open(os.path.join(root, "results", "illusion_measure.json"), "w") as fh:
        json.dump(R, fh, indent=1, default=_coerce)
    print("wrote results/illusion_measure.json")
    return 0 if all_pass else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
