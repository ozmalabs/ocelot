"""parallax_measure — CONFIRMATORY measurement for rung 116000.

Runs ONLY the arms listed in VISION_PARALLAX_PREREG.md §5, on FRESH seeds
116000-116079. Prints engine provenance FROM INSIDE the process and aborts on
divergence (§10). No wall-clock quantity is a verdict; loadavg recorded.
"""
from __future__ import annotations
import sys, os, json, time
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
from parallax_char import make_scene, group_common_fate, field_discontinuity, vector_field, SQRT5
from domains.engine_provenance import provenance_line, engine_preamble
engine_preamble()
from substrate.boot_core import boot_core, load_seeds_into
import domains.motion_group_world as mgw

EXPECT_ENGINE = "e039d2eec2dd"
N_CONF = 80
CONF_BASE = 116000            # fresh confirmatory seeds 116000..116079


def _assert_engine(tag):
    line = provenance_line()
    assert EXPECT_ENGINE in line, f"[{tag}] engine mismatch: {line}"
    return line


def eff_count(sizes):
    p = np.asarray(sizes, float); p = p / p.sum()
    return float(1.0 / np.sum(p * p))


def _ci(x):
    x = np.asarray(x, float)
    bs = [np.mean(np.random.default_rng(k).choice(x, len(x))) for k in range(1000)]
    return [float(np.mean(x)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def numpy_arm(shifts, block, grid, tau, ref_idx):
    """Sensed-field common-fate grouping over the confirmatory seeds."""
    acc = {c: {"eff": [], "lgst": [], "count": [], "median": [],
               "ref_resid_gt": [], "ref_resid_se": [], "sensor_err": [], "disc_gt": []}
           for c in ("DEPTH", "FLAT")}
    top = {"DEPTH": [], "FLAT": []}
    for i in range(N_CONF):
        rng = np.random.default_rng(CONF_BASE + i)
        sc = make_scene(rng, shifts, block, grid=grid, ref_idx=ref_idx)
        delta = np.array([0.0, float(shifts[ref_idx])])
        for cond, bk, tk in (("DEPTH", "b_depth", "t_depth"), ("FLAT", "b_flat", "t_flat")):
            V = vector_field(sc["a"], sc[bk], block)
            t = sc[tk]
            R_se = V - delta                       # efference-copy subtraction (exact integers)
            R_gt = t - delta
            lab, nl = group_common_fate(R_se, tau)
            sizes = sorted([(lab == k).sum() for k in range(nl)], reverse=True)
            acc[cond]["eff"].append(eff_count(sizes))
            acc[cond]["lgst"].append(sizes[0] / lab.size)
            acc[cond]["count"].append(nl)
            acc[cond]["median"].append(float(np.median(sizes)))
            padded = [s / lab.size for s in sizes[:5]] + [0.0] * 5
            top[cond].append(padded[:5])
            refmask = (sc["owner"] == ref_idx) if cond == "DEPTH" else np.ones_like(sc["owner"], bool)
            acc[cond]["ref_resid_gt"].append(float(np.abs(R_gt[refmask]).max()))
            acc[cond]["ref_resid_se"].append(float(np.abs(R_se[refmask]).max()))
            acc[cond]["sensor_err"].append(float(np.abs(V - t).max()))
            acc[cond]["disc_gt"].append(field_discontinuity(R_gt))
    out = {"shifts": shifts, "block": block, "grid": grid, "tau": tau, "ref_idx": ref_idx,
           "cells": (grid // block) ** 2}
    for cond in ("DEPTH", "FLAT"):
        a = acc[cond]
        out[cond] = {
            "eff_surfaces": _ci(a["eff"]), "largest_frac": _ci(a["lgst"]),
            "count": _ci(a["count"]), "median": _ci(a["median"]),
            "top5_frac_mean": np.round(np.mean(top[cond], 0), 4).tolist(),
            "ref_resid_gt_max": float(np.max(a["ref_resid_gt"])),
            "ref_resid_se_max": float(np.max(a["ref_resid_se"])),
            "sensor_err_max": float(np.max(a["sensor_err"])),
            "disc_gt_mean": float(np.mean(a["disc_gt"])),
        }
    return out


def graph_arm(shifts, block, grid, ref_idx, seeds):
    """Graph-runtime: default-OFF byte-identity, ARMED load-bearing, FLAT null,
    space constancy — via the parallax_efference seed."""
    delta = [0.0, float(shifts[ref_idx])]
    rows = []
    for sd in seeds:
        rng = np.random.default_rng(sd); sc = make_scene(rng, shifts, block, grid=grid, ref_idx=ref_idx)
        row = {"seed": sd}
        for cond, bk in (("DEPTH", "b_depth"), ("FLAT", "b_flat")):
            V = vector_field(sc["a"], sc[bk], block)

            def run(load_mine, arm):
                s, ag = boot_core()
                load_seeds_into(s, ag, ["vision_motion_group", "parallax_efference"] if load_mine
                                else ["vision_motion_group"])
                h = mgw.add_mfield(s, V)
                if load_mine:
                    for p in s.nodes("MotionParams"):
                        s.set_attr(p, "mo_efference", 1.0 if arm else 0.0)
                    if arm:
                        s.set_attr(h["field"], "efference_v", delta)
                mgw.settle(s, marm=1.0, mcontrast=1.0, mtol_exact=0.0)
                objs = mgw.objects(s)
                dom = tuple(float(x) for x in (mgw.field_attr(s, h, "dom_v") or (0, 0)))
                key = sorted((int(o["root"]), int(o["members"]),
                              (float(o["v"][0]), float(o["v"][1]))) for o in objs)
                return key, dom, mgw.assert_settled(s, h)["unsettled_pairs"]

            base_key, base_dom, base_un = run(False, False)
            off_key, off_dom, off_un = run(True, False)
            arm_key, arm_dom, arm_un = run(True, True)
            # armed surfaces (>=5 cells) velocities
            arm_surf = sorted([(v0, v1) for (_r, m, (v0, v1)) in arm_key if m >= 5])
            row[cond] = {
                "default_off_identical": (off_key == base_key),
                "baseline_dom": base_dom, "armed_dom": arm_dom,
                "load_bearing_D": int(off_key != arm_key),   # armed differs from disarmed?
                "armed_nobj": len(arm_key), "armed_surfaces": arm_surf,
                "unsettled": {"base": base_un, "off": off_un, "arm": arm_un},
            }
        rows.append(row)
    return rows


def main():
    t0 = time.time()
    prov = _assert_engine("start")
    load0 = os.getloadavg()

    # exact-to-pixel efference subtraction + byte-identical static-frame checks
    rng = np.random.default_rng(CONF_BASE)
    sc = make_scene(rng, [0, 3, 6], 8, grid=144, ref_idx=1)
    R_gt = sc["t_depth"] - np.array([0.0, 3.0])
    refmask = sc["owner"] == 1
    exact_zero = float(np.abs(R_gt[refmask]).max())
    a = sc["a"]; edges = sc["edges"]; gx = np.abs(np.diff(a, axis=1))
    bnd = float(np.mean([gx[:, c - 1] for c in edges[1:-1]])); within = float(np.mean(gx))

    res = {
        "provenance": prov, "expect_engine": EXPECT_ENGINE,
        "n_conf": N_CONF, "conf_seeds": [CONF_BASE, CONF_BASE + N_CONF - 1],
        "loadavg_start": load0,
        "efference_subtraction_exact_to_pixel": {
            "reference_band_residual_max_groundtruth": exact_zero,
            "note": "R = V - delta in exact integer arithmetic; reference-plane residual is EXACTLY 0 (space constancy).",
        },
        "byte_identical_static_frame": {
            "band_boundary_gradient": bnd, "within_band_gradient": within,
            "note": "bands INVISIBLE in the static frame `a`; `a` is one array shared by DEPTH and FLAT.",
        },
        "arms": {},
    }

    # PRIMARY + secondary numpy arms
    for name, (shifts, block, grid, ref) in {
        "primary_N3_block8": ([0, 3, 6], 8, 144, 1),
        "secondary_N2_block8": ([0, 4], 8, 144, 0),
        "inherited_bound_N3_block4": ([0, 2, 4], 4, 72, 1),
    }.items():
        res["arms"][name] = {}
        for tau, tname in ((0.0, "exact0"), (SQRT5, "sqrt5")):
            res["arms"][name][tname] = numpy_arm(shifts, block, grid, tau, ref)

    # GRAPH-RUNTIME arm (subset of seeds for the boot cost)
    _assert_engine("pre-graph")
    res["graph_runtime"] = graph_arm([0, 3, 6], 8, 144, 1, list(range(CONF_BASE, CONF_BASE + 20)))

    res["loadavg_end"] = os.getloadavg()
    res["wall_s"] = time.time() - t0
    res["provenance_after"] = provenance_line()
    res["provenance_stable"] = (res["provenance_after"] == prov)
    _assert_engine("end")

    outp = os.path.join(_ROOT, "results", "parallax.json")
    with open(outp, "w") as f:
        json.dump(res, f, indent=1)
    print("WROTE", outp)
    print("provenance:", prov, "stable:", res["provenance_stable"])
    print("loadavg start/end:", load0, res["loadavg_end"], "wall_s:", round(res["wall_s"], 1))
    print("space constancy (GT ref-band residual max):", exact_zero)
    print("static-frame band-boundary grad vs within:", round(bnd, 2), round(within, 2))
    for name in res["arms"]:
        for tname in res["arms"][name]:
            d = res["arms"][name][tname]["DEPTH"]; f = res["arms"][name][tname]["FLAT"]
            print(f"  {name}/{tname}: DEPTH eff={d['eff_surfaces'][0]:.2f}{d['eff_surfaces'][1:3]} "
                  f"lgst={d['largest_frac'][0]:.3f}{d['largest_frac'][1:3]} top5={d['top5_frac_mean']} "
                  f"|| FLAT eff={f['eff_surfaces'][0]:.2f}{f['eff_surfaces'][1:3]} "
                  f"lgst={f['largest_frac'][0]:.3f} disc_gt={f['disc_gt_mean']:.2f} "
                  f"ref_resid_se={d['ref_resid_se_max']:.1f} serr={d['sensor_err_max']:.0f}")
    g = res["graph_runtime"]
    off_ok = all(r["DEPTH"]["default_off_identical"] and r["FLAT"]["default_off_identical"] for r in g)
    lb = np.mean([r["DEPTH"]["load_bearing_D"] for r in g])
    flat0 = np.mean([r["FLAT"]["armed_nobj"] for r in g])
    print(f"  graph: default_off_identical(all)={off_ok}  load_bearing_D(mean)={lb:.2f}  FLAT_armed_nobj(mean)={flat0:.2f}")


if __name__ == "__main__":
    main()
