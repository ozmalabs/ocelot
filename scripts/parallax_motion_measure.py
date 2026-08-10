"""parallax_motion_measure — CONFIRMATORY measurement for rung 125000.

Does the parallax carve survive real MOTION? Displacement FALLS OUT of depth +
camera motion via perspective projection (not a hand-set shift). Runs ONLY the
arms in VISION_PARALLAX_MOTION_PREREG.md on FRESH seeds 125000-125079. Prints
engine provenance FROM INSIDE the process and aborts on divergence (§10). No
wall-clock quantity is a verdict; loadavg recorded.

  python scripts/parallax_motion_measure.py pilot     # burned 116000-116039
  python scripts/parallax_motion_measure.py confirm    # fresh 125000-125079
"""
from __future__ import annotations
import sys, os, json, time
_HERE = os.path.dirname(os.path.abspath(__file__)); _ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE); sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
import numpy as np
from parallax_motion_char import (make_projected_scene, carve, SQRT5,
                                  STAGE_A_BASE, STAGE_A_DEPTHS, STAGE_A_REF)
from parallax_real_char import make_real_scene, bsds_paths
from parallax_char import group_common_fate
from domains.motion_group_world import vector_field
from domains.engine_provenance import provenance_line, engine_preamble, engine_provenance
engine_preamble()

BASE, DEPTHS, REF = STAGE_A_BASE, STAGE_A_DEPTHS, STAGE_A_REF   # [300,10,5], base 30 -> shifts [0,3,6]
BLOCK, GRID = 8, 144
Z0_SINGLE = 7.5                 # single slanted plane, d0 = base/Z0 = 4 px
TILTS = [0.0, 0.2, 0.4, 0.6, 0.8]
TILTS3 = [0.0, 0.2, 0.4, 0.6]
ROTS = [0.0, 0.02, 0.04, 0.08]


def _assert_engine(tag):
    line = provenance_line()
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), f"[{tag}] source_match={p['source_match']}: {line}"
    return line


def eff_count(sizes):
    p = np.asarray(sizes, float); p = p / p.sum()
    return float(1.0 / np.sum(p * p))


def _ci(x):
    x = np.asarray(x, float)
    bs = [np.mean(np.random.default_rng(k).choice(x, len(x))) for k in range(1000)]
    return [float(np.mean(x)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def carve_windowed(sc, tau):
    """The windowed-slide baseline carve (make_real_scene dict), reused verbatim."""
    delta = np.array([0.0, float(sc["shifts"][sc["ref_idx"]])])
    V = vector_field(sc["a"], sc["b_depth"], sc["block"])
    lab, nl = group_common_fate(V - delta, tau)
    sizes = sorted([(lab == k).sum() for k in range(nl)], reverse=True)
    return eff_count(sizes), sizes[0] / lab.size


def agg_carve(scene_fn, seeds, taus=(0.0, SQRT5)):
    """Run carve over seeds; return per-tau aggregates (eff CI, largest CI,
    depth_order rate, confab, per-block step, byte-identity if a comparator scene)."""
    per = {t: {"eff": [], "lgst": [], "dok": [], "rho": [], "confab": [],
               "step": [], "wbs": [], "refres": []} for t in taus}
    for sd in seeds:
        sc = scene_fn(sd)
        step = float(np.abs(np.diff(sc["s_col"][::BLOCK])).max()) if len(set(sc["s_col"].tolist())) > 1 else 0.0
        for t in taus:
            r = carve(sc, t)
            per[t]["eff"].append(r["eff"]); per[t]["lgst"].append(r["largest"])
            per[t]["dok"].append(1.0 if r["depth_order_correct"] else 0.0)
            per[t]["rho"].append(r["depth_rank_rho"]); per[t]["confab"].append(r["confab_rate"])
            per[t]["step"].append(step); per[t]["wbs"].append(r["within_block_step_max"])
            per[t]["refres"].append(r["ref_resid_se"])
    out = {}
    for t in taus:
        d = per[t]
        out["t0" if t == 0.0 else "s5"] = {
            "eff": _ci(d["eff"]), "largest": _ci(d["lgst"]),
            "depth_order_rate": float(np.mean(d["dok"])),
            "depth_rank_rho_mean": float(np.mean(d["rho"])),
            "confab_rate": _ci(d["confab"]),
            "per_block_step_max": float(np.max(d["step"])),
            "within_block_step_max": float(np.max(d["wbs"])),
            "ref_resid_se_max": float(np.max(d["refres"])),
        }
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "confirm"
    if mode == "pilot":
        seeds = list(range(116000, 116040)); outname = "parallax_motion_pilot.json"
    else:
        seeds = list(range(125000, 125080)); outname = "parallax_motion.json"

    t0 = time.time()
    prov = _assert_engine("start"); load0 = os.getloadavg()
    paths = bsds_paths()
    res = {"mode": mode, "provenance": prov, "seeds": [seeds[0], seeds[-1]], "n": len(seeds),
           "base": BASE, "depths": DEPTHS, "ref_idx": REF, "block": BLOCK, "grid": GRID,
           "loadavg_start": load0, "sqrt5": SQRT5,
           "n_bsds_train": len(paths)}

    # ---- BASELINE floor re-earn: windowed slide [0,3,6] ----
    wperf = {t: [] for t in ("t0", "s5")}
    for sd in seeds:
        sw = make_real_scene(np.random.default_rng(sd), [0, 3, 6], BLOCK, GRID, 1, paths, select="random")
        for tau, tn in ((0.0, "t0"), (SQRT5, "s5")):
            wperf[tn].append(carve_windowed(sw, tau)[0])
    res["baseline_windowed"] = {tn: _ci(v) for tn, v in wperf.items()}

    # ---- BYTE-IDENTITY: projected fronto-parallel == windowed slide ----
    bi = []
    for sd in seeds:
        sp = make_projected_scene(np.random.default_rng(sd), DEPTHS, BASE, BLOCK, GRID, 1, paths)
        sw = make_real_scene(np.random.default_rng(sd), [0, 3, 6], BLOCK, GRID, 1, paths, select="random")
        bi.append(bool(np.array_equal(sp["a"], sw["a"]) and np.array_equal(sp["b"], sw["b_depth"])))
    res["byte_identity_projected_vs_windowed"] = {"all_true": bool(all(bi)), "n_true": int(sum(bi))}

    _assert_engine("mid")

    # ---- STAGE A: projected motion vs static control ----
    res["A1_motion"] = agg_carve(
        lambda sd: make_projected_scene(np.random.default_rng(sd), DEPTHS, BASE, BLOCK, GRID, 1, paths), seeds)
    res["A2_static"] = agg_carve(
        lambda sd: make_projected_scene(np.random.default_rng(sd), DEPTHS, 0.0, BLOCK, GRID, 1, paths), seeds)

    # ---- STAGE B1: single slanted plane, sweep tilt ----
    res["B1_single_slant"] = {}
    for tilt in TILTS:
        res["B1_single_slant"][f"tilt_{tilt}"] = agg_carve(
            lambda sd, tl=tilt: make_projected_scene(np.random.default_rng(sd), [Z0_SINGLE], BASE,
                                                     BLOCK, GRID, 0, paths, tilt=tl, tilt_bands=(0,)), seeds)

    # ---- STAGE B2: 3 planes, middle slanted, sweep tilt ----
    res["B2_three_slant"] = {}
    for tilt in TILTS3:
        res["B2_three_slant"][f"tilt_{tilt}"] = agg_carve(
            lambda sd, tl=tilt: make_projected_scene(np.random.default_rng(sd), DEPTHS, BASE,
                                                     BLOCK, GRID, 1, paths, tilt=tl, tilt_bands=(1,)),
            seeds, taus=(SQRT5,))

    # ---- STAGE B3: translation + rotation ----
    res["B3_trans_rot"] = {}
    for rot in ROTS:
        res["B3_trans_rot"][f"rot_{rot}"] = agg_carve(
            lambda sd, rt=rot: make_projected_scene(np.random.default_rng(sd), DEPTHS, BASE,
                                                    BLOCK, GRID, 1, paths, rot=rt), seeds, taus=(SQRT5,))

    # ---- STAGE B4: pure rotation (no depth) ----
    res["B4_pure_rot"] = {}
    for rot in ROTS:
        res["B4_pure_rot"][f"rot_{rot}"] = agg_carve(
            lambda sd, rt=rot: make_projected_scene(np.random.default_rng(sd), DEPTHS, 0.0,
                                                    BLOCK, GRID, 1, paths, rot=rt), seeds)

    res["loadavg_end"] = os.getloadavg(); res["wall_s"] = time.time() - t0
    res["provenance_after"] = provenance_line()
    res["provenance_stable"] = (res["provenance_after"] == prov)
    res["source_match"] = engine_provenance()["source_match"]
    _assert_engine("end")

    outp = os.path.join(_ROOT, "results", outname)
    with open(outp, "w") as f:
        json.dump(res, f, indent=1)
    print("WROTE", outp, "| mode", mode)
    print("provenance:", prov, "stable:", res["provenance_stable"], "source_match:", res["source_match"])
    print("loadavg start/end:", load0, res["loadavg_end"], "wall_s:", round(res["wall_s"], 1))
    print(f"byte_identity projected==windowed: {res['byte_identity_projected_vs_windowed']}")
    for tn in ("t0", "s5"):
        a1 = res["A1_motion"][tn]; a2 = res["A2_static"][tn]; wb = res["baseline_windowed"][tn]
        print(f"  [{tn}] baseline_windowed eff={wb[0]:.2f} | A1 eff={a1['eff'][0]:.2f}{a1['eff'][1:3]} "
              f"lgst={a1['largest'][0]:.3f} depth_order={a1['depth_order_rate']:.2f} "
              f"| A2 static eff={a2['eff'][0]:.2f}")
    print("  B1 single slant (eff t0 / eff s5 / per_block_step):")
    for tilt in TILTS:
        b = res["B1_single_slant"][f"tilt_{tilt}"]
        print(f"    tilt={tilt}: t0 eff={b['t0']['eff'][0]:.2f} | s5 eff={b['s5']['eff'][0]:.2f}"
              f"{b['s5']['eff'][1:3]} step={b['s5']['per_block_step_max']:.0f}")
    print("  B2 three-plane middle slant (eff s5 / depth_order):")
    for tilt in TILTS3:
        b = res["B2_three_slant"][f"tilt_{tilt}"]["s5"]
        print(f"    tilt={tilt}: eff={b['eff'][0]:.2f}{b['eff'][1:3]} depth_order={b['depth_order_rate']:.2f}")
    print("  B3 translation+rotation (eff s5 / depth_order):")
    for rot in ROTS:
        b = res["B3_trans_rot"][f"rot_{rot}"]["s5"]
        print(f"    rot={rot}: eff={b['eff'][0]:.2f}{b['eff'][1:3]} depth_order={b['depth_order_rate']:.2f}")
    print("  B4 pure rotation (eff t0 / eff s5):")
    for rot in ROTS:
        b = res["B4_pure_rot"][f"rot_{rot}"]
        print(f"    rot={rot}: t0 eff={b['t0']['eff'][0]:.2f} s5 eff={b['s5']['eff'][0]:.2f}")


if __name__ == "__main__":
    main()
