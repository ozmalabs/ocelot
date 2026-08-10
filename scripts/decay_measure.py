"""THE EDGE-ANCHORED DECAYING GRADIENT — the confirmatory runner
(VISION_DECAY_PREREG.md).

Runs exactly the pre-registered arms and dumps results/decay_measure.json.
Exactly these. No sweeps, no re-runs (PROTOCOL §3.6).

  ARM V   vacuity        — toggle pdecay 0->1, max|on-off|. Run FIRST (§13.2).
  ARM V2  byte-identity  — with pdecay=0, results/paint_measure.json reproduces.
  G1/ARM1 Cornsweet sign — the single-edge geometry, at the ESCALATED order.
  G1/ARM2 the decline    — |induction| vs the STIMULUS's distance from the cusp.
  ARM 3   the residual   — R1/R2/R3/R4 + F1 (69000-69099) + F2 (69100-69199).
  ARM 3b  R5 cost probe  — a real ramp inside a BOUNDED compartment.
  G2      cumulative     — the Cornsweet sawtooth. MEASURED, NOT GATED, NOT
                           POOLED with G1 (Cavanagh & Anstis 2018).
  ARM B   bounds         — three fixed flat-field widths.
  ARM P   the paint rung's own positives (I1/I2) under decay. Reported.

This file writes NO graph attribute and makes NO decision over graph state; it
lays out stimuli, ticks, and reads back.
"""
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import json  # noqa: E402
import os  # noqa: E402
import random  # noqa: E402
import sys  # noqa: E402

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import paint_world as pw  # noqa: E402
from domains import decay_world as dw  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))
import paint_measure as pm  # noqa: E402


# --------------------------------------------------------------------------- #
#  harness
# --------------------------------------------------------------------------- #
def run_decay(lum, app=None, sensed=None, *, pdecay=1.0, paint=1.0, pquant=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_paint"])
    return s, dw.run(s, lum, app, sensed, paint=paint, pdecay=pdecay, pquant=pquant)


# --------------------------------------------------------------------------- #
#  STIMULI — every one INTEGER valued (in-frame is INTEGER)
# --------------------------------------------------------------------------- #
def stim_cornsweet_w(flat=6, rows=8):
    """The paint rung's Cornsweet, with the flat far-field width as a parameter.
    `flat=6` IS `paint_measure.stim_cornsweet` exactly."""
    prof = ([100.0] * flat + [101.0, 102.0, 103.0, 104.0]
            + [96.0, 97.0, 98.0, 99.0] + [100.0] * flat)
    lum = np.tile(np.array(prof), (rows, 1))
    n = len(prof)
    left_far = [(3, c) for c in range(flat)]           # physically 100, all of them
    right_far = [(3, c) for c in range(n - flat, n)]   # physically 100, all of them
    cusp = flat + 3                                    # last column before the drop
    return lum, left_far, right_far, cusp, n


def stim_bounded_ramp():
    """R5 — a REAL linear ramp inside a BOUNDED compartment. The two steps ARE
    strict-|Δ| maxima, so the ramp region has anchors on BOTH sides. This is the
    case where the hypothesis predicts its own cost."""
    prof = ([20.0] * 4 + [50.0 + 3.0 * i for i in range(8)] + [120.0] * 4)
    return np.tile(np.array(prof), (8, 1))


def stim_cumulative(units=4):
    """G2 — a 1-D Cornsweet SAWTOOTH: one unit tiled, so every plateau is
    physically 100.0 and every cusp has the SAME polarity. NOT Cavanagh &
    Anstis's 2-D diamond stimulus (declared as a bound)."""
    unit = [100.0, 100.0, 100.0, 100.0, 101.0, 102.0, 103.0, 104.0,
            96.0, 97.0, 98.0, 99.0]
    prof = unit * units
    lum = np.tile(np.array(prof), (8, 1))
    # The pre-registered read-off: the physically-100 plateau of each INTERIOR
    # unit, columns 13 / 25 / 37. Unit 0 is skipped because its region is
    # truncated by the field border and is therefore not a translate of the
    # others; pooling it would compare a boundary artifact with an interior one.
    plateaus = [(3, 12 * k + 1) for k in range(1, units)]
    return lum, plateaus


# --------------------------------------------------------------------------- #
#  ARM V — VACUITY (§13.2). Run FIRST.
# --------------------------------------------------------------------------- #
VKEYS = ("ppaint_lum", "presid_lum", "prefuted_cell", "pdist", "panchor",
         "pregion", "korder")


def arm_V():
    lum, _, _, _, _ = stim_cornsweet_w()
    s0, h0 = run_decay(lum, pdecay=0.0)
    s1, h1 = run_decay(lum, pdecay=1.0)
    out = {k: float(np.max(np.abs(dw.field_of(s1, h1, k) - dw.field_of(s0, h0, k))))
           for k in VKEYS}
    out["plam_off"] = dw.hub_for(s0, h0, (3, 0))["plam"]
    out["plam_on"] = dw.hub_for(s1, h1, (3, 0))["plam"]
    out["ALL_ZERO_would_be_decorative"] = bool(
        all(v == 0.0 for k, v in out.items() if k in VKEYS))
    out["PASS"] = bool(out["ppaint_lum"] > 0.0 and out["presid_lum"] > 0.0)
    return out


def _canon(x):
    if isinstance(x, dict):
        return {k: _canon(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_canon(v) for v in x]
    return x


def arm_V2_byte_identity():
    """§9. With pdecay at its shipped default (0.0), EVERY arm of the paint
    rung's committed run must reproduce EXACTLY, key for key. `paint_measure`
    is re-run in-process, unedited, and compared against the pinned JSON."""
    pinned = json.load(open(os.path.join(HERE, "results", "paint_measure.json")))
    fresh = {
        "ARM_K2_vacuity": pm.arm_K2(),
        "baseline_no_spreading_into_sensed_cells":
            pm.baseline_no_spreading_into_sensed_cells(),
        "ARM_I1_neon": pm.arm_I1(),
        "ARM_I2_watercolour": pm.arm_I2(),
        "ARM_I3_cornsweet": pm.arm_I3(),
        "ARM_I4_blindspot_texture": pm.arm_I4(),
        "ARM_R": pm.arm_R(),
        "ARM_K3_scale_x4": {"I1": pm.arm_I1(scale=4, q=4.0),
                            "I2": pm.arm_I2(scale=4, q=4.0),
                            "I3": pm.arm_I3(scale=4, q=4.0),
                            "R": pm.arm_R(scale=4, q=4.0)},
        "ARM_F1_noise_floor": pm.arm_F1(),
        "ARM_F2_texture_floor": pm.arm_F2(),
        "ARM_F3_offday": pm.arm_F3(),
    }
    mismatches = []
    for k, v in fresh.items():
        if _canon(v) != _canon(pinned[k]):
            mismatches.append(k)
    return {"arms_compared": sorted(fresh.keys()),
            "mismatched_arms": mismatches,
            "IDENTICAL": bool(not mismatches),
            "shipped_pdecay_default": _shipped_pdecay()}


def _shipped_pdecay():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_paint"])
    p = list(s.nodes("PaintParams"))[0]
    return float(s.node(p)["attrs"]["pdecay"])


# --------------------------------------------------------------------------- #
#  G1 — the SINGLE-EDGE geometry. ARM 1 (sign) and ARM 2 (the decline).
# --------------------------------------------------------------------------- #
def _cornsweet_run(flat, pdecay):
    lum, lf, rf, cusp, n = stim_cornsweet_w(flat)
    s, h = run_decay(lum, pdecay=pdecay)
    left, right = (3, 0), (3, n - 1)
    pl = pw.cell_attr(s, h, left, "ppaint_lum")
    pr = pw.cell_attr(s, h, right, "ppaint_lum")
    # ARM 2's ruler is the STIMULUS's geometry, never the mechanism's `pdist`:
    # a diagnostic must not be computed by the component it checks.
    prof_l = [{"col": c, "dist_from_cusp": cusp - c,
               "induction": pw.cell_attr(s, h, (3, c), "ppaint_lum") - 100.0}
              for c in range(flat)]
    prof_r = [{"col": c, "dist_from_cusp": c - (cusp + 1),
               "induction": pw.cell_attr(s, h, (3, c), "ppaint_lum") - 100.0}
              for c in range(n - flat, n)]
    for p in (prof_l, prof_r):
        p.sort(key=lambda d: d["dist_from_cusp"])
    return {
        "flat_width": flat, "n_cols": n,
        "physical_left": float(lum[left]), "physical_right": float(lum[right]),
        "painted_left": pl, "painted_right": pr, "difference": pl - pr,
        "hub_left": dw.hub_for(s, h, left), "hub_right": dw.hub_for(s, h, right),
        "n_regions": len(pw.hubs(s, h)),
        "panchor_row3": [float(v) for v in dw.field_of(s, h, "panchor")[3]],
        "painted_profile_row3": [round(float(v), 6) for v in
                                 dw.field_of(s, h, "ppaint_lum")[3]],
        "pdist_row3": [float(v) for v in dw.field_of(s, h, "pdist")[3]],
        "induction_left": prof_l, "induction_right": prof_r,
    }


def _strictly_declining(prof):
    """|induction| strictly decreasing as distance from the edge grows, and no
    sign change within the (physically uniform) far field."""
    a = [abs(p["induction"]) for p in prof]          # already sorted by distance
    sgn = [np.sign(p["induction"]) for p in prof]
    return {"abs_by_distance": [round(float(v), 6) for v in a],
            "distances": [p["dist_from_cusp"] for p in prof],
            "strictly_declining": bool(all(a[i] > a[i + 1] for i in range(len(a) - 1))),
            "no_sign_change": bool(len(set(s for s in sgn if s != 0)) <= 1)}


def arm_1_and_2():
    base = _cornsweet_run(6, 0.0)
    dec = _cornsweet_run(6, 1.0)
    out = {"baseline_pdecay_off": base, "decay_pdecay_on": dec}
    out["ARM1"] = {
        "difference_off": base["difference"], "difference_on": dec["difference"],
        "korder_left": dec["hub_left"]["korder"],
        "korder_right": dec["hub_right"]["korder"],
        "SIGN_CORRECT": bool(dec["difference"] > 0.0),
        "ESCALATED": bool(dec["hub_left"]["korder"] == 2.0
                          and dec["hub_right"]["korder"] == 2.0),
    }
    out["ARM1"]["PASS"] = bool(out["ARM1"]["SIGN_CORRECT"] and out["ARM1"]["ESCALATED"])
    on_l = _strictly_declining(dec["induction_left"])
    on_r = _strictly_declining(dec["induction_right"])
    off_l = _strictly_declining(base["induction_left"])
    off_r = _strictly_declining(base["induction_right"])
    out["ARM2"] = {
        "decay_left": on_l, "decay_right": on_r,
        "baseline_left": off_l, "baseline_right": off_r,
        "PASS": bool(on_l["strictly_declining"] and on_r["strictly_declining"]
                     and on_l["no_sign_change"] and on_r["no_sign_change"]),
        "BASELINE_PASS": bool(off_l["strictly_declining"] and off_r["strictly_declining"]
                              and off_l["no_sign_change"] and off_r["no_sign_change"]),
    }
    # The closed form the pre-registration derived: plam = d_max/2 for a
    # one-sided region, so the far-edge weight is EXACTLY 1/3 whatever the width.
    hl = dec["hub_left"]
    out["CLOSED_FORM"] = {
        "plam": hl["plam"], "d_max": max(dec["pdist_row3"][:6] + [0.0]),
        "far_weight": hl["plam"] / (hl["plam"] + 9.0) if hl["plam"] else 0.0,
        "predicted_one_third": 1.0 / 3.0,
        "slope": hl["pslope_c_plum"],
        "far_excursion_undamped": hl["pslope_c_plum"] * 4.5,
        "mean_minus_physical": hl["pmean_lum"] - 100.0,
        "inversion_needs_slope_h_over": 3.0 * (hl["pmean_lum"] - 100.0),
    }
    return out


# --------------------------------------------------------------------------- #
#  ARM 3 — the residual arm, re-measured with the decay ON
# --------------------------------------------------------------------------- #
def _region_summary(s, h):
    rows = dw.region_report(s, h)
    big = rows[0] if rows else {}
    ncell = sum(r["pnall"] for r in rows) or 1.0
    refuted_area = sum(r["pnall"] for r in rows if r["prefuted"] > 0.5)
    return {
        "n_regions": len(rows),
        "largest_region_cells": big.get("pnall", 0.0),
        "largest_korder": big.get("korder", 0.0),
        "largest_prefuted": big.get("prefuted", 0.0),
        "largest_presid_mean": big.get("presid_mean", 0.0),
        "largest_panch_n": big.get("panch_n", 0.0),
        "largest_plam": big.get("plam", 0.0),
        "largest_slope_c": big.get("pslope_c_plum", 0.0),
        "refuted_area_fraction": refuted_area / ncell,
        "mean_cell_residual": float(np.mean(dw.field_of(s, h, "presid_lum"))),
        "any_region_refuted": bool(any(r["prefuted"] > 0.5 for r in rows)),
    }


def arm_3(seed=69600, pdecay=1.0, q=1.0):
    n = 12
    rng = random.Random(seed)
    out = {}
    s, h = run_decay(np.full((n, n), 100.0), pdecay=pdecay, pquant=q)
    out["R1_uniform"] = _region_summary(s, h)
    grad = np.tile(np.arange(n, dtype=float) * 3.0 + 50.0, (n, 1))
    s, h = run_decay(grad, pdecay=pdecay, pquant=q)
    out["R2_gradient"] = _region_summary(s, h)
    s, h = run_decay(pm.texture(rng, n, n), pdecay=pdecay, pquant=q)
    out["R3_texture"] = _region_summary(s, h)
    u, g, t = out["R1_uniform"], out["R2_gradient"], out["R3_texture"]
    out["R4_contrast"] = {
        "texture_minus_uniform_mean_residual":
            t["mean_cell_residual"] - u["mean_cell_residual"],
        "texture_refuted": t["any_region_refuted"],
        "uniform_refuted": u["any_region_refuted"],
    }
    out["PASS"] = bool(
        u["n_regions"] == 1 and u["largest_korder"] == 1.0
        and u["any_region_refuted"] is False and u["mean_cell_residual"] == 0.0
        and g["n_regions"] == 1 and g["largest_korder"] == 2.0
        and g["any_region_refuted"] is False and g["mean_cell_residual"] == 0.0
        and abs(g["largest_slope_c"] - 3.0) < 1e-12
        and t["largest_korder"] == 2.0 and t["any_region_refuted"] is True
        and t["refuted_area_fraction"] > 0.9
        and t["mean_cell_residual"] >= q / 2.0 and t["n_regions"] < 10
        and t["mean_cell_residual"] > u["mean_cell_residual"])
    return out


def arm_3_F1(pdecay=1.0):
    """n=100, seeds 69000-69099. Random luminance, ZERO chroma anywhere."""
    worst, bad = 0.0, 0
    for i in range(100):
        rng = random.Random(69000 + i)
        s, h = run_decay(pm.texture(rng, 8, 8), np.zeros((8, 8)), pdecay=pdecay)
        m = float(np.max(np.abs(dw.field_of(s, h, "ppaint_app"))))
        worst = max(worst, m)
        bad += 1 if m != 0.0 else 0
    return {"n": 100, "seeds": "69000-69099",
            "n_fields_inventing_appearance": bad, "max_abs_painted_app": worst,
            "PASS": bool(bad == 0)}


def arm_3_F2(pdecay=1.0):
    """n=100, seeds 69100-69199."""
    hits, areas, regions, resids = 0, [], [], []
    for i in range(100):
        rng = random.Random(69100 + i)
        s, h = run_decay(pm.texture(rng, 12, 12), pdecay=pdecay)
        d = _region_summary(s, h)
        hits += 1 if d["any_region_refuted"] else 0
        areas.append(d["refuted_area_fraction"])
        regions.append(d["n_regions"])
        resids.append(d["mean_cell_residual"])
    return {"n": 100, "seeds": "69100-69199",
            "fraction_any_region_refuted": hits / 100.0,
            "mean_refuted_area_fraction": float(np.mean(areas)),
            "mean_n_regions": float(np.mean(regions)),
            "mean_cell_residual": float(np.mean(resids)),
            "PASS": bool(hits / 100.0 > 0.9 and float(np.mean(regions)) < 10)}


# --------------------------------------------------------------------------- #
#  ARM 3b — R5, the cost probe. Diagnostic, NOT a pass/fail arm.
# --------------------------------------------------------------------------- #
def arm_3b_R5():
    lum = stim_bounded_ramp()
    out = {}
    for tag, d in (("pdecay_off", 0.0), ("pdecay_on", 1.0)):
        s, h = run_decay(lum, pdecay=d)
        rows = dw.region_report(s, h)
        mid = dw.hub_for(s, h, (3, 7))          # inside the ramp compartment
        out[tag] = {
            "n_regions": len(rows),
            "ramp_region": mid,
            "painted_row3": [round(float(v), 6) for v in
                             dw.field_of(s, h, "ppaint_lum")[3]],
            "pdist_row3": [float(v) for v in dw.field_of(s, h, "pdist")[3]],
            "presid_row3": [round(float(v), 6) for v in
                            dw.field_of(s, h, "presid_lum")[3]],
        }
    out["true_ramp_row3"] = [float(v) for v in lum[3]]
    a, b = out["pdecay_off"]["ramp_region"], out["pdecay_on"]["ramp_region"]
    out["FIT_UNCHANGED"] = bool(a["pslope_c_plum"] == b["pslope_c_plum"] == 3.0)
    out["RENDERING_DAMPED"] = bool(b["presid_mean"] > a["presid_mean"])
    out["REFUTED_off_on"] = [a["prefuted"], b["prefuted"]]
    out["REGRESSES"] = bool(b["prefuted"] > a["prefuted"]
                            or b["presid_mean"] > a["presid_mean"])
    return out


def arm_3b_blindspot(seed=69500):
    """Reported only. The blind-spot hole under the decay."""
    rng = random.Random(seed)
    lum, sensed, hole = pm.stim_blindspot(rng)
    out = {}
    for tag, d in (("pdecay_off", 0.0), ("pdecay_on", 1.0)):
        s, h = run_decay(lum, None, sensed, pdecay=d)
        vals = np.array([pw.cell_attr(s, h, rc, "ppaint_lum") for rc in hole])
        true = np.array([lum[rc] for rc in hole])
        out[tag] = {"fill_var": float(np.var(vals)),
                    "true_surround_var": float(np.var(true)),
                    "fill_var_over_true": float(np.var(vals)) / float(np.var(true)),
                    "n_regions": len(pw.hubs(s, h))}
    out["seed"] = seed
    out["n_hole"] = len(hole)
    return out


# --------------------------------------------------------------------------- #
#  G2 — the CUMULATIVE geometry. MEASURED, NOT GATED, NOT POOLED WITH G1.
# --------------------------------------------------------------------------- #
def arm_G2():
    lum, plateaus = stim_cumulative()
    out = {"plateau_cells": [list(p) for p in plateaus],
           "physical_at_plateaus": [float(lum[p]) for p in plateaus]}
    for tag, d in (("pdecay_off", 0.0), ("pdecay_on", 1.0)):
        s, h = run_decay(lum, pdecay=d)
        vals = [pw.cell_attr(s, h, p, "ppaint_lum") for p in plateaus]
        rows = dw.region_report(s, h)
        out[tag] = {
            "painted_at_plateaus": [round(float(v), 6) for v in vals],
            "n_regions": len(rows),
            "region_means": sorted(round(r["pmean_lum"], 6) for r in rows),
            "spread_across_plateaus": float(max(vals) - min(vals)),
            "monotone_decreasing": bool(all(vals[i] > vals[i + 1]
                                            for i in range(len(vals) - 1))),
            "monotone_increasing": bool(all(vals[i] < vals[i + 1]
                                            for i in range(len(vals) - 1))),
            "ALL_EQUAL": bool(max(vals) - min(vals) < 1e-12),
        }
    out["NOTE"] = ("1-D Cornsweet sawtooth, NOT Cavanagh & Anstis's 2-D diamond "
                   "stimulus. Reported, never pooled with G1, never gated.")
    return out


# --------------------------------------------------------------------------- #
#  ARM B — BOUNDS. Three fixed widths. Does NOT move the verdict (§8).
# --------------------------------------------------------------------------- #
def arm_B():
    out = {}
    for wdt in (3, 6, 12):
        off = _cornsweet_run(wdt, 0.0)
        on = _cornsweet_run(wdt, 1.0)
        prof = _strictly_declining(on["induction_left"])
        out["flat_%d" % wdt] = {
            "difference_off": off["difference"], "difference_on": on["difference"],
            "sign_correct_on": bool(on["difference"] > 0.0),
            "sign_correct_off": bool(off["difference"] > 0.0),
            "plam": on["hub_left"]["plam"], "slope": on["hub_left"]["pslope_c_plum"],
            "mean": on["hub_left"]["pmean_lum"],
            "declining_left": prof["strictly_declining"],
            "far_weight": (on["hub_left"]["plam"]
                           / (on["hub_left"]["plam"] + (wdt + 3.0))),
        }
    out["ALL_WIDTHS_CORRECT_SIGN_ON"] = bool(
        all(v["sign_correct_on"] for v in out.values() if isinstance(v, dict)))
    out["ALL_WIDTHS_INVERTED_OFF"] = bool(
        all(not v["sign_correct_off"] for v in out.values() if isinstance(v, dict)))
    return out


# --------------------------------------------------------------------------- #
#  ARM P — the paint rung's own positives, under the decay. Reported.
# --------------------------------------------------------------------------- #
def arm_P():
    out = {}
    lum, app, far, ind = pm.stim_neon()
    for tag, d in (("pdecay_off", 0.0), ("pdecay_on", 1.0)):
        s, h = run_decay(lum, app, pdecay=d)
        out.setdefault("I1_neon", {})[tag] = {
            "ppaint_app_at_far_cell": pw.cell_attr(s, h, far, "ppaint_app"),
            "observed_app_at_far_cell": pw.cell_attr(s, h, far, "papp"),
            "hub": dw.hub_for(s, h, far)}
    lum, app, mid = pm.stim_watercolour()
    for tag, d in (("pdecay_off", 0.0), ("pdecay_on", 1.0)):
        s, h = run_decay(lum, app, pdecay=d)
        v = pw.cell_attr(s, h, mid, "ppaint_app")
        out.setdefault("I2_watercolour", {})[tag] = {
            "ppaint_app_at_interior": v,
            "takes_INNER_sign": bool(v > 0), "takes_OUTER_sign": bool(v < 0),
            "hub": dw.hub_for(s, h, mid)}
    out["I1_PRESERVED"] = bool(
        out["I1_neon"]["pdecay_on"]["ppaint_app_at_far_cell"]
        == out["I1_neon"]["pdecay_off"]["ppaint_app_at_far_cell"])
    out["I2_STILL_INNER"] = bool(out["I2_watercolour"]["pdecay_on"]["takes_INNER_sign"])
    return out


# --------------------------------------------------------------------------- #
def main():
    out = {"provenance": provenance_line()}
    out["ARM_V_vacuity"] = arm_V()                       # FIRST (§13.2)
    out["ARM_V2_byte_identity"] = arm_V2_byte_identity()
    out["G1_ARM1_ARM2"] = arm_1_and_2()
    out["ARM_3_residual"] = arm_3()
    out["ARM_3_F1_noise_floor"] = arm_3_F1()
    out["ARM_3_F2_texture_floor"] = arm_3_F2()
    out["ARM_3b_R5_bounded_ramp"] = arm_3b_R5()
    out["ARM_3b_blindspot"] = arm_3b_blindspot()
    out["G2_cumulative"] = arm_G2()
    out["ARM_B_bounds"] = arm_B()
    out["ARM_P_paint_positives"] = arm_P()
    out["VERDICT"] = {
        "ARM1_sign": out["G1_ARM1_ARM2"]["ARM1"]["PASS"],
        "ARM2_decline": out["G1_ARM1_ARM2"]["ARM2"]["PASS"],
        "ARM3_residual": bool(out["ARM_3_residual"]["PASS"]
                              and out["ARM_3_F1_noise_floor"]["PASS"]
                              and out["ARM_3_F2_texture_floor"]["PASS"]),
    }
    out["VERDICT"]["CONJUNCTION"] = bool(all(out["VERDICT"].values()))
    path = os.path.join(HERE, "results", "decay_measure.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(out["VERDICT"], indent=1, sort_keys=True))
    print("\nwrote", path)


if __name__ == "__main__":
    main()
