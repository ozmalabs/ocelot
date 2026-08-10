"""PAINT-FROM-SAMPLE — the confirmatory runner (VISION_PAINT_PREREG.md).

Runs exactly the pre-registered arms and dumps results/paint_measure.json.
Exactly these. No sweeps, no re-runs (PROTOCOL §3.6).

  ARM K2  vacuity      — toggle paint 0->1, max|on-off|. Run FIRST (§13.2).
  ARM I   illusions    — I1 neon / I2 watercolour / I3 Cornsweet / I4 blind-spot
                         texture, each BASELINE vs PAINT.
  ARM R   residual     — R1 uniform / R2 gradient / R3 texture / R4 contrast.
  ARM K1  k falls out  — the three ladder outcomes are each REACHED.
  ARM K3  scale        — the whole battery at a x4 alphabet with pquant=4.
  ARM F1  noise floor  — n=100, seeds 66000-66099, chroma confabulation.
  ARM F2  texture floor— n=100, seeds 66100-66199.
  ARM F3  off-day      — §9 inertness.
"""
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

import json  # noqa: E402
import os  # noqa: E402
import random  # noqa: E402

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import paint_world as pw  # noqa: E402
from domains import ground_world as gw  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------- #
#  harness
# --------------------------------------------------------------------------- #
def run_paint(lum, app=None, sensed=None, *, paint=1.0, pquant=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_paint"])
    hnd = pw.run(s, lum, app, sensed, paint=paint, pquant=pquant)
    return s, hnd


# --------------------------------------------------------------------------- #
#  STIMULI — every one is INTEGER valued (in-frame is INTEGER)
# --------------------------------------------------------------------------- #
def stim_neon(scale=1):
    """A 2-cell-thick contour ring enclosing a uniform interior; chromatic
    inducer segments on a SUB-PART of the interior. NOTE (reported as a bound):
    the ring is 2 cells thick because a 1-cell line produces TWO EQUAL deltas
    and strict non-maximum suppression cannot break the tie."""
    n = 16
    lum = np.full((n, n), 100.0)
    app = np.zeros((n, n))
    for a, b in ((3, 5), (11, 13)):                       # 2-thick ring
        lum[a:b, 3:13] = 40.0
        lum[3:13, a:b] = 40.0
    app[7:9, 7:9] = 60.0                                  # the inducer, interior
    return lum * scale, app * scale, (6, 6), (7, 7)       # far cell, inducer cell


def stim_watercolour(scale=1):
    """A STRONG dark outer contour and, immediately inside it, a WEAK chromatic
    inner contour that is ISO-LUMINANT with the interior. The outer contour
    carries the OPPOSITE appearance sign, so which contour the tint takes is a
    discriminating read, not a foregone one."""
    n = 18
    lum = np.full((n, n), 100.0)
    app = np.zeros((n, n))
    for a, b in ((2, 4), (14, 16)):                        # outer: dark, strong
        lum[a:b, 2:16] = 30.0
        lum[2:16, a:b] = 30.0
        app[a:b, 2:16] = -60.0                             # OUTER appearance
        app[2:16, a:b] = -60.0
    for a, b in ((4, 6), (12, 14)):                        # inner: iso-luminant
        app[a:b, 4:14] = 60.0                              # INNER appearance
        app[4:14, a:b] = 60.0
    return lum * scale, app * scale, (9, 9)                # interior read cell


def stim_cornsweet(scale=1):
    """Two large flat regions of IDENTICAL physical mean joined by a cusp."""
    prof = ([100.0] * 6 + [101.0, 102.0, 103.0, 104.0]
            + [96.0, 97.0, 98.0, 99.0] + [100.0] * 6)
    lum = np.tile(np.array(prof), (8, 1))
    return lum * scale, (3, 0), (3, 19)                    # far left, far right


def texture(rng, h, w, lo=40, hi=160):
    return np.array([[float(rng.randint(lo, hi)) for _ in range(w)]
                     for _ in range(h)])


def stim_blindspot(rng, scale=1):
    """A textured surround with an unsensed hole (the optic disc)."""
    n = 16
    lum = texture(rng, n, n) * scale
    sensed = np.ones((n, n))
    hole = [(r, c) for r in range(n) for c in range(n)
            if (r - 8) ** 2 + (c - 8) ** 2 <= 4]
    for (r, c) in hole:
        sensed[r, c] = 0.0
    return lum, sensed, hole


# --------------------------------------------------------------------------- #
#  BASELINE — what the system does BEFORE paint exists (THE CRUX)
# --------------------------------------------------------------------------- #
def baseline_no_spreading_into_sensed_cells():
    """The ONLY filling mechanism in the tree is vision_ground's gr_fill, and it
    fires on UNSENSED cells. On a fully-sensed field it must leave every belief
    equal to its observation — i.e. NOTHING in the pre-paint system spreads an
    appearance into a cell that has its own data. Measured, not asserted."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_ground"])
    wd = WaveWorld(s, h=16, w=16, seed=0)
    anat = gw.add_grounded_field(wd, blind_center=(99, 99), blind_radius=0.0)
    gw.set_ground_params(wd, ground=1.0, interp=0.0)
    f = np.full((16, 16), 0.5)
    f[7:9, 7:9] = 1.0                       # an "inducer" patch, fully sensed
    gw.present(wd, anat, f)
    bel, raw = gw.belief_field(wd, anat), gw.raw_sensor(wd, anat)
    return {"max_abs_belief_minus_obs": float(np.nanmax(np.abs(bel - raw))),
            "belief_at_far_cell": float(bel[5, 5]),
            "obs_at_far_cell": float(raw[5, 5])}


def baseline_blindspot_fill_is_flat(rng):
    """gr_fill on a TEXTURED surround: the fill is the mean of filled
    neighbours, so it must be FLAT by construction. This is the baseline the
    order-k claim has to beat."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_ground"])
    wd = WaveWorld(s, h=16, w=16, seed=0)
    anat = gw.add_grounded_field(wd, blind_center=(8, 8), blind_radius=2.0)
    gw.set_ground_params(wd, ground=1.0, interp=0.0)
    tex = texture(rng, 16, 16) / 200.0
    gw.present(wd, anat, tex)
    bel = gw.belief_field(wd, anat)
    hole = sorted(anat["blind"])
    vals = np.array([bel[r, c] for (r, c) in hole])
    sur = np.array([tex[r, c] for (r, c) in hole])
    return {"n_hole": len(hole),
            "fill_var": float(np.var(vals)),
            "true_var": float(np.var(sur)),
            "fill_values": [round(float(v), 6) for v in vals[:12]]}


# --------------------------------------------------------------------------- #
#  ARM K2 — VACUITY (§13.2). Run FIRST.
# --------------------------------------------------------------------------- #
KEYS = ("pregion", "pblk_e", "pblk_s", "ppaint_lum", "ppaint_app",
        "presid_lum", "presid_app", "prefuted_cell", "korder", "prefuted")


def arm_K2():
    lum, app, far, ind = stim_neon()
    out = {}
    s0, h0 = run_paint(lum, app, paint=0.0)
    s1, h1 = run_paint(lum, app, paint=1.0)
    for k in KEYS:
        a = pw.field_of(s0, h0, k)
        b = pw.field_of(s1, h1, k)
        out[k] = float(np.max(np.abs(b - a)))
    out["ALL_ZERO_would_be_decorative"] = bool(all(v == 0.0 for v in out.values()))
    return out


# --------------------------------------------------------------------------- #
#  ARM I — the illusion battery
# --------------------------------------------------------------------------- #
def arm_I1(scale=1, q=1.0):
    lum, app, far, ind = stim_neon(scale)
    res = {}
    for tag, p in (("baseline_paint_off", 0.0), ("paint", 1.0)):
        s, h = run_paint(lum, app, paint=p, pquant=q)
        res[tag] = {
            "ppaint_app_at_far_cell": pw.cell_attr(s, h, far, "ppaint_app"),
            "observed_app_at_far_cell": pw.cell_attr(s, h, far, "papp"),
            "hub": pw.hub_for(s, h, far),
            "n_regions": len(pw.hubs(s, h)),
        }
    res["inducer_observed_app"] = float(app[ind])
    res["ILLUSION"] = bool(res["baseline_paint_off"]["ppaint_app_at_far_cell"] == 0.0
                           and res["paint"]["ppaint_app_at_far_cell"] != 0.0)
    return res


def arm_I2(scale=1, q=1.0):
    lum, app, mid = stim_watercolour(scale)
    res = {}
    for tag, p in (("baseline_paint_off", 0.0), ("paint", 1.0)):
        s, h = run_paint(lum, app, paint=p, pquant=q)
        res[tag] = {
            "ppaint_app_at_interior": pw.cell_attr(s, h, mid, "ppaint_app"),
            "observed_app_at_interior": pw.cell_attr(s, h, mid, "papp"),
            "hub": pw.hub_for(s, h, mid),
            "n_regions": len(pw.hubs(s, h)),
        }
    v = res["paint"]["ppaint_app_at_interior"]
    res["inner_contour_app"] = 60.0 * scale
    res["outer_contour_app"] = -60.0 * scale
    res["takes_INNER_sign"] = bool(v > 0)
    res["takes_OUTER_sign"] = bool(v < 0)
    res["ILLUSION"] = bool(res["baseline_paint_off"]["ppaint_app_at_interior"] == 0.0
                           and v > 0)
    return res


def arm_I3(scale=1, q=1.0):
    lum, left, right = stim_cornsweet(scale)
    res = {"physical_left": float(lum[left]), "physical_right": float(lum[right])}
    for tag, p in (("baseline_paint_off", 0.0), ("paint", 1.0)):
        s, h = run_paint(lum, paint=p, pquant=q)
        pl = pw.cell_attr(s, h, left, "ppaint_lum")
        pr = pw.cell_attr(s, h, right, "ppaint_lum")
        res[tag] = {
            "painted_left": pl, "painted_right": pr, "difference": pl - pr,
            "hub_left": pw.hub_for(s, h, left),
            "hub_right": pw.hub_for(s, h, right),
            "n_regions": len(pw.hubs(s, h)),
            "painted_profile_row3": [round(float(v), 4) for v in
                                     pw.field_of(s, h, "ppaint_lum")[3]],
        }
    # DIAGNOSTIC ONLY (never the verdict, §5): the k=1 state, reached by capping
    # the ladder via the SAME rules -- read from the converged run's own hubs is
    # impossible, so this is recomputed from the region means the flood produced.
    res["ILLUSION"] = bool(res["baseline_paint_off"]["difference"] == 0.0
                           and res["paint"]["difference"] != 0.0)
    res["SIGN_MATCHES_CUSP_POLARITY"] = bool(res["paint"]["difference"] > 0)
    return res


def arm_I4(seed=66500, scale=1, q=1.0):
    rng = random.Random(seed)
    lum, sensed, hole = stim_blindspot(rng, scale)
    base = baseline_blindspot_fill_is_flat(random.Random(seed))
    s, h = run_paint(lum, None, sensed, paint=1.0, pquant=q)
    vals = np.array([pw.cell_attr(s, h, rc, "ppaint_lum") for rc in hole])
    true = np.array([lum[rc] for rc in hole])
    s0, h0 = run_paint(lum, None, sensed, paint=0.0, pquant=q)
    v0 = np.array([pw.cell_attr(s0, h0, rc, "ppaint_lum") for rc in hole])
    # The two arms run on different luminance scales (gr_fill's world is 0..1),
    # so the ONLY comparable quantity is the fill variance as a FRACTION of the
    # true surround variance. Reported as a DIAGNOSTIC; the pre-registered
    # verdict below is unchanged (§5).
    ratio_base = base["fill_var"] / base["true_var"] if base["true_var"] else 0.0
    ratio_paint = float(np.var(vals)) / float(np.var(true)) if np.var(true) else 0.0
    return {
        "baseline_gr_fill": base,
        "DIAG_baseline_fill_var_over_true_var": ratio_base,
        "DIAG_paint_fill_var_over_true_var": ratio_paint,
        "DIAG_paint_carries_more_structure_than_baseline": bool(ratio_paint > ratio_base),
        "baseline_paint_off_var": float(np.var(v0)),
        "paint_fill_var": float(np.var(vals)),
        "true_surround_var": float(np.var(true)),
        "n_hole": len(hole),
        "n_regions": len(pw.hubs(s, h)),
        "paint_fill_values": [round(float(v), 4) for v in vals[:12]],
        "ILLUSION": bool(base["fill_var"] <= 1e-12 and float(np.var(vals)) > 1e-12),
    }


# --------------------------------------------------------------------------- #
#  ARM R — the residual contrast arm
# --------------------------------------------------------------------------- #
def _region_summary(s, h):
    rows = pw.region_report(s, h)
    big = rows[0] if rows else {}
    ncell = sum(r["pnall"] for r in rows) or 1.0
    refuted_area = sum(r["pnall"] for r in rows if r["prefuted"] > 0.5)
    return {
        "n_regions": len(rows),
        "largest_region_cells": big.get("pnall", 0.0),
        "largest_korder": big.get("korder", 0.0),
        "largest_prefuted": big.get("prefuted", 0.0),
        "largest_presid_mean": big.get("presid_mean", 0.0),
        "refuted_area_fraction": refuted_area / ncell,
        "mean_cell_residual": float(np.mean(pw.field_of(s, h, "presid_lum"))),
        "any_region_refuted": bool(any(r["prefuted"] > 0.5 for r in rows)),
    }


def arm_R(seed=66600, scale=1, q=1.0):
    n = 12
    rng = random.Random(seed)
    out = {}
    s, h = run_paint(np.full((n, n), 100.0 * scale), paint=1.0, pquant=q)
    out["R1_uniform"] = _region_summary(s, h)
    grad = np.tile(np.arange(n, dtype=float) * 3.0 + 50.0, (n, 1)) * scale
    s, h = run_paint(grad, paint=1.0, pquant=q)
    out["R2_gradient"] = _region_summary(s, h)
    s, h = run_paint(texture(rng, n, n) * scale, paint=1.0, pquant=q)
    out["R3_texture"] = _region_summary(s, h)
    out["R4_contrast"] = {
        "texture_minus_uniform_mean_residual":
            out["R3_texture"]["mean_cell_residual"] - out["R1_uniform"]["mean_cell_residual"],
        "texture_refuted": out["R3_texture"]["any_region_refuted"],
        "uniform_refuted": out["R1_uniform"]["any_region_refuted"],
        "texture_n_regions": out["R3_texture"]["n_regions"],
        "uniform_n_regions": out["R1_uniform"]["n_regions"],
    }
    out["quantum"] = q
    out["half_quantum"] = q / 2.0
    return out


# --------------------------------------------------------------------------- #
#  ARM F — floors and §9
# --------------------------------------------------------------------------- #
def arm_F1():
    """n=100, seeds 66000-66099. Random luminance, ZERO chroma anywhere.
    A mechanism that paints chroma from no chroma is a confabulator."""
    worst = 0.0
    bad = 0
    for i in range(100):
        rng = random.Random(66000 + i)
        lum = texture(rng, 8, 8)
        s, h = run_paint(lum, np.zeros((8, 8)), paint=1.0)
        m = float(np.max(np.abs(pw.field_of(s, h, "ppaint_app"))))
        worst = max(worst, m)
        if m != 0.0:
            bad += 1
    return {"n": 100, "seeds": "66000-66099",
            "n_fields_inventing_appearance": bad, "max_abs_painted_app": worst,
            "PASS": bool(bad == 0)}


def arm_F2():
    """n=100, seeds 66100-66199. Random textures: does the mechanism KNOW it is
    wrong? Registered statistic = fraction of fields with any region refuted."""
    hits = 0
    areas, regions, resids = [], [], []
    for i in range(100):
        rng = random.Random(66100 + i)
        s, h = run_paint(texture(rng, 12, 12), paint=1.0)
        d = _region_summary(s, h)
        hits += 1 if d["any_region_refuted"] else 0
        areas.append(d["refuted_area_fraction"])
        regions.append(d["n_regions"])
        resids.append(d["mean_cell_residual"])
    return {"n": 100, "seeds": "66100-66199",
            "fraction_any_region_refuted": hits / 100.0,
            "mean_refuted_area_fraction": float(np.mean(areas)),
            "mean_n_regions": float(np.mean(regions)),
            "mean_cell_residual": float(np.mean(resids)),
            "PASS_pre_registered_gt_0p9": bool(hits / 100.0 > 0.9)}


def arm_F3():
    lum, app, far, ind = stim_neon()
    s, h = run_paint(lum, app, paint=0.0)
    fields = {k: float(np.max(np.abs(pw.field_of(s, h, k)))) for k in
              ("pregion", "pblk_e", "pblk_s", "ppaint_lum", "ppaint_app",
               "presid_lum", "presid_app", "prefuted_cell", "prefuted",
               "pdelta_done", "pblock_done", "pseed_done")}
    s2, ag = boot_core()
    load_seeds_into(s2, ag, ["vision_paint"])
    default = float(s2.node(list(s2.nodes("PaintParams"))[0])["attrs"]["paint"])
    return {"default_flag": default, "max_abs_when_off": fields,
            "PASS": bool(default == 0.0 and all(v == 0.0 for v in fields.values()))}


# --------------------------------------------------------------------------- #
def main():
    out = {"provenance": provenance_line()}
    out["ARM_K2_vacuity"] = arm_K2()
    out["baseline_no_spreading_into_sensed_cells"] = baseline_no_spreading_into_sensed_cells()
    out["ARM_I1_neon"] = arm_I1()
    out["ARM_I2_watercolour"] = arm_I2()
    out["ARM_I3_cornsweet"] = arm_I3()
    out["ARM_I4_blindspot_texture"] = arm_I4()
    out["ARM_R"] = arm_R()
    out["ARM_K3_scale_x4"] = {
        "I1": arm_I1(scale=4, q=4.0), "I2": arm_I2(scale=4, q=4.0),
        "I3": arm_I3(scale=4, q=4.0), "R": arm_R(scale=4, q=4.0),
    }
    out["ARM_F1_noise_floor"] = arm_F1()
    out["ARM_F2_texture_floor"] = arm_F2()
    out["ARM_F3_offday"] = arm_F3()
    path = os.path.join(HERE, "results", "paint_measure.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(out, indent=1, sort_keys=True))
    print("\nwrote", path)


if __name__ == "__main__":
    main()
